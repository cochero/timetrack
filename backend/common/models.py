from django.db import models


class TimeStampedModel(models.Model):
    """Every record automatically remembers when it was created and last changed."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class OrgScopedModel(TimeStampedModel):
    """
    Every business record belongs to one Organization (one consulting/BPO firm).
    This is how we keep each company's data fully separate inside one database.
    """
    organization = models.ForeignKey(
        "accounts.Organization", on_delete=models.CASCADE
    )

    class Meta:
        abstract = True
