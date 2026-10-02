import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.local_dev')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from wger.gym_operations_payroll.models import ClubExpense
from django.utils import timezone

User = get_user_model()
admin_user = User.objects.filter(username='admin').first() or User.objects.filter(is_superuser=True).first()

client = Client()
client.force_login(admin_user)

# Create a dummy image
dummy_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xdc\xccY\xe7\x00\x00\x00\x00IEND\xaeB`\x82'
uploaded_file = SimpleUploadedFile("ceb_bill_oct.png", dummy_image_data, content_type="image/png")

post_data = {
    'title': 'Commercial Electricity Bill Proof Test',
    'category': 'electricity',
    'amount': '26500.00',
    'expense_date': str(timezone.now().date()),
    'payment_method': 'bank_transfer',
    'receipt_ref': 'CEB-TEST-7788',
    'notes': 'Attaching official CEB bill image proof',
    'receipt_image': uploaded_file
}

resp = client.post('/api/expenses/create/', data=post_data)
print("Create expense response:", resp.status_code, resp.json())
assert resp.status_code == 200
exp_id = resp.json()['expense']['id']

exp = ClubExpense.objects.get(id=exp_id)
assert exp.receipt_image, "receipt_image was not saved on ClubExpense"
print("Saved receipt image path:", exp.receipt_image.name)
print("Saved receipt image URL:", exp.receipt_image.url)

# Test media serving
resp_media = client.get(exp.receipt_image.url)
print(f"GET {exp.receipt_image.url} status: {resp_media.status_code}")
assert resp_media.status_code == 200, "Media file was not served properly"

# Test dashboard rendering
resp_dash = client.get('/dashboard/admin/?tab=tab-admin-payments')
assert resp_dash.status_code == 200
dash_html = resp_dash.content.decode('utf-8')
assert 'View Bill' in dash_html, "'View Bill' button not rendered in table"
assert exp.receipt_image.url in dash_html, "Receipt image URL not found in table row"

print("\n[SUCCESS] Receipt proof image upload, database storage, media serving, and UI View Bill button verified perfectly!")
