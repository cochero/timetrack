from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from common.permissions import IsAuthenticatedInOrg
from timetracking.models import TimeEntry
from .models import ActivitySample


class HeartbeatView(APIView):
    """
    The desktop agent posts here every interval with:
      project (id), minutes, active (bool), app, window_title
    Active minutes for a chosen project are added to that day's hours.
    """
    permission_classes = [IsAuthenticatedInOrg]

    def post(self, request):
        from projects.models import Project
        u = request.user
        data = request.data

        project = None
        pid = data.get("project")
        if pid:
            try:
                project = Project.objects.get(id=pid, organization_id=u.organization_id)
            except (Project.DoesNotExist, ValueError, TypeError):
                raise ValidationError("Unknown project.")

        active = bool(data.get("active", True))
        try:
            minutes = int(data.get("minutes", 0))
        except (ValueError, TypeError):
            minutes = 0
        minutes = max(0, min(minutes, 60))   # one heartbeat can't be more than an hour
        app = str(data.get("app", ""))[:255]
        window_title = str(data.get("window_title", ""))[:512]

        ActivitySample.objects.create(
            organization_id=u.organization_id, user=u, project=project,
            captured_at=timezone.now(), app=app, window_title=window_title,
            active=active, minutes=minutes if active else 0,
        )

        logged = 0
        if active and minutes > 0 and project:
            entry_date = timezone.localtime().date()
            entry = TimeEntry.objects.filter(
                organization_id=u.organization_id, user=u, project=project, entry_date=entry_date
            ).first()
            if entry:
                entry.minutes += minutes
                entry.save(update_fields=["minutes"])
            else:
                entry = TimeEntry.objects.create(
                    organization_id=u.organization_id, user=u, project=project,
                    client_id=project.client_id, entry_date=entry_date,
                    minutes=minutes, is_billable=project.is_billable,
                )
            logged = minutes

        return Response({"ok": True, "logged_minutes": logged})
