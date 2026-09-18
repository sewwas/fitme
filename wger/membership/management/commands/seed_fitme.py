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
        self._seed_demo_accounts_and_activities()

    def _seed_demo_accounts_and_activities(self):
        self.stdout.write('\nSeeding demo accounts, member profiles, applications, and logs...')
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group
        from django.utils import timezone
        from wger.membership.models import MemberProfile, Subscription, MemberApplication, BodyCheckIn
        from wger.zkbio_integration.models import BiometricProfile, DoorAccessLog
        from wger.gym_operations_payroll.models import StaffShift, SuddenAbsenceAlert, PayrollLedger
        from wger.nutrition_lk.models import MealLog, DailyFuelTarget
        from wger.habit.models import WorkoutStreak, HabitPing
        User = get_user_model()

        today = timezone.now().date()
        ind_plan = MembershipPlan.objects.filter(plan_type='individual').first() or MembershipPlan.objects.first()
        couples_plan = MembershipPlan.objects.filter(plan_type='couples').first() or ind_plan

        # 1. Super Admin
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@fitme.com', 'first_name': 'Super', 'last_name': 'Admin', 'is_staff': True, 'is_superuser': True}
        )
        admin_user.set_password('fitme123!')
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()
        admin_group, _ = Group.objects.get_or_create(name='super_admin')
        admin_user.groups.add(admin_group)

        # 2. Front Desk
        fd_user, _ = User.objects.get_or_create(
            username='frontdesk',
            defaults={'email': 'frontdesk@fitme.com', 'first_name': 'Amal', 'last_name': 'Perera', 'is_staff': True}
        )
        fd_user.set_password('fitme123!')
        fd_user.is_staff = True
        fd_user.save()
        fd_group, _ = Group.objects.get_or_create(name='front_desk')
        fd_user.groups.add(fd_group)

        # 3. Coach Kamal
        coach_user, _ = User.objects.get_or_create(
            username='coach_kamal',
            defaults={'email': 'kamal@fitme.com', 'first_name': 'Kamal', 'last_name': 'Gunaratne', 'is_staff': True}
        )
        coach_user.set_password('fitme123!')
        coach_user.is_staff = True
        coach_user.save()
        coach_group, _ = Group.objects.get_or_create(name='coach')
        coach_user.groups.add(coach_group)

        # 4. Member Kasun
        kasun, _ = User.objects.get_or_create(
            username='member_kasun',
            defaults={'email': 'kasun@gmail.com', 'first_name': 'Kasun', 'last_name': 'Jayawardena'}
        )
        kasun.set_password('fitme123!')
        kasun.save()
        member_group, _ = Group.objects.get_or_create(name='member')
        kasun.groups.add(member_group)

        profile_kasun, _ = MemberProfile.objects.get_or_create(
            user=kasun,
            defaults={
                'biometric_pin': '1001',
                'primary_goal': 'muscle_gain',
                'phone': '0778899001',
                'assigned_coach': coach_user,
                'starting_weight_kg': 72.5,
                'height_cm': 176.0,
            }
        )
        BiometricProfile.objects.get_or_create(
            user=kasun,
            defaults={'zk_pin': '1001', 'sync_status': 'SYNCED', 'disabled': False}
        )
        Subscription.objects.get_or_create(
            member=kasun,
            status='active',
            defaults={
                'plan': ind_plan,
                'start_date': today - timezone.timedelta(days=10),
                'end_date': today + timezone.timedelta(days=20),
                'amount_paid': 4500.00,
                'payment_method': 'card',
                'approved_by': admin_user
            }
        )
        streak_kasun, _ = WorkoutStreak.objects.get_or_create(
            member=kasun,
            defaults={'current_streak': 5, 'longest_streak': 14, 'last_checkin_date': today, 'total_checkins': 32}
        )
        DailyFuelTarget.objects.get_or_create(
            member=kasun,
            defaults={'target_calories': 2200, 'target_protein_g': 150, 'target_carbs_g': 250, 'target_fat_g': 65}
        )

        # 5. Member Nuwan (At Risk!)
        nuwan, _ = User.objects.get_or_create(
            username='member_nuwan',
            defaults={'email': 'nuwan@gmail.com', 'first_name': 'Nuwan', 'last_name': 'Bandara'}
        )
        nuwan.set_password('fitme123!')
        nuwan.save()
        nuwan.groups.add(member_group)

        profile_nuwan, _ = MemberProfile.objects.get_or_create(
            user=nuwan,
            defaults={
                'biometric_pin': '1002',
                'primary_goal': 'weight_loss',
                'phone': '0714455667',
                'assigned_coach': coach_user,
                'starting_weight_kg': 88.0,
                'height_cm': 172.0,
            }
        )
        BiometricProfile.objects.get_or_create(
            user=nuwan,
            defaults={'zk_pin': '1002', 'sync_status': 'SYNCED', 'disabled': False}
        )
        Subscription.objects.get_or_create(
            member=nuwan,
            status='active',
            defaults={
                'plan': ind_plan,
                'start_date': today - timezone.timedelta(days=25),
                'end_date': today + timezone.timedelta(days=5),
                'amount_paid': 4500.00,
                'payment_method': 'cash',
                'approved_by': admin_user
            }
        )
        WorkoutStreak.objects.get_or_create(
            member=nuwan,
            defaults={'current_streak': 1, 'longest_streak': 8, 'last_checkin_date': today - timezone.timedelta(days=3), 'total_checkins': 15}
        )

        # 6. Unreviewed Meal Logs
        MealLog.objects.get_or_create(
            member=kasun,
            notes='Lunch - Red rice, chicken curry, dhal & gotukola sambol',
            defaults={
                'meal_type': 'lunch',
                'logged_at': timezone.now() - timezone.timedelta(hours=2),
                'total_calories': 680,
                'total_protein_g': 48,
                'total_carbs_g': 78,
                'total_fat_g': 16,
                'coach_reviewed': False
            }
        )
        MealLog.objects.get_or_create(
            member=nuwan,
            notes='Breakfast - 5 string hoppers with fish curry',
            defaults={
                'meal_type': 'breakfast',
                'logged_at': timezone.now() - timezone.timedelta(hours=5),
                'total_calories': 410,
                'total_protein_g': 24,
                'total_carbs_g': 55,
                'total_fat_g': 9,
                'coach_reviewed': False
            }
        )

        # 7. Front Desk Pending Applications
        apps_data = [
            {'full_name': 'Ruwan Perera', 'email': 'ruwan.p@outlook.com', 'phone': '0771234567', 'primary_goal': 'weight_loss', 'desired_plan': ind_plan},
            {'full_name': 'Dilshan Silva', 'email': 'dilshan.silva@gmail.com', 'phone': '0719876543', 'primary_goal': 'muscle_gain', 'desired_plan': couples_plan},
            {'full_name': 'Anusha Fernando', 'email': 'anusha.f@yahoo.com', 'phone': '0755554433', 'primary_goal': 'general_fitness', 'desired_plan': ind_plan},
        ]
        for a in apps_data:
            MemberApplication.objects.get_or_create(email=a['email'], defaults=a)

        # 8. Staff Shift & Sudden Absence Alert
        shift_today, _ = StaffShift.objects.get_or_create(
            staff_user=coach_user,
            shift_date=today,
            defaults={
                'scheduled_start': '08:00:00',
                'scheduled_end': '17:00:00',
                'status': 'OFF_FLOOR',
                'is_off_floor': True,
                'actual_first_in': timezone.now() - timezone.timedelta(hours=4)
            }
        )
        SuddenAbsenceAlert.objects.get_or_create(
            shift=shift_today,
            staff_user=coach_user,
            is_resolved=False,
            defaults={
                'exit_time': timezone.now() - timezone.timedelta(minutes=35),
                'minutes_off_floor': 35,
                'admin_notes': 'Coach left premises mid-shift during floor duty.'
            }
        )

        # 9. Door Access Logs today (Turnstile 192.168.1.23)
        DoorAccessLog.objects.get_or_create(
            zk_pin='1001',
            punch_time=timezone.now() - timezone.timedelta(hours=1),
            defaults={'user': kasun, 'event_type': 'ENTRY', 'device_ip': '192.168.1.23'}
        )
        DoorAccessLog.objects.get_or_create(
            zk_pin='1002',
            punch_time=timezone.now() - timezone.timedelta(hours=2),
            defaults={'user': nuwan, 'event_type': 'ENTRY', 'device_ip': '192.168.1.23'}
        )
        DoorAccessLog.objects.get_or_create(
            zk_pin='ADMIN',
            punch_time=timezone.now() - timezone.timedelta(hours=5),
            defaults={'user': admin_user, 'event_type': 'ENTRY', 'device_ip': '192.168.1.23'}
        )

        self.stdout.write('  Seeded accounts, applications, shifts, alerts, and punches successfully!')

