from django.contrib import admin
from .models import Team, TeamMembership, Project

admin.site.register(Team)
admin.site.register(TeamMembership)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "client", "status", "is_billable", "project_manager")
    list_filter = ("status", "is_billable", "organization")
    search_fields = ("name", "code")
