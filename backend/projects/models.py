from django.conf import settings
from django.db import models
from common.models import OrgScopedModel


class Team(OrgScopedModel):
    """A group of employees, usually with one team leader."""
    name = models.CharField(max_length=255)
    team_leader = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="led_teams",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class TeamMembership(OrgScopedModel):
    """Links an employee to a team (an employee can be in more than one)."""
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="team_memberships",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["team", "user"], name="uniq_team_member")
        ]

    def __str__(self):
        return f"{self.user} in {self.team}"


class Project(OrgScopedModel):
    """A piece of work delivered for one client."""
    STATUS = [
        ("ACTIVE", "Active"),
        ("ON_HOLD", "On Hold"),
        ("COMPLETED", "Completed"),
    ]
    client = models.ForeignKey(
        "clients.Client", on_delete=models.CASCADE, related_name="projects"
    )
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, blank=True)
    project_head = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="headed_projects",
    )
    project_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="managed_projects",
    )
    status = models.CharField(max_length=20, choices=STATUS, default="ACTIVE")
    is_billable = models.BooleanField(default=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.client.name})"
