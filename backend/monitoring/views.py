from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from common.permissions import IsAuthenticatedInOrg, IsManager
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


class ActivityFeedView(APIView):
    """Manager view: one employee's day of activity, grouped into readable blocks.

    Consecutive samples on the same application are merged into a single block
    with a time span and the active minutes within it, so a manager sees a
    timeline (e.g. '09:10–09:48  Chrome  · project dashboard  · 36 min active')
    rather than dozens of one-minute rows.
    """
    permission_classes = [IsAuthenticatedInOrg, IsManager]

    def get(self, request):
        import datetime
        from collections import Counter
        from django.utils import timezone
        from accounts.models import User

        u = request.user
        user_id = request.query_params.get("user")
        date_str = request.query_params.get("date")
        if not user_id or not date_str:
            raise ValidationError("Both 'user' and 'date' are required.")
        try:
            d = datetime.date.fromisoformat(date_str)
        except ValueError:
            raise ValidationError("date must be YYYY-MM-DD.")

        # employee must belong to the manager's organization
        try:
            emp = User.objects.get(id=user_id, organization_id=u.organization_id)
        except (User.DoesNotExist, ValueError, TypeError):
            raise ValidationError("Unknown employee.")

        tz = timezone.get_current_timezone()
        start = timezone.make_aware(datetime.datetime(d.year, d.month, d.day, 0, 0), tz)
        end = start + datetime.timedelta(days=1)
        samples = list(ActivitySample.objects.filter(
            organization_id=u.organization_id, user_id=emp.id,
            captured_at__gte=start, captured_at__lt=end,
        ).order_by("captured_at"))

        blocks = []
        cur = None
        for s in samples:
            local = timezone.localtime(s.captured_at)
            app = s.app or "(unknown)"
            if cur and cur["_app"] == app:
                cur["end"] = local.strftime("%H:%M")
                cur["active_minutes"] += s.minutes
                if s.window_title:
                    cur["_titles"].append(s.window_title)
            else:
                if cur:
                    blocks.append(cur)
                cur = {
                    "_app": app, "app": app,
                    "start": local.strftime("%H:%M"), "end": local.strftime("%H:%M"),
                    "active_minutes": s.minutes,
                    "_titles": [s.window_title] if s.window_title else [],
                }
        if cur:
            blocks.append(cur)

        # finalize: pick a representative window title, drop internals
        for b in blocks:
            titles = [t for t in b.pop("_titles") if t]
            b.pop("_app", None)
            b["window_title"] = Counter(titles).most_common(1)[0][0] if titles else ""

        # day summary: total active minutes and the top apps by active minutes
        app_totals = Counter()
        total_active = 0
        for s in samples:
            total_active += s.minutes
            app_totals[s.app or "(unknown)"] += s.minutes
        top_apps = [{"app": a, "active_minutes": m} for a, m in app_totals.most_common(8)]

        return Response({
            "employee": {"id": emp.id, "name": emp.full_name or emp.email},
            "date": date_str,
            "total_active_minutes": total_active,
            "top_apps": top_apps,
            "blocks": blocks,
        })
