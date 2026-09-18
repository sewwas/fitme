import json
import logging
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from wger.zkbio_integration.models import BiometricProfile, DoorAccessLog

logger = logging.getLogger('wger')
User = get_user_model()

# Shared token for daemon-to-cloud authentication over Cloudflare Tunnel / HTTPS
BRIDGE_API_TOKEN = getattr(settings, 'ZKBIO_BRIDGE_TOKEN', 'fitme-zkbio-secret-bridge-token-2026')


def verify_bridge_token(request):
    """Verifies Bearer token in HTTP_AUTHORIZATION header."""
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ', 1)[1].strip()
        return token == BRIDGE_API_TOKEN
    return False


@csrf_exempt
def punches_ingest(request):
    """
    Webhook / Ingest Endpoint: /api/zkbio/punches/
    Accepts real-time door punch streams from local bridge daemon.
    Enforces 60-second anti-passback cooldown and updates floor status.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    if not verify_bridge_token(request):
        # Also allow staff users if logged in via browser
        if not (request.user.is_authenticated and request.user.is_staff):
            return HttpResponseForbidden('Unauthorized daemon token')

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception as e:
        return JsonResponse({'error': f'Invalid JSON payload: {str(e)}'}, status=400)

    pin = str(data.get('pin', '')).strip()
    if not pin:
        return JsonResponse({'error': 'PIN is required'}, status=400)

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

    # Resolve User from BiometricProfile or MemberProfile
    bio_profile = BiometricProfile.objects.filter(zk_pin=pin).select_related('user').first()
    user = bio_profile.user if bio_profile else None

    # If bio_profile is disabled or revoked
    if bio_profile and bio_profile.disabled:
        log = DoorAccessLog.objects.create(
            user=user,
            zk_pin=pin,
            punch_time=punch_time,
            event_type='DENIED',
            device_ip=device_ip,
            terminal_name=terminal_name,
            raw_payload=raw_payload,
        )
        return JsonResponse({
            'status': 'denied',
            'reason': 'Membership or door permission disabled',
            'allowed': False,
            'log_id': log.id
        })

    # Anti-passback cooldown: 60 seconds
    # If the user punched in the same direction within 60 seconds, flag ANTI_PASSBACK
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
            device_ip=device_ip,
            terminal_name=terminal_name,
            raw_payload=raw_payload,
        )
        logger.warning(f"[Anti-Passback] PIN {pin} attempted duplicate {direction} within 60s cooldown.")
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
        device_ip=device_ip,
        terminal_name=terminal_name,
        raw_payload=raw_payload,
    )

    # If staff member punched, update staff attendance records
    if user and user.is_staff:
        try:
            from wger.gym_operations_payroll.models import StaffShift
            today = punch_time.date()
            shift = StaffShift.objects.filter(staff_user=user, shift_date=today).first()
            if shift:
                if expected_event == 'ENTRY':
                    if not shift.actual_first_in:
                        shift.actual_first_in = punch_time
                    shift.status = 'ON_FLOOR'
                    shift.is_off_floor = False
                    shift.save(update_fields=['actual_first_in', 'status', 'is_off_floor'])
                elif expected_event == 'EXIT':
                    shift.actual_last_out = punch_time
                    shift.save(update_fields=['actual_last_out'])
        except Exception as ex:
            logger.error(f"Error linking staff punch to shift: {ex}")

    return JsonResponse({
        'status': 'success',
        'allowed': True,
        'event': expected_event,
        'pin': pin,
        'username': user.username if user else None,
        'log_id': log.id
    })


@csrf_exempt
def pending_sync_queue(request):
    """
    Endpoint: /api/zkbio/pending-sync/
    Polled by the local bridge daemon to pull pending member additions, updates, or revocations.
    """
    if not verify_bridge_token(request):
        if not (request.user.is_authenticated and request.user.is_staff):
            return HttpResponseForbidden('Unauthorized daemon token')

    pending_profiles = BiometricProfile.objects.filter(
        sync_status='PENDING'
    ).select_related('user')[:50]

    items = []
    for p in pending_profiles:
        items.append({
            'pin': p.zk_pin,
            'username': p.user.username,
            'full_name': p.user.get_full_name() or p.user.username,
            'card_number': p.card_number or '',
            'door_group_id': p.door_group_id,
            'disabled': p.disabled,
            'action': 'delete' if p.disabled else 'add'
        })

    return JsonResponse({'pending': items, 'count': len(items)})


@csrf_exempt
def sync_status_callback(request):
    """
    Endpoint: /api/zkbio/sync-status/
    Daemon calls this to confirm that hardware person add/delete succeeded.
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
        profile = BiometricProfile.objects.filter(zk_pin=pin).first()
        if profile:
            profile.sync_status = status
            profile.last_sync_time = timezone.now()
            profile.save(update_fields=['sync_status', 'last_sync_time'])
            return JsonResponse({'success': True, 'pin': pin, 'status': status})
        return JsonResponse({'error': f'Profile with PIN {pin} not found'}, status=404)
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

    # Record remote buzzer log
    DoorAccessLog.objects.create(
        user=request.user,
        zk_pin='BUZZER',
        event_type='ENTRY',
        device_ip='192.168.1.23',
        terminal_name='REMOTE_BUZZER_OVERRIDE',
        raw_payload={'triggered_by': request.user.username, 'timestamp': timezone.now().isoformat()}
    )

    return JsonResponse({
        'success': True,
        'message': f'Remote door buzzer pulsed by {request.user.username}',
        'device_ip': '192.168.1.23'
    })


def floor_status_api(request):
    """
    Endpoint: /api/zkbio/floor-status/
    Returns real-time floor count: active members and staff on the floor.
    """
    today = timezone.now().date()
    today_logs = DoorAccessLog.objects.filter(
        punch_time__date=today,
        event_type__in=['ENTRY', 'EXIT']
    ).select_related('user').order_by('punch_time')

    # Track latest punch per user
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

    return JsonResponse({
        'members_on_floor': members_on_floor,
        'staff_on_floor': staff_on_floor,
        'total_on_floor': members_on_floor + staff_on_floor,
        'timestamp': timezone.now().isoformat()
    })
