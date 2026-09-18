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
from wger.zkbio_bridge.models import DoorPunch
from wger.payroll.models import Attendance, SuddenAbsenceAlert, Payslip
from wger.core.views.user import get_role_dashboard


def role_required(*roles):
    """Decorator that checks user has one of the required group names."""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('/en/user/login')
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


@login_required
@role_required('super_admin')
def super_admin_dashboard(request):
    """Super Admin — full system overview."""
    today = timezone.now().date()

    # Stats
    active_subs = Subscription.objects.filter(status='active', end_date__gte=today)
    expiring_soon = active_subs.filter(end_date__lte=today + timezone.timedelta(days=7))
    pending_apps = MemberApplication.objects.filter(status='pending').count()
    today_punches = DoorPunch.objects.filter(punch_time__date=today).count()

    # Sudden absence alerts (unresolved)
    try:
        from wger.payroll.models import SuddenAbsenceAlert
        open_alerts = SuddenAbsenceAlert.objects.filter(returned_at__isnull=True).count()
    except Exception:
        open_alerts = 0

    context = {
        'role': 'super_admin',
        'page_title': 'Super Admin Dashboard',
        'stats': {
            'active_members': active_subs.count(),
            'expiring_soon': expiring_soon.count(),
            'pending_applications': pending_apps,
            'today_access_count': today_punches,
            'open_absence_alerts': open_alerts,
        },
        'recent_applications': MemberApplication.objects.filter(status='pending')[:5],
        'membership_plans': MembershipPlan.objects.filter(is_active=True),
    }
    return render(request, 'fitme/dashboards/super_admin.html', context)


@login_required
@role_required('front_desk', 'super_admin')
def front_desk_dashboard(request):
    """Front Desk — member queue and payments."""
    pending_apps = MemberApplication.objects.filter(status='pending').order_by('-applied_at')
    active_subs = Subscription.objects.filter(
        status='active',
        end_date__gte=timezone.now().date()
    ).select_related('member', 'plan').order_by('end_date')[:10]

    context = {
        'role': 'front_desk',
        'page_title': 'Front Desk',
        'pending_applications': pending_apps,
        'active_subscriptions': active_subs,
        'plans': MembershipPlan.objects.filter(is_active=True),
    }
    return render(request, 'fitme/dashboards/front_desk.html', context)


@login_required
@role_required('coach', 'super_admin')
def coach_dashboard(request):
    """Coach — assigned members, meal logs, habit pings."""
    from wger.nutrition_lk.models import MealLog
    from wger.habit.models import HabitPing, WorkoutStreak
    from wger.membership.models import MemberProfile

    assigned_members = MemberProfile.objects.filter(
        assigned_coach=request.user
    ).select_related('user')

    member_ids = assigned_members.values_list('user_id', flat=True)
    unreviewed_meals = MealLog.objects.filter(
        member__in=member_ids,
        coach_reviewed=False
    ).select_related('member').order_by('-logged_at')[:10]

    at_risk_streaks = WorkoutStreak.objects.filter(
        member__in=member_ids
    ).select_related('member')
    at_risk = [s for s in at_risk_streaks if s.is_at_risk()]

    context = {
        'role': 'coach',
        'page_title': 'Coach Dashboard',
        'assigned_members': assigned_members,
        'unreviewed_meals': unreviewed_meals,
        'at_risk_members': at_risk,
    }
    return render(request, 'fitme/dashboards/coach.html', context)


@login_required
@role_required('member', 'super_admin')
def member_dashboard(request):
    """Member — digital ID, streak, fuel tank."""
    from wger.nutrition_lk.models import DailyFuelTarget
    from wger.habit.models import WorkoutStreak
    from wger.membership.models import MemberProfile, BodyCheckIn

    user = request.user

    # Get or create member profile
    profile = MemberProfile.objects.filter(user=user).first()

    # Active subscription
    today = timezone.now().date()
    subscription = Subscription.objects.filter(
        member=user, status='active', end_date__gte=today
    ).first()

    # Streak
    streak, _ = WorkoutStreak.objects.get_or_create(member=user)

    # Fuel target progress
    fuel_progress = None
    try:
        target = DailyFuelTarget.objects.get(member=user)
        fuel_progress = target.daily_progress()
    except DailyFuelTarget.DoesNotExist:
        pass

    # Body check-ins for morph slider
    checkins = BodyCheckIn.objects.filter(member=user).order_by('checkin_date')[:6]

    context = {
        'role': 'member',
        'page_title': 'My Dashboard',
        'profile': profile,
        'subscription': subscription,
        'streak': streak,
        'fuel_progress': fuel_progress,
        'checkins': checkins,
    }
    return render(request, 'fitme/dashboards/member.html', context)
