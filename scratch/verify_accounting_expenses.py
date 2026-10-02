import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.local_dev')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from wger.gym_operations_payroll.models import ClubExpense
from decimal import Decimal
from django.utils import timezone

User = get_user_model()
admin_user = User.objects.filter(username='admin').first()
if not admin_user:
    admin_user = User.objects.filter(is_superuser=True).first()

print(f"Testing with user: {admin_user.username}")

client = Client()
client.force_login(admin_user)

# 1. Test Admin Dashboard with financial tab
resp = client.get('/dashboard/admin/?tab=tab-admin-payments')
print(f"GET /dashboard/admin/?tab=tab-admin-payments status: {resp.status_code}")
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
content = resp.content.decode('utf-8')
assert 'Financial Ledger, OPEX' in content, "Financial title missing from dashboard"
assert 'Club Operating Expenses (OPEX Ledger)' in content, "OPEX ledger table missing"
assert 'Billing Package Performance' in content, "Package breakdown table missing"
print("[OK] Admin Financial tab rendered with 200 OK and all tables present!")

# 2. Test Create Expense API
exp_payload = {
    'title': 'Test Water Supply Tank Refill',
    'category': 'water',
    'amount': 4500.00,
    'expense_date': str(timezone.now().date()),
    'payment_method': 'cash',
    'receipt_ref': 'TEST-WAT-001',
    'notes': 'Automated verification test'
}
resp_post = client.post('/api/expenses/create/', data=exp_payload, content_type='application/json')
print(f"POST /api/expenses/create/ status: {resp_post.status_code}, data: {resp_post.json()}")
assert resp_post.status_code == 200, f"Expected 200, got {resp_post.status_code}"
created_exp_id = resp_post.json()['expense']['id']

# 3. Test Export Expenses CSV
resp_csv = client.get('/dashboard/admin/reports/export-expenses-csv/')
print(f"GET /dashboard/admin/reports/export-expenses-csv/ status: {resp_csv.status_code}")
assert resp_csv.status_code == 200, "CSV export failed"
assert 'Content-Disposition' in resp_csv.headers
assert 'Test Water Supply Tank Refill' in resp_csv.content.decode('utf-8')
print("[OK] Expense CSV Export verified successfully!")

# 4. Test Delete Expense API
resp_del = client.post(f'/api/expenses/{created_exp_id}/delete/')
print(f"POST /api/expenses/{created_exp_id}/delete/ status: {resp_del.status_code}, data: {resp_del.json()}")
assert resp_del.status_code == 200, "Expense deletion failed"
assert not ClubExpense.objects.filter(id=created_exp_id).exists()
print("[OK] Expense deletion verified successfully!")

print("\nALL ACCOUNTING & EXPENSES TESTS PASSED PERFECTLY!")
