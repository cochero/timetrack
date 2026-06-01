import datetime

from django.db.models import Sum, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from common.permissions import IsAuthenticatedInOrg, IsManager
from timetracking.models import TimeEntry


def _hours(minutes):
    return round((minutes or 0) / 60, 2)


class BaseReportView(APIView):
    """Shared logic for all reports: manager-only, with a date range filter."""
    permission_classes = [IsAuthenticatedInOrg, IsManager]

    def date_range(self, request):
        """Defaults to the current month if no range is given. Format: YYYY-MM-DD."""
        today = datetime.date.today()
        df = request.query_params.get("date_from")
        dt = request.query_params.get("date_to")
        try:
            date_from = datetime.date.fromisoformat(df) if df else today.replace(day=1)
            date_to = datetime.date.fromisoformat(dt) if dt else today
        except ValueError:
            raise ValidationError("Dates must be in YYYY-MM-DD format")
        return date_from, date_to

    def base_qs(self, request):
        df, dt = self.date_range(request)
        qs = TimeEntry.objects.filter(
            organization_id=request.user.organization_id,
            entry_date__gte=df,
            entry_date__lte=dt,
        )
        return qs, df, dt


class HoursByClientView(BaseReportView):
    """Total hours logged for each client in the period."""
    def get(self, request):
        qs, df, dt = self.base_qs(request)
        rows = (
            qs.values("client_id", "client__name")
            .annotate(
                total=Sum("minutes"),
                billable=Sum("minutes", filter=Q(is_billable=True)),
            )
            .order_by("-total")
        )
        results = [{
            "client_id": r["client_id"],
            "client": r["client__name"],
            "total_hours": _hours(r["total"]),
            "billable_hours": _hours(r["billable"]),
        } for r in rows]
        return Response({"date_from": df, "date_to": dt, "results": results})


class HoursByEmployeeView(BaseReportView):
    """Total hours each employee logged in the period."""
    def get(self, request):
        qs, df, dt = self.base_qs(request)
        rows = (
            qs.values("user_id", "user__full_name", "user__email")
            .annotate(
                total=Sum("minutes"),
                billable=Sum("minutes", filter=Q(is_billable=True)),
            )
            .order_by("-total")
        )
        results = [{
            "user_id": r["user_id"],
            "employee": r["user__full_name"] or r["user__email"],
            "total_hours": _hours(r["total"]),
            "billable_hours": _hours(r["billable"]),
        } for r in rows]
        return Response({"date_from": df, "date_to": dt, "results": results})


class HoursByProjectView(BaseReportView):
    """Total hours per project, with its client, in the period."""
    def get(self, request):
        qs, df, dt = self.base_qs(request)
        rows = (
            qs.values("project_id", "project__name", "client__name")
            .annotate(
                total=Sum("minutes"),
                billable=Sum("minutes", filter=Q(is_billable=True)),
            )
            .order_by("-total")
        )
        results = [{
            "project_id": r["project_id"],
            "project": r["project__name"],
            "client": r["client__name"],
            "total_hours": _hours(r["total"]),
            "billable_hours": _hours(r["billable"]),
        } for r in rows]
        return Response({"date_from": df, "date_to": dt, "results": results})


class UtilizationView(BaseReportView):
    """
    Actual hours worked vs. available capacity per employee.
    Capacity assumes an 8-hour workday on weekdays in the period.
    'allocated_percentage' is how much of the person is assigned to clients.
    """
    def get(self, request):
        from allocations.models import Allocation
        from accounts.models import User

        qs, df, dt = self.base_qs(request)
        org_id = request.user.organization_id

        # actual minutes worked per user
        actual = {
            r["user_id"]: r["total"]
            for r in qs.values("user_id").annotate(total=Sum("minutes"))
        }

        # working days (Mon-Fri) in range -> capacity
        working_days = 0
        d = df
        while d <= dt:
            if d.weekday() < 5:
                working_days += 1
            d += datetime.timedelta(days=1)
        capacity_minutes = working_days * 8 * 60

        # gather employees: anyone with an active allocation or logged time
        users = {}
        active_allocs = (
            Allocation.objects.filter(organization_id=org_id, is_active=True)
            .select_related("user")
        )
        for a in active_allocs:
            row = users.setdefault(a.user_id, {
                "user_id": a.user_id,
                "employee": a.user.full_name or a.user.email,
                "allocated_percentage": 0,
            })
            row["allocated_percentage"] += a.allocation_percentage

        missing = [uid for uid in actual if uid not in users]
        for u in User.objects.filter(id__in=missing):
            users[u.id] = {
                "user_id": u.id,
                "employee": u.full_name or u.email,
                "allocated_percentage": 0,
            }

        results = []
        for uid, info in users.items():
            worked = actual.get(uid, 0) or 0
            util = round(worked / capacity_minutes * 100, 1) if capacity_minutes else 0
            results.append({
                **info,
                "actual_hours": _hours(worked),
                "capacity_hours": _hours(capacity_minutes),
                "utilization_percentage": util,
            })
        results.sort(key=lambda x: -x["utilization_percentage"])

        return Response({
            "date_from": df, "date_to": dt,
            "working_days": working_days,
            "capacity_hours": _hours(capacity_minutes),
            "results": results,
        })


class BillingExportView(BaseReportView):
    """
    Per-client billing summary for the period (managers only).
    Uses the rate SNAPSHOT stored on each time entry, so it reflects the
    rates that applied when the work was done.

    Per client it returns:
      - billable_hours / amount  (what you invoice the client)
      - cost                     (what those hours cost the firm)
      - margin                   (amount - cost)
      - unrated_hours            (billable hours that had no rate set)
    Optional filter: ?client=<id>
    """
    def get(self, request):
        qs, df, dt = self.base_qs(request)
        client_filter = request.query_params.get("client")
        if client_filter:
            qs = qs.filter(client_id=client_filter)
        qs = qs.select_related("client")

        groups = {}
        for e in qs:
            g = groups.setdefault(e.client_id, {
                "client_id": e.client_id,
                "client": e.client.name,
                "currency": e.client.billing_currency,
                "billable_hours": 0.0,
                "amount": 0.0,
                "cost": 0.0,
                "unrated_hours": 0.0,
            })
            hours = e.minutes / 60
            if e.is_billable:
                g["billable_hours"] += hours
                if e.bill_rate is not None:
                    g["amount"] += hours * float(e.bill_rate)
                else:
                    g["unrated_hours"] += hours
            if e.cost_rate is not None:
                g["cost"] += hours * float(e.cost_rate)

        results, t_amount, t_cost, t_hours, t_unrated = [], 0.0, 0.0, 0.0, 0.0
        for g in groups.values():
            g["billable_hours"] = round(g["billable_hours"], 2)
            g["amount"] = round(g["amount"], 2)
            g["cost"] = round(g["cost"], 2)
            g["margin"] = round(g["amount"] - g["cost"], 2)
            g["unrated_hours"] = round(g["unrated_hours"], 2)
            results.append(g)
            t_amount += g["amount"]; t_cost += g["cost"]
            t_hours += g["billable_hours"]; t_unrated += g["unrated_hours"]
        results.sort(key=lambda x: -x["amount"])

        return Response({
            "date_from": df, "date_to": dt,
            "results": results,
            "totals": {
                "billable_hours": round(t_hours, 2),
                "amount": round(t_amount, 2),
                "cost": round(t_cost, 2),
                "margin": round(t_amount - t_cost, 2),
                "unrated_hours": round(t_unrated, 2),
            },
        })
