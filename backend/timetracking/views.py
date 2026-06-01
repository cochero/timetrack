from django.utils import timezone
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from common.permissions import IsAuthenticatedInOrg, MANAGER_ROLES
from .models import TimeEntry, TimeLog
from .serializers import TimeEntrySerializer


class TimeEntryViewSet(viewsets.ModelViewSet):
    """Employees see/create their own time; managers see everyone's in the org."""
    serializer_class = TimeEntrySerializer
    permission_classes = [IsAuthenticatedInOrg]

    def get_queryset(self):
        u = self.request.user
        qs = (TimeEntry.objects.filter(organization_id=u.organization_id)
              .select_related("project", "client", "user"))
        if u.role not in MANAGER_ROLES:
            qs = qs.filter(user=u)
        p = self.request.query_params
        if p.get("client"): qs = qs.filter(client_id=p["client"])
        if p.get("project"): qs = qs.filter(project_id=p["project"])
        if p.get("user") and u.role in MANAGER_ROLES: qs = qs.filter(user_id=p["user"])
        if p.get("date_from"): qs = qs.filter(entry_date__gte=p["date_from"])
        if p.get("date_to"): qs = qs.filter(entry_date__lte=p["date_to"])
        if p.get("status"): qs = qs.filter(status=p["status"])
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, organization_id=self.request.user.organization_id)


# ---------- Live timer ----------

def _serialize_active(log):
    return {
        "id": log.id,
        "project": log.project_id,
        "project_name": log.project.name,
        "client_name": log.client.name,
        "started_at": log.started_at.isoformat(),
        "is_billable": log.is_billable,
    }


def _finalize(log):
    """Stop a running session and add its minutes to that day's TimeEntry."""
    now = timezone.now()
    log.ended_at = now
    minutes = max(0, int((now - log.started_at).total_seconds() // 60))
    entry = None
    if minutes > 0:
        entry_date = timezone.localtime(log.started_at).date()
        entry = TimeEntry.objects.filter(
            organization_id=log.organization_id, user=log.user,
            project=log.project, entry_date=entry_date,
        ).first()
        if entry:
            entry.minutes = entry.minutes + minutes
            entry.save(update_fields=["minutes"])
        else:
            entry = TimeEntry.objects.create(
                organization_id=log.organization_id, user=log.user,
                project=log.project, client_id=log.client_id,
                entry_date=entry_date, minutes=minutes, is_billable=log.is_billable,
            )
        log.time_entry = entry
    log.save(update_fields=["ended_at", "time_entry"])
    return {
        "minutes": minutes,
        "project_name": log.project.name,
        "entry_total_minutes": entry.minutes if entry else 0,
        "discarded": minutes == 0,
    }


class TimerActiveView(APIView):
    permission_classes = [IsAuthenticatedInOrg]

    def get(self, request):
        log = (TimeLog.objects
               .filter(organization_id=request.user.organization_id, user=request.user, ended_at__isnull=True)
               .select_related("project", "client").first())
        return Response({"active": _serialize_active(log) if log else None})


class TimerStartView(APIView):
    permission_classes = [IsAuthenticatedInOrg]

    def post(self, request):
        from projects.models import Project
        pid = request.data.get("project")
        try:
            project = Project.objects.get(id=pid, organization_id=request.user.organization_id)
        except (Project.DoesNotExist, ValueError, TypeError):
            raise ValidationError("Please choose a valid project.")
        # auto-stop any session already running (so you can switch tasks cleanly)
        for running in TimeLog.objects.filter(
            organization_id=request.user.organization_id, user=request.user, ended_at__isnull=True
        ):
            _finalize(running)
        log = TimeLog.objects.create(
            organization_id=request.user.organization_id, user=request.user,
            project=project, client_id=project.client_id,
            started_at=timezone.now(), is_billable=project.is_billable,
        )
        return Response(_serialize_active(log), status=201)


class TimerStopView(APIView):
    permission_classes = [IsAuthenticatedInOrg]

    def post(self, request):
        log = (TimeLog.objects
               .filter(organization_id=request.user.organization_id, user=request.user, ended_at__isnull=True)
               .select_related("project", "client").first())
        if not log:
            raise ValidationError("No timer is running.")
        return Response(_finalize(log))
