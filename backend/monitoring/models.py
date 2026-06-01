from django.conf import settings
from django.db import models
from common.models import OrgScopedModel


class ActivitySample(OrgScopedModel):
    """
    One reading from a desktop agent: what app/window was in focus, whether the
    person was active, and how many minutes it represents. Active minutes also
    roll into that day's TimeEntry so reports stay in one place.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="activity_samples")
    project = models.ForeignKey("projects.Project", null=True, blank=True, on_delete=models.SET_NULL, related_name="activity_samples")
    captured_at = models.DateTimeField()
    app = models.CharField(max_length=255, blank=True)
    window_title = models.CharField(max_length=512, blank=True)
    active = models.BooleanField(default=True)
    minutes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-captured_at"]
        indexes = [models.Index(fields=["organization", "user", "captured_at"])]

    def __str__(self):
        return f"{self.user} {self.app} @ {self.captured_at}"
