from django.contrib import admin
from .models import ActivitySample


@admin.register(ActivitySample)
class ActivitySampleAdmin(admin.ModelAdmin):
    list_display = ("user", "app", "window_title", "active", "minutes", "project", "captured_at")
    list_filter = ("active", "organization", "user")
    search_fields = ("app", "window_title")
