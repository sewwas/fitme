"""
Fit Me — Membership Services
Centralized subscription lifecycle, automatic expiration, and hardware biometric door revocation.
Handles ZKBio turnstile gate, Face ID, fingerprint reader, RFID card, and PIN unlock state.
"""
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model

logger = logging.getLogger('wger')
User = get_user_model()

# In-memory timestamp to prevent excessive DB queries when polled frequently by daemons
_LAST_EXPIRATION_CHECK = None
_CHECK_COOLDOWN_SECONDS = 30


def check_and_expire_subscriptions(force=False):
    """
    Checks for overdue/expired subscriptions and immediately revokes hardware door access.

    Enforcement details:
    1. Finds all Subscription records where status='active' and end_date < today.
    2. Marks each overdue subscription as status='expired' and saves it.
       (Triggers post_save signal to set BiometricProfile.disabled=True and sync_status='PENDING').
    3. Failsafe scan: Checks all BiometricProfile records for non-staff members.
       If a member has NO valid active subscription covering today (start_date <= today <= end_date),
       forces BiometricProfile.disabled = True and BiometricProfile.sync_status = 'PENDING'.
    4. Queues hardware deletion in the bridge sync queue so the physical ZKBio turnstile controller
       (192.168.1.23) deletes their Face ID template, fingerprint template, RFID card, and PIN.
    5. Returns a dict summary of actions taken.
    """
    global _LAST_EXPIRATION_CHECK
    now = timezone.now()
    today = now.date()

    if not force and _LAST_EXPIRATION_CHECK:
        elapsed = (now - _LAST_EXPIRATION_CHECK).total_seconds()
        if elapsed < _CHECK_COOLDOWN_SECONDS:
            return {'status': 'skipped', 'reason': 'Throttled (ran recently)', 'elapsed_seconds': elapsed}

    _LAST_EXPIRATION_CHECK = now

    from wger.membership.models import Subscription
    from wger.zkbio_integration.models import BiometricProfile

    expired_subs_count = 0
    hardware_revoked_count = 0
    hardware_restored_count = 0

    with transaction.atomic():
        # 1. Query subscriptions that are active but whose end_date has passed
        overdue_subs = Subscription.objects.filter(
            status='active',
            end_date__lt=today
        ).select_related('member', 'plan')

        for sub in overdue_subs:
            sub.status = 'expired'
            sub.save(update_fields=['status'])  # Post-save signal syncs BiometricProfile
            expired_subs_count += 1
            logger.info(
                f"[FitMe Expiry] Subscription #{sub.id} for {sub.member.username} "
                f"({sub.plan.name}) marked EXPIRED (ended {sub.end_date})."
            )

        # 2. Comprehensive failsafe audit: Verify every non-staff BiometricProfile
        # Members without an active subscription MUST have disabled=True
        member_bios = BiometricProfile.objects.filter(
            user__is_staff=False,
            user__is_superuser=False
        ).select_related('user')

        for bio in member_bios:
            user = bio.user
            # Check if this user currently has at least one valid active subscription
            has_active_sub = Subscription.objects.filter(
                member=user,
                status='active',
                start_date__lte=today,
                end_date__gte=today
            ).exists()

            # Member is active on user table as well
            should_have_access = bool(has_active_sub and user.is_active)

            if not should_have_access and not bio.disabled:
                # REVOKE ACCESS: Disable profile and queue hardware deletion
                bio.disabled = True
                bio.sync_status = 'PENDING'
                bio.save(update_fields=['disabled', 'sync_status'])
                hardware_revoked_count += 1
                logger.warning(
                    f"[Hardware Door Revocation] Revoked Face ID, Fingerprint, Card & PIN access for "
                    f"member '{user.username}' (PIN: {bio.zk_pin}) — subscription ended/inactive."
                )
                if bio.liveu_id:
                    try:
                        from wger.zkbio_integration.liveu_client import LiveUClient
                        LiveUClient().update_member(bio.liveu_id, status='Inactive')
                    except Exception as err:
                        logger.error(f"[LiveU Sync] Error disabling member {user.username} on LiveU: {err}")

            elif should_have_access and bio.disabled:
                # RESTORE ACCESS: Re-enable profile and queue hardware addition
                bio.disabled = False
                bio.sync_status = 'PENDING'
                bio.save(update_fields=['disabled', 'sync_status'])
                hardware_restored_count += 1
                logger.info(
                    f"[Hardware Door Restoration] Restored Face ID, Fingerprint & PIN access for "
                    f"member '{user.username}' (PIN: {bio.zk_pin}) — active subscription verified."
                )
                if bio.liveu_id:
                    try:
                        from wger.zkbio_integration.liveu_client import LiveUClient
                        LiveUClient().update_member(bio.liveu_id, status='Active')
                    except Exception as err:
                        logger.error(f"[LiveU Sync] Error enabling member {user.username} on LiveU: {err}")

    summary = {
        'status': 'success',
        'today': str(today),
        'expired_subscriptions': expired_subs_count,
        'biometric_access_revoked': hardware_revoked_count,
        'biometric_access_restored': hardware_restored_count,
        'timestamp': now.isoformat(),
    }
    if expired_subs_count or hardware_revoked_count or hardware_restored_count:
        logger.info(f"[FitMe Expiry Routine] Summary: {summary}")

    return summary


def get_member_access_summary(user):
    """
    Returns full subscription and hardware gate access status for a given user.
    Used by member dashboard, front desk lookup, and hardware validation.
    """
    from wger.membership.models import Subscription
    from wger.zkbio_integration.models import BiometricProfile

    today = timezone.now().date()
    bio_profile = BiometricProfile.objects.filter(user=user).first()

    # Staff / Superusers have permanent staff access
    if user.is_staff or user.is_superuser:
        return {
            'is_staff': True,
            'door_access_active': not (bio_profile and bio_profile.disabled),
            'subscription': None,
            'status': 'staff_access',
            'status_label': 'Staff Unlimited Access',
            'days_remaining': 999,
            'is_expired': False,
            'zk_pin': bio_profile.zk_pin if bio_profile else '',
            'face_enrolled': bio_profile.face_enrolled if bio_profile else False,
            'fingerprint_enrolled': bio_profile.fingerprint_enrolled if bio_profile else False,
        }

    # Active subscription covering today
    active_sub = Subscription.objects.filter(
        member=user,
        status='active',
        start_date__lte=today,
        end_date__gte=today
    ).select_related('plan').first()

    # Latest subscription (even if expired or cancelled)
    latest_sub = Subscription.objects.filter(member=user).order_by('-end_date').select_related('plan').first()

    has_active_sub = bool(active_sub)
    is_disabled = bool(bio_profile and bio_profile.disabled)
    door_access_active = bool(has_active_sub and not is_disabled and user.is_active)

    status = 'active'
    status_label = 'Active Member'
    reason = None

    if not has_active_sub:
        if latest_sub:
            status = 'expired'
            status_label = f"Expired ({latest_sub.end_date.strftime('%d %b %Y')})"
            reason = f"Monthly subscription ended on {latest_sub.end_date.strftime('%d %b %Y')}. Gate & Face ID access disabled."
        else:
            status = 'no_subscription'
            status_label = 'No Active Plan'
            reason = "No active subscription on file. Door access revoked."
    elif is_disabled:
        status = 'revoked'
        status_label = 'Hardware Access Revoked'
        reason = "Biometric door profile has been disabled by management."

    days_remaining = active_sub.days_remaining if active_sub else 0

    return {
        'is_staff': False,
        'door_access_active': door_access_active,
        'subscription': active_sub or latest_sub,
        'active_subscription': active_sub,
        'latest_subscription': latest_sub,
        'status': status,
        'status_label': status_label,
        'is_expired': not has_active_sub,
        'days_remaining': days_remaining,
        'reason': reason,
        'zk_pin': bio_profile.zk_pin if bio_profile else '',
        'face_enrolled': bio_profile.face_enrolled if bio_profile else False,
        'fingerprint_enrolled': bio_profile.fingerprint_enrolled if bio_profile else False,
        'bio_profile': bio_profile,
    }
