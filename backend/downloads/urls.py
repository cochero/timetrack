from django.urls import path
from .views import ChallengeView, RequestDownloadView, DownloadFileView

urlpatterns = [
    path("download/challenge/", ChallengeView.as_view()),
    path("download/request/", RequestDownloadView.as_view()),
    path("download/file/", DownloadFileView.as_view()),
]
