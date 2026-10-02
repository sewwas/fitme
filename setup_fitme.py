"""
Fit Me -- One-Command Bootstrap Script
Run this once to fully initialize the portal:
  .venv\\Scripts\\python.exe setup_fitme.py

This script:
  1. Runs all database migrations
  2. Creates the 4 permission groups
  3. Seeds Membership Plans (Individual, Couples, Student, Off-Peak)
  4. Seeds Sri Lankan food database (25 foods)
  5. Prompts to create a Super Admin account
  6. Creates a sample Coach profile
  7. Prints startup URLs
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.local_dev')

# Bootstrap Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.core.management import call_command
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()


def separator(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


# -- Step 1: Migrations ---------------------------------------------
separator("Step 1: Applying Migrations")
call_command('migrate', '--run-syncdb', verbosity=1)
print("[OK] All migrations applied.")


# -- Step 2: Load wger Required Seed Data -------------------------
separator("Step 2: Loading wger Base Data")
from wger.core.models import Language
if Language.objects.count() == 0:
    for fixture in ['languages', 'licenses', 'setting_repetition_units',
                    'setting_weight_units', 'categories', 'equipment',
                    'muscles', 'exercise-base-data']:
        call_command('loaddata', fixture, verbosity=0)
    print(f"[OK] Loaded base data ({Language.objects.count()} languages, exercise data, units).")
else:
    print(f"  -> Base data already loaded ({Language.objects.count()} languages).")


# -- Step 2: Permission Groups -------------------------------------
separator("Step 2: Creating Permission Groups")
groups = ['super_admin', 'front_desk', 'coach', 'member']
for g in groups:
    group, created = Group.objects.get_or_create(name=g)
    status = 'created' if created else 'already exists'
    print(f"  -> Group '{g}': {status}")
print("[OK] Permission groups ready.")


# -- Step 3: Membership Plans -------------------------------------
separator("Step 3: Seeding Membership Plans")
from wger.membership.models import MembershipPlan

plans_data = [
    {
        'name': 'Monthly Package',
        'plan_type': 'individual',
        'price_monthly': Decimal('4000.00'),
        'original_price': Decimal('4000.00'),
        'discount': Decimal('0.00'),
        'registration_fee': Decimal('1000.00'),
        'duration_days': 30,
        'max_members': 1,
        'description': 'Standard single member gym access. Total: Rs. 4,000 / month.',
    },
    {
        'name': '3 Months Package',
        'plan_type': 'three_months',
        'price_monthly': Decimal('11000.00'),
        'original_price': Decimal('12000.00'),
        'discount': Decimal('1000.00'),
        'registration_fee': Decimal('1000.00'),
        'duration_days': 90,
        'max_members': 1,
        'description': '3 Months package. Original Price: Rs. 12,000, Discount: Rs. 1,000. Total: Rs. 11,000.',
    },
    {
        'name': '6 Months Package',
        'plan_type': 'six_months',
        'price_monthly': Decimal('21500.00'),
        'original_price': Decimal('24000.00'),
        'discount': Decimal('2500.00'),
        'registration_fee': Decimal('1000.00'),
        'duration_days': 180,
        'max_members': 1,
        'description': '6 Months package. Original Price: Rs. 24,000, Discount: Rs. 2,500. Total: Rs. 21,500.',
    },
    {
        'name': 'Couple Monthly Package',
        'plan_type': 'couples',
        'price_monthly': Decimal('7500.00'),
        'original_price': Decimal('8000.00'),
        'discount': Decimal('500.00'),
        'registration_fee': Decimal('1000.00'),
        'duration_days': 30,
        'max_members': 2,
        'description': 'Two members sharing one monthly plan. Original Price: Rs. 8,000, Discount: Rs. 500. Total: Rs. 7,500 / month.',
    },
    {
        'name': '3 Persons Family Monthly Package',
        'plan_type': 'family_3',
        'price_monthly': Decimal('11000.00'),
        'original_price': Decimal('12000.00'),
        'discount': Decimal('1000.00'),
        'registration_fee': Decimal('1000.00'),
        'duration_days': 30,
        'max_members': 3,
        'description': '3 Persons from same family monthly package. Original Price: Rs. 12,000, Discount: Rs. 1,000. Total: Rs. 11,000 / month.',
    },
    {
        'name': 'Student Package',
        'plan_type': 'student',
        'price_monthly': Decimal('3500.00'),
        'original_price': Decimal('3500.00'),
        'discount': Decimal('0.00'),
        'registration_fee': Decimal('0.00'),
        'duration_days': 30,
        'max_members': 1,
        'description': 'Discounted plan for students with valid ID. No Registration Fee! Total: Rs. 3,500 / month.',
    },
]

for plan_data in plans_data:
    plan, created = MembershipPlan.objects.update_or_create(
        plan_type=plan_data['plan_type'],
        defaults=plan_data
    )
    status = 'created' if created else 'updated'
    print(f"  -> Plan '{plan.name}' (LKR {plan.price_monthly}/mo): {status}")
print("[OK] Membership plans seeded.")


# -- Step 4: Sri Lankan Food Database ----------------------------
separator("Step 4: Seeding Sri Lankan Food Database")
from wger.nutrition_lk.models import LocalFood
if LocalFood.objects.count() == 0:
    call_command('loaddata', 'wger/nutrition_lk/fixtures/local_foods.json', verbosity=1)
    print(f"[OK] Loaded {LocalFood.objects.count()} Sri Lankan foods.")
else:
    print(f"  -> Already has {LocalFood.objects.count()} foods -- skipping.")


# -- Step 5: Gym & GymConfig (required by wger context processor) ---
separator("Step 5: Seeding Gym & GymConfig")
from wger.gym.models import Gym
from wger.config.models import GymConfig

gym, g_created = Gym.objects.get_or_create(
    pk=1,
    defaults={
        'name': 'Fit Me Fitness Club',
        'email': 'info@fitme.lk',
        'phone': '070 762 7878',
        'zip_code': '80420',
        'city': 'Pitigala',
        'street': 'Elpitiya Road, New Town',
    }
)
print(f"  -> Gym: {'created' if g_created else 'exists'} -> {gym.name}")

gc, gc_created = GymConfig.objects.get_or_create(
    pk=1,
    defaults={'default_gym': gym}
)
print(f"  -> GymConfig pk=1: {'created' if gc_created else 'exists'}")
print("[OK] Gym config ready.")


# -- Step 6: Superuser ------------------------------------------
separator("Step 6: Create Super Admin Account")
if User.objects.filter(is_superuser=True).exists():
    print("  -> A superuser already exists -- skipping.")
else:
    print("  Enter credentials for your Super Admin account:")
    username = input("  Username [admin]: ").strip() or 'admin'
    email = input("  Email: ").strip()
    password = input("  Password: ").strip()
    if username and password:
        user = User.objects.create_superuser(username=username, email=email, password=password)
        super_group, _ = Group.objects.get_or_create(name='super_admin')
        user.groups.add(super_group)
        print(f"[OK] Superuser '{username}' created and assigned to super_admin group.")
    else:
        print("  [SKIP] Skipped -- username or password was empty.")


# -- Done -------------------------------------------------------
separator("Setup Complete!")
print("""
FitMe Portal is ready. Run the server with:

    .venv\\Scripts\\python.exe manage.py runserver 8000 --settings=settings.local_dev

Then visit:

    Portal Login:     http://localhost:8000/login/
    Member Portal:    http://localhost:8000/dashboard/
    Django Admin:     http://localhost:8000/en/user/admin-overview
    API Docs:         http://localhost:8000/api/v2/schema/ui
    Next.js Site:     http://localhost:3000  (run: cd fitme-ui && npm run dev)
""")

This script:
  1. Runs all database migrations
  2. Creates the 4 permission groups
  3. Seeds Membership Plans (Individual, Couples, Student, Off-Peak)
  4. Seeds Sri Lankan food database (25 foods)
  5. Prompts to create a Super Admin account
  6. Creates a sample Coach profile
  7. Prints startup URLs
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.local_dev')

# Bootstrap Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.core.management import call_command
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()


def separator(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


# ── Step 1: Migrations ──────────────────────────────────────────
separator("Step 1: Applying Migrations")
call_command('migrate', '--run-syncdb', verbosity=1)
print("✅ All migrations applied.")


# ── Step 2: Permission Groups ────────────────────────────────────
separator("Step 2: Creating Permission Groups")
groups = ['super_admin', 'front_desk', 'coach', 'member']
for g in groups:
    group, created = Group.objects.get_or_create(name=g)
    status = 'created' if created else 'already exists'
    print(f"  → Group '{g}': {status}")
print("✅ Permission groups ready.")


# ── Step 3: Membership Plans ─────────────────────────────────────
separator("Step 3: Seeding Membership Plans")
from wger.membership.models import MembershipPlan

plans_data = [
    {
        'name': 'Monthly Package',
        'plan_type': 'individual',
        'price_monthly': Decimal('4000.00'),
        'original_price': Decimal('4000.00'),
        'discount': Decimal('0.00'),
        'registration_fee': Decimal('1000.00'),
        'duration_days': 30,
        'max_members': 1,
        'description': 'Standard single member gym access. Total: Rs. 4,000 / month.',
    },
    {
        'name': '3 Months Package',
        'plan_type': 'three_months',
        'price_monthly': Decimal('11000.00'),
        'original_price': Decimal('12000.00'),
        'discount': Decimal('1000.00'),
        'registration_fee': Decimal('1000.00'),
        'duration_days': 90,
        'max_members': 1,
        'description': '3 Months package. Original Price: Rs. 12,000, Discount: Rs. 1,000. Total: Rs. 11,000.',
    },
    {
        'name': '6 Months Package',
        'plan_type': 'six_months',
        'price_monthly': Decimal('21500.00'),
        'original_price': Decimal('24000.00'),
        'discount': Decimal('2500.00'),
        'registration_fee': Decimal('1000.00'),
        'duration_days': 180,
        'max_members': 1,
        'description': '6 Months package. Original Price: Rs. 24,000, Discount: Rs. 2,500. Total: Rs. 21,500.',
    },
    {
        'name': 'Couple Monthly Package',
        'plan_type': 'couples',
        'price_monthly': Decimal('7500.00'),
        'original_price': Decimal('8000.00'),
        'discount': Decimal('500.00'),
        'registration_fee': Decimal('1000.00'),
        'duration_days': 30,
        'max_members': 2,
        'description': 'Two members sharing one monthly plan. Original Price: Rs. 8,000, Discount: Rs. 500. Total: Rs. 7,500 / month.',
    },
    {
        'name': '3 Persons Family Monthly Package',
        'plan_type': 'family_3',
        'price_monthly': Decimal('11000.00'),
        'original_price': Decimal('12000.00'),
        'discount': Decimal('1000.00'),
        'registration_fee': Decimal('1000.00'),
        'duration_days': 30,
        'max_members': 3,
        'description': '3 Persons from same family monthly package. Original Price: Rs. 12,000, Discount: Rs. 1,000. Total: Rs. 11,000 / month.',
    },
    {
        'name': 'Student Package',
        'plan_type': 'student',
        'price_monthly': Decimal('3500.00'),
        'original_price': Decimal('3500.00'),
        'discount': Decimal('0.00'),
        'registration_fee': Decimal('0.00'),
        'duration_days': 30,
        'max_members': 1,
        'description': 'Discounted plan for students with valid ID. No Registration Fee! Total: Rs. 3,500 / month.',
    },
]

for plan_data in plans_data:
    plan, created = MembershipPlan.objects.update_or_create(
        plan_type=plan_data['plan_type'],
        defaults=plan_data
    )
    status = 'created' if created else 'updated'
    print(f"  → Plan '{plan.name}' (LKR {plan.price_monthly}/mo): {status}")
print("✅ Membership plans seeded.")


# ── Step 4: Sri Lankan Food Database ─────────────────────────────
separator("Step 4: Seeding Sri Lankan Food Database")
from wger.nutrition_lk.models import LocalFood
if LocalFood.objects.count() == 0:
    call_command('loaddata', 'wger/nutrition_lk/fixtures/local_foods.json', verbosity=1)
    print(f"✅ Loaded {LocalFood.objects.count()} Sri Lankan foods.")
else:
    print(f"  → Already has {LocalFood.objects.count()} foods — skipping.")


# ── Step 5: Superuser ─────────────────────────────────────────────
separator("Step 5: Create Super Admin Account")
if User.objects.filter(is_superuser=True).exists():
    print("  → A superuser already exists — skipping.")
else:
    print("  Enter credentials for your Super Admin account:")
    username = input("  Username [admin]: ").strip() or 'admin'
    email = input("  Email: ").strip()
    password = input("  Password: ").strip()
    if username and password:
        user = User.objects.create_superuser(username=username, email=email, password=password)
        super_group, _ = Group.objects.get_or_create(name='super_admin')
        user.groups.add(super_group)
        print(f"✅ Superuser '{username}' created and assigned to super_admin group.")
    else:
        print("  ⚠ Skipped — username or password was empty.")


# ── Done ──────────────────────────────────────────────────────────
separator("Setup Complete!")
print("""
🚀 FitMe Portal is ready. Run the server with:

    .venv\\Scripts\\python.exe manage.py runserver 8000 --settings=settings.local_dev

Then visit:

    Portal Login:     http://localhost:8000/login/
    Member Portal:    http://localhost:8000/dashboard/
    Django Admin:     http://localhost:8000/en/user/admin-overview
    API Docs:         http://localhost:8000/api/v2/schema/ui
    Next.js Site:     http://localhost:3000  (run: cd fitme-ui && npm run dev)
""")
