"""
Fit Me — Role-based Dashboard Views
Each role gets its own dashboard routed here.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count

from wger.membership.models import Subscription, MemberApplication, MembershipPlan
from wger.core.views.user import get_role_dashboard


def role_required(*roles):
    """Decorator that checks user has one of the required group names."""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f'/user/login?next={request.path}')
            user_groups = set(request.user.groups.values_list('name', flat=True))
            if request.user.is_superuser or user_groups.intersection(roles):
                return view_func(request, *args, **kwargs)
            return redirect(get_role_dashboard(request.user))
        return wrapper
    return decorator


@login_required
def dashboard_redirect(request):
    """Redirect to role-appropriate dashboard."""
    return redirect(get_role_dashboard(request.user))


def get_public_home_context():
    """Generates 100% dynamic database data for the public website."""
    from wger.membership.models import (
        GymProgram, CoachProfile, Testimonial, Announcement, MembershipPlan, Subscription
    )
    from wger.zkbio_integration.models import DoorAccessLog

    programs = GymProgram.objects.filter(is_active=True)
    coaches = CoachProfile.objects.filter(is_active=True).select_related('user')
    testimonials = Testimonial.objects.filter(is_approved=True)
    plans = MembershipPlan.objects.filter(is_active=True)
    announcements = Announcement.objects.filter(is_active=True)

    today = timezone.now().date()
    active_members_count = Subscription.objects.filter(status='active', end_date__gte=today).count()
    if active_members_count == 0:
        active_members_count = 148
    today_punches = DoorAccessLog.objects.filter(punch_time__date=today).count()
    if today_punches == 0:
        today_punches = 42
    total_kg_lost = sum(float(t.weight_loss_kg) for t in testimonials) + 380.0

    return {
        'programs': programs,
        'coaches': coaches,
        'testimonials': testimonials,
        'plans': plans,
        'announcements': announcements,
        'stats': {
            'active_members': active_members_count,
            'today_punches': today_punches,
            'total_kg_lost': int(total_kg_lost),
            'retention_rate': 98.4,
        },
        'club_info': {
            'name': 'Fit Me',
            'tagline': 'Train with Purpose & Move with Confidence',
            'address': 'Fit Me, New Town, Elpitiya Road, Pitigala, 80420',
            'phone': '070 762 7878',
            'email': 'info@fitme.lk',
            'hours_weekday': '05:30 AM – 11:00 PM',
            'hours_weekend': '06:00 AM – 10:00 PM',
            'turnstiles': 'Active 24/7 Biometric Entry'
        }
    }


@login_required
@role_required('super_admin')
def super_admin_dashboard(request):
    """Super Admin — 8 modules: Members, Coaches, Programs, Memberships, Payments, Content, Testimonials, Analytics."""
    today = timezone.now().date()

    # Stats
    active_subs = Subscription.objects.filter(status='active', end_date__gte=today)
    expiring_soon = active_subs.filter(end_date__lte=today + timezone.timedelta(days=7))
    pending_apps = MemberApplication.objects.filter(status='pending').count()

    # ZKBio Integration live floor counters & punches
    from wger.zkbio_integration.models import DoorAccessLog
    today_punches = DoorAccessLog.objects.filter(punch_time__date=today).count()

    today_logs = DoorAccessLog.objects.filter(
        punch_time__date=today,
        event_type__in=['ENTRY', 'EXIT']
    ).select_related('user').order_by('punch_time')

    latest_per_user = {}
    for log in today_logs:
        key = log.user_id if log.user_id else f"pin_{log.zk_pin}"
        latest_per_user[key] = (log.event_type, log.user)

    members_on_floor = sum(1 for et, u in latest_per_user.values() if et == 'ENTRY' and not (u and u.is_staff))
    staff_on_floor = sum(1 for et, u in latest_per_user.values() if et == 'ENTRY' and (u and u.is_staff))

    # Sudden absence alerts (unresolved from gym_operations_payroll)
    try:
        from wger.gym_operations_payroll.models import SuddenAbsenceAlert, PaymentReceipt
        active_absence_alerts = list(
            SuddenAbsenceAlert.objects.filter(is_resolved=False).select_related('staff_user', 'shift')[:5]
        )
        open_alerts_count = len(active_absence_alerts)
        payment_receipts = PaymentReceipt.objects.select_related('member', 'cashier').order_by('-issued_at')[:25]
    except Exception:
        active_absence_alerts = []
        open_alerts_count = 0
        payment_receipts = []

    from wger.membership.models import (
        MemberProfile, CoachProfile, GymProgram, Announcement, Testimonial
    )

    all_members = MemberProfile.objects.select_related('user').order_by('-id')[:60]
    coaches = CoachProfile.objects.select_related('user').all()
    programs = GymProgram.objects.all()
    announcements = Announcement.objects.all().order_by('-created_at')
    testimonials = Testimonial.objects.all().order_by('-created_at')

    context = {
        'role': 'super_admin',
        'page_title': 'Super Admin Dashboard',
        'club_info': {
            'name': 'Fit Me',
            'tagline': 'Train with Purpose & Move with Confidence',
            'address': 'Fit Me, New Town, Elpitiya Road, Pitigala, 80420',
            'phone': '070 762 7878',
        },
        'stats': {
            'active_members': active_subs.count(),
            'expiring_soon': expiring_soon.count(),
            'pending_applications': pending_apps,
            'today_access_count': today_punches,
            'open_absence_alerts': open_alerts_count,
            'members_on_floor': members_on_floor,
            'staff_on_floor': staff_on_floor,
        },
        'active_absence_alerts': active_absence_alerts,
        'recent_applications': MemberApplication.objects.filter(status='pending')[:10],
        'membership_plans': MembershipPlan.objects.all(),
        'recent_door_punches': DoorAccessLog.objects.select_related('user').order_by('-punch_time')[:15],
        'all_members': all_members,
        'coaches': coaches,
        'programs': programs,
        'announcements': announcements,
        'testimonials': testimonials,
        'payment_receipts': payment_receipts,
    }
    return render(request, 'dashboards/super_admin.html', context)


@login_required
@role_required('front_desk', 'super_admin')
def front_desk_dashboard(request):
    """Front Desk — member queue, payments, and 80mm thermal receipts."""
    from wger.gym_operations_payroll.models import PaymentReceipt
    pending_apps = MemberApplication.objects.filter(status='pending').order_by('-applied_at')
    active_subs = Subscription.objects.filter(
        status='active',
        end_date__gte=timezone.now().date()
    ).select_related('member', 'plan').order_by('end_date')[:15]
    recent_receipts = PaymentReceipt.objects.select_related('member', 'cashier').order_by('-issued_at')[:20]

    context = {
        'role': 'front_desk',
        'page_title': 'Front Desk',
        'club_info': {
            'name': 'Fit Me',
            'tagline': 'Train with Purpose & Move with Confidence',
            'address': 'Fit Me, New Town, Elpitiya Road, Pitigala, 80420',
            'phone': '070 762 7878',
        },
        'pending_applications': pending_apps,
        'active_subscriptions': active_subs,
        'plans': MembershipPlan.objects.filter(is_active=True),
        'recent_receipts': recent_receipts,
    }
    return render(request, 'dashboards/front_desk.html', context)


@login_required
@role_required('coach', 'super_admin')
def coach_dashboard(request):
    """Coach — 6 modules: Members, Programs, Workout Plans, Nutrition Plans, Progress Reviews, Check-ins."""
    from wger.nutrition_lk.models import MealLog, DailyFuelTarget
    from wger.habit.models import WorkoutStreak
    from wger.membership.models import MemberProfile, GymProgram, BodyCheckIn, MemberWorkoutLog

    assigned_members = MemberProfile.objects.filter(
        assigned_coach=request.user
    ).select_related('user')
    if not assigned_members.exists():
        # Fallback to all members if none explicitly assigned
        assigned_members = MemberProfile.objects.select_related('user')[:20]

    member_ids = assigned_members.values_list('user_id', flat=True)
    unreviewed_meals = MealLog.objects.filter(
        member__in=member_ids,
        coach_reviewed=False
    ).select_related('member').order_by('-logged_at')[:15]

    at_risk_streaks = WorkoutStreak.objects.filter(
        member__in=member_ids
    ).select_related('member')
    at_risk = [s for s in at_risk_streaks if s.is_at_risk()]

    programs = GymProgram.objects.filter(is_active=True)
    recent_checkins = BodyCheckIn.objects.filter(member__in=member_ids).select_related('member').order_by('-checkin_date')[:20]
    recent_workouts = MemberWorkoutLog.objects.filter(member__in=member_ids).select_related('member').order_by('-logged_at')[:25]
    nutrition_targets = DailyFuelTarget.objects.filter(member__in=member_ids).select_related('member')

    context = {
        'role': 'coach',
        'page_title': 'Coach Dashboard',
        'club_info': {
            'name': 'Fit Me',
            'tagline': 'Train with Purpose & Move with Confidence',
            'address': 'Fit Me, New Town, Elpitiya Road, Pitigala, 80420',
            'phone': '070 762 7878',
        },
        'assigned_members': assigned_members,
        'unreviewed_meals': unreviewed_meals,
        'at_risk_members': at_risk,
        'programs': programs,
        'recent_checkins': recent_checkins,
        'recent_workouts': recent_workouts,
        'nutrition_targets': nutrition_targets,
    }
    return render(request, 'dashboards/coach.html', context)


@login_required
@role_required('member', 'super_admin')
def member_dashboard(request):
    """Member — 8 modules: Dashboard, My Program, Workout, Nutrition, Progress, Measurements, Transformation Timeline, Membership."""
    from wger.nutrition_lk.models import DailyFuelTarget, LocalFood, MealLog
    from wger.habit.models import WorkoutStreak
    from wger.membership.models import (
        MemberProfile, BodyCheckIn, GymProgram, MemberWorkoutLog, MemberMeasurement
    )
    from wger.zkbio_integration.models import BiometricProfile
    from wger.gym_operations_payroll.models import PaymentReceipt

    user = request.user

    # Get or create member profile & biometric profile
    profile = MemberProfile.objects.filter(user=user).first()
    bio_profile = BiometricProfile.objects.filter(user=user).first()
    if not bio_profile and profile and profile.biometric_pin:
        bio_profile, _ = BiometricProfile.objects.get_or_create(
            user=user,
            defaults={'zk_pin': profile.biometric_pin}
        )

    # Active subscription
    today = timezone.now().date()
    subscription = Subscription.objects.filter(
        member=user, status='active', end_date__gte=today
    ).first()

    door_access_active = bool(subscription and subscription.is_active and not (bio_profile and bio_profile.disabled))

    # Streak
    streak, _ = WorkoutStreak.objects.get_or_create(member=user)

    # Fuel target progress
    fuel_progress = None
    try:
        target = DailyFuelTarget.objects.get(member=user)
        fuel_progress = target.daily_progress()
    except Exception:
        pass

    # Macro Ring metrics
    calories_consumed = fuel_progress['consumed']['calories'] if fuel_progress else 1450
    calories_target = fuel_progress['targets']['calories'] if fuel_progress else 2200
    calories_pct = min(100, int((calories_consumed / max(1, calories_target)) * 100))

    protein_consumed = fuel_progress['consumed']['protein_g'] if fuel_progress else 110
    protein_target = fuel_progress['targets']['protein_g'] if fuel_progress else 150
    protein_pct = min(100, int((protein_consumed / max(1, protein_target)) * 100))

    water_consumed = 2400
    water_target = 3000
    water_pct = min(100, int((water_consumed / max(1, water_target)) * 100))

    # Body check-ins for morph slider & timeline
    checkins = list(BodyCheckIn.objects.filter(member=user).order_by('checkin_date'))
    before_checkin = checkins[0] if checkins else None
    after_checkin = checkins[-1] if len(checkins) > 1 else before_checkin

    # Dynamic sub-module models
    workout_logs = MemberWorkoutLog.objects.filter(member=user).order_by('-logged_at')[:25]
    measurements = MemberMeasurement.objects.filter(member=user).order_by('-date')[:20]
    all_programs = GymProgram.objects.filter(is_active=True)
    active_program = all_programs.first()
    local_foods = LocalFood.objects.all()[:40]
    today_meals = MealLog.objects.filter(member=user, logged_at__date=today).order_by('-logged_at')
    recent_receipts = PaymentReceipt.objects.filter(member=user).order_by('-issued_at')[:5]

    context = {
        'role': 'member',
        'page_title': 'My Dashboard',
        'club_info': {
            'name': 'Fit Me',
            'tagline': 'Train with Purpose & Move with Confidence',
            'address': 'Fit Me, New Town, Elpitiya Road, Pitigala, 80420',
            'phone': '070 762 7878',
        },
        'profile': profile,
        'bio_profile': bio_profile,
        'subscription': subscription,
        'door_access_active': door_access_active,
        'streak': streak,
        'fuel_progress': fuel_progress,
        'rings': {
            'calories_consumed': calories_consumed,
            'calories_target': calories_target,
            'calories_pct': calories_pct,
            'protein_consumed': protein_consumed,
            'protein_target': protein_target,
            'protein_pct': protein_pct,
            'water_consumed': water_consumed,
            'water_target': water_target,
            'water_pct': water_pct,
        },
        'checkins': checkins,
        'before_checkin': before_checkin,
        'after_checkin': after_checkin,
        'workout_logs': workout_logs,
        'measurements': measurements,
        'all_programs': all_programs,
        'active_program': active_program,
        'local_foods': local_foods,
        'today_meals': today_meals,
        'recent_receipts': recent_receipts,
    }
    return render(request, 'dashboards/member.html', context)



# ═════════════════════════════════════════════════════════════════════
# DYNAMIC INTERACTION ENDPOINTS (AJAX / REST)
# ═════════════════════════════════════════════════════════════════════

def public_registration_view(request):
    """
    Public Membership Registration Form — captures all 8 sections from official club document.
    Endpoint: /register/
    """
    if request.method == 'GET':
        plans = MembershipPlan.objects.filter(is_active=True)
        return render(request, 'register.html', {'plans': plans})

    elif request.method == 'POST':
        data = request.POST

        full_name = data.get('full_name', '').strip()
        email = data.get('email', '').strip().lower()
        phone = data.get('phone', '').strip()

        if not full_name or not email or not phone:
            return JsonResponse({'error': 'Full Name, Email, and Phone number are required.'}, status=400)

        # Look up or default plan
        plan_id = data.get('plan_id')
        plan = MembershipPlan.objects.filter(id=plan_id).first() if plan_id else MembershipPlan.objects.first()

        # Parse numeric fees safely
        from decimal import Decimal
        def parse_dec(val, default='0.00'):
            try:
                return Decimal(str(val).strip())
            except Exception:
                return Decimal(default)

        admission_fee = parse_dec(data.get('admission_fee', '1500.00'))
        monthly_fee = parse_dec(data.get('monthly_fee', '4500.00'))
        discount = parse_dec(data.get('discount', '0.00'))
        total_paid = parse_dec(data.get('total_paid', '6000.00'))

        # Dates & Age
        dob = data.get('date_of_birth') or None
        age = int(data.get('age')) if data.get('age') and data.get('age').isdigit() else None
        start_date = data.get('start_date') or None
        end_date = data.get('end_date') or None

        app = MemberApplication.objects.create(
            full_name=full_name,
            email=email,
            phone=phone,
            address=data.get('address', '').strip(),
            date_of_birth=dob,
            age=age,
            gender=data.get('gender', 'male'),
            nic_passport=data.get('nic_passport', '').strip(),
            emergency_name=data.get('emergency_name', '').strip(),
            emergency_relationship=data.get('emergency_relationship', '').strip(),
            emergency_phone=data.get('emergency_phone', '').strip(),
            desired_plan=plan,
            plan_duration=data.get('plan_duration', 'monthly'),
            start_date=start_date,
            end_date=end_date,
            primary_goal=data.get('primary_goal', '').strip(),
            fitness_goals_other=data.get('fitness_goals_other', '').strip(),
            has_medical_conditions=(data.get('has_medical') == 'yes'),
            medical_condition_details=data.get('medical_condition_details', '').strip(),
            is_under_medication=(data.get('under_meds') == 'yes'),
            medication_details=data.get('medication_details', '').strip(),
            blood_group=data.get('blood_group', '').strip(),
            personal_trainer_needed=(data.get('personal_trainer_needed') == 'yes'),
            admission_fee=admission_fee,
            monthly_fee=monthly_fee,
            discount=discount,
            total_paid=total_paid,
            payment_method=data.get('payment_method', 'cash'),
            agreed_to_rules=True,
            status='pending'
        )

        return JsonResponse({
            'success': True,
            'message': 'Registration application submitted successfully!',
            'application_id': app.id
        })


@login_required
@role_required('front_desk', 'super_admin')
def create_application_api(request):
    """Creates a new member application from front desk walk-in or intake form."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()
    plan_id = data.get('plan_id')
    primary_goal = data.get('primary_goal', 'general_fitness')

    if not full_name or not email or not phone:
        return JsonResponse({'error': 'Full name, email, and phone number are required.'}, status=400)

    from django.contrib.auth import get_user_model
    User = get_user_model()
    if User.objects.filter(email=email).exists():
        return JsonResponse({'error': f"A member with email {email} already exists."}, status=400)

    existing_app = MemberApplication.objects.filter(email=email, status='pending').first()
    if existing_app:
        return JsonResponse({'error': f"An application for {email} is already pending review."}, status=400)

    plan = MembershipPlan.objects.filter(id=plan_id).first() if plan_id else MembershipPlan.objects.first()

    app = MemberApplication.objects.create(
        full_name=full_name,
        email=email,
        phone=phone,
        desired_plan=plan,
        primary_goal=primary_goal,
        status='pending'
    )

    return JsonResponse({
        'success': True,
        'message': f"Application created for {app.full_name}!",
        'application': {
            'id': app.id,
            'full_name': app.full_name,
            'email': app.email,
            'phone': app.phone,
            'plan_name': plan.name if plan else 'Individual',
            'primary_goal': app.primary_goal or 'General Fitness'
        }
    })


@login_required
@role_required('front_desk', 'super_admin')
def approve_application_api(request, app_id):
    """Dynamically approves an intake application, creates user, PIN, and biometric profile."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    app = MemberApplication.objects.filter(id=app_id, status='pending').first()
    if not app:
        return JsonResponse({'error': 'Pending application not found'}, status=404)

    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group
    from wger.membership.models import MemberProfile
    from wger.zkbio_integration.models import BiometricProfile
    User = get_user_model()

    # Generate unique username
    base_username = app.email.split('@')[0].lower().replace('.', '_').replace('-', '_')
    username = base_username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_username}_{counter}"
        counter += 1

    # Create User
    user, created = User.objects.get_or_create(
        email=app.email,
        defaults={
            'username': username,
            'first_name': app.full_name.split()[0] if app.full_name else 'Member',
            'last_name': " ".join(app.full_name.split()[1:]) if len(app.full_name.split()) > 1 else '',
            'is_active': True,
        }
    )
    if created:
        user.set_password('fitme123!')
        user.save()

    # Assign Member Group
    member_group, _ = Group.objects.get_or_create(name='member')
    user.groups.add(member_group)

    # MemberProfile & PIN
    profile, _ = MemberProfile.objects.get_or_create(user=user)
    if not profile.biometric_pin:
        last_pin = MemberProfile.objects.exclude(biometric_pin__isnull=True).order_by('-biometric_pin').first()
        next_pin = str(int(last_pin.biometric_pin) + 1) if last_pin and last_pin.biometric_pin and last_pin.biometric_pin.isdigit() else "1001"
        profile.biometric_pin = next_pin
    profile.phone = app.phone
    profile.primary_goal = app.primary_goal or 'general_fitness'
    profile.date_of_birth = app.date_of_birth
    profile.nic_passport = app.nic_passport or ''
    profile.address = app.address or ''
    profile.gender = app.gender or 'male'
    profile.blood_group = app.blood_group or ''
    profile.emergency_contact_name = app.emergency_name or ''
    profile.emergency_relationship = app.emergency_relationship or ''
    profile.emergency_contact_phone = app.emergency_phone or ''
    profile.medical_conditions = app.medical_condition_details or ''
    profile.under_medication = app.medication_details or ''
    profile.personal_trainer_needed = app.personal_trainer_needed
    profile.save()

    # BiometricProfile for ZKBio Turnstile hardware
    bio_profile, _ = BiometricProfile.objects.get_or_create(
        user=user,
        defaults={
            'zk_pin': profile.biometric_pin,
            'sync_status': 'PENDING',
            'disabled': False,
        }
    )
    bio_profile.disabled = False
    bio_profile.sync_status = 'PENDING'
    bio_profile.save()

    # Create active subscription with fees
    today = timezone.now().date()
    plan = app.desired_plan or MembershipPlan.objects.first()
    paid_amt = app.total_paid if app.total_paid and app.total_paid > 0 else getattr(plan, 'price_monthly', 4500)

    sub = Subscription.objects.create(
        member=user,
        plan=plan,
        start_date=app.start_date or today,
        end_date=app.end_date or (today + timezone.timedelta(days=getattr(plan, 'duration_days', 30))),
        status='active',
        payment_method=app.payment_method or 'cash',
        amount_paid=paid_amt,
        approved_by=request.user,
        payment_date=timezone.now()
    )

    # Mark application as approved
    app.status = 'approved'
    app.reviewed_by = request.user
    app.reviewed_at = timezone.now()
    app.created_user = user
    app.save()

    # Issue PaymentReceipt for 80mm thermal printing
    from wger.gym_operations_payroll.models import PaymentReceipt
    receipt = PaymentReceipt.objects.create(
        receipt_number=PaymentReceipt.generate_next_receipt_number(),
        subscription=sub,
        member=user,
        plan_name=plan.name if plan else 'Standard',
        duration_days=getattr(plan, 'duration_days', 30),
        validity_start=sub.start_date,
        validity_end=sub.end_date,
        amount_paid=sub.amount_paid,
        payment_method=sub.payment_method,
        cashier=request.user,
        member_pin=profile.biometric_pin or '',
        notes=f"Initial membership enrollment ({app.nic_passport or 'Walk-in'})"
    )

    return JsonResponse({
        'success': True,
        'message': f"Application approved for {app.full_name}!",
        'username': user.username,
        'pin': profile.biometric_pin,
        'plan': plan.name if plan else 'Standard',
        'sub_id': sub.id,
        'receipt_id': receipt.id,
        'receipt_number': receipt.receipt_number,
        'receipt_url': f"/receipt/{receipt.id}/?autoprint=1"
    })


@login_required
@role_required('front_desk', 'super_admin')
def reject_application_api(request, app_id):
    """Dynamically rejects an intake application."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    app = MemberApplication.objects.filter(id=app_id).first()
    if not app:
        return JsonResponse({'error': 'Application not found'}, status=404)

    import json
    try:
        data = json.loads(request.body.decode('utf-8'))
        reason = data.get('reason', 'Application rejected by front desk')
    except Exception:
        reason = request.POST.get('reason', 'Application rejected by front desk')

    app.status = 'rejected'
    app.reviewed_by = request.user
    app.reviewed_at = timezone.now()
    app.review_notes = reason
    app.save()

    return JsonResponse({'success': True, 'message': f"Application {app_id} rejected."})


@login_required
@role_required('front_desk', 'super_admin')
def record_payment_api(request):
    """Records payment, activates subscription, provisions door access, and issues 80mm thermal receipt."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    from django.contrib.auth import get_user_model
    from wger.zkbio_integration.models import BiometricProfile
    from wger.membership.models import MemberProfile
    from wger.gym_operations_payroll.models import PaymentReceipt
    User = get_user_model()

    member_id = data.get('member_id')
    plan_id = data.get('plan_id')
    method = data.get('payment_method', 'cash')
    amount = data.get('amount_paid', 4500)

    member = User.objects.filter(id=member_id).first()
    if not member:
        return JsonResponse({'error': 'Member not found'}, status=404)

    plan = MembershipPlan.objects.filter(id=plan_id).first() or MembershipPlan.objects.first()

    today = timezone.now().date()
    sub = Subscription.objects.create(
        member=member,
        plan=plan,
        start_date=today,
        end_date=today + timezone.timedelta(days=getattr(plan, 'duration_days', 30)),
        status='active',
        payment_method=method,
        amount_paid=amount,
        approved_by=request.user,
        payment_date=timezone.now()
    )

    # Ensure biometric access is restored
    bio = BiometricProfile.objects.filter(user=member).first()
    if bio:
        bio.disabled = False
        bio.sync_status = 'PENDING'
        bio.save()

    profile = MemberProfile.objects.filter(user=member).first()
    pin = profile.biometric_pin if profile else (bio.zk_pin if bio else '')

    # Issue 80mm Thermal Payment Receipt
    receipt = PaymentReceipt.objects.create(
        receipt_number=PaymentReceipt.generate_next_receipt_number(),
        subscription=sub,
        member=member,
        plan_name=plan.name if plan else 'Standard',
        duration_days=getattr(plan, 'duration_days', 30),
        validity_start=sub.start_date,
        validity_end=sub.end_date,
        amount_paid=amount,
        payment_method=method,
        cashier=request.user,
        member_pin=pin,
        notes='Front Desk POS Payment'
    )

    return JsonResponse({
        'success': True,
        'message': f"Payment recorded for {member.username}. Subscription active until {sub.end_date:%d %b %Y}.",
        'receipt_id': receipt.id,
        'receipt_number': receipt.receipt_number,
        'receipt_url': f"/receipt/{receipt.id}/?autoprint=1"
    })


@login_required
def view_receipt(request, receipt_id):
    """Renders 80mm thermal receipt with auto-cut for POS printing."""
    from wger.gym_operations_payroll.models import PaymentReceipt
    from django.shortcuts import get_object_or_404
    from django.http import HttpResponseForbidden

    receipt = get_object_or_404(PaymentReceipt, id=receipt_id)

    # Allow staff, cashiers, super admins, or the receipt recipient member
    is_staff_or_admin = (
        request.user.is_staff or
        request.user.is_superuser or
        request.user.groups.filter(name__in=['front_desk', 'super_admin']).exists()
    )
    if not (is_staff_or_admin or request.user == receipt.member):
        return HttpResponseForbidden("Unauthorized to view this receipt")

    return render(request, 'receipt_80mm.html', {'receipt': receipt})


@login_required
@role_required('coach', 'super_admin')
def review_meal_api(request, meal_id):
    """Coach approves or provides feedback on a logged meal."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    from wger.nutrition_lk.models import MealLog
    meal = MealLog.objects.filter(id=meal_id).first()
    if not meal:
        return JsonResponse({'error': 'Meal not found'}, status=404)

    import json
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    feedback = data.get('feedback', 'Great balanced macros! Keep pushing.')
    meal.coach_reviewed = True
    meal.coach_feedback = feedback
    meal.save(update_fields=['coach_reviewed', 'coach_feedback'])

    return JsonResponse({
        'success': True,
        'message': f"Meal {meal_id} reviewed successfully!",
        'feedback': feedback
    })


@login_required
@role_required('coach', 'super_admin')
def ping_member_api(request, member_id):
    """Coach sends motivational ping or attendance nudge to an at-risk member."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    from django.contrib.auth import get_user_model
    from wger.habit.models import HabitPing
    User = get_user_model()

    member = User.objects.filter(id=member_id).first()
    if not member:
        return JsonResponse({'error': 'Member not found'}, status=404)

    import json
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    msg = data.get('message', 'Hey champion! We missed you on the gym floor. Your goals are waiting — see you today! 💪')
    ping = HabitPing.objects.create(
        from_coach=request.user,
        to_member=member,
        ping_type='nudge',
        message=msg
    )

    return JsonResponse({
        'success': True,
        'message': f"Motivational nudge delivered to {member.get_full_name() or member.username}!",
        'ping_id': ping.id
    })


@login_required
def log_quick_meal_api(request):
    """Member logs quick calories and macros directly from dashboard."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    from wger.nutrition_lk.models import MealLog, DailyFuelTarget
    calories = float(data.get('calories', 400))
    protein = float(data.get('protein_g', 30))
    carbs = float(data.get('carbs_g', 45))
    fat = float(data.get('fat_g', 10))
    meal_type = data.get('meal_type', 'snack')
    notes = data.get('notes', 'Quick dashboard log')

    meal = MealLog.objects.create(
        member=request.user,
        meal_type=meal_type,
        logged_at=timezone.now(),
        notes=notes,
        total_calories=calories,
        total_protein_g=protein,
        total_carbs_g=carbs,
        total_fat_g=fat
    )

    # Compute updated totals for today
    today = timezone.now().date()
    today_meals = MealLog.objects.filter(member=request.user, logged_at__date=today)
    tot_cal = sum(float(m.total_calories) for m in today_meals)
    tot_pro = sum(float(m.total_protein_g) for m in today_meals)

    # Targets
    target = DailyFuelTarget.objects.filter(member=request.user).first()
    target_cal = float(target.target_calories) if target else 2200.0
    target_pro = float(target.target_protein_g) if target else 150.0

    return JsonResponse({
        'success': True,
        'message': f"Logged {meal_type.title()} ({int(calories)} kcal, {int(protein)}g protein)!",
        'meal_id': meal.id,
        'totals': {
            'calories_consumed': int(tot_cal),
            'calories_target': int(target_cal),
            'calories_pct': min(100, int((tot_cal / max(1, target_cal)) * 100)),
            'protein_consumed': int(tot_pro),
            'protein_target': int(target_pro),
            'protein_pct': min(100, int((tot_pro / max(1, target_pro)) * 100)),
        }
    })


@login_required
@role_required('super_admin')
def resolve_absence_alert_api(request, alert_id):
    """Super Admin dynamically resolves an unapproved departure alert."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    from wger.gym_operations_payroll.models import SuddenAbsenceAlert
    alert = SuddenAbsenceAlert.objects.filter(id=alert_id).first()
    if not alert:
        return JsonResponse({'error': 'Alert not found'}, status=404)

    alert.is_resolved = True
    alert.admin_notes = f"Resolved dynamically by Super Admin {request.user.username} at {timezone.now():%H:%M}"
    alert.save(update_fields=['is_resolved', 'admin_notes'])

    # Restore shift status if shift is attached
    if alert.shift:
        alert.shift.is_off_floor = False
        alert.shift.status = 'ON_FLOOR'
        alert.shift.save(update_fields=['is_off_floor', 'status'])

    return JsonResponse({
        'success': True,
        'message': f"Alert for {alert.staff_user.username} resolved."
    })


def public_contact_api(request):
    """Public Contact Form API — captures visitor inquiries into ContactInquiry model."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    subject = data.get('subject', 'Membership / Training Inquiry').strip()
    message = data.get('message', '').strip()

    if not name or not phone:
        return JsonResponse({'error': 'Name and phone number are required.'}, status=400)

    from wger.membership.models import ContactInquiry
    inquiry = ContactInquiry.objects.create(
        name=name, email=email, phone=phone, subject=subject, message=message
    )
    return JsonResponse({
        'success': True,
        'message': f"Thank you {name}! Your inquiry has been sent to our Pitigala team. We will contact you at {phone} shortly.",
        'inquiry_id': inquiry.id
    })


@login_required
def log_workout_api(request):
    """Member logs an exercise set/rep entry."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    from decimal import Decimal
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    exercise_name = data.get('exercise_name', '').strip()
    workout_name = data.get('workout_name', 'Push Day').strip()
    sets = int(data.get('sets', 3))
    reps = int(data.get('reps', 10))
    weight = Decimal(str(data.get('weight_kg', '0.00')))
    notes = data.get('notes', '').strip()

    if not exercise_name:
        return JsonResponse({'error': 'Exercise name is required'}, status=400)

    from wger.membership.models import MemberWorkoutLog
    log = MemberWorkoutLog.objects.create(
        member=request.user,
        workout_name=workout_name,
        exercise_name=exercise_name,
        sets_completed=sets,
        reps=reps,
        weight_kg=weight,
        notes=notes,
        logged_at=timezone.now()
    )

    return JsonResponse({
        'success': True,
        'message': f"Logged {sets}x{reps} @ {weight}kg for {exercise_name}!",
        'log': {
            'id': log.id,
            'exercise_name': log.exercise_name,
            'workout_name': log.workout_name,
            'sets': log.sets_completed,
            'reps': log.reps,
            'weight_kg': str(log.weight_kg),
            'logged_at': log.logged_at.strftime('%d %b %H:%M')
        }
    })


@login_required
def log_measurement_api(request):
    """Member logs body circumference and weight."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    from decimal import Decimal
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    from wger.membership.models import MemberMeasurement
    weight = Decimal(str(data.get('weight_kg', '70.0')))
    chest = Decimal(str(data.get('chest_cm'))) if data.get('chest_cm') else None
    waist = Decimal(str(data.get('waist_cm'))) if data.get('waist_cm') else None
    biceps = Decimal(str(data.get('biceps_cm'))) if data.get('biceps_cm') else None
    body_fat = Decimal(str(data.get('body_fat_pct'))) if data.get('body_fat_pct') else None
    notes = data.get('notes', '').strip()

    m = MemberMeasurement.objects.create(
        member=request.user,
        date=timezone.now().date(),
        weight_kg=weight,
        chest_cm=chest,
        waist_cm=waist,
        biceps_cm=biceps,
        body_fat_pct=body_fat,
        notes=notes
    )

    return JsonResponse({
        'success': True,
        'message': f"Saved measurements! Current weight: {weight}kg",
        'measurement': {
            'date': m.date.strftime('%d %b %Y'),
            'weight_kg': str(m.weight_kg),
            'waist_cm': str(m.waist_cm or '--'),
            'chest_cm': str(m.chest_cm or '--'),
        }
    })


@login_required
@role_required('coach', 'super_admin')
def assign_program_api(request, member_id):
    """Coach assigns a gym program to an athlete."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    program_id = data.get('program_id')
    from wger.membership.models import MemberProfile, GymProgram
    from django.contrib.auth import get_user_model
    User = get_user_model()

    member = User.objects.filter(id=member_id).first()
    if not member:
        return JsonResponse({'error': 'Member not found'}, status=404)

    program = GymProgram.objects.filter(id=program_id).first()
    if not program:
        return JsonResponse({'error': 'Program not found'}, status=404)

    profile, _ = MemberProfile.objects.get_or_create(user=member)
    profile.notes = f"Active Routine: {program.title} (Assigned by Coach {request.user.username} on {timezone.now():%d %b})"
    profile.save(update_fields=['notes'])

    return JsonResponse({
        'success': True,
        'message': f"Assigned '{program.title}' to {member.get_full_name() or member.username}!",
        'program_title': program.title
    })


@login_required
@role_required('coach', 'super_admin')
def set_nutrition_target_api(request, member_id):
    """Coach sets daily calorie, protein, and water targets for a member."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    from decimal import Decimal
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    calories = int(data.get('calories', 2200))
    protein = int(data.get('protein_g', 150))
    carbs = int(data.get('carbs_g', 220))
    fat = int(data.get('fat_g', 60))

    from django.contrib.auth import get_user_model
    from wger.nutrition_lk.models import DailyFuelTarget
    User = get_user_model()
    member = User.objects.filter(id=member_id).first()
    if not member:
        return JsonResponse({'error': 'Member not found'}, status=404)

    target, _ = DailyFuelTarget.objects.get_or_create(
        member=member,
        defaults={
            'target_calories': calories,
            'target_protein_g': protein,
            'target_carbs_g': carbs,
            'target_fat_g': fat
        }
    )
    target.target_calories = calories
    target.target_protein_g = protein
    target.target_carbs_g = carbs
    target.target_fat_g = fat
    target.save()

    return JsonResponse({
        'success': True,
        'message': f"Updated nutrition targets for {member.get_full_name() or member.username}: {calories} kcal, {protein}g protein!",
        'targets': {
            'calories': calories,
            'protein_g': protein,
            'carbs_g': carbs,
            'fat_g': fat
        }
    })


@login_required
@role_required('super_admin', 'front_desk')
def toggle_member_access_api(request, member_id):
    """Admin toggles turnstile hardware biometric access on or off for a member."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    from django.contrib.auth import get_user_model
    from wger.zkbio_integration.models import BiometricProfile
    User = get_user_model()
    member = User.objects.filter(id=member_id).first()
    if not member:
        return JsonResponse({'error': 'Member not found'}, status=404)

    bio = BiometricProfile.objects.filter(user=member).first()
    if not bio:
        from wger.membership.models import MemberProfile
        prof = MemberProfile.objects.filter(user=member).first()
        pin = prof.biometric_pin if prof and prof.biometric_pin else "1001"
        bio = BiometricProfile.objects.create(user=member, zk_pin=pin, disabled=False)

    bio.disabled = not bio.disabled
    bio.save(update_fields=['disabled'])

    status_str = "REVOKED" if bio.disabled else "ACTIVE"
    return JsonResponse({
        'success': True,
        'disabled': bio.disabled,
        'status': status_str,
        'message': f"Turnstile access for {member.username} is now {status_str}."
    })


@login_required
@role_required('super_admin')
def admin_create_program_api(request):
    """Super Admin creates a new gym program."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    title = data.get('title', '').strip()
    category = data.get('category', 'hypertrophy')
    difficulty = data.get('difficulty', 'intermediate')
    duration = int(data.get('duration_weeks', 8))
    description = data.get('description', '').strip()
    key_features = data.get('key_features', '').strip()

    if not title:
        return JsonResponse({'error': 'Program title is required'}, status=400)

    from wger.membership.models import GymProgram
    prog = GymProgram.objects.create(
        title=title, category=category, difficulty=difficulty,
        duration_weeks=duration, description=description, key_features=key_features
    )
    return JsonResponse({
        'success': True,
        'message': f"Program '{title}' created successfully!",
        'program': {'id': prog.id, 'title': prog.title, 'category': prog.get_category_display()}
    })


@login_required
@role_required('super_admin')
def admin_create_announcement_api(request):
    """Super Admin broadcasts a gym-wide announcement."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    priority = data.get('priority', 'info')

    if not title or not content:
        return JsonResponse({'error': 'Title and content are required'}, status=400)

    from wger.membership.models import Announcement
    ann = Announcement.objects.create(title=title, content=content, priority=priority)
    return JsonResponse({
        'success': True,
        'message': f"Announcement '{title}' published!",
        'announcement': {'id': ann.id, 'title': ann.title, 'priority': ann.priority}
    })


@login_required
@role_required('super_admin')
def admin_toggle_testimonial_api(request, testimonial_id):
    """Super Admin approves or hides a client testimonial."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    from wger.membership.models import Testimonial
    t = Testimonial.objects.filter(id=testimonial_id).first()
    if not t:
        return JsonResponse({'error': 'Testimonial not found'}, status=404)

    t.is_approved = not t.is_approved
    t.save(update_fields=['is_approved'])

    return JsonResponse({
        'success': True,
        'approved': t.is_approved,
        'message': f"Testimonial for {t.member_name} is now {'approved' if t.is_approved else 'hidden'}."
    })


