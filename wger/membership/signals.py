"""
Fit Me — Membership Signals
Auto-manages biometric hardware access when subscriptions change state.
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

logger = logging.getLogger('wger')


@receiver(post_save, sender='membership.Subscription')
def sync_biometric_access_on_subscription_change(sender, instance, created, **kwargs):
    """
    When a Subscription is saved:
    - If active → ensure BiometricProfile is enabled (disabled=False)
    - If expired/cancelled/suspended → disable BiometricProfile (disabled=True)
    This is the critical link between membership status and hardware turnstile access.
    """
    try:
        from wger.zkbio_integration.models import BiometricProfile

        user = instance.member
        bio = BiometricProfile.objects.filter(user=user).first()
        if not bio:
            return

        today = timezone.now().date()
        has_active_sub = sender.objects.filter(
            member=user,
            status='active',
            end_date__gte=today,
        ).exclude(pk=instance.pk).exists()

        # Check the current instance itself
        current_is_active = (
            instance.status == 'active' and
            instance.start_date <= today <= instance.end_date
        )

        should_have_access = current_is_active or has_active_sub

        if bio.disabled == (not should_have_access):
            return  # No change needed

        bio.disabled = not should_have_access
        bio.sync_status = 'PENDING'  # Queue for hardware sync
        bio.save(update_fields=['disabled', 'sync_status'])

        action = 'GRANTED' if should_have_access else 'REVOKED'
        logger.info(
            f"[ZKBio Signal] Door access {action} for {user.username} "
            f"(Subscription #{instance.pk} → {instance.status})"
        )
    except Exception as e:
        logger.error(f"[ZKBio Signal] Failed to sync biometric access for subscription #{instance.pk}: {e}")
