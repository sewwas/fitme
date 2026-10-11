"""
Fit Me Fitness Email Service
Handles transactional member onboarding, welcome invitations, and cryptographic password setup links.
"""

import logging
import threading
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

logger = logging.getLogger('wger.email_service')


def get_base_url(request=None):
    """
    Resolves the base URL (protocol + host) for public links.
    Prioritizes request header/host if available, falls back to SITE_URL setting.
    """
    if request:
        protocol = 'https' if request.is_secure() else 'http'
        # Check X-Forwarded-Proto if behind reverse proxy (e.g. Render / Cloudflare)
        x_proto = request.META.get('HTTP_X_FORWARDED_PROTO')
        if x_proto:
            protocol = x_proto.split(',')[0].strip()
        host = request.get_host()
        return f"{protocol}://{host}"

    site_url = getattr(settings, 'SITE_URL', 'https://fitmefitness.lk')
    return site_url.rstrip('/')


def generate_password_set_url(user, request=None):
    """
    Generates a secure, cryptographically signed one-time password setup / reset URL for the user.
    Uses Django's built-in PasswordResetTokenGenerator.
    """
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    base_url = get_base_url(request)
    return f"{base_url}/user/password/reset/check/{uid}/{token}/"


def _send_email_worker(subject, text_body, html_body, to_email, from_email):
    """Internal synchronous sender run in background thread."""
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=from_email,
            to=[to_email],
        )
        if html_body:
            msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)
        logger.info(f"[EmailService] Successfully sent '{subject}' to {to_email}")
    except Exception as ex:
        logger.error(f"[EmailService] Failed sending '{subject}' to {to_email}: {ex}", exc_info=True)


def send_welcome_password_setup_email(user, request=None, is_async=True):
    """
    Dispatches a high-priority branded welcome email to a new member or staff user,
    providing their Member PIN, account info, and a one-click password setup link.
    """
    if not user.email:
        logger.warning(f"[EmailService] Cannot send welcome email: User {user.username} has no email address.")
        return False, "User has no email address."

    # Retrieve associated MemberProfile or details
    pin = "—"
    plan_name = "Fit Me Membership"
    try:
        from wger.membership.models import MemberProfile, Subscription
        profile = MemberProfile.objects.filter(user=user).first()
        if profile and profile.biometric_pin:
            pin = profile.biometric_pin

        sub = Subscription.objects.filter(member=user).select_related('plan').order_by('-start_date').first()
        if sub and sub.plan:
            plan_name = sub.plan.name
    except Exception as ex:
        logger.debug(f"[EmailService] Could not lookup member profile/sub for {user.username}: {ex}")

    setup_url = generate_password_set_url(user, request)
    base_url = get_base_url(request)

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'Fit Me <hello@fitmefitness.lk>')
    subject = "🏋️ Welcome to Fit Me Fitness Club — Set Your Password"

    context = {
        'user': user,
        'full_name': user.get_full_name() or user.username,
        'username': user.username,
        'email': user.email,
        'pin': pin,
        'plan_name': plan_name,
        'setup_url': setup_url,
        'base_url': base_url,
    }

    try:
        html_body = render_to_string('email/welcome_set_password.html', context)
        text_body = render_to_string('email/welcome_set_password.txt', context)
    except Exception as ex:
        logger.error(f"[EmailService] Template rendering error: {ex}", exc_info=True)
        # Fallback plaintext
        text_body = (
            f"Hello {user.get_full_name() or user.username},\n\n"
            f"Welcome to Fit Me Fitness Club! Your account has been created.\n"
            f"Your Member PIN: {pin}\n\n"
            f"Please click the link below to set your password and access the member portal:\n"
            f"{setup_url}\n\n"
            f"This link expires in 72 hours.\n\n"
            f"— Fit Me Team, Pitigala"
        )
        html_body = None

    if is_async:
        thread = threading.Thread(
            target=_send_email_worker,
            args=(subject, text_body, html_body, user.email, from_email),
            daemon=True
        )
        thread.start()
        return True, "Email queued for immediate delivery."
    else:
        _send_email_worker(subject, text_body, html_body, user.email, from_email)
        return True, "Email sent successfully."
