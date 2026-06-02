from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("accounts.management_urls")),
    path("api/", include("clients.urls")),
    path("api/", include("projects.urls")),
    path("api/", include("allocations.urls")),
    path("api/", include("timetracking.urls")),
    path("api/", include("reports.urls")),
    path("api/", include("monitoring.urls")),
    path("api/", include("downloads.urls")),
]
