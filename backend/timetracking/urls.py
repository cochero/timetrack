from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import TimeEntryViewSet, TimerActiveView, TimerStartView, TimerStopView

router = DefaultRouter()
router.register("time-entries", TimeEntryViewSet, basename="time-entry")

urlpatterns = router.urls + [
    path("timer/active/", TimerActiveView.as_view()),
    path("timer/start/", TimerStartView.as_view()),
    path("timer/stop/", TimerStopView.as_view()),
]
