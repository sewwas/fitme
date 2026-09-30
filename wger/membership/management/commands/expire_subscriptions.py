"""
Fit Me Management Command: expire_subscriptions
Checks for expired subscriptions and revokes door turnstile, Face ID, Fingerprint, and PIN access.

Usage:
    python manage.py expire_subscriptions
    python manage.py expire_subscriptions --force
"""
from django.core.management.base import BaseCommand
from wger.membership.services import check_and_expire_subscriptions


class Command(BaseCommand):
    help = 'Auto-expires past-due member subscriptions and revokes ZKBio biometric door & turnstile access.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Bypass the 30-second cooldown check and enforce expiration immediately.',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        self.stdout.write(self.style.NOTICE('Running Fit Me subscription expiration & door revocation audit...'))
        
        result = check_and_expire_subscriptions(force=force)
        
        if result.get('status') == 'skipped':
            self.stdout.write(self.style.WARNING(f"Audit skipped: {result.get('reason')}"))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"Completed successfully on {result.get('today')}:\n"
                f"  - Subscriptions marked Expired: {result.get('expired_subscriptions')}\n"
                f"  - Biometric hardware passes revoked: {result.get('biometric_access_revoked')}\n"
                f"  - Biometric hardware passes restored: {result.get('biometric_access_restored')}"
            ))
