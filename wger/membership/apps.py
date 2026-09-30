from django.apps import AppConfig


class MembershipConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'wger.membership'
    verbose_name = 'Fit Me — Membership'

    def ready(self):
        import wger.membership.signals  # noqa: F401 — connects all signals
