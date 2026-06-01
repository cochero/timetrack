from django.urls import path
from .views import (
    HoursByClientView, HoursByEmployeeView, HoursByProjectView, UtilizationView, BillingExportView,
)

urlpatterns = [
    path("reports/hours-by-client/", HoursByClientView.as_view()),
    path("reports/hours-by-employee/", HoursByEmployeeView.as_view()),
    path("reports/hours-by-project/", HoursByProjectView.as_view()),
    path("reports/utilization/", UtilizationView.as_view()),
    path("reports/billing-export/", BillingExportView.as_view()),
]
