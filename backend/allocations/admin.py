from django.contrib import admin
from .models import Allocation


@admin.register(Allocation)
class AllocationAdmin(admin.ModelAdmin):
    list_display = (
        "user", "project", "allocation_type",
        "allocation_percentage", "is_active",
    )
    list_filter = ("allocation_type", "is_active", "organization")
    search_fields = ("user__email", "project__name")
