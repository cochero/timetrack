from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from common.permissions import IsAuthenticatedInOrg
from timetracking.models import TimeEntry
from .models import ActivitySample


class HeartbeatView(APIView):
    """
    The desktop agent posts here every interval. Fields:
      activity_type : WORK | INTERNAL_MEETING | CLIENT_MEETING  (default WORK)
      project       : project id            (WORK)
      client        : client id             (CLIENT_MEETING)
      description    : meeting topic/notes  (meetings)
      entry_id      : the meeting entry to keep adding to (returned on first tick)
      minutes, active, app, window_title

    WORK minutes roll into that day's single project entry. Meeting minutes add
    to one dedicated entry per meeting (tracked via entry_id), so each meeting
    keeps its own description.
    """
    permission_classes = [IsAuthenticatedInOrg]

    def post(self, request):
        from projects.models import Project
        from clients.models import Client
        u = request.user
        data = request.data

        activity = data.get("activity_type", "WORK")
        if activity not in ("WORK", "INTERNAL_MEETING", "CLIENT_MEETING"):
            activity = "WORK"

        active = bool(data.get("active", True))
        try:
            minutes = int(data.get("minutes", 0))
        except (ValueError, TypeError):
            minutes = 0
        minutes = max(0, min(minutes, 60))
        app = str(data.get("app", ""))[:255]
        window_title = str(data.get("window_title", ""))[:512]
        description = str(data.get("description", ""))[:2000]

        project = None
        if activity == "WORK" and data.get("project"):
            try:
                project = Project.objects.get(id=data["project"], organization_id=u.organization_id)
            except (Project.DoesNotExist, ValueError, TypeError):
                raise ValidationError("Unknown project.")

        client = None
        if activity == "CLIENT_MEETING":
            try:
                client = Client.objects.get(id=data.get("client"), organization_id=u.organization_id)
            except (Client.DoesNotExist, ValueError, TypeError):
                raise ValidationError("Unknown client.")

        ActivitySample.objects.create(
            organization_id=u.organization_id, user=u, project=project,
            captured_at=timezone.now(), app=app, window_title=window_title,
            active=active, minutes=minutes if active else 0,
        )

        logged, entry_id = 0, data.get("entry_id")
        if active and minutes > 0:
            entry_date = timezone.localtime().date()
            entry = None

            if activity == "WORK" and project:
                entry = TimeEntry.objects.filter(
                    organization_id=u.organization_id, user=u, project=project,
                    activity_type="WORK", entry_date=entry_date,
                ).first()
                if not entry:
                    entry = TimeEntry(
                        organization_id=u.organization_id, user=u, project=project,
                        client_id=project.client_id, entry_date=entry_date,
                        minutes=0, is_billable=project.is_billable, activity_type="WORK",
                    )
            elif activity in ("INTERNAL_MEETING", "CLIENT_MEETING"):
                if entry_id:
                    entry = TimeEntry.objects.filter(
                        id=entry_id, organization_id=u.organization_id, user=u,
                        activity_type=activity,
                    ).first()
                if not entry:
                    entry = TimeEntry(
                        organization_id=u.organization_id, user=u, entry_date=entry_date,
                        minutes=0, activity_type=activity, description=description,
                        client=client if activity == "CLIENT_MEETING" else None,
                    )

            if entry is not None:
                entry.minutes = (entry.minutes or 0) + minutes
                entry.save()
                logged, entry_id = minutes, entry.id

        return Response({"ok": True, "logged_minutes": logged, "entry_id": entry_id})
