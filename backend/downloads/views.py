import os
import random

from django.conf import settings
from django.core import signing
from django.http import FileResponse, Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import ValidationError

from .models import DownloadLead

CAPTCHA_SALT = "klicktime-captcha"
DOWNLOAD_SALT = "klicktime-download"
CAPTCHA_MAX_AGE = 600      # 10 minutes to solve
DOWNLOAD_MAX_AGE = 120     # token good for 2 minutes


def _client_ip(request):
    fwd = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class ChallengeView(APIView):
    """Issue a simple math CAPTCHA. Returns a question and a signed token."""
    permission_classes = [AllowAny]

    def get(self, request):
        a, b = random.randint(1, 9), random.randint(1, 9)
        token = signing.dumps(a + b, salt=CAPTCHA_SALT)
        return Response({"question": f"What is {a} + {b}?", "token": token})


class RequestDownloadView(APIView):
    """Validate name + CAPTCHA, record the lead, return a one-time download token."""
    permission_classes = [AllowAny]

    def post(self, request):
        name = str(request.data.get("name", "")).strip()
        token = request.data.get("token", "")
        answer = request.data.get("answer", "")
        if not name:
            raise ValidationError({"name": "Please enter your name."})
        try:
            expected = signing.loads(token, salt=CAPTCHA_SALT, max_age=CAPTCHA_MAX_AGE)
        except signing.BadSignature:
            raise ValidationError({"captcha": "The challenge expired. Please try again."})
        try:
            if int(answer) != int(expected):
                raise ValueError
        except (ValueError, TypeError):
            raise ValidationError({"captcha": "Incorrect answer. Please try again."})

        DownloadLead.objects.create(
            name=name[:120], file_key="klicktime",
            ip=_client_ip(request), user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
        )
        dl_token = signing.dumps({"k": "klicktime", "n": name[:120]}, salt=DOWNLOAD_SALT)
        return Response({"download_token": dl_token})


class DownloadFileView(APIView):
    """Stream the installer if the one-time token is valid and recent."""
    permission_classes = [AllowAny]

    def get(self, request):
        token = request.GET.get("t", "")
        try:
            signing.loads(token, salt=DOWNLOAD_SALT, max_age=DOWNLOAD_MAX_AGE)
        except signing.BadSignature:
            raise Http404("Link expired. Please request the download again.")
        path = getattr(settings, "KLICKTIME_INSTALLER_PATH", "")
        if not path or not os.path.exists(path):
            raise Http404("Installer is not available yet.")
        return FileResponse(open(path, "rb"), as_attachment=True, filename="KlickTimeSetup.exe")


class LatestVersionView(APIView):
    """Tells the KlickTime desktop app the latest released version.

    The version itself is a single setting (KLICKTIME_LATEST_VERSION) so a
    release is just one value to change. Public so the app can check freely.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            "version": getattr(settings, "KLICKTIME_LATEST_VERSION", "1.0.0"),
            "download_url": "/download",
        })
