import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.local_dev')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth import get_user_model
from wger.membership.models import MembershipPlan, Subscription

User = get_user_model()

client = Client()

print("--- Testing Super Admin vs Club Admin ---")

# 1. Super Admin login test
logged_in_super = client.login(username='admin', password='fitme123!')
print("Super Admin logged in:", logged_in_super)
resp_super = client.get('/dashboard/admin/')
print(f"Super Admin GET /dashboard/admin/ status: {resp_super.status_code}")
assert resp_super.status_code == 200
assert b"+ Make New Plan" in resp_super.content
assert b"Super Admin (Master)" in resp_super.content
print("Confirmed '+ Make New Plan' and 'Super Admin (Master)' badge visible to Super Admin")

# Test creating plan as Super Admin
res_plan = client.post('/api/plans/create/', data={
    'name': 'Test Super Plan',
    'plan_type': 'test_super_type',
    'price_monthly': '9999.00',
    'original_price': '12000.00',
    'discount': '2001.00',
    'registration_fee': '1000.00',
    'duration_days': 30,
    'max_members': 1,
    'description': 'Test description'
}, content_type='application/json')
print(f"Super Admin create plan status: {res_plan.status_code}, response: {res_plan.json().get('message')}")
assert res_plan.status_code == 200
created_plan_id = res_plan.json()['plan']['id']

# Clean up created plan
MembershipPlan.objects.filter(id=created_plan_id).delete()

client.logout()

# 2. Club Admin (admin_ops) login test
logged_in_ops = client.login(username='admin_ops', password='fitme123!')
print("\nClub Admin logged in:", logged_in_ops)
resp_ops = client.get('/dashboard/admin/')
print(f"Club Admin GET /dashboard/admin/ status: {resp_ops.status_code}")
assert resp_ops.status_code == 200
assert b"Club Admin" in resp_ops.content
assert b"+ Make New Plan" not in resp_ops.content
assert b"Override Locked" not in resp_ops.content
assert b"Super Admin Protected" not in resp_ops.content
assert b">Locked<" not in resp_ops.content
print("Confirmed '+ Make New Plan', 'Override Locked', and 'Protected' are ALL HIDDEN from Club Admin (only active options visible)")

# Test unauthorized create plan attempt by Club Admin
res_unauth_plan = client.post('/api/plans/create/', data={
    'name': 'Hacked Plan',
    'plan_type': 'hacked_type',
    'price_monthly': '1.00'
}, content_type='application/json')
print(f"Club Admin create plan attempt status: {res_unauth_plan.status_code}, json: {res_unauth_plan.json()}")
assert res_unauth_plan.status_code == 403

# Test unauthorized subscription data override attempt by Club Admin
first_sub = Subscription.objects.first()
if first_sub:
    res_unauth_sub = client.post(f'/api/subscriptions/{first_sub.id}/override/', data={
        'end_date': '2030-01-01',
        'status': 'active'
    }, content_type='application/json')
    print(f"Club Admin sub override attempt status: {res_unauth_sub.status_code}, json: {res_unauth_sub.json()}")
    assert res_unauth_sub.status_code == 403
    print("Confirmed Club Admin cannot override subscription data (403 Forbidden)")

client.logout()
print("\nALL ROLE SEPARATION TESTS PASSED WITH 100% SUCCESS!")
