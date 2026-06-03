from django.urls import path
from .views import HeartbeatView, ActivityFeedView

urlpatterns = [
    path("agent/heartbeat/", HeartbeatView.as_view()),
    path("activity/feed/", ActivityFeedView.as_view()),
]
