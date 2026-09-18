import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

logger = logging.getLogger('wger')


@receiver(post_save, sender='membership.Subscription')
def handle_subscription_change(sender, instance, **kwargs):
    """
    When a member's subscription status changes:
    If expired, cancelled, or suspended -> revoke door permissions (disabled = True).
    If active and dates valid -> restore door permissions (disabled = False).
    Sets sync_status = 'PENDING' so local bridge daemon updates ZKBio CVAccess controller.
    """
    from wger.zkbio_integration.models import BiometricProfile

    user = instance.member
    profile = BiometricProfile.objects.filter(user=user).first()
    if not profile:
        return

    today = timezone.now().date()
    is_valid_active = (
        instance.status == 'active' and
        instance.start_date <= today <= instance.end_date
    )

    if not is_valid_active:
        if not profile.disabled or profile.sync_status != 'PENDING':
            profile.disabled = True
            profile.sync_status = 'PENDING'
            profile.save(update_fields=['disabled', 'sync_status'])
            logger.info(f"[ZKBio Signal] Revoking door access for {user.username} (PIN: {profile.zk_pin}) due to subscription change.")
    else:
        if profile.disabled or profile.sync_status == 'REVOKED':
            profile.disabled = False
            profile.sync_status = 'PENDING'
            profile.save(update_fields=['disabled', 'sync_status'])
            logger.info(f"[ZKBio Signal] Restoring door access for {user.username} (PIN: {profile.zk_pin}).")
