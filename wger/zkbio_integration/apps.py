from django.apps import AppConfig


class ZKBioIntegrationConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'wger.zkbio_integration'
    verbose_name = 'ZKBio Biometric Integration'

    def ready(self):
        import wger.zkbio_integration.signals  # noqa: F401
