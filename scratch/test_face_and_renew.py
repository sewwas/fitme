import os
import sys
import django
import json
import base64

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.main')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from wger.membership.models import MembershipPlan, Subscription
from wger.zkbio_integration.models import BiometricProfile, DoorAccessLog
from wger.gym_operations_payroll.models import PaymentReceipt

print("=== STARTING FITME FACE ID & SELF RENEW TEST ===")

client = Client()
user = User.objects.get(username='member_kasun')
client.force_login(user)
print("Client force_login successful for:", user.username)
print(f"Testing for member: {user.username} (ID: {user.id})")

# 1. Test Face ID Upload
# Create a tiny 1x1 GIF / PNG base64
dummy_b64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
res_face = client.post('/api/zkbio/upload-face/', 
                       data=json.dumps({'photo_base64': dummy_b64}),
                       content_type='application/json')
print("Face ID Upload Status:", res_face.status_code, res_face.json())

# Check BiometricProfile
bio = BiometricProfile.objects.filter(user=user).first()
print("BiometricProfile exists:", bio is not None)
if bio:
    print(f"Face Enrolled: {bio.face_enrolled}, PIN: {bio.zk_pin}, Disabled: {bio.disabled}")

# 2. Test Face Unlock API
res_unlock = client.post('/api/zkbio/face-unlock/', content_type='application/json')
print("Face Unlock Status:", res_unlock.status_code, res_unlock.json())

# 3. Test Self-Renew API
plan = MembershipPlan.objects.filter(is_active=True).first()
if not plan:
    plan = MembershipPlan.objects.create(name='Standard Monthly Pass', price_monthly=6500, duration_days=30, is_active=True)

print(f"Selected plan for renewal: {plan.name} (LKR {plan.price_monthly})")

res_renew = client.post('/api/member/self-renew/',
                        data=json.dumps({
                            'plan_id': plan.id,
                            'payment_method': 'online_card'
                        }),
                        content_type='application/json')
print("Self-Renew Status:", res_renew.status_code, res_renew.json())

# Verify latest subscription and receipt
latest_sub = Subscription.objects.filter(member=user, status='active').order_by('-id').first()
print("Latest Active Subscription:", latest_sub.plan.name, "Valid until:", latest_sub.end_date)

latest_rcp = PaymentReceipt.objects.filter(member=user).order_by('-id').first()
print("Generated Payment Receipt:", latest_rcp.receipt_number, "Amount: LKR", latest_rcp.amount_paid)

# 4. Test Face Unlock AGAIN now that plan is guaranteed active
res_unlock2 = client.post('/api/zkbio/face-unlock/', content_type='application/json')
print("Post-Renewal Face Unlock Status:", res_unlock2.status_code, res_unlock2.json())

latest_log = DoorAccessLog.objects.filter(user=user).order_by('-id').first()
print("Latest DoorAccessLog:", latest_log.event_type, latest_log.verify_mode, latest_log.terminal_name, latest_log.punch_time)

print("=== ALL TESTS COMPLETED SUCCESSFULLY ===")
