import os
import json
import base64
import logging
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile

from wger.zkbio_integration.models import BiometricProfile, DoorAccessLog, BiometricCommand
from wger.membership.models import Subscription, MemberProfile
from wger.membership.services import check_and_expire_subscriptions

logger = logging.getLogger('wger')
User = get_user_model()

# Shared token for daemon-to-cloud authentication over Cloudflare Tunnel / HTTPS
# Token is loaded from ZKBIO_BRIDGE_TOKEN in Django settings (set via LIVEU_BRANCH_API_KEY env var).
# No hardcoded fallback tokens — all authentication must go through env config.
BRIDGE_API_TOKEN = getattr(settings, 'ZKBIO_BRIDGE_TOKEN', '')


def verify_bridge_token(request):
    """Verifies Bearer token in HTTP_AUTHORIZATION header against ZKBIO_BRIDGE_TOKEN setting."""
    if not BRIDGE_API_TOKEN:
        logger.error('[ZKBio Auth] ZKBIO_BRIDGE_TOKEN is not configured in settings!')
        return False
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ', 1)[1].strip()
        return token == BRIDGE_API_TOKEN
    return False


def _parse_verify_mode(raw_mode):
    """Normalizes ZKTeco verification mode integer or string to standard choice."""
    if raw_mode in [15, '15', 'face', 'FACE', 'FACE_ID', 'face_id']:
        return 'FACE_ID'
    if raw_mode in [1, '1', 'finger', 'fingerprint', 'FINGERPRINT']:
        return 'FINGERPRINT'
    if raw_mode in [4, '4', 'card', 'rfid', 'CARD']:
        return 'CARD'
    if raw_mode in ['buzzer', 'override', 'BUZZER']:
        return 'BUZZER'
    return 'FACE_ID' # Default to Face ID as primary biometrics


@csrf_exempt
def punches_ingest(request):
    """
    Webhook / Ingest Endpoint: /api/zkbio/punches/
    Accepts real-time door punch streams from local bridge daemon.
    1. Enforces dynamic subscription validity (blocks expired members immediately).
    2. Enforces 60-second anti-passback cooldown.
    3. Records verify_mode (Face ID or Fingerprint).
    4. Updates staff floor attendance shifts.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    if not verify_bridge_token(request):
        if not (request.user.is_authenticated and request.user.is_staff):
            return HttpResponseForbidden('Unauthorized daemon token')

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception as e:
        return JsonResponse({'error': f'Invalid JSON payload: {str(e)}'}, status=400)

    pin = str(data.get('pin', '')).strip()
    if not pin:
        return JsonResponse({'error': 'Hardware PIN is required'}, status=400)

    punch_time_raw = data.get('punch_time')
    if punch_time_raw:
        try:
            punch_time = timezone.datetime.fromisoformat(punch_time_raw.replace('Z', '+00:00'))
        except Exception:
            punch_time = timezone.now()
    else:
        punch_time = timezone.now()

    direction = data.get('direction', 'IN').upper() # IN or OUT
    device_ip = data.get('device_ip', '192.168.1.23')
    terminal_name = data.get('terminal_name', 'MAIN_TURNSTILE')
    raw_payload = data.get('raw_payload', data)
    verify_mode = _parse_verify_mode(data.get('verify_mode') or raw_payload.get('verify_mode', 15))

    # Resolve User from BiometricProfile or MemberProfile
    bio_profile = BiometricProfile.objects.filter(zk_pin=pin).select_related('user').first()
    user = bio_profile.user if bio_profile else None
    if not user:
        mp = MemberProfile.objects.filter(biometric_pin=pin).select_related('user').first()
        if mp:
            user = mp.user
            bio_profile, _ = BiometricProfile.objects.get_or_create(user=user, defaults={'zk_pin': pin})

    # Ensure any past-due subscriptions are expired before evaluating punch
    check_and_expire_subscriptions()

    # If bio_profile is disabled or revoked
    if bio_profile and bio_profile.disabled:
        denied_reason = 'Door, Face ID, and biometric access revoked: Membership expired or profile disabled'
        if user and not user.is_staff:
            last_sub = Subscription.objects.filter(member=user).order_by('-end_date').first()
            if last_sub:
                denied_reason = f"Monthly subscription ended on {last_sub.end_date:%d %b %Y}. Turnstile gate, Face ID, and PIN access are disabled."
            else:
                denied_reason = "No active membership subscription on file. Door access revoked."

        log = DoorAccessLog.objects.create(
            user=user,
            zk_pin=pin,
            punch_time=punch_time,
            event_type='DENIED',
            verify_mode=verify_mode,
            device_ip=device_ip,
            terminal_name=terminal_name,
            raw_payload={**raw_payload, 'reason': denied_reason},
        )
        return JsonResponse({
            'status': 'denied',
            'reason': denied_reason,
            'allowed': False,
            'log_id': log.id
        })

    # Dynamic Subscription Validation for Gym Members (Non-Staff)
    if user and not user.is_staff:
        today = punch_time.date() if punch_time else timezone.now().date()
        active_sub = Subscription.objects.filter(
            member=user,
            status='active',
            start_date__lte=today,
            end_date__gte=today
        ).first()

        if not active_sub:
            # Check latest expired subscription to give informative reason
            last_sub = Subscription.objects.filter(member=user).order_by('-end_date').first()
            if last_sub:
                reason = f"Monthly subscription ended on {last_sub.end_date:%d %b %Y}. Turnstile gate, Face ID, and PIN access are disabled."
            else:
                reason = "No active membership subscription on file. Door access revoked."

            # Automatically flag profile disabled to sync revocation to hardware
            if bio_profile and not bio_profile.disabled:
                bio_profile.disabled = True
                bio_profile.sync_status = 'PENDING'
                bio_profile.save(update_fields=['disabled', 'sync_status'])

            log = DoorAccessLog.objects.create(
                user=user,
                zk_pin=pin,
                punch_time=punch_time,
                event_type='DENIED',
                verify_mode=verify_mode,
                device_ip=device_ip,
                terminal_name=terminal_name,
                raw_payload={**raw_payload, 'reason': reason},
            )
            return JsonResponse({
                'status': 'denied',
                'reason': reason,
                'allowed': False,
                'log_id': log.id
            })

    # Anti-passback cooldown: 60 seconds
    cooldown_cutoff = punch_time - timedelta(seconds=60)
    recent_punch = DoorAccessLog.objects.filter(
        zk_pin=pin,
        punch_time__gte=cooldown_cutoff,
        punch_time__lte=punch_time + timedelta(seconds=5)
    ).order_by('-punch_time').first()

    expected_event = 'ENTRY' if direction == 'IN' else 'EXIT'

    if recent_punch and recent_punch.event_type == expected_event:
        log = DoorAccessLog.objects.create(
            user=user,
            zk_pin=pin,
            punch_time=punch_time,
            event_type='ANTI_PASSBACK',
            verify_mode=verify_mode,
            device_ip=device_ip,
            terminal_name=terminal_name,
            raw_payload=raw_payload,
        )
        logger.warning(f"[Anti-Passback] Hardware ID {pin} duplicate {direction} within 60s cooldown.")
        return JsonResponse({
            'status': 'anti_passback',
            'reason': 'Anti-passback cooldown active (60s)',
            'allowed': False,
            'log_id': log.id
        }, status=429)

    # Valid entry or exit
    log = DoorAccessLog.objects.create(
        user=user,
        zk_pin=pin,
        punch_time=punch_time,
        event_type=expected_event,
        verify_mode=verify_mode,
        device_ip=device_ip,
        terminal_name=terminal_name,
        raw_payload=raw_payload,
    )

    # If staff member punched, update staff attendance records with Morning & Evening Split Session support
    if user and user.is_staff:
        try:
            from wger.gym_operations_payroll.models import StaffShift, StaffWorkSchedule
            today = punch_time.date()
            shift = StaffShift.objects.filter(staff_user=user, shift_date=today).first()
            if not shift:
                # Auto-provision daily shift based on staff contract or Split default
                work_sched = StaffWorkSchedule.objects.filter(staff_user=user).first()
                if work_sched:
                    is_active, s_type, s_start, s_end = work_sched.get_schedule_for_weekday(today.weekday())
                else:
                    is_active = True
                    s_type = 'FULL_SPLIT'
                    s_start = timezone.datetime.strptime('05:00', '%H:%M').time()
                    s_end = timezone.datetime.strptime('21:00', '%H:%M').time()

                shift = StaffShift.objects.create(
                    staff_user=user,
                    shift_date=today,
                    shift_type=s_type if is_active else 'REST_DAY',
                    scheduled_start=s_start or timezone.datetime.strptime('05:00', '%H:%M').time(),
                    scheduled_end=s_end or timezone.datetime.strptime('21:00', '%H:%M').time(),
                    is_rest_day=(not is_active),
                    status='REST_DAY' if not is_active else 'SCHEDULED'
                )

            # Determine whether punch belongs to Morning (05:00 - 12:00) or Evening (15:00 - 21:00) session
            punch_hour = punch_time.hour
            punch_minute = punch_time.minute
            time_decimal = punch_hour + (punch_minute / 60.0)

            if time_decimal < 13.5:
                # ── Morning Session Window (04:00 - 13:30) ──
                if expected_event == 'ENTRY':
                    if not shift.morning_in:
                        shift.morning_in = punch_time
                    shift.status = 'ON_FLOOR'
                    shift.is_off_floor = False
                elif expected_event == 'EXIT':
                    shift.morning_out = punch_time
                    # If departure around 12:00 noon gym closure, mark off-floor without sudden absence penalty
                    shift.status = 'OFF_FLOOR'
            else:
                # ── Evening Session Window (13:30 - 23:00) ──
                if expected_event == 'ENTRY':
                    if not shift.evening_in:
                        shift.evening_in = punch_time
                    shift.status = 'ON_FLOOR'
                    shift.is_off_floor = False
                elif expected_event == 'EXIT':
                    shift.evening_out = punch_time
                    shift.status = 'COMPLETED'

            # Sync aggregate actual punches & calculate overtime
            if shift.morning_in and not shift.actual_first_in:
                shift.actual_first_in = shift.morning_in
            elif not shift.actual_first_in and shift.evening_in:
                shift.actual_first_in = shift.evening_in

            if shift.evening_out:
                shift.actual_last_out = shift.evening_out
            elif shift.morning_out and not shift.actual_last_out:
                shift.actual_last_out = shift.morning_out

            shift.overtime_minutes = shift.calculate_overtime_minutes()
            shift.save(update_fields=[
                'morning_in', 'morning_out', 'evening_in', 'evening_out',
                'actual_first_in', 'actual_last_out', 'overtime_minutes',
                'status', 'is_off_floor'
            ])
        except Exception as ex:
            logger.error(f"Error linking staff punch to shift: {ex}")

    # Update workout streak on every valid gym ENTRY
    if user and expected_event == 'ENTRY':
        try:
            from wger.habit.models import WorkoutStreak
            streak, _ = WorkoutStreak.objects.get_or_create(member=user)
            streak.record_checkin()
        except Exception as ex:
            logger.error(f"Error updating workout streak for {pin}: {ex}")

    _RECENT_PUNCHES_CACHE['ts'] = 0
    _FLOOR_STATUS_CACHE['ts'] = 0

    return JsonResponse({
        'status': 'success',
        'allowed': True,
        'event': expected_event,
        'verify_mode': verify_mode,
        'pin': pin,
        'username': user.username if user else None,
        'log_id': log.id
    })


@csrf_exempt
def pending_sync_queue(request):
    """
    Endpoint: /api/zkbio/pending-sync/
    Polled by the local bridge daemon to pull pending member additions, portrait photos, or revocations.
    """
    if not verify_bridge_token(request):
        if not (request.user.is_authenticated and request.user.is_staff):
            return HttpResponseForbidden('Unauthorized daemon token')

    # Automatically audit and expire past-due subscriptions so bridge immediately receives action='delete'
    check_and_expire_subscriptions()

    pending_profiles = BiometricProfile.objects.filter(
        sync_status='PENDING'
    ).select_related('user')[:50]

    items = []
    for p in pending_profiles:
        photo_b64 = None
        photo_url = ''
        mp = getattr(p.user, 'member_profile', None)
        if mp and mp.profile_photo:
            try:
                photo_path = mp.profile_photo.path
                if os.path.exists(photo_path):
                    with open(photo_path, 'rb') as pf:
                        photo_b64 = base64.b64encode(pf.read()).decode('utf-8')
                photo_url = request.build_absolute_uri(mp.profile_photo.url)
            except Exception as pe:
                logger.warning(f"Could not encode profile photo for user {p.user.username}: {pe}")

        items.append({
            'pin': p.zk_pin,
            'username': p.user.username,
            'full_name': p.user.get_full_name() or p.user.username,
            'card_number': p.card_number or '',
            'door_group_id': p.door_group_id,
            'face_enrolled': p.face_enrolled,
            'fingerprint_enrolled': p.fingerprint_enrolled,
            'photo_base64': photo_b64,
            'photo_url': photo_url,
            'disabled': p.disabled,
            'action': 'delete' if p.disabled else 'add'
        })

    return JsonResponse({'pending': items, 'count': len(items)})


@csrf_exempt
def sync_status_callback(request):
    """
    Endpoint: /api/zkbio/sync-status/
    Daemon calls this to confirm that hardware person add/delete/photo sync succeeded.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    if not verify_bridge_token(request):
        if not (request.user.is_authenticated and request.user.is_staff):
            return HttpResponseForbidden('Unauthorized daemon token')

    try:
        data = json.loads(request.body.decode('utf-8'))
        pin = data.get('pin')
        status = data.get('status', 'SYNCED')
        face_enrolled = data.get('face_enrolled')
        fingerprint_enrolled = data.get('fingerprint_enrolled')

        profile = BiometricProfile.objects.filter(zk_pin=pin).first()
        if profile:
            profile.sync_status = status
            profile.last_sync_time = timezone.now()
            if face_enrolled is not None:
                profile.face_enrolled = bool(face_enrolled)
            if fingerprint_enrolled is not None:
                profile.fingerprint_enrolled = bool(fingerprint_enrolled)
            profile.save()
            return JsonResponse({'success': True, 'pin': pin, 'status': status})
        return JsonResponse({'error': f'Profile with PIN {pin} not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def get_or_create_biometric_profile(user):
    """
    Safely retrieves or creates a BiometricProfile for a user,
    guaranteeing a unique, conflict-free zk_pin.
    """
    bio_profile = BiometricProfile.objects.filter(user=user).first()
    mp, _ = MemberProfile.objects.get_or_create(user=user)

    if not bio_profile:
        target_pin = mp.biometric_pin
        if not target_pin or BiometricProfile.objects.filter(zk_pin=target_pin).exists():
            from wger.core.views.fitme_dashboards import generate_unique_biometric_pin
            target_pin = generate_unique_biometric_pin()
            mp.biometric_pin = target_pin
            mp.save(update_fields=['biometric_pin'])
        bio_profile = BiometricProfile.objects.create(
            user=user,
            zk_pin=target_pin,
            sync_status='PENDING'
        )
    else:
        if not bio_profile.zk_pin:
            target_pin = mp.biometric_pin
            if not target_pin or BiometricProfile.objects.filter(zk_pin=target_pin).exclude(user=user).exists():
                from wger.core.views.fitme_dashboards import generate_unique_biometric_pin
                target_pin = generate_unique_biometric_pin()
            bio_profile.zk_pin = target_pin
            bio_profile.save(update_fields=['zk_pin'])
            mp.biometric_pin = target_pin
            mp.save(update_fields=['biometric_pin'])
        elif not mp.biometric_pin or mp.biometric_pin != bio_profile.zk_pin:
            mp.biometric_pin = bio_profile.zk_pin
            mp.save(update_fields=['biometric_pin'])

    return bio_profile, mp


@csrf_exempt
def upload_face_api(request):
    """
    Endpoint: /api/zkbio/upload-face/
    Allows front desk, admin, or member to upload/capture a portrait photo for Face ID hardware enrollment.
    Accepts: user_id or pin, and photo file OR photo_base64.
    """
    if not request.user.is_authenticated and not verify_bridge_token(request):
        return HttpResponseForbidden('Authentication or valid bridge token required')

    user_id = request.POST.get('user_id') or request.POST.get('member_id')
    pin = request.POST.get('pin')
    photo_file = request.FILES.get('photo') or request.FILES.get('profile_photo')
    photo_b64 = request.POST.get('photo_base64')

    # Also handle JSON payload if sent via fetch(JSON.stringify())
    if not photo_file and not photo_b64 and request.body:
        try:
            body_data = json.loads(request.body.decode('utf-8'))
            user_id = user_id or body_data.get('user_id') or body_data.get('member_id')
            pin = pin or body_data.get('pin')
            photo_b64 = body_data.get('photo_base64')
        except Exception:
            pass

    target_user = None
    # Staff / Superuser, Front Desk, Coach or bridge token can specify any user; regular member can only register own face
    user_groups = set(request.user.groups.values_list('name', flat=True)) if request.user.is_authenticated else set()
    is_staff = request.user.is_authenticated and (
        request.user.is_staff or request.user.is_superuser or
        bool(user_groups.intersection({'Front Desk', 'Coach', 'Super Admin'}))
    )
    is_bridge = verify_bridge_token(request)

    if (is_staff or is_bridge) and user_id:
        target_user = User.objects.filter(id=user_id).first()
    elif (is_staff or is_bridge) and pin:
        bio = BiometricProfile.objects.filter(zk_pin=pin).first()
        if bio:
            target_user = bio.user
    elif request.user.is_authenticated:
        target_user = request.user

    if not target_user:
        return JsonResponse({'error': 'Target user not found'}, status=404)

    bio_profile, mp = get_or_create_biometric_profile(target_user)

    if photo_b64:
        # Strip header if present (e.g. data:image/jpeg;base64,)
        if ',' in photo_b64:
            photo_b64 = photo_b64.split(',', 1)[1]
        try:
            img_data = base64.b64decode(photo_b64)
            file_name = f"member_{target_user.id}_face.jpg"
            mp.profile_photo.save(file_name, ContentFile(img_data), save=True)
        except Exception as e:
            return JsonResponse({'error': f'Failed to decode base64 photo: {str(e)}'}, status=400)
    elif photo_file:
        mp.profile_photo = photo_file
        mp.save()
    else:
        return JsonResponse({'error': 'Photo file or photo_base64 is required'}, status=400)

    # Mark face enrolled and pending sync
    bio_profile.face_enrolled = True
    bio_profile.sync_status = 'PENDING'
    bio_profile.save(update_fields=['face_enrolled', 'sync_status'])

    # Queue hardware command for turnstile terminal
    BiometricCommand.objects.create(
        command_type='UPLOAD_FACE',
        zk_pin=bio_profile.zk_pin,
        user=target_user,
        status='PENDING',
        payload={'photo_url': mp.profile_photo.url}
    )

    return JsonResponse({
        'success': True,
        'message': f"Face ID successfully registered for {target_user.get_full_name() or target_user.username}!",
        'photo_url': mp.profile_photo.url,
        'pin': bio_profile.zk_pin,
        'face_enrolled': True
    })


@csrf_exempt
def face_unlock_api(request):
    """
    Endpoint: /api/zkbio/face-unlock/
    Face ID Verification & Turnstile Door Unlock:
    Simulates / triggers optical Face ID turnstile unlock for member.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    user = request.user
    from wger.membership.services import check_and_expire_subscriptions, get_member_access_summary
    check_and_expire_subscriptions()
    summary = get_member_access_summary(user)
    bio = BiometricProfile.objects.filter(user=user).first()
    pin = bio.zk_pin if bio else (getattr(user, 'member_profile', None).biometric_pin if hasattr(user, 'member_profile') else f"#{1000 + user.id}")

    if not bio or not bio.face_enrolled:
        return JsonResponse({
            'success': False,
            'unlocked': False,
            'error': 'Face ID is not registered yet. Please scan or upload your face photo first.'
        }, status=400)

    if summary['door_access_active']:
        log = DoorAccessLog.objects.create(
            user=user,
            zk_pin=pin,
            event_type='ENTRY',
            verify_mode='FACE_ID',
            device_ip='192.168.1.23',
            terminal_name='MAIN_TURNSTILE_FACE_CAM',
            raw_payload={'face_verified': True, 'method': 'face_recognition'}
        )
        return JsonResponse({
            'success': True,
            'unlocked': True,
            'message': f"Face Verified! Turnstile Speed Gate Unlocked. Welcome, {user.get_full_name() or user.username}!",
            'pin': pin,
            'punch_id': log.id,
            'timestamp': log.punch_time.strftime('%H:%M:%S')
        })
    else:
        log = DoorAccessLog.objects.create(
            user=user,
            zk_pin=pin,
            event_type='DENIED',
            verify_mode='FACE_ID',
            device_ip='192.168.1.23',
            terminal_name='MAIN_TURNSTILE_FACE_CAM',
            raw_payload={'face_verified': True, 'reason': 'Membership expired'}
        )
        return JsonResponse({
            'success': False,
            'unlocked': False,
            'error': 'Access Denied: Membership Expired. Turnstile remained locked. Please renew your plan to restore door access.',
            'expired': True
        }, status=403)



@csrf_exempt
def enroll_fingerprint_api(request):
    """
    Endpoint: /api/zkbio/enroll-fingerprint/
    Dispatches a command to put the turnstile terminal (192.168.1.23) into 3-tap fingerprint enrollment mode.
    """
    if not (request.user.is_authenticated and request.user.is_staff):
        return HttpResponseForbidden('Staff credentials required')

    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else request.POST
    except Exception:
        data = request.POST

    user_id = data.get('user_id')
    pin = data.get('pin')

    target_user = None
    if user_id:
        target_user = User.objects.filter(id=user_id).first()
    elif pin:
        bio = BiometricProfile.objects.filter(zk_pin=pin).first()
        if bio:
            target_user = bio.user

    if not target_user:
        return JsonResponse({'error': 'Member not found'}, status=404)

    bio_profile, mp = get_or_create_biometric_profile(target_user)

    cmd = BiometricCommand.objects.create(
        command_type='ENROLL_FP',
        zk_pin=bio_profile.zk_pin,
        user=target_user,
        status='PENDING',
        payload={'user_id': target_user.id, 'name': target_user.get_full_name() or target_user.username}
    )

    return JsonResponse({
        'success': True,
        'command_id': cmd.id,
        'pin': bio_profile.zk_pin,
        'member_name': target_user.get_full_name() or target_user.username,
        'message': f"Turnstile optical reader ready! Please ask member to place finger 3 times."
    })


@csrf_exempt
def check_command_status_api(request, command_id):
    """
    Endpoint: /api/zkbio/command-status/<int:command_id>/
    Allows UI to poll the execution status of a fingerprint or face enrollment command.
    """
    cmd = BiometricCommand.objects.filter(id=command_id).first()
    if not cmd:
        return JsonResponse({'error': 'Command not found'}, status=404)

    return JsonResponse({
        'command_id': cmd.id,
        'status': cmd.status,
        'command_type': cmd.command_type,
        'pin': cmd.zk_pin,
        'result_message': cmd.result_message,
        'executed_at': cmd.executed_at.isoformat() if cmd.executed_at else None
    })


@csrf_exempt
def pending_commands_api(request):
    """
    Endpoint: /api/zkbio/pending-commands/
    Polled by bridge daemon to pick up pending hardware actions (e.g. START_ENROLL_FP).
    """
    if not verify_bridge_token(request):
        if not (request.user.is_authenticated and request.user.is_staff):
            return HttpResponseForbidden('Unauthorized daemon token')

    pending = BiometricCommand.objects.filter(status='PENDING')[:10]
    items = []
    for c in pending:
        items.append({
            'id': c.id,
            'command_type': c.command_type,
            'zk_pin': c.zk_pin,
            'payload': c.payload,
            'device_ip': c.device_ip
        })
    return JsonResponse({'commands': items, 'count': len(items)})


@csrf_exempt
def update_command_status_api(request):
    """
    Endpoint: /api/zkbio/update-command/
    Bridge daemon updates execution result of a hardware command.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    if not verify_bridge_token(request):
        if not (request.user.is_authenticated and request.user.is_staff):
            return HttpResponseForbidden('Unauthorized daemon token')

    try:
        data = json.loads(request.body.decode('utf-8'))
        command_id = data.get('command_id')
        status = data.get('status', 'COMPLETED')
        message = data.get('result_message', '')

        cmd = BiometricCommand.objects.filter(id=command_id).first()
        if not cmd:
            return JsonResponse({'error': 'Command not found'}, status=404)

        cmd.status = status
        cmd.result_message = message
        cmd.executed_at = timezone.now()
        cmd.save()

        # If fingerprint enrollment completed, update BiometricProfile
        if cmd.command_type == 'ENROLL_FP' and status == 'COMPLETED':
            bio = BiometricProfile.objects.filter(zk_pin=cmd.zk_pin).first()
            if bio:
                bio.fingerprint_enrolled = True
                bio.sync_status = 'SYNCED'
                bio.save(update_fields=['fingerprint_enrolled', 'sync_status'])

        return JsonResponse({'success': True, 'command_id': cmd.id, 'status': status})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
def remote_buzzer_trigger(request):
    """
    Endpoint: /api/zkbio/remote-buzzer/
    Admin-authorized trigger to buzz open turnstile door immediately on 192.168.1.23.
    """
    if not (request.user.is_authenticated and request.user.is_staff):
        return HttpResponseForbidden('Staff credentials required')

    DoorAccessLog.objects.create(
        user=request.user,
        zk_pin='BUZZER',
        event_type='ENTRY',
        verify_mode='BUZZER',
        device_ip='192.168.1.23',
        terminal_name='REMOTE_BUZZER_OVERRIDE',
        raw_payload={'triggered_by': request.user.username, 'timestamp': timezone.now().isoformat()}
    )

    return JsonResponse({
        'success': True,
        'message': f'Remote door buzzer pulsed by {request.user.username}',
        'device_ip': '192.168.1.23'
    })


# Micro-cache for high-frequency polling endpoints to eliminate SQLite locks and CPU spikes
_FLOOR_STATUS_CACHE = {'ts': 0, 'data': None}
_RECENT_PUNCHES_CACHE = {'ts': 0, 'data': None}


def floor_status_api(request):
    """
    Endpoint: /api/zkbio/floor-status/
    Returns real-time floor count: active members and staff on the floor.
    Micro-cached for 3 seconds to avoid continuous SQLite table scans.
    """
    import time
    now_ts = time.time()
    if _FLOOR_STATUS_CACHE['data'] and (now_ts - _FLOOR_STATUS_CACHE['ts'] < 3.0):
        return JsonResponse(_FLOOR_STATUS_CACHE['data'])

    today = timezone.now().date()
    today_logs = DoorAccessLog.objects.filter(
        punch_time__date=today,
        event_type__in=['ENTRY', 'EXIT']
    ).select_related('user').order_by('punch_time')

    user_latest_event = {}
    for log in today_logs:
        key = log.user_id if log.user_id else f"pin_{log.zk_pin}"
        user_latest_event[key] = (log.event_type, log.user)

    members_on_floor = 0
    staff_on_floor = 0

    for key, (event_type, user) in user_latest_event.items():
        if event_type == 'ENTRY':
            if user and user.is_staff:
                staff_on_floor += 1
            else:
                members_on_floor += 1

    payload = {
        'members_on_floor': members_on_floor,
        'staff_on_floor': staff_on_floor,
        'total_on_floor': members_on_floor + staff_on_floor,
        'timestamp': timezone.now().isoformat()
    }
    _FLOOR_STATUS_CACHE['ts'] = now_ts
    _FLOOR_STATUS_CACHE['data'] = payload

    return JsonResponse(payload)


def recent_punches_api(request):
    """
    Endpoint: /api/zkbio/recent-punches/
    Returns the latest 15 door access attempts for real-time front desk monitoring.
    Uses batch queries and a 3-second micro-cache to eliminate N+1 DB bottlenecks.
    """
    import time
    now_ts = time.time()
    if _RECENT_PUNCHES_CACHE['data'] and (now_ts - _RECENT_PUNCHES_CACHE['ts'] < 3.0):
        return JsonResponse(_RECENT_PUNCHES_CACHE['data'])

    logs = list(DoorAccessLog.objects.select_related('user', 'user__member_profile').order_by('-punch_time')[:15])
    user_ids = [l.user_id for l in logs if l.user_id]

    user_plans = {}
    if user_ids:
        active_subs = Subscription.objects.filter(
            member_id__in=user_ids,
            status='active'
        ).select_related('plan')
        for sub in active_subs:
            if sub.member_id not in user_plans and sub.plan:
                user_plans[sub.member_id] = sub.plan.name

    items = []
    for l in logs:
        user = l.user
        photo_url = ''
        full_name = 'Walk-in / Hardware Scan'
        plan_name = user_plans.get(l.user_id, 'Floor Access') if l.user_id else 'Floor Access'

        if user:
            full_name = user.get_full_name() or user.username
            mp = getattr(user, 'member_profile', None)
            if mp and mp.profile_photo:
                try:
                    photo_url = mp.profile_photo.url
                except Exception:
                    photo_url = ''

        reason = ''
        if isinstance(l.raw_payload, dict):
            reason = l.raw_payload.get('reason', '')

        items.append({
            'id': l.id,
            'user_name': user.username if user else f"PIN:{l.zk_pin}",
            'full_name': full_name,
            'photo_url': photo_url,
            'punch_time': l.punch_time.strftime('%H:%M:%S'),
            'punch_date': l.punch_time.strftime('%d %b'),
            'event_type': l.event_type,
            'verify_mode': l.verify_mode,
            'allowed': l.event_type in ['ENTRY', 'EXIT'],
            'reason': reason,
            'plan_name': plan_name,
            'terminal_name': l.terminal_name
        })

    payload = {'punches': items, 'count': len(items)}
    _RECENT_PUNCHES_CACHE['ts'] = now_ts
    _RECENT_PUNCHES_CACHE['data'] = payload

    return JsonResponse(payload)
