from django.urls import path
from .views import ChallengeView, RequestDownloadView, DownloadFileView, LatestVersionView

urlpatterns = [
    path("download/challenge/", ChallengeView.as_view()),
    path("download/request/", RequestDownloadView.as_view()),
    path("download/file/", DownloadFileView.as_view()),
    path("klicktime/version/", LatestVersionView.as_view()),
]
