from django.db import models


class DownloadLead(models.Model):
    """A record of someone who requested the KlickTime installer (public page)."""
    name = models.CharField(max_length=120)
    file_key = models.CharField(max_length=60, default="klicktime")
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} @ {self.created_at:%Y-%m-%d %H:%M}"
