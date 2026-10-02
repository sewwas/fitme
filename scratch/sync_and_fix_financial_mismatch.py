import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.local_dev')
django.setup()

from django.db.models import Sum
from decimal import Decimal
from django.contrib.auth import get_user_model
from wger.membership.models import Subscription, MembershipPlan
from wger.gym_operations_payroll.models import PaymentReceipt
from wger.pos.models import POSSale
from django.utils import timezone

User = get_user_model()
admin = User.objects.filter(is_superuser=True).first() or User.objects.filter(username='admin').first()

print("=== AUDIT BEFORE FIX ===")
sub_sum = Subscription.objects.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
rcpt_sum = PaymentReceipt.objects.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
pos_sum = POSSale.objects.filter(status='COMPLETED').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
print(f"Total Subscription dues recorded: LKR {sub_sum}")
print(f"Total Payment Receipts recorded:   LKR {rcpt_sum}")
print(f"Total POS Store sales recorded:    LKR {pos_sum}")
print(f"Discrepancy (Missing in Receipts): LKR {sub_sum - rcpt_sum}")

# Find all subscriptions that have no PaymentReceipt
missing_subs = Subscription.objects.filter(receipts__isnull=True).order_by('id')
print(f"\nFound {missing_subs.count()} subscriptions without PaymentReceipts. Backfilling now...")

for s in missing_subs:
    rcpt_num = PaymentReceipt.generate_next_receipt_number()
    # Use start_date as issued_at date
    issued_dt = timezone.make_aware(timezone.datetime.combine(s.start_date, timezone.datetime.min.time()))
    rcpt = PaymentReceipt.objects.create(
        receipt_number=rcpt_num,
        member=s.member,
        subscription=s,
        cashier=s.approved_by or admin,
        plan_name=s.plan.name,
        duration_days=s.plan.duration_days,
        validity_start=s.start_date,
        validity_end=s.end_date,
        amount_paid=s.amount_paid,
        payment_method=s.payment_method or 'cash',
        issued_at=issued_dt,
        notes=f"Official receipt backfilled for subscription #{s.id}"
    )
    print(f"  + Generated {rcpt.receipt_number} for {s.member.username} ({s.plan.name}): LKR {s.amount_paid}")

print("\n=== AUDIT AFTER FIX ===")
sub_sum_after = Subscription.objects.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
rcpt_sum_after = PaymentReceipt.objects.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
print(f"Total Subscription dues recorded: LKR {sub_sum_after}")
print(f"Total Payment Receipts recorded:   LKR {rcpt_sum_after}")
print(f"Discrepancy:                       LKR {sub_sum_after - rcpt_sum_after}")
assert sub_sum_after == rcpt_sum_after, "Receipts and Subscriptions still do not match!"

print("\n=== BILLING PACKAGES BREAKDOWN VERIFICATION ===")
for p in MembershipPlan.objects.all():
    p_subs = Subscription.objects.filter(plan=p)
    p_rcpts = PaymentReceipt.objects.filter(subscription__plan=p)
    p_sub_sum = p_subs.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
    p_rcpt_sum = p_rcpts.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
    print(f"Plan: {p.name:<30} Subs: {p_subs.count():<3} Sub Total: LKR {p_sub_sum:<10} Rcpt Total: LKR {p_rcpt_sum:<10} Match: {p_sub_sum == p_rcpt_sum}")

print("\n[SUCCESS] Financial reconciliation complete! All subscription dues now match 100% with the ledger!")
