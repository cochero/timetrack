from django.conf import settings
from django.db import models
from common.models import OrgScopedModel


class Allocation(OrgScopedModel):
    """
    Connects an employee to a project (and therefore to a client).

    This is the most important table in the system. It answers:
      - Who works for which client?
      - Are they DEDICATED (only this client) or SHARED (split across clients)?
      - What % of their time, and at what bill/cost rate?
    """

    class Type(models.TextChoices):
        DEDICATED = "DEDICATED", "Dedicated"   # works for one client only
        SHARED = "SHARED", "Shared"            # split across several clients

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="allocations",
    )
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="allocations"
    )
    allocation_type = models.CharField(
        max_length=20, choices=Type.choices, default=Type.SHARED
    )
    allocation_percentage = models.PositiveIntegerField(
        default=100, help_text="Share of this person's time, 0-100"
    )
    bill_rate = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="What the client is charged per hour",
    )
    cost_rate = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="What this person costs the firm per hour",
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-is_active", "user_id"]

    @property
    def client(self):
        return self.project.client

    def __str__(self):
        return f"{self.user} -> {self.project} ({self.allocation_type})"
