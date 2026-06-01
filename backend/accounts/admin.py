from django.contrib import admin
from .models import Organization, User

admin.site.register(Organization)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name", "role", "organization", "is_active")
    list_filter = ("role", "is_active", "organization")
    search_fields = ("email", "full_name", "employee_code")
