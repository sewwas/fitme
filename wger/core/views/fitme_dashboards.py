"""
Fit Me — Role-based Dashboard Views
Each role gets its own dashboard routed here.
"""
import functools
import json
import calendar
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count

from wger.membership.models import Subscription, MemberApplication, MembershipPlan, CoachProfile, MemberProfile
from wger.core.views.user import get_role_dashboard


def role_required(*roles):
    """Decorator that checks user has one of the required group names."""
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                if request.path.startswith('/api/') or '/api/' in request.path:
                    return JsonResponse({'error': 'Authentication required'}, status=401)
                return redirect(f'/user/login?next={request.path}')
            user_groups = set(request.user.groups.values_list('name', flat=True))
            if request.user.is_superuser or user_groups.intersection(roles):
                return view_func(request, *args, **kwargs)
            if request.path.startswith('/api/') or '/api/' in request.path or request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({'error': f"Forbidden: Insufficient privileges. Required role(s): {', '.join(roles)}"}, status=403)
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
    today_punches = DoorAccessLog.objects.filter(punch_time__date=today).count()
    total_kg_lost = sum(float(t.weight_loss_kg) for t in testimonials if t.weight_loss_kg)

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
            'email': 'hello@fitmefitness.lk',
            'hours_weekday': '05:30 AM – 11:00 PM',
            'hours_weekend': '06:00 AM – 10:00 PM',
            'turnstiles': 'Biometric Entry'
        }
    }


@login_required
@role_required('super_admin', 'admin')
def super_admin_dashboard(request, active_tab=None):
    """Admin Console — Operations for Super Admin (full control + data overrides + plan builder) & Admin (operations & reporting)."""
    from django.db.models import Count, Q, Sum

    today = timezone.now().date()
    current_tab = active_tab or request.GET.get('tab', 'tab-admin-members')
    is_super_admin = request.user.is_superuser or request.user.groups.filter(name='super_admin').exists()
    current_role = 'super_admin' if is_super_admin else 'admin'

    # Stats
    sub_stat_aggs = Subscription.objects.filter(status='active', end_date__gte=today).aggregate(
        active_cnt=Count('id'),
        expiring_cnt=Count('id', filter=Q(end_date__lte=today + timezone.timedelta(days=7)))
    )
    active_members_count = sub_stat_aggs['active_cnt'] or 0
    expiring_soon_count = sub_stat_aggs['expiring_cnt'] or 0
    pending_apps = MemberApplication.objects.filter(status='pending').count()

    # ZKBio Integration live floor counters & punches
    from wger.zkbio_integration.models import DoorAccessLog
    from wger.gym_operations_payroll.models import StaffShift
    from datetime import timedelta

    today_punches = DoorAccessLog.objects.filter(punch_time__date=today).count()
    cutoff_floor = timezone.now() - timedelta(hours=10)

    today_logs = DoorAccessLog.objects.filter(
        Q(punch_time__date=today) | Q(punch_time__gte=cutoff_floor),
        event_type__in=['ENTRY', 'EXIT']
    ).select_related('user').order_by('punch_time')

    latest_per_user = {}
    for log in today_logs:
        key = log.user_id if log.user_id else f"pin_{log.zk_pin}_{log.id}"
        latest_per_user[key] = (log.event_type, log.user)

    members_on_floor = sum(1 for et, u in latest_per_user.values() if et == 'ENTRY' and not (u and u.is_staff))
    staff_on_floor_set = set(u.id for et, u in latest_per_user.values() if et == 'ENTRY' and (u and u.is_staff))

    # Also include any staff with active shift marked 'ON_FLOOR' today
    for s_user_id in StaffShift.objects.filter(shift_date=today, status='ON_FLOOR').values_list('staff_user_id', flat=True):
        staff_on_floor_set.add(s_user_id)

    staff_on_floor = len(staff_on_floor_set)

    # Sudden absence alerts (unresolved from gym_operations_payroll)
    try:
        from wger.gym_operations_payroll.models import SuddenAbsenceAlert, PaymentReceipt
        active_absence_alerts = list(
            SuddenAbsenceAlert.objects.filter(is_resolved=False).select_related('staff_user', 'shift')[:5]
        )
        open_alerts_count = len(active_absence_alerts)
        payment_receipts = PaymentReceipt.objects.select_related('member', 'cashier').order_by('-issued_at')[:25]
    except Exception as exc:
        logger.warning(f"[Dashboard] Error fetching absence alerts/receipts: {exc}")
        active_absence_alerts = []
        open_alerts_count = 0
        payment_receipts = []

    from wger.membership.models import (
        MemberProfile, CoachProfile, GymProgram, Announcement, Testimonial
    )
    from django.contrib.auth import get_user_model
    from wger.zkbio_integration.models import BiometricProfile

    User = get_user_model()

    # Fetch all system users & staff with their roles & hardware statuses
    # Super Admin sees ALL users; Admin NEVER sees Super Admins.
    users_qs = User.objects.exclude(userprofile__is_temporary=True).prefetch_related('groups').select_related(
        'member_profile', 'coach_profile', 'biometric_profile'
    ).order_by('-id')

    if not is_super_admin:
        users_qs = users_qs.exclude(is_superuser=True).exclude(groups__name='super_admin')

    all_system_users = []
    user_stats = {
        'total': 0,
        'super_admin': 0,
        'admin': 0,
        'front_desk': 0,
        'coach': 0,
        'member': 0,
        'active': 0,
        'disabled': 0,
    }

    for u in users_qs:
        groups = {g.name for g in u.groups.all()}
        if u.is_superuser or 'super_admin' in groups:
            primary_role = 'super_admin'
            role_label = 'Super Admin'
            role_color = 'var(--neon-lime)'
            role_badge_class = 'badge-super-admin'
        elif 'admin' in groups:
            primary_role = 'admin'
            role_label = 'Admin'
            role_color = '#00F0FF'
            role_badge_class = 'badge-admin'
        elif 'front_desk' in groups:
            primary_role = 'front_desk'
            role_label = 'Front Desk'
            role_color = 'var(--cyan)'
            role_badge_class = 'badge-front-desk'
        elif 'coach' in groups:
            primary_role = 'coach'
            role_label = 'Coach'
            role_color = '#F59E0B'
            role_badge_class = 'badge-coach'
        else:
            primary_role = 'member'
            role_label = 'Member'
            role_color = '#A855F7'
            role_badge_class = 'badge-member'

        user_stats['total'] += 1
        user_stats[primary_role] = user_stats.get(primary_role, 0) + 1
        if u.is_active:
            user_stats['active'] += 1
        else:
            user_stats['disabled'] += 1

        phone = ''
        nic_passport = ''
        pin = ''
        has_gate_access = False

        photo_url = ''
        if hasattr(u, 'member_profile') and u.member_profile:
            phone = u.member_profile.phone or phone
            nic_passport = u.member_profile.nic_passport or nic_passport
            pin = u.member_profile.biometric_pin or pin
            if u.member_profile.profile_photo:
                try:
                    photo_url = u.member_profile.profile_photo.url
                except Exception:
                    pass
        if hasattr(u, 'coach_profile') and u.coach_profile:
            phone = u.coach_profile.phone or phone
        if hasattr(u, 'biometric_profile') and u.biometric_profile:
            pin = u.biometric_profile.zk_pin or pin
            has_gate_access = not u.biometric_profile.disabled

        all_system_users.append({
            'user': u,
            'id': u.id,
            'username': u.username,
            'full_name': u.get_full_name() or u.username,
            'email': u.email,
            'photo_url': photo_url,
            'primary_role': primary_role,
            'role_label': role_label,
            'role_color': role_color,
            'role_badge_class': role_badge_class,
            'phone': phone or '—',
            'nic_passport': nic_passport or '—',
            'pin': pin or '—',
            'has_gate_access': has_gate_access,
            'date_joined': u.date_joined,
            'is_active': u.is_active,
        })

    all_members_qs = MemberProfile.objects.exclude(user__userprofile__is_temporary=True).select_related('user')
    if not is_super_admin:
        all_members_qs = all_members_qs.exclude(user__is_superuser=True).exclude(user__groups__name='super_admin')
    all_members = list(all_members_qs.order_by('-id')[:60])
    member_user_ids = [m.user_id for m in all_members if m.user_id]
    if member_user_ids:
        subs_qs = Subscription.objects.filter(
            member_id__in=member_user_ids
        ).select_related('plan').prefetch_related('buddy_links__partner_member').order_by('-created_at')
        latest_sub_by_user = {}
        for s in subs_qs:
            if s.member_id not in latest_sub_by_user:
                latest_sub_by_user[s.member_id] = s

        from wger.gym_operations_payroll.models import BuddyMembership
        buddy_links_qs = BuddyMembership.objects.filter(
            partner_member_id__in=member_user_ids
        ).select_related('subscription__plan', 'subscription__member', 'primary_member').order_by('-subscription__end_date')
        buddy_by_user = {}
        for bl in buddy_links_qs:
            if bl.partner_member_id not in buddy_by_user:
                buddy_by_user[bl.partner_member_id] = bl

        for m in all_members:
            m.latest_sub = latest_sub_by_user.get(m.user_id)
            m.linked_as_partner = buddy_by_user.get(m.user_id)
    else:
        for m in all_members:
            m.latest_sub = None
            m.linked_as_partner = None

    coaches = CoachProfile.objects.select_related('user').all()
    programs = GymProgram.objects.all()
    announcements = Announcement.objects.all().order_by('-created_at')
    testimonials = Testimonial.objects.all().order_by('-created_at')

    # ── Financial & Sales Reports Aggregation ──
    from decimal import Decimal
    from django.db.models import Sum
    from wger.pos.models import POSSale, POSSaleItem, POSProduct, POSInventoryAudit, POSCashDrawerAudit

    today = timezone.localdate()
    week_start = today - timezone.timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    from wger.gym_operations_payroll.models import ClubExpense, PaymentReceipt

    # 0. Auto-link PaymentReceipt for any subscription lacking one (ensures seamless billing auditability)
    orphaned_subs = list(Subscription.objects.filter(receipts__isnull=True, amount_paid__gt=0).select_related('member', 'plan'))
    for o_sub in orphaned_subs:
        issue_dt = timezone.now()
        if getattr(o_sub, 'payment_date', None):
            issue_dt = o_sub.payment_date
        elif getattr(o_sub, 'start_date', None):
            issue_dt = timezone.datetime.combine(o_sub.start_date, timezone.datetime.min.time(), tzinfo=timezone.get_current_timezone())
        PaymentReceipt.objects.create(
            receipt_number=PaymentReceipt.generate_next_receipt_number(),
            subscription=o_sub,
            member=o_sub.member,
            plan_name=o_sub.plan.name if o_sub.plan else 'Standard',
            duration_days=getattr(o_sub.plan, 'duration_days', 30),
            validity_start=o_sub.start_date,
            validity_end=o_sub.end_date,
            amount_paid=o_sub.amount_paid,
            package_amount=o_sub.amount_paid,
            payment_method=o_sub.payment_method or 'cash',
            notes="Auto-linked receipt for membership enrollment",
            issued_at=issue_dt
        )

    # 1. Membership Revenue & Payment Breakdown in 1 query
    pr_aggs = PaymentReceipt.objects.aggregate(
        total=Sum('amount_paid'),
        today=Sum('amount_paid', filter=Q(issued_at__date=today)),
        week=Sum('amount_paid', filter=Q(issued_at__date__gte=week_start)),
        month=Sum('amount_paid', filter=Q(issued_at__date__gte=month_start)),
        today_cash=Sum('amount_paid', filter=Q(issued_at__date=today, payment_method__icontains='cash')),
        today_card=Sum('amount_paid', filter=Q(issued_at__date=today, payment_method__icontains='card')),
        today_bank=Sum('amount_paid', filter=Q(issued_at__date=today, payment_method__icontains='bank')),
    )
    total_membership_rev = pr_aggs['total'] or Decimal('0.00')
    today_membership_rev = pr_aggs['today'] or Decimal('0.00')
    week_membership_rev = pr_aggs['week'] or Decimal('0.00')
    month_membership_rev = pr_aggs['month'] or Decimal('0.00')
    today_cash_mem = pr_aggs['today_cash'] or Decimal('0.00')
    today_card_mem = pr_aggs['today_card'] or Decimal('0.00')
    today_bank_mem = pr_aggs['today_bank'] or Decimal('0.00')

    # 2. POS Store & Bar Revenue & Methods in 1 query
    pos_aggs = POSSale.objects.filter(status='COMPLETED').aggregate(
        total=Sum('total_amount'),
        today=Sum('total_amount', filter=Q(created_at__date=today)),
        week=Sum('total_amount', filter=Q(created_at__date__gte=week_start)),
        month=Sum('total_amount', filter=Q(created_at__date__gte=month_start)),
        today_cash=Sum('total_amount', filter=Q(created_at__date=today, payment_method='CASH')),
        today_card=Sum('total_amount', filter=Q(created_at__date=today, payment_method='CARD')),
        today_koko=Sum('total_amount', filter=Q(created_at__date=today, payment_method='KOKO')),
        today_bank=Sum('total_amount', filter=Q(created_at__date=today, payment_method='BANK_TRANSFER')),
    )
    total_pos_rev = pos_aggs['total'] or Decimal('0.00')
    today_pos_rev = pos_aggs['today'] or Decimal('0.00')
    week_pos_rev = pos_aggs['week'] or Decimal('0.00')
    month_pos_rev = pos_aggs['month'] or Decimal('0.00')
    today_cash_pos = pos_aggs['today_cash'] or Decimal('0.00')
    today_card_pos = pos_aggs['today_card'] or Decimal('0.00')
    today_koko_pos = pos_aggs['today_koko'] or Decimal('0.00')
    today_bank_pos = pos_aggs['today_bank'] or Decimal('0.00')

    # 3. Combined Gross Totals
    total_gross_rev = total_membership_rev + total_pos_rev
    today_gross_rev = today_membership_rev + today_pos_rev
    week_gross_rev = week_membership_rev + week_pos_rev
    month_gross_rev = month_membership_rev + month_pos_rev

    # 4. Club Operating Expenses (OPEX) in 1 query
    exp_aggs = ClubExpense.objects.aggregate(
        total=Sum('amount'),
        today=Sum('amount', filter=Q(expense_date=today)),
        week=Sum('amount', filter=Q(expense_date__gte=week_start)),
        month=Sum('amount', filter=Q(expense_date__gte=month_start)),
    )
    total_expenses = exp_aggs['total'] or Decimal('0.00')
    today_expenses = exp_aggs['today'] or Decimal('0.00')
    week_expenses = exp_aggs['week'] or Decimal('0.00')
    month_expenses = exp_aggs['month'] or Decimal('0.00')

    # 5. Net Profit (Gross Inflow - OPEX)
    total_net_profit = total_gross_rev - total_expenses
    today_net_profit = today_gross_rev - today_expenses
    week_net_profit = week_gross_rev - week_expenses
    month_net_profit = month_gross_rev - month_expenses

    # 6. Payment Method Breakdown (Today)
    today_drawer_audit = POSCashDrawerAudit.objects.filter(audit_date__date=today).order_by('-audit_date').first()
    today_drawer_float = today_drawer_audit.opening_float if today_drawer_audit else Decimal('0.00')
    today_cash_total = today_drawer_float + today_cash_mem + today_cash_pos
    today_card_total = today_card_mem + today_card_pos
    today_bank_total = today_bank_mem + today_bank_pos
    today_digital_total = today_card_total + today_koko_pos + today_bank_total

    # 7. Plan Performance & Billing Package Breakdown
    all_plans = list(MembershipPlan.objects.all())
    from django.db.models import Count, Q
    sub_counts = {
        s['plan_id']: s for s in Subscription.objects.values('plan_id').annotate(
            total_cnt=Count('id'),
            active_cnt=Count('id', filter=Q(status='active', end_date__gte=today)),
            total_amt=Sum('amount_paid')
        )
    }
    receipt_by_plan = {
        r['subscription__plan_id']: r['total']
        for r in PaymentReceipt.objects.filter(subscription__plan_id__isnull=False)
        .values('subscription__plan_id')
        .annotate(total=Sum('amount_paid'))
    }

    plan_performance = []
    for pl in all_plans:
        s_data = sub_counts.get(pl.id, {})
        active_cnt = s_data.get('active_cnt', 0)
        total_sub_cnt = s_data.get('total_cnt', 0)
        plan_rev = receipt_by_plan.get(pl.id) or s_data.get('total_amt') or Decimal('0.00')
        rev_share = (float(plan_rev) / float(total_membership_rev) * 100) if total_membership_rev > 0 else 0
        plan_performance.append({
            'plan': pl,
            'active_subscribers': active_cnt,
            'total_subscribers': total_sub_cnt,
            'revenue': plan_rev,
            'revenue_share_pct': round(rev_share, 1)
        })
    plan_performance.sort(key=lambda x: x['revenue'], reverse=True)

    # 8. Recent Club Expenses
    recent_expenses = ClubExpense.objects.select_related('recorded_by').order_by('-expense_date', '-id')[:30]

    # 9. Top-Selling POS Products
    top_pos_products = list(
        POSSaleItem.objects.filter(sale__status='COMPLETED')
        .values('product_name', 'sku')
        .annotate(units_sold=Sum('quantity'), revenue=Sum('total_price'))
        .order_by('-revenue')[:10]
    )

    # 10. Unified Ledger Transactions (Combined Membership Receipts + POS Sales)
    combined_ledger = []
    for pr in PaymentReceipt.objects.select_related('member', 'cashier').order_by('-issued_at')[:30]:
        combined_ledger.append({
            'receipt_number': pr.receipt_number,
            'type': 'Membership',
            'type_badge': 'badge-lime',
            'customer': pr.member.get_full_name() or pr.member.username,
            'cashier': pr.cashier.username if pr.cashier else 'System',
            'method': pr.payment_method.upper(),
            'amount': pr.amount_paid,
            'timestamp': pr.issued_at,
            'url': f'/receipt/{pr.id}/',
        })

    for ps in POSSale.objects.filter(status='COMPLETED').select_related('cashier', 'customer_member').order_by('-created_at')[:30]:
        combined_ledger.append({
            'receipt_number': ps.receipt_number,
            'type': 'POS Store',
            'type_badge': 'badge-cyan',
            'customer': ps.customer_name,
            'cashier': ps.cashier.username if ps.cashier else 'Staff',
            'method': ps.payment_method,
            'amount': ps.total_amount,
            'timestamp': ps.created_at,
            'url': f'/pos/receipt/{ps.receipt_number}/',
        })

    combined_ledger.sort(key=lambda x: x['timestamp'], reverse=True)
    combined_ledger = combined_ledger[:50]

    # 11. Inventory Audit & Stock Reconciliation Telemetry
    all_pos_products = list(POSProduct.objects.filter(is_active=True).select_related('category'))
    pos_cost_valuation = sum(p.cost_price * p.stock_quantity for p in all_pos_products)
    pos_retail_valuation = sum(p.price * p.stock_quantity for p in all_pos_products)
    pos_total_units = sum(p.stock_quantity for p in all_pos_products)

    missing_stock_products = [p for p in all_pos_products if p.has_audit_discrepancy or p.stock_quantity <= 0]
    recent_inventory_audits = POSInventoryAudit.objects.select_related('product', 'auditor').order_by('-audit_date')[:25]
    total_shrinkage_loss = POSInventoryAudit.objects.filter(discrepancy__lt=0).aggregate(total=Sum('variance_value'))['total'] or Decimal('0.00')
    recent_drawer_audits = POSCashDrawerAudit.objects.select_related('cashier').order_by('-audit_date')[:10]

    finance = {
        'total_gross_rev': total_gross_rev,
        'total_membership_rev': total_membership_rev,
        'total_pos_rev': total_pos_rev,
        'today_gross_rev': today_gross_rev,
        'today_membership_rev': today_membership_rev,
        'today_pos_rev': today_pos_rev,
        'week_gross_rev': week_gross_rev,
        'week_membership_rev': week_membership_rev,
        'week_pos_rev': week_pos_rev,
        'month_gross_rev': month_gross_rev,
        'month_membership_rev': month_membership_rev,
        'month_pos_rev': month_pos_rev,
        'total_expenses': total_expenses,
        'today_expenses': today_expenses,
        'week_expenses': week_expenses,
        'month_expenses': month_expenses,
        'total_net_profit': total_net_profit,
        'today_net_profit': today_net_profit,
        'week_net_profit': week_net_profit,
        'month_net_profit': month_net_profit,
        'today_cash_total': today_cash_total,
        'today_card_total': today_card_total,
        'today_koko_pos': today_koko_pos,
        'today_bank_total': today_bank_total,
        'today_digital_total': today_digital_total,
        'plan_performance': plan_performance,
        'recent_expenses': recent_expenses,
        'top_pos_products': top_pos_products,
        'combined_ledger': combined_ledger,
        'pos_cost_valuation': pos_cost_valuation,
        'pos_retail_valuation': pos_retail_valuation,
        'pos_total_units': pos_total_units,
        'missing_stock_products': missing_stock_products,
        'missing_stock_count': len(missing_stock_products),
        'recent_inventory_audits': recent_inventory_audits,
        'total_shrinkage_loss': abs(total_shrinkage_loss),
        'recent_drawer_audits': recent_drawer_audits,
    }

    # ── Financial Audit, Revenue Telemetry & Discrepancy Diagnostics ──
    from django.core.cache import cache
    current_year = today.year
    audit_cache_key = f'fitme_audit_monthly_trends_{today.year}_{today.month}_{today.day}'
    cached_audit = cache.get(audit_cache_key)
    if cached_audit:
        audit_monthly_trends = cached_audit['trends']
        audit_annual_rev = cached_audit['annual_rev']
        audit_pt_rev = cached_audit['pt_rev']
        audit_pkg_rev = cached_audit['pkg_rev']
        audit_pos_total = cached_audit['pos_total']
    else:
        audit_monthly_trends = []
        for i in range(5, -1, -1):
            y = today.year
            m = today.month - i
            while m <= 0:
                m += 12
                y -= 1
            d_in_m = calendar.monthrange(y, m)[1]
            m_start = timezone.datetime(y, m, 1, 0, 0, 0, tzinfo=timezone.get_current_timezone())
            m_end = timezone.datetime(y, m, d_in_m, 23, 59, 59, tzinfo=timezone.get_current_timezone())

            m_mem_rev = PaymentReceipt.objects.filter(
                issued_at__range=[m_start, m_end]
            ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')

            m_pos_rev = POSSale.objects.filter(
                status='COMPLETED',
                created_at__range=[m_start, m_end]
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

            m_opex = ClubExpense.objects.filter(
                expense_date__range=[m_start.date(), m_end.date()]
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

            m_gross = m_mem_rev + m_pos_rev
            m_net = m_gross - m_opex

            audit_monthly_trends.append({
                'label': m_start.strftime('%b %Y'),
                'month': m_start.strftime('%b %Y'),
                'membership_rev': float(m_mem_rev),
                'pos_rev': float(m_pos_rev),
                'gross_rev': float(m_gross),
                'inflow': float(m_gross),
                'opex': float(m_opex),
                'net_profit': float(m_net),
                'margin': float(m_net),
            })

        audit_annual_rev = PaymentReceipt.objects.aggregate(total=Sum('annual_fee_amount'))['total'] or Decimal('0.00')
        audit_pt_rev = PaymentReceipt.objects.aggregate(total=Sum('coaching_amount'))['total'] or Decimal('0.00')
        audit_pkg_rev = PaymentReceipt.objects.aggregate(total=Sum('package_amount'))['total'] or Decimal('0.00')
        audit_pos_total = POSSale.objects.filter(status='COMPLETED').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        cache.set(audit_cache_key, {
            'trends': audit_monthly_trends,
            'annual_rev': audit_annual_rev,
            'pt_rev': audit_pt_rev,
            'pkg_rev': audit_pkg_rev,
            'pos_total': audit_pos_total,
        }, timeout=120)

    if audit_pkg_rev == 0 and total_membership_rev > 0:
        audit_pkg_rev = max(Decimal('0.00'), total_membership_rev - audit_annual_rev - audit_pt_rev)

    revenue_streams_data = {
        'membership': float(audit_pkg_rev),
        'pos': float(audit_pos_total),
        'annual_fee': float(audit_annual_rev),
        'coaching': float(audit_pt_rev),
    }

    revenue_streams_list = [
        {'stream': 'Membership Packages', 'amount': float(audit_pkg_rev), 'color': '#76C043'},
        {'stream': 'POS Café & Store', 'amount': float(audit_pos_total), 'color': '#00F0FF'},
        {'stream': 'Annual Registration Fees', 'amount': float(audit_annual_rev), 'color': '#F59E0B'},
        {'stream': 'Personal Coaching', 'amount': float(audit_pt_rev), 'color': '#A855F7'},
    ]

    exp_cats_qs = list(ClubExpense.objects.values('category').annotate(total=Sum('amount')).order_by('-total'))
    exp_cat_labels_map = dict(ClubExpense.CATEGORY_CHOICES) if hasattr(ClubExpense, 'CATEGORY_CHOICES') else {
        'rent': 'Facility Rent',
        'electricity': 'Electricity (CEB)',
        'water': 'Water & Utilities',
        'staff_salary': 'Staff Payroll',
        'maintenance': 'Equipment Maintenance',
        'supplements_stock': 'Supplements Stock',
        'cleaning': 'Cleaning & Sanitation',
        'marketing': 'Marketing & Promo',
        'other': 'General OPEX'
    }
    expenses_by_category_data = [
        {
            'category': c['category'],
            'label': exp_cat_labels_map.get(c['category'], c['category'].replace('_', ' ').title()),
            'total': float(c['total'] or 0),
            'amount': float(c['total'] or 0),
        }
        for c in exp_cats_qs
    ]

    pay_methods_qs = list(PaymentReceipt.objects.values('payment_method').annotate(total=Sum('amount_paid')).order_by('-total'))
    pay_methods_labels_map = {
        'cash': 'Cash Drawer',
        'card': 'POS Card Terminal',
        'online_card': 'Online Card Gateway',
        'bank_transfer': 'Direct Bank QR / Slip',
        'koko': 'Koko Pay (Installments)',
    }
    payments_by_method_data = [
        {
            'method': p['payment_method'],
            'label': pay_methods_labels_map.get(p['payment_method'], p['payment_method'].replace('_', ' ').title()),
            'total': float(p['total'] or 0),
            'amount': float(p['total'] or 0),
        }
        for p in pay_methods_qs
    ]

    active_sub_members = list(Subscription.objects.filter(
        status='active', end_date__gte=today
    ).values_list('member_id', flat=True).distinct())

    paid_annual_member_ids = set(PaymentReceipt.objects.filter(
        issued_at__year=current_year,
        annual_fee_amount__gt=0
    ).values_list('member_id', flat=True))

    active_subs_qs = Subscription.objects.filter(
        status='active', end_date__gte=today
    ).select_related('plan').order_by('end_date')
    latest_subs = {s.member_id: s for s in active_subs_qs}

    missing_annual_fee_members = []
    for prof in MemberProfile.objects.filter(user_id__in=active_sub_members).select_related('user'):
        if prof.user_id not in paid_annual_member_ids:
            # Active gym members who registered/joined in the current calendar year paid their registration upon joining
            if prof.join_date and prof.join_date.year >= current_year:
                continue

            sub = latest_subs.get(prof.user_id)
            plan = sub.plan if sub else None
            # Students are exempt from annual registration fee (LKR 0)
            if plan and (getattr(plan, 'is_student_plan', False) or plan.plan_type == 'student' or 'student' in (plan.name or '').lower()):
                continue
            fee_due = plan.registration_fee if (plan and getattr(plan, 'registration_fee', None) is not None) else Decimal('1000.00')
            missing_annual_fee_members.append({
                'user_id': prof.user_id,
                'name': prof.user.get_full_name() or prof.user.username,
                'phone': prof.phone or '—',
                'pin': prof.biometric_pin or prof.user_id,
                'plan_name': plan.name if plan else 'Standard Package',
                'fee_due': fee_due,
                'join_date': prof.join_date,
            })


    expired_unrenewed_subs = list(Subscription.objects.filter(
        end_date__lt=today
    ).exclude(
        member_id__in=active_sub_members
    ).select_related('member', 'plan').order_by('-end_date')[:25])

    missing_bio_members = []
    bio_map = {b.user_id: b for b in BiometricProfile.objects.filter(user_id__in=active_sub_members)}
    for prof in MemberProfile.objects.filter(user_id__in=active_sub_members).select_related('user'):
        b = bio_map.get(prof.user_id)
        face_missing = not (b and b.face_enrolled)
        fp_missing = not (b and b.fingerprint_enrolled)
        if face_missing or fp_missing:
            missing_bio_members.append({
                'user_id': prof.user_id,
                'name': prof.user.get_full_name() or prof.user.username,
                'phone': prof.phone or '—',
                'pin': prof.biometric_pin or prof.user_id,
                'face_missing': face_missing,
                'fp_missing': fp_missing,
            })

    missing_bill_expenses = list(ClubExpense.objects.filter(
        Q(receipt_image='') | Q(receipt_image__isnull=True)
    ).select_related('recorded_by').order_by('-expense_date', '-id')[:25])

    stock_issues = list(POSProduct.objects.filter(
        Q(stock_quantity__lte=0) | Q(has_audit_discrepancy=True)
    ).select_related('category').order_by('stock_quantity')[:25])

    # ── User Role & RBAC Security Audit ──
    user_role_issues = []
    audit_users_qs = User.objects.exclude(userprofile__is_temporary=True).prefetch_related('groups').order_by('id')
    for u in audit_users_qs:
        # If Admin (not Super Admin), hide Super Admins from the audit report as well
        if not is_super_admin and (u.is_superuser or u.groups.filter(name='super_admin').exists()):
            continue

        groups = set(u.groups.values_list('name', flat=True))
        issues = []
        if u.is_superuser and 'super_admin' not in groups:
            issues.append('Superuser account missing super_admin group')
        if ('super_admin' in groups or u.is_superuser) and 'member' in groups:
            issues.append('Super Admin has conflicting member group')
        if 'admin' in groups and 'member' in groups:
            issues.append('Admin has conflicting member group')
        if 'coach' in groups and 'member' in groups:
            issues.append('Coach has conflicting member group')
        if 'front_desk' in groups and 'member' in groups:
            issues.append('Front Desk staff has conflicting member group')
        if not groups:
            issues.append('No security group/role assigned')
        if u.is_staff and not groups.intersection({'super_admin', 'admin', 'front_desk', 'coach'}):
            issues.append('Staff flag active without staff group')

        if issues:
            primary = 'member'
            if u.is_superuser or 'super_admin' in groups:
                primary = 'super_admin'
            elif 'admin' in groups:
                primary = 'admin'
            elif 'front_desk' in groups:
                primary = 'front_desk'
            elif 'coach' in groups:
                primary = 'coach'

            user_role_issues.append({
                'user_id': u.id,
                'username': u.username,
                'name': u.get_full_name() or u.username,
                'email': u.email or '—',
                'primary_role': primary,
                'current_groups': list(groups),
                'issues': issues,
                'is_active': u.is_active,
                'is_staff': u.is_staff,
            })

    total_audit_discrepancies = (
        len(missing_annual_fee_members) +
        len(expired_unrenewed_subs) +
        len(missing_bill_expenses) +
        len(stock_issues) +
        len(user_role_issues)
    )

    from wger.membership.models import MembershipDiscountAudit
    discount_audits = list(MembershipDiscountAudit.objects.select_related(
        'member', 'authorized_by', 'plan', 'receipt'
    ).order_by('-created_at')[:50])

    financial_audit = {
        'current_year': str(current_year),
        'monthly_trends': audit_monthly_trends,
        'monthly_trends_json': json.dumps(audit_monthly_trends),
        'revenue_streams': revenue_streams_list,
        'revenue_streams_dict': revenue_streams_data,
        'revenue_streams_json': json.dumps(revenue_streams_list),
        'expenses_by_category': expenses_by_category_data,
        'expenses_by_category_json': json.dumps(expenses_by_category_data),
        'payments_by_method': payments_by_method_data,
        'payments_by_method_json': json.dumps(payments_by_method_data),
        'missing_annual_fee_members': missing_annual_fee_members,
        'missing_annual_fee_count': len(missing_annual_fee_members),
        'expired_unrenewed_subs': expired_unrenewed_subs,
        'expired_unrenewed_count': len(expired_unrenewed_subs),
        'missing_bio_members': [],
        'missing_bio_count': 0,
        'missing_bill_expenses': missing_bill_expenses,
        'missing_bills_count': len(missing_bill_expenses),
        'stock_issues': stock_issues,
        'stock_issues_count': len(stock_issues),
        'user_role_issues': user_role_issues,
        'user_role_issues_count': len(user_role_issues),
        'discount_audits': discount_audits,
        'discount_audits_count': len(discount_audits),
        'total_audit_discrepancies': total_audit_discrepancies,
    }

    # ── Monthly Staff Payroll Ledger ──
    from wger.gym_operations_payroll.models import PayrollLedger, StaffShift
    from wger.membership.models import MemberProfile

    now_date = timezone.now().date()
    req_month_str = request.GET.get('payroll_month')
    if req_month_str:
        try:
            first_of_selected_month = timezone.datetime.strptime(req_month_str, '%Y-%m').date().replace(day=1)
        except Exception:
            first_of_selected_month = now_date.replace(day=1)
    else:
        first_of_selected_month = now_date.replace(day=1)

    last_day_num = calendar.monthrange(first_of_selected_month.year, first_of_selected_month.month)[1]
    last_of_selected_month = first_of_selected_month.replace(day=last_day_num)

    # Build available months for dropdown selector (current + past 11 months)
    available_months = []
    month_cursor = now_date.replace(day=1)
    for _ in range(12):
        m_val = month_cursor.strftime('%Y-%m')
        available_months.append({
            'value': m_val,
            'label': month_cursor.strftime('%B %Y'),
            'is_selected': (m_val == first_of_selected_month.strftime('%Y-%m'))
        })
        if month_cursor.month == 1:
            month_cursor = month_cursor.replace(year=month_cursor.year - 1, month=12)
        else:
            month_cursor = month_cursor.replace(month=month_cursor.month - 1)

    payroll_ledgers = list(PayrollLedger.objects.filter(
        month=first_of_selected_month
    ).select_related('staff_user').prefetch_related('staff_user__groups').order_by('staff_user__username'))

    if not payroll_ledgers:
        try:
            from wger.gym_operations_payroll.tasks import calculate_monthly_payroll
            calculate_monthly_payroll(first_of_selected_month.year, first_of_selected_month.month)
            payroll_ledgers = list(PayrollLedger.objects.filter(
                month=first_of_selected_month
            ).select_related('staff_user').prefetch_related('staff_user__groups').order_by('staff_user__username'))
        except Exception as exc:
            logger.warning(f"[Dashboard] Failed to calculate/fetch monthly payroll for {first_of_selected_month}: {exc}")

    # If requester is Admin (not Super Admin), exclude Super Admins from payroll ledgers
    if not is_super_admin:
        payroll_ledgers = [
            l for l in payroll_ledgers
            if not (l.staff_user.is_superuser or l.staff_user.groups.filter(name='super_admin').exists())
        ]

    # Attach PT client breakdown (7000/3000/4000 split) and duty attendance summary to each ledger
    staff_user_ids = [l.staff_user_id for l in payroll_ledgers]
    shifts_by_staff = {}
    if staff_user_ids:
        month_shifts = list(StaffShift.objects.filter(
            staff_user_id__in=staff_user_ids,
            shift_date__range=[first_of_selected_month, last_of_selected_month]
        ))
        for s in month_shifts:
            shifts_by_staff.setdefault(s.staff_user_id, []).append(s)

    profiles_by_coach = {}
    if staff_user_ids:
        from django.db.models import Prefetch
        coached_profiles_qs = MemberProfile.objects.filter(
            assigned_coach_id__in=staff_user_ids,
            personal_trainer_needed=True,
            user__is_staff=False,
            user__is_superuser=False,
            user__is_active=True,
        ).select_related('user').prefetch_related(
            Prefetch(
                'user__subscriptions',
                queryset=Subscription.objects.filter(
                    status='active',
                    start_date__lte=last_of_selected_month,
                    end_date__gte=first_of_selected_month
                ).select_related('plan').order_by('-start_date')
            )
        )
        for cp in coached_profiles_qs:
            profiles_by_coach.setdefault(cp.assigned_coach_id, []).append(cp)

    for l in payroll_ledgers:
        g = next(iter(l.staff_user.groups.all()), None)
        l.role_name = g.name if g else ('Super Admin' if l.staff_user.is_superuser else 'Staff')
        l.role_slug = l.role_name.lower().replace(' ', '-')

        pt_clients = []
        seen_athletes = set()
        for cp in profiles_by_coach.get(l.staff_user_id, []):
            if cp.user_id in seen_athletes:
                continue
            active_s = next(iter(cp.user.subscriptions.all()), None)
            if active_s:
                seen_athletes.add(cp.user_id)
                pt_clients.append({
                    'name': cp.user.get_full_name() or cp.user.username,
                    'username': cp.user.username,
                    'phone': cp.phone or '—',
                    'plan_name': active_s.plan.name if active_s.plan else 'Personal Coaching Package',
                    'package_fee': 7000.00,
                    'gym_share': 3000.00,
                    'coach_share': 4000.00,
                    'sub_start': active_s.start_date.strftime('%d %b %Y'),
                    'sub_end': active_s.end_date.strftime('%d %b %Y'),
                })

        l.pt_clients_data = pt_clients
        l.pt_clients_count = len(pt_clients)
        l.pt_clients_json = json.dumps(pt_clients)
        l.total_pt_package_revenue = len(pt_clients) * 7000.0
        l.total_gym_share = len(pt_clients) * 3000.0
        l.total_coach_commission = len(pt_clients) * 4000.0

        # Synchronize unfinalized ledger commissions to match deduplicated active coached athletes (1 payout per athlete)
        computed_commissions = Decimal(str(l.total_coach_commission)).quantize(Decimal('0.01'))
        if not l.is_finalized and l.pt_commissions != computed_commissions:
            l.pt_commissions = computed_commissions
            PayrollLedger.objects.filter(id=l.id).update(pt_commissions=computed_commissions)

        st_shifts = shifts_by_staff.get(l.staff_user_id, [])
        l.att_scheduled_shifts = len(st_shifts)
        l.att_completed_shifts = sum(1 for s in st_shifts if s.actual_first_in is not None)
        l.att_late_minutes = sum(s.calculate_late_minutes() for s in st_shifts)
        l.att_overtime_minutes = sum(s.overtime_minutes for s in st_shifts)
        l.att_absence_minutes = sum(s.unapproved_absence_minutes for s in st_shifts)
        l.attendance_json = json.dumps({
            'scheduled': l.att_scheduled_shifts,
            'completed': l.att_completed_shifts,
            'late_minutes': l.att_late_minutes,
            'overtime_minutes': l.att_overtime_minutes,
            'absence_minutes': l.att_absence_minutes,
        })

    from wger.gym_operations_payroll.models import StaffSalaryAdvance

    total_payroll_net = sum(l.net_salary for l in payroll_ledgers)
    total_payroll_base = sum(l.base_salary for l in payroll_ledgers)
    total_payroll_commissions = sum(l.pt_commissions for l in payroll_ledgers)
    total_payroll_overtime = sum(l.overtime_pay for l in payroll_ledgers)
    total_payroll_penalties = sum(l.late_minutes_penalty + l.sudden_absence_penalty for l in payroll_ledgers)
    total_payroll_epf_employee = sum(l.epf_employee_8 for l in payroll_ledgers)
    total_payroll_epf_employer = sum(l.epf_employer_12 for l in payroll_ledgers)
    total_payroll_etf_employer = sum(l.etf_employer_3 for l in payroll_ledgers)
    total_payroll_advances = sum(l.salary_advance_deduction for l in payroll_ledgers)
    total_gym_cost = sum(l.gym_total_cost for l in payroll_ledgers)

    payroll_stats = {
        'month_label': first_of_selected_month.strftime('%B %Y'),
        'month_value': first_of_selected_month.strftime('%Y-%m'),
        'total_staff': len(payroll_ledgers),
        'total_net': float(total_payroll_net),
        'total_base': float(total_payroll_base),
        'total_commissions': float(total_payroll_commissions),
        'total_overtime': float(total_payroll_overtime),
        'total_penalties': float(total_payroll_penalties),
        'total_epf_employee': float(total_payroll_epf_employee),
        'total_epf_employer': float(total_payroll_epf_employer),
        'total_etf_employer': float(total_payroll_etf_employer),
        'total_advances': float(total_payroll_advances),
        'total_gym_cost': float(total_gym_cost),
    }

    # ── Staff Attendance & Shift Rosters ──
    recent_staff_shifts = list(StaffShift.objects.filter(
        shift_date__range=[first_of_selected_month, last_of_selected_month]
    ).select_related('staff_user').order_by('-shift_date', '-scheduled_start')[:40])
    if not recent_staff_shifts:
        recent_staff_shifts = list(StaffShift.objects.select_related('staff_user').order_by('-shift_date', '-scheduled_start')[:40])
    if not is_super_admin:
        recent_staff_shifts = [
            s for s in recent_staff_shifts
            if not (s.staff_user.is_superuser or s.staff_user.groups.filter(name='super_admin').exists())
        ]
    staff_users_list = [u for u in all_system_users if u['user'].is_staff and u['user'].is_active]

    recent_salary_advances = list(StaffSalaryAdvance.objects.select_related('staff_user', 'approved_by').order_by('-request_date', '-id')[:25])
    if not is_super_admin:
        recent_salary_advances = [
            a for a in recent_salary_advances
            if not (a.staff_user.is_superuser or a.staff_user.groups.filter(name='super_admin').exists())
        ]

    context = {
        'is_super_admin': is_super_admin,
        'role': current_role,
        'user_role': current_role,
        'page_title': 'Admin Console',
        'active_tab': current_tab,
        'selected_payroll_month': first_of_selected_month.strftime('%Y-%m'),
        'available_months': available_months,
        'club_info': {
            'name': 'Fit Me',
            'tagline': 'Train with Purpose & Move with Confidence',
            'address': 'Fit Me, New Town, Elpitiya Road, Pitigala, 80420',
            'phone': '070 762 7878',
        },
        'stats': {
            'active_members': active_members_count,
            'expiring_soon': expiring_soon_count,
            'pending_applications': pending_apps,
            'today_access_count': today_punches,
            'open_absence_alerts': open_alerts_count,
            'members_on_floor': members_on_floor,
            'staff_on_floor': staff_on_floor,
            'total_on_floor': members_on_floor + staff_on_floor,
            'floor_capacity': 60,
            'floor_occupancy_pct': min(100, int(((members_on_floor + staff_on_floor) / 60) * 100)),
            'zkbio_terminal': {
                'ip': '192.168.1.23',
                'port': 4370,
                'name': 'ZKTeco SpeedFace-V5L Turnstile',
                'status': 'ONLINE',
                'latency_ms': 1,
                'anti_passback': 'ACTIVE (60s)',
                'relay_state': 'ARMED',
            },
        },
        'finance': finance,
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
        'all_system_users': all_system_users,
        'user_stats': user_stats,
        'payroll_ledgers': payroll_ledgers,
        'payroll_stats': payroll_stats,
        'recent_staff_shifts': recent_staff_shifts,
        'staff_users_list': staff_users_list,
        'recent_salary_advances': recent_salary_advances,
        'financial_audit': financial_audit,
        'discount_audits': discount_audits,
        'current_year': str(current_year),
        'is_super_admin': is_super_admin,
        'current_role': current_role,
    }
    return render(request, 'dashboards/super_admin.html', context)


@login_required
@role_required('super_admin', 'admin')
def admin_users_view(request):
    """Direct view for /dashboard/admin/users/ — loads the admin console on Staff & Roles tab."""
    return super_admin_dashboard(request, active_tab='tab-admin-users')


@login_required
@role_required('front_desk', 'admin', 'super_admin')
def front_desk_dashboard(request):
    """Front Desk — member queue, biometric enrollment, live turnstile monitor, payments, and 80mm thermal receipts."""
    from wger.gym_operations_payroll.models import PaymentReceipt
    from wger.zkbio_integration.models import DoorAccessLog

    pending_apps = MemberApplication.objects.filter(status='pending').order_by('-applied_at')
    active_subs = Subscription.objects.filter(
        status='active',
        end_date__gte=timezone.now().date()
    ).select_related('member', 'plan', 'member__biometric_profile', 'member__member_profile').prefetch_related('buddy_links__partner_member').order_by('end_date')[:50]
    recent_receipts = PaymentReceipt.objects.select_related('member', 'cashier').order_by('-issued_at')[:20]
    recent_punches = DoorAccessLog.objects.select_related('user', 'user__member_profile').order_by('-punch_time')[:10]

    from django.contrib.auth import get_user_model
    from django.db.models import Q
    User = get_user_model()
    all_members = list(User.objects.filter(
        groups__name='member',
        is_staff=False,
        is_superuser=False
    ).exclude(
        groups__name__in=['super_admin', 'admin', 'front_desk', 'coach']
    ).exclude(
        userprofile__is_temporary=True
    ).select_related(
        'member_profile', 'biometric_profile', 'member_profile__assigned_coach'
    ).prefetch_related('subscriptions__plan').order_by('first_name', 'username'))

    current_year = timezone.now().year
    yearly_receipt_member_ids = set(
        PaymentReceipt.objects.filter(
            issued_at__year=current_year
        ).filter(
            Q(annual_fee_amount__gt=0) |
            Q(notes__icontains='Annual') | 
            Q(notes__icontains='Yearly') | 
            Q(notes__icontains='Registration') |
            Q(notes__icontains='Initial membership enrollment')
        ).values_list('member_id', flat=True)
    )

    today_date = timezone.now().date()
    for m in all_members:
        has_receipt = m.id in yearly_receipt_member_ids
        notes_paid = False
        prof = getattr(m, 'member_profile', None)
        if prof and prof.notes:
            pn = prof.notes.lower()
            if str(current_year) in prof.notes and ('annual' in pn or 'yearly' in pn or 'registration' in pn):
                notes_paid = True
        joined_this_year = bool(prof and prof.join_date and prof.join_date.year >= current_year)
        m.has_paid_yearly_this_year = has_receipt or notes_paid or joined_this_year

        # Detect active / expired subscription dates
        subs = list(m.subscriptions.all())
        active_list = [s for s in subs if s.status == 'active' and s.end_date >= today_date]
        if active_list:
            best_active = max(active_list, key=lambda s: s.end_date)
            m.has_active_subscription = True
            m.active_sub = best_active
            m.active_sub_end_str = best_active.end_date.strftime('%d %b %Y')
            m.active_sub_end_iso = best_active.end_date.isoformat()
            m.active_plan_name = best_active.plan.name if best_active.plan else 'Active Plan'
            m.active_plan_id = best_active.plan_id
            m.latest_sub_end_str = m.active_sub_end_str
        else:
            m.has_active_subscription = False
            m.active_sub = None
            m.active_sub_end_str = ''
            m.active_sub_end_iso = ''
            m.active_plan_name = ''
            if subs:
                latest_sub = max(subs, key=lambda s: s.end_date)
                m.latest_sub_end_str = latest_sub.end_date.strftime('%d %b %Y')
                m.active_plan_id = latest_sub.plan_id
            else:
                m.latest_sub_end_str = ''
                m.active_plan_id = None

    for sub in active_subs:
        if hasattr(sub, 'member'):
            m = sub.member
            has_receipt = m.id in yearly_receipt_member_ids
            notes_paid = False
            prof = getattr(m, 'member_profile', None)
            if prof and prof.notes:
                pn = prof.notes.lower()
                if str(current_year) in prof.notes and ('annual' in pn or 'yearly' in pn or 'registration' in pn):
                    notes_paid = True
            m.has_paid_yearly_this_year = has_receipt or notes_paid
            m.has_active_subscription = True
            m.active_sub_end_str = sub.end_date.strftime('%d %b %Y')
            m.active_sub_end_iso = sub.end_date.isoformat()
            m.active_plan_name = sub.plan.name if sub.plan else 'Active Plan'
            m.active_plan_id = sub.plan_id
            m.latest_sub_end_str = m.active_sub_end_str

    from wger.gym_operations_payroll.models import BuddyMembership
    from wger.membership.models import MembershipDiscountAudit

    all_member_ids = [m.id for m in all_members]
    buddy_links_fd = {
        bl.partner_member_id: bl
        for bl in BuddyMembership.objects.filter(
            partner_member_id__in=all_member_ids
        ).select_related('subscription__plan', 'subscription__member', 'primary_member')
    }

    # 1. First priority: Uncollected pending concessions explicitly awaiting Front Desk counter billing
    pending_concessions = MembershipDiscountAudit.objects.filter(
        member_id__in=all_member_ids,
        receipt__isnull=True
    ).select_related('authorized_by', 'plan').order_by('-created_at')

    pending_concessions_map = {}
    for aud in pending_concessions:
        if aud.member_id not in pending_concessions_map:
            pending_concessions_map[aud.member_id] = aud

    # 2. Second priority: Approved recurring concessions on file (e.g. staff perk, hardship, discount policy)
    latest_audits = MembershipDiscountAudit.objects.filter(
        member_id__in=all_member_ids
    ).select_related('authorized_by', 'plan').order_by('-created_at')

    latest_audit_map = {}
    for aud in latest_audits:
        if aud.member_id not in latest_audit_map:
            latest_audit_map[aud.member_id] = aud

    for m in all_members:
        m.linked_as_partner = buddy_links_fd.get(m.id)
        if m.id in pending_concessions_map:
            m.pending_concession = pending_concessions_map[m.id]
        elif m.id in latest_audit_map and latest_audit_map[m.id].discount_amount and latest_audit_map[m.id].discount_amount > 0:
            m.pending_concession = latest_audit_map[m.id]
        else:
            m.pending_concession = None

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
        'all_members': all_members,
        'all_system_users': [],
        'plans': MembershipPlan.objects.filter(is_active=True),
        'coaches': CoachProfile.objects.filter(is_active=True).select_related('user'),
        'recent_receipts': recent_receipts,
        'recent_door_punches': recent_punches,
        'is_admin_user': request.user.is_superuser or request.user.groups.filter(name__in=['admin', 'super_admin']).exists(),
        'staff_users_list': [
            {'id': u.id, 'username': u.username, 'full_name': u.get_full_name() or u.username}
            for u in User.objects.filter(is_staff=True, is_active=True).exclude(is_superuser=True).exclude(groups__name='super_admin').order_by('username')
        ],
    }
    return render(request, 'dashboards/front_desk.html', context)



@login_required
@role_required('coach', 'super_admin')
def coach_dashboard(request):
    """Coach — 6 modules: Members, Programs, Workout Plans, Nutrition Plans, Progress Reviews, Check-ins."""
    from wger.nutrition_lk.models import MealLog, DailyFuelTarget
    from wger.habit.models import WorkoutStreak
    from wger.membership.models import MemberProfile, GymProgram, BodyCheckIn, MemberWorkoutLog

    # Coaches can ONLY see genuine members (strictly member role, no staff/admins/superadmins)
    assigned_members = MemberProfile.objects.filter(
        assigned_coach=request.user,
        user__is_staff=False,
        user__is_superuser=False,
        user__groups__name='member'
    ).exclude(
        user__userprofile__is_temporary=True
    ).select_related('user', 'assigned_program')

    all_active_members = MemberProfile.objects.filter(
        user__is_active=True,
        user__is_staff=False,
        user__is_superuser=False,
        user__groups__name='member'
    ).exclude(
        user__userprofile__is_temporary=True
    ).select_related('user', 'assigned_program', 'assigned_coach').order_by('user__first_name', 'user__username')

    if not assigned_members.exists():
        # Fallback to active members if none explicitly assigned
        assigned_members = all_active_members[:20]

    from wger.zkbio_integration.models import DoorAccessLog
    recent_floor_punches = list(DoorAccessLog.objects.filter(
        event_type='ENTRY',
        punch_time__date=timezone.now().date()
    ).select_related('user').order_by('-punch_time')[:20])
    floor_user_ids = set(p.user_id for p in recent_floor_punches if p.user_id)

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
    at_risk_ids = [s.member_id for s in at_risk]

    # ── Coach Monthly Earnings, Commissions & Payslip ──
    from wger.gym_operations_payroll.models import PayrollLedger, StaffShift
    import calendar
    from decimal import Decimal

    curr_first_day = timezone.now().date().replace(day=1)
    curr_last_day_num = calendar.monthrange(curr_first_day.year, curr_first_day.month)[1]
    curr_last_day = curr_first_day.replace(day=curr_last_day_num)

    coach_ledger = PayrollLedger.objects.filter(
        staff_user=request.user,
        month=curr_first_day
    ).first()

    if not coach_ledger:
        try:
            from wger.gym_operations_payroll.tasks import calculate_monthly_payroll
            calculate_monthly_payroll(curr_first_day.year, curr_first_day.month)
            coach_ledger = PayrollLedger.objects.filter(
                staff_user=request.user,
                month=curr_first_day
            ).first()
        except Exception:
            pass

    # Coached PT Athletes with 7000/3000/4000 split
    coach_pt_clients = []
    pt_member_user_ids = [mp.user_id for mp in assigned_members if mp.personal_trainer_needed and mp.user_id]
    active_subs_by_user = {}
    if pt_member_user_ids:
        for s in Subscription.objects.filter(
            member_id__in=pt_member_user_ids,
            status='active',
            start_date__lte=curr_last_day,
            end_date__gte=curr_first_day
        ).select_related('plan').order_by('-start_date'):
            if s.member_id not in active_subs_by_user:
                active_subs_by_user[s.member_id] = s

    for mem_prof in assigned_members:
        if mem_prof.personal_trainer_needed:
            active_s = active_subs_by_user.get(mem_prof.user_id)
            if active_s:
                coach_pt_clients.append({
                    'name': mem_prof.user.get_full_name() or mem_prof.user.username,
                    'username': mem_prof.user.username,
                    'phone': mem_prof.phone or '—',
                    'plan_name': active_s.plan.name if active_s.plan else 'Personal Coaching',
                    'package_fee': Decimal('7000.00'),
                    'gym_share': Decimal('3000.00'),
                    'coach_share': Decimal('4000.00'),
                    'validity': f"{active_s.start_date.strftime('%d %b')} – {active_s.end_date.strftime('%d %b %Y')}",
                })

    if coach_ledger and not coach_ledger.is_finalized:
        computed_comm = Decimal(len(coach_pt_clients)) * Decimal('4000.00')
        if coach_ledger.pt_commissions != computed_comm:
            coach_ledger.pt_commissions = computed_comm
            PayrollLedger.objects.filter(id=coach_ledger.id).update(pt_commissions=computed_comm)

    coach_shifts = list(StaffShift.objects.filter(
        staff_user=request.user,
        shift_date__range=[curr_first_day, curr_last_day]
    ).order_by('-shift_date'))

    coach_attendance = {
        'scheduled': len(coach_shifts),
        'completed': len([s for s in coach_shifts if s.actual_first_in]),
        'late_minutes': sum(s.calculate_late_minutes() for s in coach_shifts),
        'overtime_minutes': sum(s.overtime_minutes for s in coach_shifts),
    }

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
        'all_active_members': all_active_members,
        'recent_floor_punches': recent_floor_punches,
        'floor_user_ids': floor_user_ids,
        'unreviewed_meals': unreviewed_meals,
        'at_risk_members': at_risk,
        'at_risk_ids': at_risk_ids,
        'programs': programs,
        'recent_checkins': recent_checkins,
        'recent_workouts': recent_workouts,
        'nutrition_targets': nutrition_targets,
        'coach_ledger': coach_ledger,
        'coach_pt_clients': coach_pt_clients,
        'coach_shifts': coach_shifts,
        'coach_attendance': coach_attendance,
        'curr_month_label': curr_first_day.strftime('%B %Y'),
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

    # Fetch comprehensive access status
    from wger.membership.services import get_member_access_summary

    access_summary = get_member_access_summary(user)
    subscription = access_summary['subscription']
    door_access_active = access_summary['door_access_active']
    today = timezone.now().date()

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

    from wger.nutrition_lk.models import WaterLog
    today_water_logs = WaterLog.objects.filter(member=user, logged_at__date=today)
    water_consumed_ml = sum(w.amount_ml for w in today_water_logs)
    water_target_ml = fuel_progress['targets'].get('water_ml', 3000) if fuel_progress else 3000
    water_consumed = round(water_consumed_ml / 1000, 1)
    water_target = round(water_target_ml / 1000, 1)
    water_pct = min(100, int((water_consumed_ml / max(1, water_target_ml)) * 100))

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
    recent_receipts = PaymentReceipt.objects.filter(member=user).order_by('-issued_at')[:15]

    # Assessments & Coach Prescription Status
    from wger.membership.models import NutritionAssessment, WorkoutAssessment
    latest_nut_assessment = NutritionAssessment.objects.filter(member=user).order_by('-assessment_date', '-id').first()
    latest_wrk_assessment = WorkoutAssessment.objects.filter(member=user).order_by('-assessment_date', '-id').first()
    coach_plan_status = 'NOT_SUBMITTED'
    if latest_nut_assessment or latest_wrk_assessment:
        statuses = [a.status for a in [latest_nut_assessment, latest_wrk_assessment] if a]
        if any(s in ['reviewed', 'assigned', 'active'] for s in statuses):
            coach_plan_status = 'ACTIVE_APPROVED'
        else:
            coach_plan_status = 'PENDING_REVIEW'

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
        'access_summary': access_summary,
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
        'membership_plans': MembershipPlan.objects.filter(is_active=True),
        'latest_nut_assessment': latest_nut_assessment,
        'latest_wrk_assessment': latest_wrk_assessment,
        'coach_plan_status': coach_plan_status,
        'is_coach': request.user.groups.filter(name__in=['coach', 'gym_trainer']).exists(),
        'is_admin': request.user.is_staff or request.user.is_superuser or request.user.groups.filter(name__in=['gym_manager', 'super_admin']).exists(),
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
        from wger.membership.models import CoachProfile
        coaches = CoachProfile.objects.filter(is_active=True).select_related('user')
        return render(request, 'register.html', {'plans': plans, 'coaches': coaches})

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

        # Yearly fee (default 1000, 0 for student)
        default_yearly = '0.00' if (plan and plan.plan_type == 'student') else '1000.00'
        default_monthly = str(plan.price_monthly) if (plan and getattr(plan, 'price_monthly', None)) else '4000.00'
        admission_fee = parse_dec(data.get('admission_fee', default_yearly), default_yearly)
        monthly_fee = parse_dec(data.get('monthly_fee', default_monthly), default_monthly)
        discount = parse_dec(data.get('discount', '0.00'), '0.00')
        calc_total = str(max(Decimal('0.00'), admission_fee + monthly_fee - discount))
        total_paid = parse_dec(data.get('total_paid', calc_total), calc_total)

        # Dates & Age
        dob = data.get('date_of_birth') or None
        age = int(data.get('age')) if data.get('age') and data.get('age').isdigit() else None
        start_date = data.get('start_date') or None
        end_date = data.get('end_date') or None


        # Calculate actual age from date of birth if available
        if dob:
            try:
                from datetime import date
                dob_d = date.fromisoformat(str(dob))
                t_date = timezone.now().date()
                calculated_applicant_age = t_date.year - dob_d.year - ((t_date.month, t_date.day) < (dob_d.month, dob_d.day))
                age = calculated_applicant_age
            except Exception:
                pass

        # Strict Age Validation for Student Package: only under 19 (age <= 18) allowed. At 19+, general package is mandatory.
        if plan and (getattr(plan, 'is_student_plan', False) or plan.plan_type == 'student' or 'student' in (plan.name or '').lower()):
            if age is None and not dob:
                return JsonResponse({
                    'success': False,
                    'error': 'Date of birth is required to verify Student Package eligibility (must be age 18 or under).'
                }, status=400)
            if age is not None and age >= 19:
                return JsonResponse({
                    'success': False,
                    'error': f'The Student Package is strictly available for students aged 18 and under. Because the applicant is {age} years old, please select a general membership package (e.g. Monthly Package).'
                }, status=400)

        # Preferred coach lookup
        from django.contrib.auth import get_user_model
        User = get_user_model()
        preferred_coach_id = data.get('preferred_coach_id')
        preferred_coach = User.objects.filter(id=preferred_coach_id).first() if preferred_coach_id else None
        pt_needed = (data.get('personal_trainer_needed') == 'yes') or (plan and plan.plan_type == 'personal_coaching') or bool(preferred_coach)


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
            personal_trainer_needed=pt_needed,
            preferred_coach=preferred_coach,
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
@role_required('front_desk', 'admin', 'super_admin')
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


def generate_unique_biometric_pin():
    """
    Safely generates the next available unique numeric PIN across both
    MemberProfile and BiometricProfile tables atomically.
    """
    from wger.membership.models import MemberProfile
    return MemberProfile.get_next_pin()


@login_required
@role_required('front_desk', 'admin', 'super_admin')
def approve_application_api(request, app_id):
    """Dynamically approves an intake application, creates user, PIN, and biometric profile."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
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

        # Look up or create User safely
        user = User.objects.filter(email=app.email).first()
        created = False
        if not user:
            user = User.objects.create(
                username=username,
                email=app.email,
                first_name=app.full_name.split()[0] if app.full_name else 'Member',
                last_name=" ".join(app.full_name.split()[1:]) if len(app.full_name.split()) > 1 else '',
                is_active=True,
            )
            user.set_unusable_password()
            user.save()
            created = True

        # Assign Member Group
        member_group, _ = Group.objects.get_or_create(name='member')
        user.groups.add(member_group)

        # MemberProfile & PIN
        profile, _ = MemberProfile.objects.get_or_create(user=user)
        pin_taken = False
        if profile.biometric_pin:
            pin_taken = BiometricProfile.objects.filter(zk_pin=profile.biometric_pin).exclude(user=user).exists() or \
                        MemberProfile.objects.filter(biometric_pin=profile.biometric_pin).exclude(user=user).exists()

        if not profile.biometric_pin or pin_taken:
            profile.biometric_pin = generate_unique_biometric_pin()

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
        if not profile.join_date:
            profile.join_date = app.start_date or (app.applied_at.date() if app.applied_at else timezone.now().date())
        profile.save()


        # BiometricProfile for ZKBio Turnstile hardware / LiveU Cloud
        bio_profile = BiometricProfile.objects.filter(user=user).first()
        if not bio_profile:
            target_pin = profile.biometric_pin
            if BiometricProfile.objects.filter(zk_pin=target_pin).exists():
                target_pin = generate_unique_biometric_pin()
                profile.biometric_pin = target_pin
                profile.save(update_fields=['biometric_pin'])

            bio_profile = BiometricProfile.objects.create(
                user=user,
                zk_pin=target_pin,
                sync_status='PENDING',
                disabled=False,
            )
        else:
            if not bio_profile.zk_pin:
                target_pin = profile.biometric_pin
                if BiometricProfile.objects.filter(zk_pin=target_pin).exclude(user=user).exists():
                    target_pin = generate_unique_biometric_pin()
                bio_profile.zk_pin = target_pin
                profile.biometric_pin = target_pin
                profile.save(update_fields=['biometric_pin'])
            else:
                profile.biometric_pin = bio_profile.zk_pin
                profile.save(update_fields=['biometric_pin'])
            bio_profile.disabled = False
            bio_profile.sync_status = 'PENDING'
            bio_profile.save()

        # Auto-provision to LiveU Cloud hardware if configured
        try:
            from wger.zkbio_integration.liveu_client import LiveUClient
            liveu = LiveUClient()
            if liveu.is_configured:
                cloud_res = liveu.create_member(
                    member_id=profile.biometric_pin,
                    name=app.full_name,
                    uid=app.nic_passport or profile.phone,
                    status="Active"
                )
                if cloud_res and cloud_res.get('_id'):
                    bio_profile.liveu_id = cloud_res['_id']
                    bio_profile.sync_status = 'SYNCED'
                    bio_profile.save(update_fields=['liveu_id', 'sync_status'])
        except Exception as ex:
            import logging
            logging.getLogger('wger').error(f"[LiveU Cloud] Failed to register member on LiveU: {ex}")

        import json
        payload = {}
        if request.body:
            try:
                payload = json.loads(request.body)
            except Exception:
                pass

        # Determine membership plan (allow overriding desired plan upon approval)
        from decimal import Decimal
        def parse_dec(val, fallback):
            try:
                return Decimal(str(val).strip())
            except Exception:
                return fallback

        plan_id = payload.get('plan_id')
        plan = None
        if plan_id:
            plan = MembershipPlan.objects.filter(id=plan_id).first()
        if not plan:
            plan = app.desired_plan or MembershipPlan.objects.first()

        # Strict Age Validation for Student Package: only under 19 (age <= 18) allowed. At 19+, general package is mandatory.
        if plan and (getattr(plan, 'is_student_plan', False) or plan.plan_type == 'student' or 'student' in (plan.name or '').lower()):
            app_age = getattr(app, 'calculated_age', None) or app.age
            if app_age is not None and app_age >= 19:
                return JsonResponse({
                    'error': f"Cannot enroll under Student Package: {app.full_name} is {app_age} years old. Student packages are restricted to ages 18 and under. When turning 19, a general package is required."
                }, status=400)


        # Fee calculations: First year fee (annual registration fee) & package fee
        default_first_year = Decimal('0.00') if (plan and plan.plan_type == 'student') else Decimal(str(getattr(plan, 'registration_fee', 1000.00)))
        default_pkg_fee = Decimal(str(getattr(plan, 'price_monthly', 4000.00)))

        if 'package_amount' in payload:
            package_amount = parse_dec(payload['package_amount'], default_pkg_fee)
        elif app.monthly_fee and app.monthly_fee > 0:
            package_amount = app.monthly_fee
        else:
            package_amount = default_pkg_fee

        if 'first_year_fee' in payload:
            first_year_fee = parse_dec(payload['first_year_fee'], default_first_year)
        elif 'annual_fee_amount' in payload:
            first_year_fee = parse_dec(payload['annual_fee_amount'], default_first_year)
        elif app.admission_fee and app.admission_fee > 0:
            first_year_fee = app.admission_fee
        else:
            first_year_fee = default_first_year

        if 'total_paid' in payload:
            total_paid = parse_dec(payload['total_paid'], package_amount + first_year_fee)
        elif app.total_paid and app.total_paid > 0:
            total_paid = app.total_paid
        else:
            total_paid = package_amount + first_year_fee

        payment_method = payload.get('payment_method') or app.payment_method or 'cash'
        receipt_notes = payload.get('notes') or f"Initial membership enrollment ({app.nic_passport or 'Walk-in'})"

        today = timezone.now().date()
        duration_days = getattr(plan, 'duration_days', 30) if plan else 30
        end_date = app.end_date if (app.end_date and not plan_id) else (today + timezone.timedelta(days=duration_days))

        # Create active subscription with fees
        sub = Subscription.objects.create(
            member=user,
            plan=plan,
            start_date=app.start_date or today,
            end_date=end_date,
            status='active',
            payment_method=payment_method,
            amount_paid=total_paid,
            approved_by=request.user,
            payment_date=timezone.now()
        )

        # Mark application as approved with updated plan and fees
        app.desired_plan = plan
        app.admission_fee = first_year_fee
        app.monthly_fee = package_amount
        app.total_paid = total_paid
        app.payment_method = payment_method
        app.status = 'approved'
        app.reviewed_by = request.user
        app.reviewed_at = timezone.now()
        app.created_user = user
        app.save()

        # Issue PaymentReceipt for 80mm thermal printing with package and first year fee itemized
        from wger.gym_operations_payroll.models import PaymentReceipt
        receipt = PaymentReceipt.objects.create(
            receipt_number=PaymentReceipt.generate_next_receipt_number(),
            subscription=sub,
            member=user,
            plan_name=plan.name if plan else 'Standard',
            duration_days=duration_days,
            validity_start=sub.start_date,
            validity_end=sub.end_date,
            amount_paid=total_paid,
            package_amount=package_amount,
            annual_fee_amount=first_year_fee,
            payment_method=payment_method,
            cashier=request.user,
            member_pin=profile.biometric_pin or '',
            notes=receipt_notes
        )

        # Dispatch branded welcome email with secure password setup link
        from wger.core.email_service import send_welcome_password_setup_email
        email_sent, _ = send_welcome_password_setup_email(user, request=request, is_async=True)

        return JsonResponse({
            'success': True,
            'message': f"Application approved for {app.full_name}! Password setup email sent to {user.email}.",
            'username': user.username,
            'email_sent': email_sent,
            'email': user.email,
            'pin': profile.biometric_pin,
            'plan': plan.name if plan else 'Standard',
            'sub_id': sub.id,
            'receipt_id': receipt.id,
            'receipt_number': receipt.receipt_number,
            'receipt_url': request.build_absolute_uri(f"/receipt/{receipt.id}/?autoprint=1")
        })
    except Exception as ex:
        import logging
        logging.getLogger('wger').error(f"[approve_application_api] Error approving app {app_id}: {ex}", exc_info=True)
        return JsonResponse({'error': f"Failed to approve application: {str(ex)}"}, status=500)


@login_required
@role_required('front_desk', 'admin', 'super_admin')
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
@role_required('front_desk', 'admin', 'super_admin')
def record_payment_api(request):
    """Records payment, activates subscription, provisions door access, and issues 80mm thermal receipt."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        import json
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            data = request.POST

        from decimal import Decimal
        from django.contrib.auth import get_user_model
        from django.db import transaction
        from wger.zkbio_integration.models import BiometricProfile
        from wger.membership.models import MemberProfile
        from wger.gym_operations_payroll.models import PaymentReceipt
        from wger.gym_operations_payroll.models import PayrollLedger
        User = get_user_model()

        member_id = data.get('member_id')
        plan_id = data.get('plan_id')
        method = data.get('payment_method', 'cash')
        amount = data.get('amount_paid', 4000)
        include_yearly_fee = bool(data.get('include_yearly_fee', False))
        yearly_fee_val = data.get('yearly_fee_amount', 0)
        try:
            yearly_fee_amount = Decimal(str(yearly_fee_val or 0))
        except Exception:
            yearly_fee_amount = Decimal('0.00')

        try:
            amount_dec = Decimal(str(amount or 0))
        except Exception:
            return JsonResponse({'success': False, 'error': 'Invalid payment amount.'}, status=400)

        member = User.objects.filter(id=member_id).first()
        if not member:
            return JsonResponse({'success': False, 'error': 'Member not found'}, status=404)

        plan = MembershipPlan.objects.filter(id=plan_id).first() or MembershipPlan.objects.first()

        # Strict Age Validation for Student Package: only under 19 (age <= 18) allowed. At 19+, general package is mandatory.
        if plan and (getattr(plan, 'is_student_plan', False) or plan.plan_type == 'student' or 'student' in (plan.name or '').lower()):
            m_profile = MemberProfile.objects.filter(user=member).first()
            mem_age = getattr(m_profile, 'age', None)
            if mem_age is not None and mem_age >= 19:
                return JsonResponse({
                    'success': False,
                    'error': f"The Student Package is strictly for members aged 18 and under. {member.get_full_name() or member.username} is {mem_age} years old and must select a general membership package."
                }, status=400)

        coaching_only = bool(data.get('coaching_only', False))
        today = timezone.now().date()
        # Seamless renewal: if member already has an active subscription expiring in the future, extend from that end date
        latest_active_sub = Subscription.objects.filter(
            member=member, status='active', end_date__gte=today
        ).order_by('-end_date').first()

        if coaching_only and latest_active_sub:
            start_date = today
            end_date = max(latest_active_sub.end_date, today + timezone.timedelta(days=getattr(plan, 'duration_days', 30)))
        else:
            start_date = (latest_active_sub.end_date + timezone.timedelta(days=1)) if latest_active_sub else today
            end_date = start_date + timezone.timedelta(days=getattr(plan, 'duration_days', 30))

        # Check for existing pending subscription from Super Admin override
        existing_pending_sub = Subscription.objects.filter(
            member=member, status='pending_payment'
        ).order_by('-created_at').first()

        # Check for approved Super Admin concession awaiting Front Desk billing
        from wger.membership.models import MembershipDiscountAudit
        pending_concession = MembershipDiscountAudit.objects.filter(
            member=member,
            receipt__isnull=True
        ).order_by('-created_at').first()

        latest_concession = None
        if not pending_concession:
            latest_concession = MembershipDiscountAudit.objects.filter(
                member=member
            ).order_by('-created_at').first()
            if latest_concession and latest_concession.discount_amount and latest_concession.discount_amount > Decimal('0.00'):
                concession_discount_amount = latest_concession.discount_amount
            else:
                concession_discount_amount = Decimal('0.00')
        else:
            concession_discount_amount = pending_concession.discount_amount if pending_concession else Decimal('0.00')

        with transaction.atomic():
            if existing_pending_sub:
                sub = existing_pending_sub
                sub.plan = plan
                sub.start_date = start_date
                sub.end_date = end_date
                sub.status = 'active'
                sub.payment_method = method
                sub.amount_paid = amount_dec
                sub.approved_by = request.user
                sub.payment_date = timezone.now()
                sub.save()
            else:
                sub = Subscription.objects.create(
                    member=member,
                    plan=plan,
                    start_date=start_date,
                    end_date=end_date,
                    status='active',
                    payment_method=method,
                    amount_paid=amount_dec,
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

            # Coach attribution and 7000 Personal Coaching split (4000 coach payslip / 3000 gym)
            coach_id = data.get('coach_id')
            assigned_coach_user = None
            if coach_id:
                assigned_coach_user = User.objects.filter(id=coach_id).first()
                if assigned_coach_user and profile:
                    profile.assigned_coach = assigned_coach_user
                    profile.personal_trainer_needed = True
                    profile.save(update_fields=['assigned_coach', 'personal_trainer_needed'])
            elif profile and profile.assigned_coach:
                assigned_coach_user = profile.assigned_coach

            # Check if this is a personal coaching package or coach was assigned with coaching payment
            is_personal_coaching = (
                (plan and getattr(plan, 'plan_type', '') == 'personal_coaching') or
                (plan and 'coaching' in plan.name.lower()) or
                bool(assigned_coach_user and amount_dec >= Decimal('7000.00'))
            )

            receipt_notes = 'Front Desk POS Payment'
            if pending_concession and concession_discount_amount > 0:
                receipt_notes = f"{receipt_notes} | Admin Concession: -LKR {concession_discount_amount:,.2f} ({pending_concession.get_reason_category_display()})"

            if is_personal_coaching and assigned_coach_user:
                first_of_month = today.replace(day=1)
                ledger, _ = PayrollLedger.objects.get_or_create(
                    staff_user=assigned_coach_user,
                    month=first_of_month,
                    defaults={
                        'base_salary': Decimal('75000.00'),
                        'pt_commissions': Decimal('0.00'),
                    }
                )
                coach_cut = Decimal('4000.00')
                gym_cut = Decimal('3000.00')
                ledger.pt_commissions = (ledger.pt_commissions or Decimal('0.00')) + coach_cut
                coach_name = assigned_coach_user.get_full_name() or assigned_coach_user.username
                ledger.notes = (ledger.notes + f"\n+ LKR 4,000 PT Commission for member {member.username} ({plan.name if plan else 'Coaching'}).").strip()
                ledger.save(update_fields=['pt_commissions', 'notes'])
                if coaching_only:
                    receipt_notes = f"{receipt_notes} | Personal Coaching Add-on (Monthly Active Pass) | LKR {gym_cut} Gym Facility Fee | LKR {coach_cut} Coach ({coach_name})"
                else:
                    receipt_notes = f"{receipt_notes} | Personal Coaching Split: LKR {gym_cut} Gym Facility Fee | LKR {coach_cut} Coach ({coach_name})"

            # Handle Yearly Registration / Renewal Fee
            if include_yearly_fee:
                if yearly_fee_amount > 0:
                    receipt_notes = f"{receipt_notes} | Includes Annual Registration/Renewal Fee: LKR {yearly_fee_amount:,.0f}"
                    if profile:
                        profile.notes = (profile.notes + f"\nAnnual Registration/Renewal Fee LKR {yearly_fee_amount:,.0f} paid on {today}.").strip()
                        profile.save(update_fields=['notes'])
                elif getattr(plan, 'plan_type', '') == 'student':
                    receipt_notes = f"{receipt_notes} | Student Package: LKR 0 Annual Registration Fee (Free)"

            reference_note = str(data.get('reference_note', '')).strip()
            if reference_note:
                receipt_notes = f"{receipt_notes} | Ref: {reference_note}"

            # Update subscription notes for full auditability
            sub.notes = (sub.notes or '') + ("\n" + receipt_notes if sub.notes else receipt_notes)
            sub.save(update_fields=['notes'])

            # Compute granular billing amounts for accurate receipt itemization
            if not include_yearly_fee:
                yearly_fee_amount = Decimal('0.00')

            package_amount_raw = data.get('package_amount')
            coaching_amount_raw = data.get('coaching_amount')
            coach_name_str = (assigned_coach_user.get_full_name() or assigned_coach_user.username) if assigned_coach_user else ''

            if package_amount_raw is not None and coaching_amount_raw is not None:
                try:
                    package_amount = Decimal(str(package_amount_raw))
                except Exception:
                    package_amount = Decimal('0.00')
                try:
                    coaching_amount = Decimal(str(coaching_amount_raw))
                except Exception:
                    coaching_amount = Decimal('0.00')
            else:
                if coaching_only:
                    package_amount = Decimal('0.00')
                    coaching_amount = Decimal('7000.00')
                elif is_personal_coaching and assigned_coach_user and (not plan or plan.plan_type != 'personal_coaching'):
                    coaching_amount = Decimal('7000.00')
                    package_amount = max(Decimal('0.00'), amount_dec - coaching_amount - yearly_fee_amount)
                else:
                    coaching_amount = Decimal('0.00')
                    if concession_discount_amount > Decimal('0.00') and plan:
                        package_amount = plan.price_monthly
                    else:
                        package_amount = max(Decimal('0.00'), amount_dec - yearly_fee_amount)

            # Issue 80mm Thermal Payment Receipt with Granular Line-Items
            receipt = PaymentReceipt.objects.create(
                receipt_number=PaymentReceipt.generate_next_receipt_number(),
                subscription=sub,
                member=member,
                plan_name=plan.name if plan else 'Standard',
                duration_days=getattr(plan, 'duration_days', 30),
                validity_start=sub.start_date,
                validity_end=sub.end_date,
                amount_paid=amount_dec,
                package_amount=package_amount,
                discount_amount=concession_discount_amount,
                coaching_amount=coaching_amount,
                annual_fee_amount=yearly_fee_amount,
                coach_name=coach_name_str,
                payment_method=method,
                cashier=request.user,
                member_pin=pin,
                notes=receipt_notes
            )

            # Settle pending MembershipDiscountAudit
            if pending_concession:
                pending_concession.receipt = receipt
                pending_concession.final_amount_paid = amount_dec
                pending_concession.subscription = sub
                pending_concession.justification = (pending_concession.justification + f" | Settled at Front Desk by {request.user.username} (Receipt #{receipt.receipt_number})").strip()
                pending_concession.save(update_fields=['receipt', 'final_amount_paid', 'subscription', 'justification'])
            elif concession_discount_amount > Decimal('0.00') and latest_concession:
                MembershipDiscountAudit.objects.create(
                    member=member,
                    authorized_by=latest_concession.authorized_by or request.user,
                    subscription=sub,
                    plan=sub.plan,
                    discount_type=latest_concession.discount_type,
                    original_price=plan.price_monthly if plan else Decimal('4000.00'),
                    discount_value=latest_concession.discount_value,
                    discount_amount=concession_discount_amount,
                    annual_fee_waived=latest_concession.annual_fee_waived,
                    final_amount_paid=amount_dec,
                    reason_category=latest_concession.reason_category,
                    justification=f"Renewal under approved {latest_concession.get_reason_category_display()} concession (Auth by @{latest_concession.authorized_by.username}) | Settled at Front Desk by {request.user.username} (Receipt #{receipt.receipt_number})",
                    receipt=receipt
                )

        return JsonResponse({
            'success': True,
            'message': f"Payment recorded for {member.username}. Subscription active until {sub.end_date:%d %b %Y}.",
            'receipt_id': receipt.id,
            'receipt_number': receipt.receipt_number,
            'receipt_url': f"/receipt/{receipt.id}/?autoprint=1"
        })
    except Exception as e:
        logger.exception("Failed to record payment: %s", e)
        return JsonResponse({'success': False, 'error': f"Payment recording failed: {str(e)}"}, status=400)


@login_required
@role_required('front_desk', 'admin', 'super_admin')
def assign_coach_api(request, member_id):
    """Front Desk or Super Admin assigns or updates a personal coach for a member."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    from django.contrib.auth import get_user_model
    from wger.membership.models import MemberProfile
    User = get_user_model()
    member = User.objects.filter(id=member_id).first()
    if not member:
        return JsonResponse({'error': 'Member not found'}, status=404)

    coach_id = data.get('coach_id')
    profile, _ = MemberProfile.objects.get_or_create(user=member)
    if coach_id:
        coach = User.objects.filter(id=coach_id).first()
        if not coach:
            return JsonResponse({'error': 'Coach not found'}, status=404)
        profile.assigned_coach = coach
        profile.personal_trainer_needed = True
        coach_name = coach.get_full_name() or coach.username
    else:
        profile.assigned_coach = None
        profile.personal_trainer_needed = False
        coach_name = 'None'

    profile.save(update_fields=['assigned_coach', 'personal_trainer_needed'])
    return JsonResponse({
        'success': True,
        'message': f"Personal coach for {member.username} set to '{coach_name}'.",
        'coach_name': coach_name
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

    club_info = {
        'name': 'FIT ME FITNESS & HEALTH CLUB',
        'tagline': 'TRAIN WITH PURPOSE & MOVE WITH CONFIDENCE',
        'address': 'New Town, Elpitiya Road, Pitigala, 80420',
        'phone': '070 762 7878',
        'email': 'hello@fitmefitness.lk',
        'web': 'www.fitmefitness.lk',
    }

    return render(request, 'receipt_80mm.html', {
        'receipt': receipt,
        'club_info': club_info,
        'is_staff_or_admin': is_staff_or_admin,
    })


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
@role_required('front_desk', 'admin', 'super_admin')
def desk_member_lookup_api(request):
    """
    Universal Member Quick-Search for Front Desk.
    Searches by name, phone, or PIN.
    Returns: full athlete status (Active / Expired / Unpaid / In Gym Now) + quick actions.
    """
    from django.contrib.auth import get_user_model
    from django.db.models import Q
    from wger.membership.models import Subscription
    from wger.gym_operations_payroll.models import PaymentReceipt
    from wger.zkbio_integration.models import DoorAccessLog

    User = get_user_model()
    q = request.GET.get('q', '').strip()
    if not q or len(q) < 2:
        return JsonResponse({'results': []})

    clean_q = q.lstrip('#').replace('FM', '').replace('fm', '').strip()
    user_q = (
        Q(first_name__icontains=q) |
        Q(last_name__icontains=q) |
        Q(username__icontains=q) |
        Q(email__icontains=q) |
        Q(member_profile__phone__icontains=q) |
        Q(member_profile__nic_passport__icontains=q) |
        Q(biometric_profile__zk_pin__icontains=q)
    )
    if clean_q and clean_q != q:
        user_q |= Q(biometric_profile__zk_pin__icontains=clean_q)
        if clean_q.isdigit():
            user_q |= Q(id=int(clean_q))

    is_super_admin = request.user.is_superuser or request.user.groups.filter(name='super_admin').exists()
    users_qs = User.objects.filter(user_q).exclude(userprofile__is_temporary=True).select_related('member_profile', 'biometric_profile')
    if not is_super_admin:
        users_qs = users_qs.exclude(is_superuser=True).exclude(groups__name='super_admin')
    user_groups = set(request.user.groups.values_list('name', flat=True))
    if 'coach' in user_groups and not is_super_admin and not (user_groups.intersection({'admin', 'front_desk'})):
        users_qs = users_qs.filter(groups__name='member', is_staff=False, is_superuser=False)

    users = users_qs.distinct()[:15]

    today = timezone.now().date()
    results = []
    for u in users:
        sub = Subscription.objects.filter(member=u, status='active', end_date__gte=today).order_by('-end_date').first()
        if not sub:
            sub = Subscription.objects.filter(member=u).order_by('-end_date').first()

        mem_prof = getattr(u, 'member_profile', None)
        bio_prof = getattr(u, 'biometric_profile', None)

        # Baseline plan & subscription details
        plan_name = 'No Plan'
        sub_status = 'NO_PLAN'
        days_left = 0
        end_date_str = ''

        if sub:
            plan_name = sub.plan.name if sub.plan else 'Standard Membership'
            end_date_str = sub.end_date.strftime('%d %b %Y') if sub.end_date else ''
            if sub.status == 'active' and sub.end_date and sub.end_date >= today:
                sub_status = 'ACTIVE'
                days_left = max(0, (sub.end_date - today).days)
            elif sub.status == 'active' and sub.end_date and sub.end_date < today:
                sub_status = 'EXPIRED'
                days_left = 0
            else:
                sub_status = (sub.status or 'INACTIVE').upper()
                days_left = 0

        photo_url = ''
        if mem_prof and getattr(mem_prof, 'profile_photo', None):
            try:
                photo_url = mem_prof.profile_photo.url
            except Exception:
                photo_url = ''

        latest_punch = None
        if bio_prof and bio_prof.zk_pin:
            latest_punch = DoorAccessLog.objects.filter(
                punch_time__date=today
            ).filter(
                Q(user=u) | Q(zk_pin=bio_prof.zk_pin)
            ).order_by('-punch_time').first()
        else:
            latest_punch = DoorAccessLog.objects.filter(
                punch_time__date=today,
                user=u
            ).order_by('-punch_time').first()

        on_floor = (latest_punch.event_type == 'ENTRY') if latest_punch else False
        last_receipt = PaymentReceipt.objects.filter(member=u).order_by('-issued_at').first()

        yearly_paid_q = PaymentReceipt.objects.filter(
            member=u,
            issued_at__year=today.year
        ).filter(
            Q(notes__icontains='Annual') | 
            Q(notes__icontains='Yearly') | 
            Q(notes__icontains='Registration') |
            Q(notes__icontains='Initial membership enrollment')
        ).exists()
        notes_paid_u = bool(mem_prof and mem_prof.notes and str(today.year) in mem_prof.notes and ('annual' in mem_prof.notes.lower() or 'yearly' in mem_prof.notes.lower() or 'registration' in mem_prof.notes.lower()))
        yearly_fee_paid = yearly_paid_q or notes_paid_u

        from wger.gym_operations_payroll.models import BuddyMembership
        is_linked_partner = False
        partner_primary_name = ''
        buddy_link = BuddyMembership.objects.filter(
            partner_member=u
        ).select_related('subscription__plan', 'subscription__member', 'primary_member').order_by('-subscription__end_date').first()

        if buddy_link and (not sub or sub.status != 'active' or (sub.end_date and sub.end_date < today)):
            sub = buddy_link.subscription
            is_linked_partner = True
            partner_primary_name = buddy_link.primary_member.get_full_name() or buddy_link.primary_member.username
            plan_name = f"{sub.plan.name} (Partner of {partner_primary_name})" if sub.plan else f"Partner of {partner_primary_name}"
            end_date_str = sub.end_date.strftime('%d %b %Y') if sub.end_date else ''
            if sub.status == 'active' and sub.end_date and sub.end_date >= today:
                sub_status = 'ACTIVE'
                days_left = max(0, (sub.end_date - today).days)
            else:
                sub_status = 'EXPIRED'
                days_left = 0

        linked_partners_names = []
        if sub and sub.plan and sub.plan.max_members > 1:
            for bl in sub.buddy_links.select_related('partner_member').all():
                linked_partners_names.append(bl.partner_member.get_full_name() or bl.partner_member.username)

        results.append({
            'id': u.id,
            'name': u.get_full_name() or u.username,
            'username': u.username,
            'phone': getattr(mem_prof, 'phone', '') or '',
            'pin': getattr(bio_prof, 'zk_pin', '') or str(u.id),
            'face_enrolled': getattr(bio_prof, 'face_enrolled', False) if bio_prof else False,
            'fingerprint_enrolled': getattr(bio_prof, 'fingerprint_enrolled', False) if bio_prof else False,
            'plan_name': plan_name,
            'sub_status': sub_status,
            'days_left': days_left,
            'end_date': end_date_str,
            'is_linked_partner': is_linked_partner,
            'partner_primary_name': partner_primary_name,
            'linked_partners_names': linked_partners_names,
            'on_floor': on_floor,
            'last_punch_time': latest_punch.punch_time.strftime('%H:%M:%S') if latest_punch else '',
            'last_receipt_id': last_receipt.id if last_receipt else None,
            'photo_url': photo_url,
            'yearly_fee_paid': yearly_fee_paid,
        })

    return JsonResponse({'results': results})


@login_required
@role_required('front_desk', 'admin', 'coach', 'super_admin')
def member_full_profile_api(request, member_id):
    """Returns complete 360-degree dossier for a gym member."""
    from django.contrib.auth import get_user_model
    from django.db.models import Q
    from wger.membership.models import MemberProfile, Subscription, MemberApplication
    from wger.zkbio_integration.models import BiometricProfile, DoorAccessLog
    from wger.gym_operations_payroll.models import PaymentReceipt
    User = get_user_model()

    member = User.objects.filter(id=member_id).first()
    if not member:
        return JsonResponse({'error': 'Member not found'}, status=404)

    is_super_admin = request.user.is_superuser or request.user.groups.filter(name='super_admin').exists()
    if (member.is_superuser or member.groups.filter(name='super_admin').exists()) and not is_super_admin:
        return JsonResponse({'error': 'Unauthorized: Super Admin profiles are restricted.'}, status=403)

    user_groups = set(request.user.groups.values_list('name', flat=True))
    if 'coach' in user_groups and not is_super_admin and not (user_groups.intersection({'admin', 'front_desk'})):
        if member.is_staff or member.is_superuser or not member.groups.filter(name='member').exists():
            return JsonResponse({'error': 'Unauthorized: Coaches can only view member profiles.'}, status=403)

    prof = getattr(member, 'member_profile', None)
    bio = getattr(member, 'biometric_profile', None)

    today = timezone.now().date()
    # Subscriptions
    active_sub = Subscription.objects.filter(member=member, status='active', end_date__gte=today).order_by('-end_date').first()
    latest_sub = active_sub or Subscription.objects.filter(member=member).order_by('-end_date').first()

    from wger.gym_operations_payroll.models import BuddyMembership
    buddy_link = BuddyMembership.objects.filter(
        partner_member=member
    ).select_related('subscription__plan', 'subscription__member', 'primary_member').order_by('-subscription__end_date').first()
    is_partner = False
    partner_primary_name = ''
    if buddy_link and (not active_sub or not active_sub.is_active):
        is_partner = True
        partner_primary_name = buddy_link.primary_member.get_full_name() or buddy_link.primary_member.username
        if buddy_link.subscription.status == 'active' and buddy_link.subscription.end_date >= today:
            active_sub = buddy_link.subscription
        latest_sub = latest_sub or buddy_link.subscription

    # Receipts
    receipts_qs = PaymentReceipt.objects.filter(member=member).order_by('-issued_at')[:6]
    receipts_list = [{
        'id': r.id,
        'number': r.receipt_number,
        'date': r.issued_at.strftime('%d %b %Y'),
        'plan_name': r.plan_name,
        'amount': float(r.amount_paid),
        'method': r.payment_method.upper(),
        'notes': r.notes or ''
    } for r in receipts_qs]

    # Door Access & Attendance
    latest_punch = DoorAccessLog.objects.filter(user=member).order_by('-punch_time').first()
    total_punches_month = DoorAccessLog.objects.filter(
        user=member, 
        event_type='ENTRY', 
        punch_time__year=today.year, 
        punch_time__month=today.month
    ).count()

    # Calculate Age
    age = None
    if prof and prof.date_of_birth:
        dob = prof.date_of_birth
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    else:
        app = MemberApplication.objects.filter(created_user=member).first()
        if app and app.age:
            age = app.age

    # Coach details
    coach_name = None
    if prof and prof.assigned_coach:
        coach_name = prof.assigned_coach.get_full_name() or prof.assigned_coach.username

    # Training Program
    program_title = None
    if prof and prof.assigned_program:
        program_title = prof.assigned_program.title

    # Photo URL
    photo_url = None
    if prof and prof.profile_photo:
        try:
            photo_url = prof.profile_photo.url
        except Exception:
            pass

    return JsonResponse({
        'success': True,
        'member': {
            'id': member.id,
            'name': member.get_full_name() or member.username,
            'username': member.username,
            'email': member.email,
            'phone': prof.phone if prof else '',
            'nic_passport': prof.nic_passport if prof else '',
            'gender': (prof.gender or 'N/A').capitalize() if prof else 'N/A',
            'dob': prof.date_of_birth.strftime('%d %b %Y') if (prof and prof.date_of_birth) else 'N/A',
            'age': age or 'N/A',
            'blood_group': prof.blood_group if prof else 'N/A',
            'address': prof.address if prof else '',
            'photo_url': photo_url,
            'date_joined': (prof.effective_join_date.strftime('%d %b %Y') if (prof and prof.effective_join_date) else member.date_joined.strftime('%d %b %Y')),
            'join_date': (prof.join_date.strftime('%d %b %Y') if (prof and prof.join_date) else None),

            # Emergency
            'emergency_name': prof.emergency_contact_name if prof else '',
            'emergency_relationship': prof.emergency_relationship if prof else '',
            'emergency_phone': prof.emergency_contact_phone if prof else '',
            # Medical
            'medical_conditions': prof.medical_conditions if prof else '',
            'under_medication': prof.under_medication if prof else '',
            'primary_goal': prof.get_primary_goal_display() if prof else 'General Fitness',
            # Coaching & Program
            'assigned_coach': coach_name,
            'personal_trainer_needed': prof.personal_trainer_needed if prof else False,
            'assigned_program': program_title,
            'notes': prof.notes if prof else '',
            # Subscription
            'plan_name': (f"{latest_sub.plan.name} (Partner of {partner_primary_name})" if is_partner else (latest_sub.plan.name if (latest_sub and latest_sub.plan) else 'No Active Plan')),
            'sub_status': 'ACTIVE' if (active_sub and active_sub.end_date >= today) else ('EXPIRED' if latest_sub else 'NONE'),
            'validity_start': latest_sub.start_date.strftime('%d %b %Y') if latest_sub else '',
            'validity_end': latest_sub.end_date.strftime('%d %b %Y') if latest_sub else '',
            'days_remaining': (latest_sub.end_date - today).days if (active_sub and latest_sub.end_date >= today) else 0,
            'amount_paid': float(latest_sub.amount_paid) if latest_sub else 0,
            'is_partner': is_partner,
            'partner_primary_name': partner_primary_name,
            'linked_partners': [
                {
                    'id': bl.id,
                    'name': bl.partner_member.get_full_name() or bl.partner_member.username,
                    'username': bl.partner_member.username,
                    'pin': getattr(getattr(bl.partner_member, 'biometric_profile', None), 'zk_pin', '')
                }
                for bl in (latest_sub.buddy_links.select_related('partner_member__biometric_profile').all() if latest_sub and latest_sub.plan and latest_sub.plan.max_members > 1 else [])
            ],
            # Hardware
            'pin': bio.zk_pin if bio else str(member.id),
            'face_enrolled': bio.face_enrolled if bio else False,
            'fingerprint_enrolled': bio.fingerprint_enrolled if bio else False,
            'gate_access_active': member.is_active and not (bio and bio.disabled),
            'last_punch_time': latest_punch.punch_time.strftime('%d %b %Y, %I:%M %p') if latest_punch else 'Never',
            'month_attendance_count': total_punches_month,
            # Receipts
            'receipts': receipts_list,
            'yearly_fee_paid': (
                PaymentReceipt.objects.filter(
                    member=member,
                    issued_at__year=today.year
                ).filter(
                    Q(notes__icontains='Annual') | 
                    Q(notes__icontains='Yearly') | 
                    Q(notes__icontains='Registration') |
                    Q(notes__icontains='Initial membership enrollment')
                ).exists() or bool(
                    prof and prof.notes and str(today.year) in prof.notes and (
                        'annual' in prof.notes.lower() or 'yearly' in prof.notes.lower() or 'registration' in prof.notes.lower()
                    )
                )
            ),
        }
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
    schedule_days = data.get('schedule_days', '')
    schedule_slot = data.get('schedule_slot', '')
    coach_notes = str(data.get('coach_notes', '')).strip()

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
    profile.assigned_program = program

    update_fields = ['assigned_program']
    if schedule_days or schedule_slot or coach_notes:
        schedule_summary = f"{schedule_days} [{schedule_slot}]"
        if coach_notes:
            schedule_summary += f" &bull; {coach_notes}"
        profile.notes = schedule_summary
        update_fields.append('notes')

    profile.save(update_fields=update_fields)

    return JsonResponse({
        'success': True,
        'message': f"Assigned '{program.title}' & schedule to {member.get_full_name() or member.username}!",
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

    water_ml = int(data.get('water_ml', 3000))

    target, _ = DailyFuelTarget.objects.get_or_create(
        member=member,
        defaults={
            'target_calories': calories,
            'target_protein_g': protein,
            'target_carbs_g': carbs,
            'target_fat_g': fat,
            'target_water_ml': water_ml,
        }
    )
    target.target_calories = calories
    target.target_protein_g = protein
    target.target_carbs_g = carbs
    target.target_fat_g = fat
    target.target_water_ml = water_ml
    target.save()

    return JsonResponse({
        'success': True,
        'message': f"Updated nutrition targets for {member.get_full_name() or member.username}: {calories} kcal, {protein}g protein, {water_ml}ml water!",
        'targets': {
            'calories': calories,
            'protein_g': protein,
            'carbs_g': carbs,
            'fat_g': fat,
            'water_ml': water_ml
        }
    })


@login_required
def log_water_api(request):
    """Member logs water consumption (+250ml, +500ml, etc.)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    import json
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST
    try:
        amount_ml = int(data.get('amount_ml', 250))
    except (ValueError, TypeError):
        amount_ml = 250

    from wger.nutrition_lk.models import WaterLog, DailyFuelTarget
    WaterLog.objects.create(member=request.user, amount_ml=amount_ml)

    today = timezone.now().date()
    water_logs = WaterLog.objects.filter(member=request.user, logged_at__date=today)
    today_water_ml = sum(w.amount_ml for w in water_logs)
    target_obj = DailyFuelTarget.objects.filter(member=request.user).first()
    target_water_ml = target_obj.target_water_ml if (target_obj and hasattr(target_obj, 'target_water_ml')) else 3000
    water_pct = min(100, int((today_water_ml / max(1, target_water_ml)) * 100))

    return JsonResponse({
        'success': True,
        'message': f"Logged +{amount_ml}ml water! Today's total: {round(today_water_ml / 1000, 1)}L",
        'water_consumed': round(today_water_ml / 1000, 1),
        'water_target': round(target_water_ml / 1000, 1),
        'water_pct': water_pct,
        'today_water_ml': today_water_ml
    })


@login_required
@role_required('super_admin', 'admin', 'front_desk')
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
def admin_edit_program_api(request, prog_id):
    """Super Admin edits an existing gym program."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    from wger.membership.models import GymProgram
    prog = GymProgram.objects.filter(id=prog_id).first()
    if not prog:
        return JsonResponse({'error': 'Program not found.'}, status=404)

    if 'title' in data and data['title'].strip():
        prog.title = data['title'].strip()
    if 'category' in data and data['category'].strip():
        prog.category = data['category'].strip()
    if 'difficulty' in data and data['difficulty'].strip():
        prog.difficulty = data['difficulty'].strip()
    if 'duration_weeks' in data and data['duration_weeks']:
        prog.duration_weeks = int(data['duration_weeks'])
    if 'sessions_per_week' in data and data['sessions_per_week']:
        prog.sessions_per_week = int(data['sessions_per_week'])
    if 'description' in data:
        prog.description = data['description'].strip()
    if 'key_features' in data:
        prog.key_features = data['key_features'].strip()
    if 'is_active' in data:
        prog.is_active = bool(data['is_active'])

    prog.save()
    return JsonResponse({
        'success': True,
        'message': f"Program '{prog.title}' updated successfully!",
        'program': {
            'id': prog.id,
            'title': prog.title,
            'category': prog.get_category_display(),
            'difficulty': prog.get_difficulty_display(),
            'duration_weeks': prog.duration_weeks,
            'sessions_per_week': prog.sessions_per_week,
            'is_active': prog.is_active
        }
    })


@login_required
@role_required('super_admin')
def admin_delete_program_api(request, prog_id):
    """Super Admin deletes a gym program."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    from wger.membership.models import GymProgram
    prog = GymProgram.objects.filter(id=prog_id).first()
    if not prog:
        return JsonResponse({'error': 'Program not found.'}, status=404)

    title = prog.title
    prog.delete()
    return JsonResponse({
        'success': True,
        'message': f"Program '{title}' deleted from catalog."
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


# ─────────────────────────────────────────────────────────────
# ── User & Staff Management APIs (Super Admin) ──────────────
# ─────────────────────────────────────────────────────────────

@login_required
@role_required('super_admin')
def admin_create_user_api(request):
    """
    Super Admin creates a new User & Staff member with assigned Role (Super Admin, Front Desk, Coach, Member),
    provisions credentials, profiles, and hardware biometric gate access.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    role = data.get('role', 'member').strip()
    phone = data.get('phone', '').strip()
    nic_passport = data.get('nic_passport', '').strip()
    enable_gate = bool(data.get('enable_gate_access', True))

    if not username:
        return JsonResponse({'error': 'Username is required.'}, status=400)
    if not email:
        return JsonResponse({'error': 'Email address is required.'}, status=400)
    if password and len(password) < 6:
        return JsonResponse({'error': 'Password must be at least 6 characters long if provided.'}, status=400)
    if role not in ['super_admin', 'admin', 'front_desk', 'coach', 'member']:
        return JsonResponse({'error': f'Invalid role: {role}'}, status=400)

    send_invite = data.get('send_invite', True)
    if isinstance(send_invite, str):
        send_invite = send_invite.lower() in ('true', '1', 'yes', 'on')

    is_super_admin = request.user.is_superuser or request.user.groups.filter(name='super_admin').exists()
    if role in ['super_admin', 'admin'] and not is_super_admin:
        return JsonResponse({'error': 'Unauthorized: Only Super Admin can provision Admin or Super Admin accounts.'}, status=403)

    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group
    from wger.core.models import UserProfile
    from wger.membership.models import MemberProfile, CoachProfile
    from wger.zkbio_integration.models import BiometricProfile

    User = get_user_model()
    if User.objects.filter(username=username).exists():
        return JsonResponse({'error': f"Username '{username}' is already taken."}, status=400)
    if User.objects.filter(email=email).exists():
        return JsonResponse({'error': f"A user with email '{email}' already exists."}, status=400)

    # Create the User
    is_staff = role in ['super_admin', 'admin', 'front_desk', 'coach']
    is_superuser = (role == 'super_admin')
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password if password else None,
        first_name=first_name,
        last_name=last_name,
        is_staff=is_staff,
        is_superuser=is_superuser,
        is_active=True,
    )
    if not password:
        user.set_unusable_password()
        user.save()

    # Assign Django Group
    group, _ = Group.objects.get_or_create(name=role)
    user.groups.add(group)

    # Required wger UserProfile
    UserProfile.objects.get_or_create(user=user)

    # Biometric PIN generation
    custom_pin = data.get('biometric_pin', '').strip()
    if custom_pin:
        pin = custom_pin
    else:
        pin = generate_unique_biometric_pin()

    # If Coach role, create CoachProfile
    if role == 'coach':
        coach_title = data.get('coach_title', 'Certified Strength & Conditioning Coach').strip()
        specialties = data.get('specialties', 'General Fitness, Biomechanics').strip()
        try:
            years_exp = int(data.get('years_experience', 3))
        except (ValueError, TypeError):
            years_exp = 3
        bio = data.get('bio', '').strip()

        CoachProfile.objects.create(
            user=user,
            title=coach_title,
            specialties=specialties,
            years_experience=years_exp,
            bio=bio,
            phone=phone
        )

    # Create MemberProfile
    starting_weight = None
    if data.get('starting_weight_kg'):
        try:
            from decimal import Decimal
            starting_weight = Decimal(data.get('starting_weight_kg'))
        except Exception:
            starting_weight = None

    # Create MemberProfile only if role is 'member'
    if role == 'member':
        MemberProfile.objects.create(
            user=user,
            phone=phone,
            nic_passport=nic_passport,
            biometric_pin=pin,
            primary_goal=data.get('primary_goal', 'general_fitness'),
            starting_weight_kg=starting_weight,
            emergency_contact_name=data.get('emergency_name', ''),
            emergency_contact_phone=data.get('emergency_phone', ''),
        )

    # BiometricProfile for turnstile hardware / LiveU Cloud
    bio = BiometricProfile.objects.create(
        user=user,
        zk_pin=pin,
        disabled=not enable_gate,
        sync_status='PENDING'
    )
    try:
        from wger.zkbio_integration.liveu_client import LiveUClient
        liveu = LiveUClient()
        if liveu.is_configured:
            cloud_res = liveu.create_member(
                member_id=pin,
                name=user.get_full_name() or user.username,
                uid=nic_passport or phone,
                status="Active" if enable_gate else "Inactive"
            )
            if cloud_res and cloud_res.get('_id'):
                bio.liveu_id = cloud_res['_id']
                bio.sync_status = 'SYNCED'
                bio.save(update_fields=['liveu_id', 'sync_status'])
    except Exception as ex:
        import logging
        logging.getLogger('wger').error(f"[LiveU Cloud] Error registering {user.username}: {ex}")

    email_sent = False
    if send_invite or not password:
        from wger.core.email_service import send_welcome_password_setup_email
        email_sent, _ = send_welcome_password_setup_email(user, request=request, is_async=True)

    role_labels = {
        'super_admin': 'Super Admin',
        'admin': 'Admin',
        'front_desk': 'Front Desk',
        'coach': 'Coach',
        'member': 'Member'
    }

    return JsonResponse({
        'success': True,
        'message': f"User '{username}' successfully created with role '{role_labels[role]}'." + (" Password setup email sent." if email_sent else ""),
        'email_sent': email_sent,
        'user': {
            'id': user.id,
            'username': user.username,
            'full_name': user.get_full_name() or user.username,
            'email': user.email,
            'role': role,
            'role_label': role_labels[role],
            'phone': phone,
            'nic_passport': nic_passport,
            'pin': pin,
            'is_active': user.is_active,
            'has_gate_access': enable_gate
        }
    })


@login_required
@role_required('front_desk', 'admin', 'super_admin')
def resend_member_invite_api(request, member_id):
    """
    Re-sends the branded welcome email and cryptographic password setup link to a member.
    Callable by Front Desk or Super Admin.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    from django.contrib.auth import get_user_model
    User = get_user_model()
    member = User.objects.filter(id=member_id).first()
    if not member:
        return JsonResponse({'error': 'Member not found.'}, status=404)
    if not member.email:
        return JsonResponse({'error': f"Member '{member.username}' has no email address configured."}, status=400)

    from wger.core.email_service import send_welcome_password_setup_email
    email_sent, msg = send_welcome_password_setup_email(member, request=request, is_async=True)

    return JsonResponse({
        'success': True,
        'email_sent': email_sent,
        'message': f"Welcome & password setup email sent to {member.email}!"
    })


@login_required
@role_required('super_admin')
def admin_update_user_role_api(request, user_id):
    """Change a user's role and permission group dynamically."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    is_super_admin = request.user.is_superuser or request.user.groups.filter(name='super_admin').exists()
    if not is_super_admin:
        return JsonResponse({'error': 'Unauthorized: Only Super Admin has permission to override user roles.'}, status=403)

    new_role = data.get('role', '').strip()
    if new_role not in ['super_admin', 'admin', 'front_desk', 'coach', 'member']:
        return JsonResponse({'error': f'Invalid role: {new_role}'}, status=400)

    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group
    from wger.membership.models import CoachProfile

    User = get_user_model()
    target_user = User.objects.filter(id=user_id).first()
    if not target_user:
        return JsonResponse({'error': 'User not found'}, status=404)

    # Prevent demoting the requesting user from super_admin accidentally
    if target_user == request.user and new_role != 'super_admin':
        return JsonResponse({'error': 'You cannot remove Super Admin role from your own current session.'}, status=400)

    # Clear previous role groups
    for r in ['super_admin', 'admin', 'front_desk', 'coach', 'member']:
        g = Group.objects.filter(name=r).first()
        if g:
            target_user.groups.remove(g)

    # Add new role group
    new_group, _ = Group.objects.get_or_create(name=new_role)
    target_user.groups.add(new_group)

    # Update Django staff and superuser flags
    target_user.is_staff = new_role in ['super_admin', 'admin', 'front_desk', 'coach']
    target_user.is_superuser = (new_role == 'super_admin')
    target_user.save(update_fields=['is_staff', 'is_superuser'])

    # Ensure coach profile if promoted to coach
    if new_role == 'coach' and not CoachProfile.objects.filter(user=target_user).exists():
        CoachProfile.objects.create(
            user=target_user,
            title='Certified Fitness Coach',
            specialties='Strength Training, Biomechanics',
            years_experience=3
        )

    role_labels = {
        'super_admin': 'Super Admin',
        'admin': 'Admin',
        'front_desk': 'Front Desk',
        'coach': 'Coach',
        'member': 'Member'
    }

    return JsonResponse({
        'success': True,
        'message': f"Role for {target_user.username} updated to {role_labels[new_role]}.",
        'role': new_role,
        'role_label': role_labels[new_role]
    })


@login_required
@role_required('super_admin')
def admin_toggle_user_active_api(request, user_id):
    """Toggle user active status (suspend/activate account) and turnstile gate."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    from django.contrib.auth import get_user_model
    from wger.zkbio_integration.models import BiometricProfile

    User = get_user_model()
    target_user = User.objects.filter(id=user_id).first()
    if not target_user:
        return JsonResponse({'error': 'User not found'}, status=404)

    if target_user == request.user:
        return JsonResponse({'error': 'You cannot disable your own active account.'}, status=400)

    target_user.is_active = not target_user.is_active
    target_user.save(update_fields=['is_active'])

    # Sync biometric gate access
    bio = BiometricProfile.objects.filter(user=target_user).first()
    if bio:
        bio.disabled = not target_user.is_active
        bio.sync_status = 'PENDING'
        bio.save(update_fields=['disabled', 'sync_status'])

    action_word = "activated" if target_user.is_active else "suspended / deactivated"
    return JsonResponse({
        'success': True,
        'is_active': target_user.is_active,
        'message': f"User account '{target_user.username}' has been {action_word}."
    })


@login_required
@role_required('super_admin')
def admin_reset_user_password_api(request, user_id):
    """Super Admin resets a user's password."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    new_password = data.get('new_password', '').strip()
    if not new_password or len(new_password) < 6:
        return JsonResponse({'error': 'New password must be at least 6 characters long.'}, status=400)

    from django.contrib.auth import get_user_model
    User = get_user_model()
    target_user = User.objects.filter(id=user_id).first()
    if not target_user:
        return JsonResponse({'error': 'User not found'}, status=404)

    target_user.set_password(new_password)
    target_user.save()

    return JsonResponse({
        'success': True,
        'message': f"Password for '{target_user.username}' was successfully reset."
    })


@login_required
@role_required('super_admin', 'admin')
def admin_audit_align_roles_api(request):
    """
    Audit & Auto-Align User Roles and Permission Groups.
    Ensures strict role integrity:
    - Super Admins only have 'super_admin' (never member)
    - Admins only have 'admin' (never member)
    - Coaches only have 'coach' (never member)
    - Front Desk only have 'front_desk' (never member)
    - Members only have 'member'
    - Assigns proper group to unassigned users based on staff flag.
    - Normal Admins cannot touch or modify Super Admins.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group
    User = get_user_model()

    is_super_admin = request.user.is_superuser or request.user.groups.filter(name='super_admin').exists()

    super_group, _ = Group.objects.get_or_create(name='super_admin')
    admin_group, _ = Group.objects.get_or_create(name='admin')
    front_desk_group, _ = Group.objects.get_or_create(name='front_desk')
    coach_group, _ = Group.objects.get_or_create(name='coach')
    member_group, _ = Group.objects.get_or_create(name='member')

    fixed_count = 0
    actions_taken = []

    users_qs = User.objects.exclude(userprofile__is_temporary=True).prefetch_related('groups').order_by('id')
    for u in users_qs:
        # If Admin, skip Super Admins completely
        if (u.is_superuser or u.groups.filter(name='super_admin').exists()) and not is_super_admin:
            continue

        groups = set(u.groups.values_list('name', flat=True))
        modified = False

        # 1. Super Admin cleanup
        if u.is_superuser or 'super_admin' in groups:
            if is_super_admin:
                if 'super_admin' not in groups:
                    u.groups.add(super_group)
                    modified = True
                # Super Admin shouldn't have member or conflicting groups
                for non_super in [member_group, admin_group, front_desk_group, coach_group]:
                    if non_super.name in groups:
                        u.groups.remove(non_super)
                        modified = True
                u.is_staff = True
                u.is_superuser = True
                u.save(update_fields=['is_staff', 'is_superuser'])
                if modified:
                    actions_taken.append(f"Aligned Super Admin permissions for @{u.username}")
                    fixed_count += 1
            continue

        # 2. Staff roles with conflicting member group
        if 'admin' in groups and 'member' in groups:
            u.groups.remove(member_group)
            u.is_staff = True
            u.is_superuser = False
            u.save(update_fields=['is_staff', 'is_superuser'])
            actions_taken.append(f"Removed conflicting member role from Admin @{u.username}")
            fixed_count += 1
            continue

        if 'coach' in groups and 'member' in groups:
            u.groups.remove(member_group)
            u.is_staff = True
            u.is_superuser = False
            u.save(update_fields=['is_staff', 'is_superuser'])
            actions_taken.append(f"Removed conflicting member role from Coach @{u.username}")
            fixed_count += 1
            continue

        if 'front_desk' in groups and 'member' in groups:
            u.groups.remove(member_group)
            u.is_staff = True
            u.is_superuser = False
            u.save(update_fields=['is_staff', 'is_superuser'])
            actions_taken.append(f"Removed conflicting member role from Front Desk @{u.username}")
            fixed_count += 1
            continue

        # 3. Users without groups
        if not groups:
            if u.is_staff:
                u.groups.add(front_desk_group)
                actions_taken.append(f"Assigned Front Desk group to staff account @{u.username}")
            else:
                u.groups.add(member_group)
                actions_taken.append(f"Assigned Member group to athlete account @{u.username}")
            fixed_count += 1
            continue

    return JsonResponse({
        'success': True,
        'fixed_count': fixed_count,
        'actions': actions_taken,
        'message': f"Role audit completed: {fixed_count} account(s) normalized and aligned." if fixed_count > 0 else "All user accounts and permission groups are already 100% compliant!"
    })


# ─────────────────────────────────────────────────────────────
# ── Super Admin Dedicated: Plan Builder & Data Overrides ────
# ─────────────────────────────────────────────────────────────

@login_required
@role_required('super_admin', 'admin')
def admin_create_plan_api(request):
    """Admin / Super Admin creates a new MembershipPlan (Make Plan feature)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    is_authorized = request.user.is_superuser or request.user.groups.filter(name__in=['super_admin', 'admin']).exists() or request.user.is_staff
    if not is_authorized:
        return JsonResponse({'error': 'Unauthorized: Only Admin or Super Admin has permission to make plans.'}, status=403)

    import json
    from decimal import Decimal
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    name = data.get('name', '').strip()
    plan_type = data.get('plan_type', '').strip().lower().replace(' ', '_')
    price_val = data.get('price_monthly')
    orig_val = data.get('original_price') or price_val
    disc_val = data.get('discount', 0)
    reg_val = data.get('registration_fee', 1000)
    duration_days = int(data.get('duration_days', 30))
    max_members = int(data.get('max_members', 1))
    description = data.get('description', '').strip()

    if not name or not plan_type or price_val is None:
        return JsonResponse({'error': 'Plan Name, Type Code, and Payable Price are required.'}, status=400)

    from wger.membership.models import MembershipPlan
    if MembershipPlan.objects.filter(plan_type=plan_type).exists():
        return JsonResponse({'error': f"Plan type code '{plan_type}' already exists. Please choose a unique code."}, status=400)

    try:
        price_monthly = Decimal(str(price_val))
        original_price = Decimal(str(orig_val)) if orig_val else price_monthly
        discount = Decimal(str(disc_val))
        registration_fee = Decimal(str(reg_val))
    except Exception as ex:
        return JsonResponse({'error': f"Invalid numeric value: {ex}"}, status=400)

    plan = MembershipPlan.objects.create(
        name=name,
        plan_type=plan_type,
        price_monthly=price_monthly,
        original_price=original_price,
        discount=discount,
        registration_fee=registration_fee,
        duration_days=duration_days,
        max_members=max_members,
        description=description,
        is_active=True
    )
    return JsonResponse({
        'success': True,
        'message': f"Plan '{name}' successfully created!",
        'plan': {
            'id': plan.id,
            'name': plan.name,
            'plan_type': plan.plan_type,
            'price_monthly': float(plan.price_monthly),
            'original_price': float(plan.original_price or plan.price_monthly),
            'discount': float(plan.discount),
            'registration_fee': float(plan.registration_fee),
            'duration_days': plan.duration_days,
            'max_members': plan.max_members,
        }
    })


@login_required
@role_required('super_admin', 'admin')
def admin_edit_plan_api(request, plan_id):
    """Admin / Super Admin edits plan and overrides pricing / discounts (Data Override)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    is_authorized = request.user.is_superuser or request.user.groups.filter(name__in=['super_admin', 'admin']).exists() or request.user.is_staff
    if not is_authorized:
        return JsonResponse({'error': 'Unauthorized: Only Admin or Super Admin can override plan data.'}, status=403)

    import json
    from decimal import Decimal
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    from wger.membership.models import MembershipPlan
    plan = MembershipPlan.objects.filter(id=plan_id).first()
    if not plan:
        return JsonResponse({'error': 'Plan not found.'}, status=404)

    if 'name' in data and data['name'].strip():
        plan.name = data['name'].strip()
    if 'price_monthly' in data and data['price_monthly'] is not None:
        plan.price_monthly = Decimal(str(data['price_monthly']))
    if 'original_price' in data and data['original_price'] is not None:
        plan.original_price = Decimal(str(data['original_price'])) if data['original_price'] != '' else None
    if 'discount' in data and data['discount'] is not None:
        plan.discount = Decimal(str(data['discount']))
    if 'registration_fee' in data and data['registration_fee'] is not None:
        plan.registration_fee = Decimal(str(data['registration_fee']))
    if 'duration_days' in data and data['duration_days']:
        plan.duration_days = int(data['duration_days'])
    if 'max_members' in data and data['max_members']:
        plan.max_members = int(data['max_members'])
    if 'description' in data:
        plan.description = str(data['description']).strip()
    if 'is_active' in data:
        plan.is_active = bool(data['is_active'])

    plan.save()
    return JsonResponse({
        'success': True,
        'message': f"Plan '{plan.name}' pricing and parameters updated!",
        'plan': {
            'id': plan.id,
            'name': plan.name,
            'price_monthly': float(plan.price_monthly),
            'original_price': float(plan.original_price or plan.price_monthly),
            'discount': float(plan.discount),
            'registration_fee': float(plan.registration_fee),
            'duration_days': plan.duration_days,
            'max_members': plan.max_members,
            'is_active': plan.is_active
        }
    })


@login_required
@role_required('super_admin', 'admin')
def admin_toggle_plan_api(request, plan_id):
    """Admin / Super Admin toggles plan active status."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    is_authorized = request.user.is_superuser or request.user.groups.filter(name__in=['super_admin', 'admin']).exists() or request.user.is_staff
    if not is_authorized:
        return JsonResponse({'error': 'Unauthorized: Only Admin or Super Admin can toggle plan status.'}, status=403)

    from wger.membership.models import MembershipPlan
    plan = MembershipPlan.objects.filter(id=plan_id).first()
    if not plan:
        return JsonResponse({'error': 'Plan not found.'}, status=404)

    plan.is_active = not plan.is_active
    plan.save(update_fields=['is_active'])
    status_str = "Active" if plan.is_active else "Inactive"
    return JsonResponse({
        'success': True,
        'is_active': plan.is_active,
        'message': f"Plan '{plan.name}' is now {status_str}."
    })


@login_required
@role_required('super_admin', 'admin')
def admin_delete_plan_api(request, plan_id):
    """
    Admin / Super Admin deletes or archives a MembershipPlan.
    If historical subscriptions exist, archives it (is_active=False) to protect financial records.
    If no subscriptions exist, permanently deletes the record.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    is_authorized = request.user.is_superuser or request.user.groups.filter(name__in=['super_admin', 'admin']).exists() or request.user.is_staff
    if not is_authorized:
        return JsonResponse({'error': 'Unauthorized: Only Admin or Super Admin can delete plans.'}, status=403)

    from wger.membership.models import MembershipPlan, Subscription
    plan = MembershipPlan.objects.filter(id=plan_id).first()
    if not plan:
        return JsonResponse({'error': 'Plan not found.'}, status=404)

    plan_name = plan.name
    subs_count = Subscription.objects.filter(plan=plan).count()

    if subs_count > 0:
        plan.is_active = False
        plan.save(update_fields=['is_active'])
        return JsonResponse({
            'success': True,
            'archived': True,
            'message': f"Plan '{plan_name}' has {subs_count} member subscription(s) attached. It has been deactivated & archived from public catalogs to protect historical invoices."
        })
    else:
        plan.delete()
        return JsonResponse({
            'success': True,
            'archived': False,
            'message': f"Plan '{plan_name}' permanently deleted."
        })


@login_required
@role_required('super_admin', 'admin')
def admin_override_subscription_api(request, sub_id):
    """
    Admin / Super Admin Master Data Override:
    Manually override subscription expiry date, amount paid, status, or plan parameters.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    is_authorized = request.user.is_superuser or request.user.groups.filter(name__in=['super_admin', 'admin']).exists() or request.user.is_staff
    if not is_authorized:
        return JsonResponse({'error': 'Unauthorized: Only Admin or Super Admin can perform subscription data overrides.'}, status=403)

    import json
    from decimal import Decimal
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    from wger.membership.models import Subscription, MembershipPlan
    sub = Subscription.objects.select_related('member', 'plan').filter(id=sub_id).first()
    if not sub:
        return JsonResponse({'error': 'Subscription not found.'}, status=404)

    # Master date overrides
    if 'end_date' in data and data['end_date']:
        try:
            sub.end_date = timezone.datetime.strptime(data['end_date'].strip(), '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Invalid end_date format (YYYY-MM-DD required).'}, status=400)

    if 'start_date' in data and data['start_date']:
        try:
            sub.start_date = timezone.datetime.strptime(data['start_date'].strip(), '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Invalid start_date format (YYYY-MM-DD required).'}, status=400)

    if 'amount_paid' in data and data['amount_paid'] is not None and str(data['amount_paid']).strip() != '':
        sub.amount_paid = Decimal(str(data['amount_paid']))

    if 'status' in data and data['status'] in ['active', 'expired', 'suspended', 'cancelled', 'pending_payment']:
        sub.status = data['status']

    if 'plan_id' in data and data['plan_id']:
        p = MembershipPlan.objects.filter(id=data['plan_id']).first()
        if p:
            if getattr(p, 'is_student_plan', False) or p.plan_type == 'student' or 'student' in (p.name or '').lower():
                from wger.membership.models import MemberProfile
                prof = MemberProfile.objects.filter(user=sub.member).first()
                if prof and prof.age is not None and prof.age >= 19 and not data.get('force'):
                    return JsonResponse({
                        'error': f'Cannot assign Student Package: Member is {prof.age} years old (Student Package is restricted to ages 18 and under).'
                    }, status=400)
            sub.plan = p


    # Concession & Discount Processing (Super Admin Exclusive)
    disc_type = data.get('discount_type', 'none')
    disc_value = Decimal(str(data.get('discount_value') or 0))
    disc_amount = Decimal(str(data.get('discount_amount') or 0))
    reason_cat = data.get('reason_category', 'management_comp')
    settlement_mode = data.get('settlement_mode', 'front_desk')  # 'front_desk' or 'collected_now'
    std_price = sub.plan.price_monthly if sub.plan else Decimal('0.00')
    net_payable = max(Decimal('0.00'), std_price - disc_amount) if disc_amount > Decimal('0.00') else std_price

    from wger.gym_operations_payroll.models import PaymentReceipt
    from wger.membership.models import MembershipDiscountAudit
    from wger.zkbio_integration.models import BiometricProfile

    receipt = None
    is_partial_concession = (disc_type in ['percentage', 'flat'] and disc_amount > Decimal('0.00'))

    if disc_type == 'full_waiver':
        # 100% Free pass — Zero payable, active immediately, gate unlocked, LKR 0 receipt
        sub.amount_paid = Decimal('0.00')
        sub.status = 'active'
        disc_amount = std_price

        # Arm gate turnstile
        bio, _ = BiometricProfile.objects.get_or_create(
            user=sub.member,
            defaults={'zk_pin': str(1000 + sub.member.id)}
        )
        bio.disabled = False
        bio.sync_status = 'PENDING'
        bio.save(update_fields=['disabled', 'sync_status'])

        receipt = PaymentReceipt.objects.filter(subscription=sub).first()
        if receipt:
            receipt.validity_start = sub.start_date
            receipt.validity_end = sub.end_date
            receipt.amount_paid = Decimal('0.00')
            receipt.discount_amount = disc_amount
            receipt.plan_name = sub.plan.name
            receipt.notes = '100% Complimentary VIP / Management Fee Waiver'
            receipt.save()
        else:
            receipt = PaymentReceipt.objects.create(
                receipt_number=PaymentReceipt.generate_next_receipt_number(),
                subscription=sub,
                member=sub.member,
                plan_name=sub.plan.name if sub.plan else 'Complimentary',
                duration_days=sub.plan.duration_days if sub.plan else 30,
                validity_start=sub.start_date,
                validity_end=sub.end_date,
                amount_paid=Decimal('0.00'),
                discount_amount=disc_amount,
                payment_method='cash',
                cashier=request.user,
                notes='100% Complimentary VIP / Management Fee Waiver'
            )

    elif is_partial_concession:
        if settlement_mode == 'front_desk':
            # Member has NOT paid yet! Pending payment at Front Desk counter.
            # Gate remains locked until front desk collects remaining amount.
            sub.status = 'pending_payment'
            sub.amount_paid = Decimal('0.00')
            receipt = None  # No receipt until front desk collects the money!

            bio = BiometricProfile.objects.filter(user=sub.member).first()
            if bio:
                bio.disabled = True
                bio.sync_status = 'PENDING'
                bio.save(update_fields=['disabled', 'sync_status'])
        else:
            # Super Admin physically received the cash right now
            sub.status = 'active'
            sub.amount_paid = net_payable

            bio, _ = BiometricProfile.objects.get_or_create(
                user=sub.member,
                defaults={'zk_pin': str(1000 + sub.member.id)}
            )
            bio.disabled = False
            bio.sync_status = 'PENDING'
            bio.save(update_fields=['disabled', 'sync_status'])

            receipt = PaymentReceipt.objects.create(
                receipt_number=PaymentReceipt.generate_next_receipt_number(),
                subscription=sub,
                member=sub.member,
                plan_name=sub.plan.name if sub.plan else 'Custom',
                duration_days=sub.plan.duration_days if sub.plan else 30,
                validity_start=sub.start_date,
                validity_end=sub.end_date,
                amount_paid=net_payable,
                discount_amount=disc_amount,
                payment_method='cash',
                cashier=request.user,
                notes=f'Admin collected LKR {net_payable} (-LKR {disc_amount} concession)'
            )
    else:
        # Standard override without concession
        if sub.status == 'active':
            bio, _ = BiometricProfile.objects.get_or_create(
                user=sub.member,
                defaults={'zk_pin': str(1000 + sub.member.id)}
            )
            bio.disabled = False
            bio.sync_status = 'PENDING'
            bio.save(update_fields=['disabled', 'sync_status'])

    notes = data.get('notes', '').strip()
    timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')
    concession_str = f" [Concession: {disc_type.upper()} -LKR {disc_amount} | {reason_cat} | Mode: {settlement_mode}]" if disc_amount > Decimal('0.00') or disc_type == 'full_waiver' else ""
    override_note = f"\n[Admin Data Override by {request.user.username} at {timestamp}{concession_str}]: {notes}" if notes else f"\n[Admin Data Override by {request.user.username} at {timestamp}{concession_str}]"
    sub.notes = (sub.notes or '') + override_note
    sub.save()

    # Formal Concession Audit Logging
    if is_partial_concession or disc_type == 'full_waiver':
        justification_text = notes or f"Admin {disc_type} override concession"
        if is_partial_concession and settlement_mode == 'front_desk':
            justification_text += f" | Pending Front Desk collection of LKR {net_payable:,.2f}"

        # Clean up any previous un-settled audit record for this subscription to avoid duplicates
        MembershipDiscountAudit.objects.filter(subscription=sub, receipt__isnull=True).delete()

        MembershipDiscountAudit.objects.create(
            member=sub.member,
            authorized_by=request.user,
            subscription=sub,
            plan=sub.plan,
            discount_type=disc_type,
            original_price=std_price,
            discount_value=disc_value,
            discount_amount=disc_amount,
            annual_fee_waived=True,
            final_amount_paid=Decimal('0.00') if (is_partial_concession and settlement_mode == 'front_desk') else (sub.amount_paid or Decimal('0.00')),
            reason_category=reason_cat,
            justification=justification_text,
            receipt=receipt
        )

    msg = f"Subscription #{sub.id} for {sub.member.username} updated."
    if is_partial_concession and settlement_mode == 'front_desk':
        msg = f"Concession of LKR {disc_amount:,.0f} approved for {sub.member.username}. Subscription set to Pending Payment (Due: LKR {net_payable:,.0f}). Member must pay at Front Desk."
    elif disc_type == 'full_waiver':
        msg = f"100% Complimentary Free Pass activated for {sub.member.username}. Turnstile gate unlocked immediately."

    return JsonResponse({
        'success': True,
        'message': f"Subscription #{sub.id} for {sub.member.username} was successfully overridden by Admin.",
        'subscription': {
            'id': sub.id,
            'status': sub.status,
            'end_date': str(sub.end_date),
            'amount_paid': float(sub.amount_paid),
            'plan_name': sub.plan.name
        }
    })


@login_required
@role_required('super_admin', 'admin')
def admin_export_financial_csv(request):
    """Export unified financial & sales ledger to CSV for bookkeeping / Excel."""
    import csv
    from django.http import HttpResponse
    from wger.gym_operations_payroll.models import PaymentReceipt
    from wger.pos.models import POSSale

    response = HttpResponse(content_type='text/csv')
    today_str = timezone.now().strftime('%Y%m%d_%H%M')
    response['Content-Disposition'] = f'attachment; filename="fitme_ledger_{today_str}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Timestamp', 'Receipt #', 'Category', 'Customer', 'Cashier', 'Payment Method', 'Amount (LKR)'])

    rows = []
    for pr in PaymentReceipt.objects.select_related('member', 'cashier').all():
        rows.append((
            pr.issued_at,
            pr.receipt_number,
            'Membership Fee',
            pr.member.get_full_name() or pr.member.username,
            pr.cashier.username if pr.cashier else 'System',
            pr.payment_method.upper(),
            float(pr.amount_paid)
        ))

    for ps in POSSale.objects.filter(status='COMPLETED').select_related('cashier').all():
        rows.append((
            ps.created_at,
            ps.receipt_number,
            'POS Bar & Supplements',
            ps.customer_name,
            ps.cashier.username if ps.cashier else 'Staff',
            ps.payment_method,
            float(ps.total_amount)
        ))

    rows.sort(key=lambda r: r[0], reverse=True)
    for r in rows:
        writer.writerow([r[0].strftime('%Y-%m-%d %H:%M:%S'), r[1], r[2], r[3], r[4], r[5], f"{r[6]:.2f}"])

    return response


@login_required
@role_required('super_admin', 'admin')
def admin_export_members_csv(request):
    """Export full members roster with subscription status & biometric PINs to CSV."""
    import csv
    from django.http import HttpResponse
    from django.contrib.auth import get_user_model
    from wger.membership.services import get_member_access_summary
    User = get_user_model()

    response = HttpResponse(content_type='text/csv')
    today_str = timezone.now().strftime('%Y%m%d_%H%M')
    response['Content-Disposition'] = f'attachment; filename="fitme_members_roster_{today_str}.csv"'

    writer = csv.writer(response)
    writer.writerow(['User ID', 'Full Name', 'Username', 'Email', 'Phone', 'Hardware PIN', 'Active Plan', 'Days Left', 'Turnstile Gate Status', 'Face ID Enrolled'])

    members = User.objects.filter(
        groups__name='member',
        is_staff=False,
        is_superuser=False
    ).exclude(
        groups__name__in=['super_admin', 'admin', 'front_desk', 'coach']
    ).exclude(
        userprofile__is_temporary=True
    ).select_related('member_profile', 'biometric_profile').order_by('id')

    for m in members:
        prof = getattr(m, 'member_profile', None)
        bio = getattr(m, 'biometric_profile', None)
        summary = get_member_access_summary(m)
        sub = summary.get('active_subscription')

        writer.writerow([
            m.id,
            m.get_full_name() or m.username,
            m.username,
            m.email or 'N/A',
            prof.phone if prof and prof.phone else 'N/A',
            bio.zk_pin if bio else (prof.biometric_pin if prof else 'N/A'),
            sub.plan.name if sub and sub.plan else 'No Active Plan',
            sub.days_remaining if sub else 0,
            'ACTIVE' if summary.get('door_access_active') else 'LOCKED',
            'YES' if bio and bio.face_enrolled else 'NO'
        ])

    return response


@login_required
@role_required('super_admin', 'admin')
def admin_create_expense_api(request):
    """Record an operational expense for the club facility with optional bill/receipt attachment."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    from decimal import Decimal
    if request.content_type and 'application/json' in request.content_type:
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            data = {}
    else:
        data = request.POST

    title = data.get('title', '').strip()
    category = data.get('category', 'other')
    amount_val = data.get('amount')
    expense_date_str = data.get('expense_date')
    payment_method = data.get('payment_method', 'cash')
    receipt_ref = data.get('receipt_ref', '').strip()
    notes = data.get('notes', '').strip()

    if not title or amount_val is None:
        return JsonResponse({'error': 'Title and Amount are required.'}, status=400)

    try:
        amount = Decimal(str(amount_val))
    except Exception:
        return JsonResponse({'error': 'Invalid amount value.'}, status=400)

    expense_date = timezone.now().date()
    if expense_date_str:
        try:
            expense_date = timezone.datetime.strptime(expense_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    receipt_file = request.FILES.get('receipt_image') or request.FILES.get('receipt_file')

    from wger.gym_operations_payroll.models import ClubExpense
    exp = ClubExpense.objects.create(
        title=title,
        category=category,
        amount=amount,
        expense_date=expense_date,
        payment_method=payment_method,
        recorded_by=request.user,
        receipt_ref=receipt_ref,
        notes=notes,
        receipt_image=receipt_file
    )

    return JsonResponse({
        'success': True,
        'message': f"Expense '{title}' (LKR {amount}) recorded successfully.",
        'expense': {
            'id': exp.id,
            'title': exp.title,
            'category': exp.get_category_display(),
            'amount': float(exp.amount),
            'expense_date': str(exp.expense_date),
            'payment_method': exp.get_payment_method_display(),
            'receipt_ref': exp.receipt_ref,
            'receipt_image_url': exp.receipt_image.url if exp.receipt_image else None
        }
    })


@login_required
@role_required('super_admin')
def admin_delete_expense_api(request, expense_id):
    """Super Admin deletes an expense."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    from wger.gym_operations_payroll.models import ClubExpense
    exp = ClubExpense.objects.filter(id=expense_id).first()
    if not exp:
        return JsonResponse({'error': 'Expense not found.'}, status=404)

    title = exp.title
    exp.delete()
    return JsonResponse({
        'success': True,
        'message': f"Expense '{title}' deleted."
    })


@login_required
@role_required('super_admin', 'admin')
def admin_upload_expense_receipt_api(request, expense_id):
    """Super Admin & Admin attaches receipt/bill proof image to an existing expense."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    from wger.gym_operations_payroll.models import ClubExpense
    exp = ClubExpense.objects.filter(id=expense_id).first()
    if not exp:
        return JsonResponse({'error': 'Expense record not found.'}, status=404)

    receipt_file = request.FILES.get('receipt_image') or request.FILES.get('receipt_file')
    if not receipt_file:
        return JsonResponse({'error': 'Please select a bill image or PDF to upload.'}, status=400)

    exp.receipt_image = receipt_file
    exp.save(update_fields=['receipt_image'])

    return JsonResponse({
        'success': True,
        'message': f"Receipt proof attached to expense '{exp.title}' successfully.",
        'receipt_image_url': exp.receipt_image.url if exp.receipt_image else None
    })


@login_required
@role_required('super_admin', 'admin')
def admin_export_expenses_csv(request):
    """Export operating expenses log to CSV."""
    import csv
    from django.http import HttpResponse
    from wger.gym_operations_payroll.models import ClubExpense

    response = HttpResponse(content_type='text/csv')
    today_str = timezone.now().strftime('%Y%m%d_%H%M')
    response['Content-Disposition'] = f'attachment; filename="fitme_expenses_{today_str}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Title', 'Category', 'Amount (LKR)', 'Payment Method', 'Recorded By', 'Receipt Ref', 'Notes'])

    for e in ClubExpense.objects.select_related('recorded_by').all():
        writer.writerow([
            e.expense_date,
            e.title,
            e.get_category_display(),
            f"{e.amount:.2f}",
            e.get_payment_method_display(),
            e.recorded_by.username if e.recorded_by else 'System',
            e.receipt_ref,
            e.notes
        ])

    return response


@login_required
@role_required('super_admin', 'admin', 'front_desk')
def admin_daily_eod_report(request):
    """
    Renders printable Daily End of Day (EOD) Cash Drawer Reconciliation & Sales Report.
    """
    from decimal import Decimal
    from django.db.models import Sum
    from wger.gym_operations_payroll.models import PaymentReceipt
    from wger.pos.models import POSSale, POSSaleItem

    date_str = request.GET.get('date')
    if date_str:
        try:
            report_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            report_date = timezone.now().date()
    else:
        report_date = timezone.now().date()

    # Receipts for date
    membership_receipts = PaymentReceipt.objects.filter(issued_at__date=report_date).select_related('member', 'cashier')
    pos_sales = POSSale.objects.filter(created_at__date=report_date, status='COMPLETED').select_related('cashier')

    mem_total = membership_receipts.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
    pos_total = pos_sales.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    gross_total = mem_total + pos_total

    # Cash drawer totals
    cash_mem = membership_receipts.filter(payment_method__iexact='cash').aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
    cash_pos = pos_sales.filter(payment_method='CASH').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    cash_total = cash_mem + cash_pos

    # Card & digital
    card_mem = membership_receipts.filter(payment_method__iexact='card').aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
    card_pos = pos_sales.filter(payment_method='CARD').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    card_total = card_mem + card_pos

    koko_pos = pos_sales.filter(payment_method='KOKO').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    bank_mem = membership_receipts.filter(payment_method__icontains='bank').aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
    bank_pos = pos_sales.filter(payment_method='BANK_TRANSFER').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    bank_total = bank_mem + bank_pos

    # POS Items sold on that day
    pos_items_summary = list(
        POSSaleItem.objects.filter(sale__created_at__date=report_date, sale__status='COMPLETED')
        .values('product_name')
        .annotate(qty=Sum('quantity'), revenue=Sum('total_price'))
        .order_by('-revenue')
    )

    context = {
        'report_date': report_date,
        'gross_total': gross_total,
        'mem_total': mem_total,
        'pos_total': pos_total,
        'cash_total': cash_total,
        'card_total': card_total,
        'koko_pos': koko_pos,
        'bank_total': bank_total,
        'opening_float': Decimal('10000.00'),
        'expected_drawer_cash': Decimal('10000.00') + cash_total,
        'membership_receipts': membership_receipts,
        'pos_sales': pos_sales,
        'pos_items_summary': pos_items_summary,
        'club_info': {
            'name': 'Fit Me Fitness Club',
            'tagline': 'Train with Purpose & Move with Confidence',
            'address': 'New Town, Elpitiya Road, Pitigala, 80420',
            'phone': '070 762 7878',
        }
    }
    return render(request, 'dashboards/reports/daily_eod.html', context)


@login_required
def member_self_renew_api(request):
    """
    Endpoint: /api/member/self-renew/
    Allows member to self-renew subscription, automatically unlocking the turnstile
    and generating an official payment receipt.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    from datetime import timedelta
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    plan_id = data.get('plan_id')
    payment_method = data.get('payment_method', 'online_card')
    from wger.membership.models import MembershipPlan, Subscription
    from wger.zkbio_integration.models import BiometricProfile
    from wger.gym_operations_payroll.models import PaymentReceipt
    from wger.membership.services import check_and_expire_subscriptions

    plan = MembershipPlan.objects.filter(id=plan_id, is_active=True).first()
    if not plan:
        return JsonResponse({'error': 'Please select an active membership package.'}, status=400)

    # Strict Age Validation for Student Package: only under 19 (age <= 18) allowed. At 19+, general package is mandatory.
    if getattr(plan, 'is_student_plan', False) or plan.plan_type == 'student' or 'student' in (plan.name or '').lower():
        from wger.membership.models import MemberProfile
        mem_profile = MemberProfile.objects.filter(user=request.user).first()
        user_age = getattr(mem_profile, 'age', None)
        if user_age is not None and user_age >= 19:
            return JsonResponse({
                'error': f'You are currently {user_age} years old. The Student Package is strictly available for members aged 18 and under. When turning 19, a general membership package is required.'
            }, status=400)


    today = timezone.now().date()
    current_sub = Subscription.objects.filter(
        member=request.user,
        status='active',
        end_date__gte=today
    ).order_by('-end_date').first()

    if current_sub:
        start_date = current_sub.end_date + timedelta(days=1)
    else:
        start_date = today

    end_date = start_date + timedelta(days=plan.duration_days)

    # Create new active subscription
    new_sub = Subscription.objects.create(
        member=request.user,
        plan=plan,
        start_date=start_date,
        end_date=end_date,
        status='active',
        amount_paid=plan.price_monthly,
        notes=f"Self-Service Renewal via Member Portal ({payment_method})"
    )

    # Immediate biometric restoration
    bio, _ = BiometricProfile.objects.get_or_create(
        user=request.user,
        defaults={'zk_pin': str(1000 + request.user.id)}
    )
    bio.disabled = False
    bio.sync_status = 'PENDING'
    bio.save(update_fields=['disabled', 'sync_status'])

    # Generate official receipt
    receipt_num = PaymentReceipt.generate_next_receipt_number()
    receipt = PaymentReceipt.objects.create(
        receipt_number=receipt_num,
        member=request.user,
        subscription=new_sub,
        plan_name=plan.name,
        duration_days=plan.duration_days,
        validity_start=new_sub.start_date,
        validity_end=new_sub.end_date,
        amount_paid=new_sub.amount_paid,
        payment_method=payment_method,
        member_pin=bio.zk_pin,
        notes="Self-Service Member Portal Instant Renewal"
    )

    check_and_expire_subscriptions(force=True)

    return JsonResponse({
        'success': True,
        'message': f"Plan successfully renewed! Turnstile Face ID and PIN access unlocked until {new_sub.end_date.strftime('%d %b %Y')}.",
        'receipt_id': receipt.id,
        'receipt_number': receipt.receipt_number,
        'end_date': str(new_sub.end_date),
        'plan_name': plan.name
    })


@login_required
@role_required('super_admin', 'admin', 'front_desk')
def admin_link_partner_api(request, subscription_id):
    """
    Links a secondary / partner member account to a multi-user subscription (Couples 2-User or Family 3-User).
    Supports either linking an existing member account OR quick-registering a new member account with credentials & biometric profile.
    Automatically provisions their independent ZKBio Face ID/PIN biometric turnstile profile.
    Accessible to Super Admin, Club Admin, and Front Desk staff.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    import re
    import logging
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group
    from wger.membership.models import Subscription, MemberProfile
    from wger.gym_operations_payroll.models import BuddyMembership
    from wger.zkbio_integration.models import BiometricProfile
    from wger.membership.services import check_and_expire_subscriptions

    logger = logging.getLogger(__name__)
    User = get_user_model()
    sub = Subscription.objects.filter(id=subscription_id).select_related('plan', 'member').first()
    if not sub:
        return JsonResponse({'error': 'Subscription not found.'}, status=404)

    if sub.plan.max_members <= 1:
        return JsonResponse({'error': f"Plan '{sub.plan.name}' is an individual package (1 User only). Cannot link additional members."}, status=400)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    action = data.get('action', '').strip()
    partner_id = data.get('partner_id')
    partner_user = None
    is_new_account = False

    # Mode 1: Quick Register & Link New Member
    if action == 'register_and_link' or data.get('full_name'):
        full_name = data.get('full_name', '').strip()
        phone = data.get('phone', '').strip()
        email = data.get('email', '').strip()
        gender = data.get('gender', 'male').strip().lower()
        nic_passport = data.get('nic_passport', '').strip()
        password = data.get('password', '').strip()
        primary_goal = data.get('primary_goal', 'general_fitness').strip()

        if not full_name:
            return JsonResponse({'error': 'Please provide the partner full name to register them.'}, status=400)

        # Smart duplicate check: check if phone or email is already registered
        if phone:
            existing_prof = MemberProfile.objects.filter(phone=phone).select_related('user').first()
            if existing_prof and existing_prof.user:
                partner_user = existing_prof.user
        if not partner_user and email:
            partner_user = User.objects.filter(email__iexact=email).first()

        if not partner_user:
            # Generate clean, unique username
            base_name = re.sub(r'[^a-zA-Z0-9]', '_', full_name.lower().strip())
            base_name = re.sub(r'_+', '_', base_name).strip('_') or 'member'
            username = base_name
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_name}_{counter}"
                counter += 1

            if not email:
                email = f"{username}@fitmefitness.lk"

            name_parts = full_name.split()
            first_name = name_parts[0]
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

            partner_user = User.objects.create(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_active=True
            )
            # Assign login password
            initial_password = password if password else 'Fitme@123'
            partner_user.set_password(initial_password)
            partner_user.save()

            # Assign to Member group
            member_group, _ = Group.objects.get_or_create(name='member')
            partner_user.groups.add(member_group)

            # Generate unique Biometric PIN
            new_pin = generate_unique_biometric_pin()
            profile = MemberProfile.objects.create(
                user=partner_user,
                phone=phone,
                nic_passport=nic_passport,
                gender=gender if gender in ['male', 'female', 'other'] else 'male',
                primary_goal=primary_goal or 'general_fitness',
                biometric_pin=new_pin,
                notes=f"Auto-registered & linked as partner under {sub.member.get_full_name() or sub.member.username}'s {sub.plan.name}"
            )
            is_new_account = True
        else:
            profile = getattr(partner_user, 'member_profile', None)
            if not profile:
                new_pin = generate_unique_biometric_pin()
                profile = MemberProfile.objects.create(
                    user=partner_user,
                    phone=phone,
                    nic_passport=nic_passport,
                    gender=gender if gender in ['male', 'female', 'other'] else 'male',
                    biometric_pin=new_pin,
                    notes=f"Linked as partner under {sub.member.get_full_name() or sub.member.username}'s {sub.plan.name}"
                )

    # Mode 2: Link Existing Member
    elif partner_id:
        partner_user = User.objects.filter(id=partner_id).first()
    else:
        partner_query = data.get('partner_username', '').strip()
        if partner_query:
            partner_user = User.objects.filter(username__iexact=partner_query).first() or User.objects.filter(email__iexact=partner_query).first()

    if not partner_user:
        return JsonResponse({'error': 'Please select or provide a valid member to link.'}, status=400)

    if partner_user.id == sub.member_id:
        return JsonResponse({'error': 'Cannot link the primary subscription holder to themselves.'}, status=400)

    if BuddyMembership.objects.filter(subscription=sub, partner_member=partner_user).exists():
        return JsonResponse({'error': f"{partner_user.get_full_name() or partner_user.username} is already linked to this package."}, status=400)

    current_partners_count = BuddyMembership.objects.filter(subscription=sub).count()
    max_additional_members = sub.plan.max_members - 1
    if current_partners_count >= max_additional_members:
        return JsonResponse({'error': f"This {sub.plan.name} has reached its limit of {sub.plan.max_members} users ({max_additional_members} additional partner slots filled)."}, status=400)

    # Create link
    buddy_link = BuddyMembership.objects.create(
        primary_member=sub.member,
        partner_member=partner_user,
        subscription=sub
    )

    # Ensure partner has BiometricProfile and PIN
    target_pin = getattr(getattr(partner_user, 'member_profile', None), 'biometric_pin', None) or str(1000 + partner_user.id)
    bio, _ = BiometricProfile.objects.get_or_create(
        user=partner_user,
        defaults={'zk_pin': target_pin}
    )
    if not bio.zk_pin:
        bio.zk_pin = target_pin

    if sub.is_active:
        bio.disabled = False
        bio.sync_status = 'PENDING'
        bio.save(update_fields=['zk_pin', 'disabled', 'sync_status'])

    # Auto-provision to LiveU Cloud hardware if configured
    try:
        from wger.zkbio_integration.liveu_client import LiveUClient
        liveu = LiveUClient()
        if liveu.is_configured:
            liveu.create_member(
                member_id=bio.zk_pin,
                name=partner_user.get_full_name() or partner_user.username,
                phone=getattr(getattr(partner_user, 'member_profile', None), 'phone', ''),
                pin=bio.zk_pin
            )
    except Exception as err:
        logger.warning(f"LiveU sync during partner link: {err}")

    check_and_expire_subscriptions(force=True)

    partner_name = partner_user.get_full_name() or partner_user.username
    account_note = " New member account created with login access!" if is_new_account else ""
    return JsonResponse({
        'success': True,
        'message': f"Linked {partner_name} to {sub.member.username}'s {sub.plan.name}!{account_note} Turnstile PIN: #FM{bio.zk_pin}",
        'link_id': buddy_link.id,
        'partner': {
            'id': partner_user.id,
            'username': partner_user.username,
            'name': partner_name,
            'pin': bio.zk_pin,
            'is_new': is_new_account
        }
    })


@login_required
@role_required('super_admin', 'admin', 'front_desk')
def admin_unlink_partner_api(request, link_id):
    """
    Unlinks a secondary / partner member from a subscription and immediately revokes their turnstile access.
    Accessible to Super Admin, Club Admin, and Front Desk staff.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    from wger.gym_operations_payroll.models import BuddyMembership
    from wger.membership.services import check_and_expire_subscriptions

    link = BuddyMembership.objects.filter(id=link_id).select_related('partner_member', 'subscription__plan').first()
    if not link:
        return JsonResponse({'error': 'Buddy link not found.'}, status=404)

    partner_name = link.partner_member.get_full_name() or link.partner_member.username
    plan_name = link.subscription.plan.name
    link.delete()

    check_and_expire_subscriptions(force=True)

    return JsonResponse({
        'success': True,
        'message': f"Unlinked {partner_name} from {plan_name}. Hardware turnstile access has been revoked."
    })


# ═════════════════════════════════════════════════════════════════════
# PAYROLL, SHIFT ROSTER & ADVANCE OPERATIONS (MODULARIZED)
# ═════════════════════════════════════════════════════════════════════
from .fitme_payroll_views import (
    admin_recalculate_payroll_api,
    admin_adjust_payroll_ledger_api,
    admin_delete_payroll_ledger_api,
    admin_finalize_payroll_ledger_api,
    admin_export_payroll_csv,
    admin_payroll_thermal_slip_view,
    admin_clock_staff_attendance_api,
    admin_create_staff_shift_api,
    admin_toggle_shift_leave_api,
    admin_enroll_staff_payroll_api,
    admin_get_pt_breakdown_api,
    admin_get_staff_work_schedule_api,
    admin_save_staff_work_schedule_api,
    admin_generate_bulk_roster_api,
    admin_issue_salary_advance_api,
    admin_advance_thermal_voucher_view,
)


@login_required
@role_required('super_admin')
def admin_audit_align_roles_api(request):
    """
    Comprehensive Audit API:
    1. Audits and aligns user roles and group assignments across the Fit Me system.
    2. Audits the Monthly Staff Payroll Register to detect non-staff users (superadmins, pure admins).
    3. If action='clean_payroll_admins', purges non-staff administrators from the payroll ledger.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group
    from wger.gym_operations_payroll.models import PayrollLedger
    from django.db.models import Q

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    action = data.get('action', 'audit')
    User = get_user_model()

    # 1. Audit non-staff in payroll
    admin_payroll_qs = PayrollLedger.objects.filter(
        Q(staff_user__is_superuser=True) |
        (Q(staff_user__groups__name__in=['super_admin', 'admin']) & ~Q(staff_user__groups__name__in=['coach', 'front_desk']))
    ).select_related('staff_user')

    admin_payroll_count = admin_payroll_qs.count()
    cleaned_count = 0

    if action == 'clean_payroll_admins':
        cleaned_count = admin_payroll_qs.delete()[0]

    # 2. Check role groupings
    super_admin_group, _ = Group.objects.get_or_create(name='super_admin')
    admin_group, _ = Group.objects.get_or_create(name='admin')
    coach_group, _ = Group.objects.get_or_create(name='coach')
    front_desk_group, _ = Group.objects.get_or_create(name='front_desk')
    member_group, _ = Group.objects.get_or_create(name='member')

    super_admins_count = User.objects.filter(Q(is_superuser=True) | Q(groups__name='super_admin')).distinct().count()
    admins_count = User.objects.filter(groups__name='admin').exclude(is_superuser=True).distinct().count()
    coaches_count = User.objects.filter(groups__name='coach').distinct().count()
    front_desk_count = User.objects.filter(groups__name='front_desk').distinct().count()

    message = "Audit completed successfully."
    if action == 'clean_payroll_admins':
        message = f"Cleaned {cleaned_count} administrator entries from the Staff Payroll Register."

    return JsonResponse({
        'success': True,
        'message': message,
        'audit': {
            'super_admins': super_admins_count,
            'admins': admins_count,
            'coaches': coaches_count,
            'front_desk': front_desk_count,
            'admin_payroll_records_detected': admin_payroll_count,
            'admin_payroll_records_cleaned': cleaned_count
        }
    })



