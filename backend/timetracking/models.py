from django.conf import settings
from django.db import models
from common.models import OrgScopedModel


class Timesheet(OrgScopedModel):
    """A wrapper around one person's time entries for a period (e.g. a week),
    used for the submit -> approve workflow."""

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        SUBMITTED = "SUBMITTED", "Submitted"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="timesheets"
    )
    period_start = models.DateField()
    period_end = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="approved_timesheets",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    total_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-period_start"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "period_start", "period_end"],
                name="uniq_timesheet_period",
            )
        ]

    def __str__(self):
        return f"{self.user} {self.period_start}..{self.period_end}"


class TimeEntry(OrgScopedModel):
    """One block of logged time: who, which client/project, which day, how long."""

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    class Activity(models.TextChoices):
        WORK = "WORK", "Project work"
        BREAK = "BREAK", "Break"
        INTERNAL_MEETING = "INTERNAL_MEETING", "Internal meeting"
        CLIENT_MEETING = "CLIENT_MEETING", "Client meeting"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="time_entries"
    )
    activity_type = models.CharField(max_length=20, choices=Activity.choices, default=Activity.WORK)
    # project is required for WORK, empty for breaks/meetings
    project = models.ForeignKey(
        "projects.Project", null=True, blank=True, on_delete=models.PROTECT, related_name="time_entries"
    )
    # client: copied from project for WORK, chosen directly for a CLIENT_MEETING,
    # and empty for breaks / internal meetings.
    client = models.ForeignKey(
        "clients.Client", null=True, blank=True, on_delete=models.PROTECT, related_name="time_entries"
    )
    timesheet = models.ForeignKey(
        Timesheet, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="entries",
    )
    entry_date = models.DateField()
    minutes = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    is_billable = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    # Rate SNAPSHOT: frozen from the employee's allocation when the entry is
    # first saved, so changing a rate later never rewrites old invoices.
    bill_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cost_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="approved_entries",
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-entry_date"]
        indexes = [
            models.Index(fields=["organization", "user", "entry_date"]),
            models.Index(fields=["organization", "client", "entry_date"]),
            models.Index(fields=["organization", "project", "entry_date"]),
        ]

    def save(self, *args, **kwargs):
        # Breaks and internal meetings carry no client/project and are never billable.
        if self.activity_type in (self.Activity.BREAK, self.Activity.INTERNAL_MEETING):
            self.project = None
            self.client = None
            self.is_billable = False
        # Project work: keep the denormalized client in sync with the chosen project.
        elif self.activity_type == self.Activity.WORK:
            if self.project_id and not self.client_id:
                self.client_id = self.project.client_id
        # Client meeting: attaches directly to a client, no project.
        elif self.activity_type == self.Activity.CLIENT_MEETING:
            self.project = None

        # On first save, snapshot the rates so changing a rate later never
        # rewrites old entries. Work uses the project allocation; a client
        # meeting uses any active allocation under that client (else any).
        if self._state.adding and self.bill_rate is None and self.cost_rate is None:
            from allocations.models import Allocation
            base = Allocation.objects.filter(
                organization_id=self.organization_id, user_id=self.user_id, is_active=True
            )
            alloc = None
            if self.activity_type == self.Activity.WORK and self.project_id:
                alloc = base.filter(project_id=self.project_id).order_by("-id").first()
            elif self.activity_type == self.Activity.CLIENT_MEETING and self.client_id:
                alloc = (base.filter(project__client_id=self.client_id).order_by("-id").first()
                         or base.order_by("-id").first())
            if alloc:
                self.bill_rate = alloc.bill_rate
                self.cost_rate = alloc.cost_rate
        super().save(*args, **kwargs)

    @property
    def hours(self):
        return round(self.minutes / 60, 2)

    def __str__(self):
        return f"{self.user} {self.entry_date} {self.minutes}m"


class TimeLog(OrgScopedModel):
    """
    A single work session captured by the live timer, with real start/stop
    times. When stopped, its minutes are rolled into that day's TimeEntry,
    so reports and billing stay in one place.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="time_logs"
    )
    project = models.ForeignKey(
        "projects.Project", on_delete=models.PROTECT, related_name="time_logs"
    )
    client = models.ForeignKey(
        "clients.Client", on_delete=models.PROTECT, related_name="time_logs"
    )
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)   # null = still running
    is_billable = models.BooleanField(default=True)
    note = models.TextField(blank=True)
    time_entry = models.ForeignKey(
        "timetracking.TimeEntry", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="logs",
    )

    class Meta:
        ordering = ["-started_at"]
        indexes = [models.Index(fields=["organization", "user", "ended_at"])]

    @property
    def minutes(self):
        from django.utils import timezone
        end = self.ended_at or timezone.now()
        return max(0, int((end - self.started_at).total_seconds() // 60))

    def __str__(self):
        return f"{self.user} {self.project} {self.started_at}"
