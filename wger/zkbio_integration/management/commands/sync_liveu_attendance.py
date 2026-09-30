"""
Fit Me — LiveU Cloud Attendance Sync Command
Polls LiveU Cloud API (v1.0) and imports new attendance records into DoorAccessLog.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from wger.zkbio_integration.liveu_client import LiveUClient


class Command(BaseCommand):
    help = 'Sync real-time turnstile attendance logs from LiveU Cloud'

    def add_arguments(self, parser):
        parser.add_argument(
            '--from',
            dest='from_date',
            default=None,
            help='Start date in YYYY-MM-DD format (defaults to today)',
        )
        parser.add_argument(
            '--to',
            dest='to_date',
            default=None,
            help='End date in YYYY-MM-DD format',
        )

    def handle(self, *args, **options):
        client = LiveUClient()
        if not client.is_configured:
            self.stdout.write(self.style.WARNING(
                "LIVEU_BRANCH_API_KEY is not set. Please add it to your .env file."
            ))
            return

        from_date = options['from_date'] or timezone.now().date().isoformat()
        to_date = options['to_date']

        self.stdout.write(f"Syncing LiveU Cloud attendance records from {from_date}...")
        result = client.sync_cloud_attendances(from_date=from_date, to_date=to_date)

        if result.get('status') == 'success':
            self.stdout.write(self.style.SUCCESS(
                f"Sync completed: {result['synced']} new records imported, {result['skipped']} skipped (already present)."
            ))
        else:
            self.stdout.write(self.style.NOTICE(f"LiveU sync status: {result.get('status')}"))
