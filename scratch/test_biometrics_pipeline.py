import os
import sys
import json
import base64
from datetime import timedelta
import django

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.main')
django.setup()

import sys
sys.stdout.reconfigure(encoding='utf-8')
from django.test import Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from wger.membership.models import MemberProfile, MembershipPlan, Subscription
from wger.zkbio_integration.models import BiometricProfile, DoorAccessLog, BiometricCommand

User = get_user_model()
client = Client()

print("=" * 60)
print("🏋️ FIT ME — 100% FACE ID & FINGERPRINT BIOMETRICS TEST")
print("=" * 60)

# 1. Ensure staff user exists for authenticated endpoints
staff_user, _ = User.objects.get_or_create(
    username='test_frontdesk',
    defaults={'is_staff': True, 'email': 'frontdesk@fitme.lk', 'first_name': 'Front', 'last_name': 'Desk'}
)
staff_user.is_staff = True
staff_user.save()
client.force_login(staff_user)

# 2. Create / Get Test Member with Active Subscription
plan, _ = MembershipPlan.objects.get_or_create(
    plan_type='individual',
    defaults={'name': 'Individual Standard', 'price_monthly': 4500, 'duration_days': 30}
)

member_user, _ = User.objects.get_or_create(
    username='dilshan_test_member',
    defaults={'email': 'dilshan@fitme.lk', 'first_name': 'Dilshan', 'last_name': 'Perera'}
)
mp, _ = MemberProfile.objects.get_or_create(
    user=member_user,
    defaults={'biometric_pin': '1999', 'phone': '0771234567'}
)
if not mp.biometric_pin:
    mp.biometric_pin = '1999'
    mp.save()

bio_profile, _ = BiometricProfile.objects.get_or_create(
    user=member_user,
    defaults={'zk_pin': mp.biometric_pin, 'face_enrolled': False, 'fingerprint_enrolled': False}
)
bio_profile.disabled = False
bio_profile.save()

# Active Subscription
today = timezone.now().date()
Subscription.objects.filter(member=member_user).delete()
sub = Subscription.objects.create(
    member=member_user,
    plan=plan,
    start_date=today - timedelta(days=2),
    end_date=today + timedelta(days=28),
    status='active',
    amount_paid=4500
)

print(f"✓ Test Member Ready: {member_user.username} (Hardware ID: #FM{mp.biometric_pin})")
print(f"✓ Active Subscription: Valid until {sub.end_date}")

# --- TEST 1: Face ID WebCam / Photo Upload Endpoint ---
print("\n--- [TEST 1] Upload Face ID Template ---")
# 1x1 white pixel JPEG in base64
dummy_jpeg_b64 = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA="

face_resp = client.post('/api/zkbio/upload-face/', json.dumps({
    'user_id': member_user.id,
    'pin': mp.biometric_pin,
    'photo_base64': dummy_jpeg_b64
}), content_type='application/json')

assert face_resp.status_code == 200, f"Face upload failed: {face_resp.content}"
face_data = face_resp.json()
assert face_data.get('success') is True, "Face upload success flag not True"

bio_profile.refresh_from_db()
mp.refresh_from_db()
assert bio_profile.face_enrolled is True, "bio_profile.face_enrolled should be True"
assert bool(mp.profile_photo), "Member profile photo was not saved"
print(f"✓ Face ID enrolled successfully: {face_data.get('message')}")
print(f"✓ Member photo stored at: {mp.profile_photo.url}")

# --- TEST 2: Fingerprint Turnstile Enrollment Command Dispatch ---
print("\n--- [TEST 2] Trigger Turnstile Fingerprint Enrollment ---")
fp_resp = client.post('/api/zkbio/enroll-fingerprint/', json.dumps({
    'user_id': member_user.id,
    'pin': mp.biometric_pin
}), content_type='application/json')

assert fp_resp.status_code == 200, f"Fingerprint enroll failed: {fp_resp.content}"
fp_data = fp_resp.json()
cmd_id = fp_data.get('command_id')
assert cmd_id is not None, "Command ID missing"
print(f"✓ Fingerprint enrollment command queued: ID {cmd_id}")

# Verify Bridge Daemon Pending Commands endpoint
cmd_poll_resp = client.get('/api/zkbio/pending-commands/', HTTP_AUTHORIZATION='Bearer fitme-zkbio-secret-bridge-token-2026')
assert cmd_poll_resp.status_code == 200
pending_cmds = cmd_poll_resp.json().get('commands', [])
matching_cmd = [c for c in pending_cmds if c['id'] == cmd_id]
assert len(matching_cmd) == 1, "Daemon failed to see pending enrollment command"
print("✓ Local Bridge Daemon successfully fetched pending turnstile command")

# Daemon executes 3-touch optical read and completes command
update_resp = client.post('/api/zkbio/update-command/', json.dumps({
    'command_id': cmd_id,
    'status': 'COMPLETED',
    'result_message': 'Sensor captured 3 scans successfully'
}), content_type='application/json', HTTP_AUTHORIZATION='Bearer fitme-zkbio-secret-bridge-token-2026')

assert update_resp.status_code == 200
bio_profile.refresh_from_db()
assert bio_profile.fingerprint_enrolled is True, "bio_profile.fingerprint_enrolled should now be True"
print(f"✓ Fingerprint enrollment marked COMPLETED: bio_profile.fingerprint_enrolled = {bio_profile.fingerprint_enrolled}")

# --- TEST 3: Dynamic Real-time Door Access (Face ID Scan) ---
print("\n--- [TEST 3] Real-time Face ID Turnstile Punch ---")
# Clear previous logs for clean anti-passback test
DoorAccessLog.objects.filter(zk_pin=mp.biometric_pin).delete()

punch_face_resp = client.post('/api/zkbio/punches/', json.dumps({
    'pin': mp.biometric_pin,
    'direction': 'IN',
    'verify_mode': 'FACE_ID',
    'device_ip': '192.168.1.23',
    'terminal_name': 'MAIN_TURNSTILE'
}), content_type='application/json', HTTP_AUTHORIZATION='Bearer fitme-zkbio-secret-bridge-token-2026')

assert punch_face_resp.status_code == 200, f"Punch failed: {punch_face_resp.content}"
punch_face_data = punch_face_resp.json()
assert punch_face_data.get('allowed') is True, "Active member Face ID was denied"
assert punch_face_data.get('verify_mode') == 'FACE_ID', "Verify mode was not FACE_ID"
print(f"✓ Face ID Access GRANTED: {punch_face_data}")

# --- TEST 4: Anti-Passback 60s Cooldown ---
print("\n--- [TEST 4] Anti-Passback Cooldown Enforcement ---")
duplicate_resp = client.post('/api/zkbio/punches/', json.dumps({
    'pin': mp.biometric_pin,
    'direction': 'IN',
    'verify_mode': 'FACE_ID'
}), content_type='application/json', HTTP_AUTHORIZATION='Bearer fitme-zkbio-secret-bridge-token-2026')

assert duplicate_resp.status_code == 429, f"Anti-passback failed to block: {duplicate_resp.status_code}"
dup_data = duplicate_resp.json()
assert dup_data.get('status') == 'anti_passback', "Status should be anti_passback"
print(f"✓ Anti-passback BLOCKED duplicate entry within 60s: {dup_data}")

# --- TEST 5: Optical Fingerprint Exit Punch ---
print("\n--- [TEST 5] Optical Fingerprint Exit Punch ---")
punch_fp_resp = client.post('/api/zkbio/punches/', json.dumps({
    'pin': mp.biometric_pin,
    'direction': 'OUT',
    'verify_mode': 'FINGERPRINT',
    'device_ip': '192.168.1.23'
}), content_type='application/json', HTTP_AUTHORIZATION='Bearer fitme-zkbio-secret-bridge-token-2026')

assert punch_fp_resp.status_code == 200
punch_fp_data = punch_fp_resp.json()
assert punch_fp_data.get('allowed') is True
assert punch_fp_data.get('verify_mode') == 'FINGERPRINT'
print(f"✓ Fingerprint Exit GRANTED: {punch_fp_data}")

# --- TEST 6: Expired Subscription Dynamic Lockout ---
print("\n--- [TEST 6] Expired Subscription Dynamic Lockout ---")
# Expire subscription
sub.start_date = today - timedelta(days=40)
sub.end_date = today - timedelta(days=10)
sub.status = 'expired'
sub.save()

expired_punch_resp = client.post('/api/zkbio/punches/', json.dumps({
    'pin': mp.biometric_pin,
    'direction': 'IN',
    'verify_mode': 'FACE_ID'
}), content_type='application/json', HTTP_AUTHORIZATION='Bearer fitme-zkbio-secret-bridge-token-2026')

assert expired_punch_resp.status_code == 200
exp_data = expired_punch_resp.json()
assert exp_data.get('allowed') is False, "Expired member should NOT be allowed"
assert exp_data.get('status') == 'denied', "Status should be denied"
print(f"✓ Expired Member Door Access DENIED: {exp_data.get('reason')}")

bio_profile.refresh_from_db()
assert bio_profile.disabled is True, "Hardware profile should be automatically disabled"
print(f"✓ BiometricProfile.disabled automatically set to True for hardware sync")

# --- TEST 7: Live Feed APIs ---
print("\n--- [TEST 7] Live Feed & Reception Monitor APIs ---")
recent_resp = client.get('/api/zkbio/recent-punches/')
assert recent_resp.status_code == 200
recent_data = recent_resp.json()
assert 'punches' in recent_data and len(recent_data['punches']) > 0
print(f"✓ Recent Punches API returned {len(recent_data['punches'])} events for front-desk live monitor")

floor_resp = client.get('/api/zkbio/floor-status/')
assert floor_resp.status_code == 200
floor_data = floor_resp.json()
print(f"✓ Floor Status API: Members on Floor = {floor_data.get('members_on_floor')}, Staff = {floor_data.get('staff_on_floor')}")

# Restore active sub for clean state
sub.start_date = today
sub.end_date = today + timedelta(days=30)
sub.status = 'active'
sub.save()
bio_profile.disabled = False
bio_profile.save()

print("\n" + "=" * 60)
print("🎉 ALL BIOMETRIC PIPELINE TESTS PASSED 100%!")
print("=" * 60)
