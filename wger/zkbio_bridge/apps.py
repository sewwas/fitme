from django.apps import AppConfig

class ZkbioBridgeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'wger.zkbio_bridge'

    def ready(self):
        import wger.zkbio_bridge.signals
