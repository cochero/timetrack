from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from common.models import TimeStampedModel
from .managers import UserManager


class Organization(TimeStampedModel):
    """One consulting / BPO firm. Everything else hangs off this."""
    PLAN_CHOICES = [
        ("FREE", "Free"),
        ("STANDARD", "Standard"),
        ("PREMIUM", "Premium"),
    ]
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    timezone = models.CharField(max_length=64, default="Asia/Kolkata")
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default="FREE")
    is_active = models.BooleanField(default=True)
    # Org-wide: minutes of inactivity before KlickTime pauses logging.
    idle_timeout_minutes = models.PositiveIntegerField(default=5)

    def __str__(self):
        return self.name


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    """A person inside an organization. Their role decides what they can do."""

    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        ADMIN = "ADMIN", "Admin"
        PROJECT_HEAD = "PROJECT_HEAD", "Project Head"
        PROJECT_MANAGER = "PROJECT_MANAGER", "Project Manager"
        TEAM_LEADER = "TEAM_LEADER", "Team Leader"
        EMPLOYEE = "EMPLOYEE", "Employee"

    organization = models.ForeignKey(
        Organization, null=True, blank=True,
        on_delete=models.CASCADE, related_name="users",
    )
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, blank=True)
    employee_code = models.CharField(max_length=50, blank=True)
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.EMPLOYEE
    )
    timezone = models.CharField(max_length=64, default="Asia/Kolkata")
    default_cost_rate = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
