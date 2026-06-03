from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from monitoring.models import ActivitySample


class Command(BaseCommand):
    help = "Delete activity samples older than the retention window (default 90 days)."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=90, help="Retention window in days.")

    def handle(self, *args, **opts):
        days = opts["days"]
        cutoff = timezone.now() - timedelta(days=days)
        deleted, _ = ActivitySample.objects.filter(captured_at__lt=cutoff).delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} activity samples older than {days} days."))
