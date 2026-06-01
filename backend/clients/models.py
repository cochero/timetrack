from django.db import models
from common.models import OrgScopedModel


class Client(OrgScopedModel):
    """An external company that the firm provides services to."""
    STATUS = [("ACTIVE", "Active"), ("INACTIVE", "Inactive")]
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="ACTIVE")
    billing_currency = models.CharField(max_length=3, default="INR")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
