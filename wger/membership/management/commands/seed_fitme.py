"""
Fit Me management command: seed all initial data.
Usage: python manage.py seed_fitme
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from wger.membership.models import MembershipPlan
from wger.nutrition_lk.models import LocalFood


class Command(BaseCommand):
    help = 'Seed Fit Me initial data: RBAC groups, membership plans, Sri Lankan food DB'

    def handle(self, *args, **options):
        self._seed_groups()
        self._seed_plans()
        self._seed_foods()
        self.stdout.write(self.style.SUCCESS('\n=== Fit Me seed complete ==='))

    def _seed_groups(self):
        self.stdout.write('Creating RBAC groups...')
        for name in ['super_admin', 'front_desk', 'coach', 'member']:
            _, created = Group.objects.get_or_create(name=name)
            status = 'Created' if created else 'Exists'
            self.stdout.write(f'  {status}: {name}')

    def _seed_plans(self):
        self.stdout.write('\nSeeding membership plans...')
        plans = [
            {'name': 'Individual', 'plan_type': 'individual', 'price_monthly': 4500.00, 'duration_days': 30, 'max_members': 1, 'description': 'Standard single member gym access.'},
            {'name': 'Couples / Buddy', 'plan_type': 'couples', 'price_monthly': 7500.00, 'duration_days': 30, 'max_members': 2, 'description': 'Two members sharing one plan.'},
            {'name': 'Student', 'plan_type': 'student', 'price_monthly': 3000.00, 'duration_days': 30, 'max_members': 1, 'description': 'Discounted plan for students with valid ID.'},
            {'name': 'Off-Peak', 'plan_type': 'off_peak', 'price_monthly': 2500.00, 'duration_days': 30, 'max_members': 1, 'description': 'Access limited to 6am-12pm and 2pm-5pm weekdays.'},
        ]
        for p in plans:
            obj, created = MembershipPlan.objects.get_or_create(plan_type=p['plan_type'], defaults=p)
            status = 'Created' if created else 'Exists'
            self.stdout.write(f'  {status}: {obj.name} — LKR {obj.price_monthly}/mo')

    def _seed_foods(self):
        self.stdout.write('\nSeeding Sri Lankan food database...')
        foods = [
            # Rice & Grains
            {'name_en': 'Steamed White Rice', 'name_si': 'Sudu Buth', 'category': 'rice_grains', 'calories_per_100g': 130, 'protein_g': 2.7, 'carbs_g': 28.2, 'fat_g': 0.3, 'fiber_g': 0.4, 'default_serving_g': 200},
            {'name_en': 'Red Rice (Rathu Kekulu)', 'name_si': 'Rathu Kekulu Buth', 'category': 'rice_grains', 'calories_per_100g': 111, 'protein_g': 2.6, 'carbs_g': 23.5, 'fat_g': 0.9, 'fiber_g': 1.8, 'default_serving_g': 200},
            {'name_en': 'String Hoppers (Indi Appa)', 'name_si': 'Indi Appa', 'category': 'rice_grains', 'calories_per_100g': 140, 'protein_g': 3.0, 'carbs_g': 31.0, 'fat_g': 0.5, 'fiber_g': 0.3, 'default_serving_g': 150},
            {'name_en': 'Pittu', 'name_si': 'Pittu', 'category': 'rice_grains', 'calories_per_100g': 180, 'protein_g': 4.5, 'carbs_g': 38.0, 'fat_g': 1.0, 'fiber_g': 1.2, 'default_serving_g': 150},
            {'name_en': 'Roti (Plain)', 'name_si': 'Pol Roti', 'category': 'rice_grains', 'calories_per_100g': 290, 'protein_g': 7.0, 'carbs_g': 44.0, 'fat_g': 9.5, 'fiber_g': 2.5, 'default_serving_g': 80},
            {'name_en': 'Hoppers (Appa)', 'name_si': 'Appa', 'category': 'rice_grains', 'calories_per_100g': 162, 'protein_g': 3.2, 'carbs_g': 32.5, 'fat_g': 2.5, 'fiber_g': 0.8, 'default_serving_g': 100},
            {'name_en': 'Samaposha', 'name_si': 'Samaposha', 'category': 'rice_grains', 'calories_per_100g': 379, 'protein_g': 12.5, 'carbs_g': 68.0, 'fat_g': 6.0, 'fiber_g': 4.5, 'default_serving_g': 50},
            {'name_en': 'Bread (White Loaf)', 'name_si': 'Paan', 'category': 'rice_grains', 'calories_per_100g': 265, 'protein_g': 9.0, 'carbs_g': 49.0, 'fat_g': 3.2, 'fiber_g': 2.7, 'default_serving_g': 60},
            # Curries
            {'name_en': 'Dhal Curry (Parippu)', 'name_si': 'Parippu', 'category': 'curry_stew', 'calories_per_100g': 116, 'protein_g': 7.6, 'carbs_g': 14.5, 'fat_g': 3.5, 'fiber_g': 3.8, 'default_serving_g': 150},
            {'name_en': 'Chicken Curry', 'name_si': 'Kukul Mas Curry', 'category': 'curry_stew', 'calories_per_100g': 165, 'protein_g': 18.0, 'carbs_g': 4.5, 'fat_g': 8.5, 'fiber_g': 0.5, 'default_serving_g': 150},
            {'name_en': 'Fish Curry', 'name_si': 'Maalu Curry', 'category': 'curry_stew', 'calories_per_100g': 140, 'protein_g': 17.0, 'carbs_g': 3.0, 'fat_g': 6.5, 'fiber_g': 0.3, 'default_serving_g': 150},
            {'name_en': 'Jackfruit Curry (Kos)', 'name_si': 'Kos Curry', 'category': 'curry_stew', 'calories_per_100g': 95, 'protein_g': 2.2, 'carbs_g': 18.5, 'fat_g': 2.0, 'fiber_g': 2.5, 'default_serving_g': 150},
            {'name_en': 'Pol Sambol', 'name_si': 'Pol Sambol', 'category': 'curry_stew', 'calories_per_100g': 185, 'protein_g': 2.5, 'carbs_g': 6.0, 'fat_g': 17.0, 'fiber_g': 4.0, 'default_serving_g': 50},
            {'name_en': 'Egg Curry', 'name_si': 'Bittara Curry', 'category': 'curry_stew', 'calories_per_100g': 148, 'protein_g': 10.5, 'carbs_g': 3.0, 'fat_g': 10.5, 'fiber_g': 0.2, 'default_serving_g': 150},
            {'name_en': 'Beef Curry', 'name_si': 'Harak Mas Curry', 'category': 'curry_stew', 'calories_per_100g': 185, 'protein_g': 19.0, 'carbs_g': 3.5, 'fat_g': 10.5, 'fiber_g': 0.3, 'default_serving_g': 150},
            # Protein
            {'name_en': 'Boiled Egg', 'name_si': 'Bittara', 'category': 'protein', 'calories_per_100g': 155, 'protein_g': 13.0, 'carbs_g': 1.1, 'fat_g': 11.0, 'fiber_g': 0.0, 'default_serving_g': 60},
            {'name_en': 'Grilled Chicken Breast', 'name_si': 'Kukul Mas', 'category': 'protein', 'calories_per_100g': 165, 'protein_g': 31.0, 'carbs_g': 0.0, 'fat_g': 3.6, 'fiber_g': 0.0, 'default_serving_g': 150},
            {'name_en': 'Canned Tuna', 'name_si': 'Tuna', 'category': 'protein', 'calories_per_100g': 109, 'protein_g': 25.5, 'carbs_g': 0.0, 'fat_g': 0.8, 'fiber_g': 0.0, 'default_serving_g': 85},
            {'name_en': 'Whey Protein Shake', 'name_si': 'Protein Powder', 'category': 'supplements', 'calories_per_100g': 373, 'protein_g': 75.0, 'carbs_g': 8.0, 'fat_g': 5.5, 'fiber_g': 1.0, 'default_serving_g': 30},
            # Vegetables
            {'name_en': 'Gotukola Sambol', 'name_si': 'Gotukola', 'category': 'vegetables', 'calories_per_100g': 43, 'protein_g': 2.5, 'carbs_g': 5.0, 'fat_g': 1.5, 'fiber_g': 2.5, 'default_serving_g': 80},
            {'name_en': 'Mallum (mixed greens)', 'name_si': 'Mallum', 'category': 'vegetables', 'calories_per_100g': 35, 'protein_g': 2.8, 'carbs_g': 4.0, 'fat_g': 0.8, 'fiber_g': 3.5, 'default_serving_g': 80},
            {'name_en': 'Spinach (Nivithi)', 'name_si': 'Nivithi', 'category': 'vegetables', 'calories_per_100g': 23, 'protein_g': 2.9, 'carbs_g': 3.6, 'fat_g': 0.4, 'fiber_g': 2.2, 'default_serving_g': 80},
            # Fruits
            {'name_en': 'Banana (Ambul)', 'name_si': 'Ambul Kesel', 'category': 'fruits', 'calories_per_100g': 89, 'protein_g': 1.1, 'carbs_g': 22.8, 'fat_g': 0.3, 'fiber_g': 2.6, 'default_serving_g': 120},
            {'name_en': 'King Coconut Water', 'name_si': 'Thambili', 'category': 'beverages', 'calories_per_100g': 22, 'protein_g': 0.7, 'carbs_g': 5.0, 'fat_g': 0.1, 'fiber_g': 0.2, 'default_serving_g': 350},
            {'name_en': 'Curd (Buffalo)', 'name_si': 'Meekiri', 'category': 'dairy', 'calories_per_100g': 98, 'protein_g': 4.5, 'carbs_g': 3.8, 'fat_g': 7.0, 'fiber_g': 0.0, 'default_serving_g': 100},
        ]
        created_count = sum(1 for f in foods if LocalFood.objects.get_or_create(name_en=f['name_en'], defaults=f)[1])
        self.stdout.write(f'  Seeded {created_count} new / {len(foods) - created_count} already existed')
