from django.contrib import admin
from .models import TimeEntry, Timesheet, TimeLog


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ("user", "client", "project", "entry_date", "minutes", "status")
    list_filter = ("status", "is_billable", "organization", "client")
    search_fields = ("user__email", "description")


@admin.register(Timesheet)
class TimesheetAdmin(admin.ModelAdmin):
    list_display = ("user", "period_start", "period_end", "status", "total_minutes")
    list_filter = ("status", "organization")


@admin.register(TimeLog)
class TimeLogAdmin(admin.ModelAdmin):
    list_display = ("user", "project", "started_at", "ended_at")
    list_filter = ("organization",)
