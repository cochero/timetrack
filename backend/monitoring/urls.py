from django.urls import path
from .views import HeartbeatView

urlpatterns = [path("agent/heartbeat/", HeartbeatView.as_view())]
