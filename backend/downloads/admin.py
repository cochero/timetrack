from django.contrib import admin
from .models import DownloadLead


@admin.register(DownloadLead)
class DownloadLeadAdmin(admin.ModelAdmin):
    list_display = ("name", "file_key", "ip", "created_at")
    search_fields = ("name", "ip")
    list_filter = ("file_key", "created_at")
