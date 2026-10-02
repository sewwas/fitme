import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.local_dev')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from wger.membership.models import MembershipPlan, Subscription
from wger.gym_operations_payroll.models import BuddyMembership
from wger.zkbio_integration.models import BiometricProfile
from wger.membership.services import get_member_access_summary, check_and_expire_subscriptions
from datetime import timedelta
from django.utils import timezone

User = get_user_model()
admin_user = User.objects.filter(username='admin').first() or User.objects.filter(is_superuser=True).first()

# Setup primary and partner users
primary_user, _ = User.objects.get_or_create(username='test_primary_couple', defaults={'first_name': 'Kamal', 'last_name': 'Perera'})
partner_user, _ = User.objects.get_or_create(username='test_partner_couple', defaults={'first_name': 'Nimali', 'last_name': 'Perera'})
third_user, _ = User.objects.get_or_create(username='test_third_user', defaults={'first_name': 'Sunil', 'last_name': 'Perera'})

# Get or create Couples plan (max_members=2)
couple_plan = MembershipPlan.objects.filter(max_members=2, is_active=True).first()
if not couple_plan:
    couple_plan = MembershipPlan.objects.create(
        name="Couples Test Plan",
        plan_type="couples_test",
        price_monthly=7500,
        duration_days=30,
        max_members=2,
        is_active=True
    )

today = timezone.now().date()
# Create active subscription for primary user
sub, _ = Subscription.objects.get_or_create(
    member=primary_user,
    plan=couple_plan,
    defaults={
        'start_date': today,
        'end_date': today + timedelta(days=30),
        'status': 'active',
        'amount_paid': couple_plan.price_monthly
    }
)
sub.status = 'active'
sub.start_date = today
sub.end_date = today + timedelta(days=30)
sub.save()

# Check initial status: Primary should have access, Partner should NOT have access yet
primary_summary = get_member_access_summary(primary_user)
partner_summary = get_member_access_summary(partner_user)

print("Primary before link: active =", primary_summary['door_access_active'])
print("Partner before link: active =", partner_summary['door_access_active'])
assert primary_summary['door_access_active'] is True
assert partner_summary['door_access_active'] is False

# Test Linking Partner via API
client = Client()
client.force_login(admin_user)

link_resp = client.post(f'/api/subscriptions/{sub.id}/link-partner/', data={'partner_id': partner_user.id}, content_type='application/json')
print("Link response:", link_resp.status_code, link_resp.json())
assert link_resp.status_code == 200
link_id = link_resp.json()['link_id']

# Check Partner status after link
partner_summary_after = get_member_access_summary(partner_user)
print("Partner after link: active =", partner_summary_after['door_access_active'], "status_label =", partner_summary_after['status_label'])
assert partner_summary_after['door_access_active'] is True
assert partner_summary_after['is_partner'] is True

# Test Limit: Trying to link 3rd member to 2-member plan must fail
excess_resp = client.post(f'/api/subscriptions/{sub.id}/link-partner/', data={'partner_id': third_user.id}, content_type='application/json')
print("Excess partner link status (expected 400):", excess_resp.status_code, excess_resp.json())
assert excess_resp.status_code == 400

# Test Unlink API
unlink_resp = client.post(f'/api/buddy-links/{link_id}/delete/')
print("Unlink status:", unlink_resp.status_code, unlink_resp.json())
assert unlink_resp.status_code == 200

# Check Partner status after unlink: door access should be revoked
partner_summary_unlinked = get_member_access_summary(partner_user)
print("Partner after unlink: active =", partner_summary_unlinked['door_access_active'])
assert partner_summary_unlinked['door_access_active'] is False

# Re-link partner for demonstration
client.post(f'/api/subscriptions/{sub.id}/link-partner/', data={'partner_id': partner_user.id}, content_type='application/json')
print("\n[SUCCESS] 1 User vs 2 Users / 3 Users Multi-User link tested and verified 100% working!")
