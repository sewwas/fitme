from django.db.models.signals import post_save
from django.dispatch import receiver
import requests
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()
ZKBIO_DAEMON_URL = getattr(settings, 'ZKBIO_DAEMON_URL', 'http://localhost:3000/api/zkbio/webhook')

@receiver(post_save, sender=User)
def sync_user_to_zkbio(sender, instance, created, **kwargs):
    """
    Signal to trigger a webhook to the local bridge daemon whenever a user's status changes.
    If is_active is True, they are pushed to the hardware. If False, they are revoked.
    """
    payload = {
        "user_id": instance.id,
        "username": instance.username,
        "is_active": instance.is_active,
        "pin": getattr(instance, 'zkbio_access', None).pin if hasattr(instance, 'zkbio_access') else None
    }
    
    try:
        requests.post(f"{ZKBIO_DAEMON_URL}/sync", json=payload, timeout=5)
    except requests.exceptions.RequestException as e:
        print(f"Failed to sync user {instance.id} to ZKBio Bridge: {e}")
