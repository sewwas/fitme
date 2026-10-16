"""
Fit Me — Staff Payroll, Attendance & Roster Operations
Extracted from fitme_dashboards.py for modular maintainability.
"""
import json
import csv
import calendar
import logging
from decimal import Decimal
from datetime import timedelta

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.utils import timezone
from django.contrib.auth import get_user_model

from wger.core.views.fitme_dashboards import role_required

logger = logging.getLogger(__name__)

# ═════════════════════════════════════════════════════════════════════
# SUPER ADMIN: PAYROLL & COMMISSION MANAGEMENT APIS
# ═════════════════════════════════════════════════════════════════════

@login_required
@role_required('super_admin', 'admin')
def admin_recalculate_payroll_api(request):
    """Triggers monthly payroll consolidation task for all staff users."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    year = data.get('year')
    month = data.get('month')
    try:
        year = int(year) if year else None
        month = int(month) if month else None
    except (ValueError, TypeError):
        year, month = None, None

    from wger.gym_operations_payroll.tasks import calculate_monthly_payroll
    result_msg = calculate_monthly_payroll(year=year, month=month)
    return JsonResponse({
        'success': True,
        'message': result_msg or 'Monthly payroll recalculated and consolidated successfully.'
    })


@login_required
@role_required('super_admin', 'admin')
def admin_adjust_payroll_ledger_api(request, ledger_id):
    """Allows Super Admin to adjust ledger fields (base salary, commissions, overtime, penalties, notes)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    from decimal import Decimal
    from wger.gym_operations_payroll.models import PayrollLedger
    ledger = PayrollLedger.objects.filter(id=ledger_id).first()
    if not ledger:
        return JsonResponse({'error': 'Payroll ledger not found'}, status=404)

    def parse_dec(val, curr):
        try:
            return Decimal(str(val).strip())
        except Exception:
            return curr

    from wger.gym_operations_payroll.models import StaffWorkSchedule

    if 'base_salary' in data:
        ledger.base_salary = parse_dec(data['base_salary'], ledger.base_salary)
    if 'pt_commissions' in data:
        ledger.pt_commissions = parse_dec(data['pt_commissions'], ledger.pt_commissions)
    if 'overtime_pay' in data:
        ledger.overtime_pay = parse_dec(data['overtime_pay'], ledger.overtime_pay)
    if 'late_minutes_penalty' in data:
        ledger.late_minutes_penalty = parse_dec(data['late_minutes_penalty'], ledger.late_minutes_penalty)
    if 'sudden_absence_penalty' in data:
        ledger.sudden_absence_penalty = parse_dec(data['sudden_absence_penalty'], ledger.sudden_absence_penalty)
    if 'salary_advance_deduction' in data:
        ledger.salary_advance_deduction = parse_dec(data['salary_advance_deduction'], ledger.salary_advance_deduction)

    # Statutory EPF (8% employee, 12% employer) & ETF (3% employer) enable/disable & adjustments
    if 'epf_etf_eligible' in data:
        is_eligible = str(data['epf_etf_eligible']).lower() in ['true', '1', 'yes']
        StaffWorkSchedule.objects.filter(staff_user=ledger.staff_user).update(epf_etf_eligible=is_eligible)
        if not is_eligible:
            ledger.epf_employee_8 = Decimal('0.00')
            ledger.epf_employer_12 = Decimal('0.00')
            ledger.etf_employer_3 = Decimal('0.00')
        else:
            if 'epf_employee_8' in data and data['epf_employee_8'] != '':
                ledger.epf_employee_8 = parse_dec(data['epf_employee_8'], (ledger.base_salary * Decimal('0.08')).quantize(Decimal('0.01')))
            else:
                ledger.epf_employee_8 = (ledger.base_salary * Decimal('0.08')).quantize(Decimal('0.01'))

            if 'epf_employer_12' in data and data['epf_employer_12'] != '':
                ledger.epf_employer_12 = parse_dec(data['epf_employer_12'], (ledger.base_salary * Decimal('0.12')).quantize(Decimal('0.01')))
            else:
                ledger.epf_employer_12 = (ledger.base_salary * Decimal('0.12')).quantize(Decimal('0.01'))

            if 'etf_employer_3' in data and data['etf_employer_3'] != '':
                ledger.etf_employer_3 = parse_dec(data['etf_employer_3'], (ledger.base_salary * Decimal('0.03')).quantize(Decimal('0.01')))
            else:
                ledger.etf_employer_3 = (ledger.base_salary * Decimal('0.03')).quantize(Decimal('0.01'))
    else:
        if 'epf_employee_8' in data:
            ledger.epf_employee_8 = parse_dec(data['epf_employee_8'], ledger.epf_employee_8)
        if 'epf_employer_12' in data:
            ledger.epf_employer_12 = parse_dec(data['epf_employer_12'], ledger.epf_employer_12)
        if 'etf_employer_3' in data:
            ledger.etf_employer_3 = parse_dec(data['etf_employer_3'], ledger.etf_employer_3)

    if 'notes' in data:
        ledger.notes = str(data['notes']).strip()

    ledger.save()
    return JsonResponse({
        'success': True,
        'message': f"Payroll updated for {ledger.staff_user.username}.",
        'ledger': {
            'id': ledger.id,
            'base_salary': float(ledger.base_salary),
            'pt_commissions': float(ledger.pt_commissions),
            'overtime_pay': float(ledger.overtime_pay),
            'late_minutes_penalty': float(ledger.late_minutes_penalty),
            'sudden_absence_penalty': float(ledger.sudden_absence_penalty),
            'salary_advance_deduction': float(ledger.salary_advance_deduction),
            'epf_employee_8': float(ledger.epf_employee_8),
            'epf_employer_12': float(ledger.epf_employer_12),
            'etf_employer_3': float(ledger.etf_employer_3),
            'net_salary': float(ledger.net_salary),
            'notes': ledger.notes,
            'is_finalized': ledger.is_finalized
        }
    })


@login_required
@role_required('super_admin', 'admin')
def admin_delete_payroll_ledger_api(request, ledger_id):
    """Deletes a staff payroll ledger record."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    from wger.gym_operations_payroll.models import PayrollLedger
    ledger = PayrollLedger.objects.select_related('staff_user').filter(id=ledger_id).first()
    if not ledger:
        return JsonResponse({'error': 'Payroll ledger record not found'}, status=404)

    # Scoping check: Admins cannot delete Super Admins
    is_super = request.user.is_superuser or request.user.groups.filter(name='super_admin').exists()
    target_is_super = ledger.staff_user.is_superuser or ledger.staff_user.groups.filter(name='super_admin').exists()
    if target_is_super and not is_super:
        return JsonResponse({'error': 'Permission denied. Only Super Admin can manage Super Admin records.'}, status=403)

    staff_name = ledger.staff_user.get_full_name() or ledger.staff_user.username
    period_str = ledger.month.strftime('%B %Y')
    ledger.delete()

    return JsonResponse({
        'success': True,
        'message': f"Payroll record for {staff_name} ({period_str}) deleted successfully."
    })


@login_required
@role_required('super_admin', 'admin')
def admin_finalize_payroll_ledger_api(request, ledger_id):
    """Toggles finalized lock on a staff payroll ledger."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    from wger.gym_operations_payroll.models import PayrollLedger
    ledger = PayrollLedger.objects.filter(id=ledger_id).first()
    if not ledger:
        return JsonResponse({'error': 'Payroll ledger not found'}, status=404)

    ledger.is_finalized = not ledger.is_finalized
    ledger.finalized_at = timezone.now() if ledger.is_finalized else None
    ledger.save(update_fields=['is_finalized', 'finalized_at'])

    status_str = "Finalized & Approved" if ledger.is_finalized else "Re-opened as Draft"
    return JsonResponse({
        'success': True,
        'message': f"Payroll for {ledger.staff_user.username} is now {status_str}.",
        'is_finalized': ledger.is_finalized,
        'finalized_at': ledger.finalized_at.strftime('%Y-%m-%d %H:%M') if ledger.finalized_at else None
    })


@login_required
@role_required('super_admin', 'admin')
def admin_export_payroll_csv(request):
    """Export monthly payroll ledgers to CSV."""
    import csv
    from django.http import HttpResponse
    from wger.gym_operations_payroll.models import PayrollLedger

    response = HttpResponse(content_type='text/csv')
    today_str = timezone.now().strftime('%Y%m%d_%H%M')
    response['Content-Disposition'] = f'attachment; filename="fitme_payroll_{today_str}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Month', 'Staff Username', 'Full Name', 'Role', 'Base Salary (LKR)', 'PT Commissions (LKR)', 'Overtime Pay (LKR)', 'Late Penalty (LKR)', 'Absence Penalty (LKR)', 'Net Salary (LKR)', 'Finalized', 'Notes'])

    is_super_admin = request.user.is_superuser or request.user.groups.filter(name='super_admin').exists()
    ledgers_qs = PayrollLedger.objects.select_related('staff_user').order_by('-month', 'staff_user__username')
    if not is_super_admin:
        ledgers_qs = ledgers_qs.exclude(staff_user__is_superuser=True).exclude(staff_user__groups__name='super_admin')

    for l in ledgers_qs:
        role_name = l.staff_user.groups.first().name if l.staff_user.groups.exists() else ('Super Admin' if l.staff_user.is_superuser else 'Staff')
        writer.writerow([
            l.month.strftime('%Y-%m'),
            l.staff_user.username,
            l.staff_user.get_full_name() or l.staff_user.username,
            role_name,
            f"{l.base_salary:.2f}",
            f"{l.pt_commissions:.2f}",
            f"{l.overtime_pay:.2f}",
            f"{l.late_minutes_penalty:.2f}",
            f"{l.sudden_absence_penalty:.2f}",
            f"{l.net_salary:.2f}",
            'YES' if l.is_finalized else 'NO',
            l.notes.replace('\n', ' ')
        ])

    return response


@login_required
def admin_payroll_thermal_slip_view(request, ledger_id):
    """Renders 80mm thermal payslip with auto-cut for POS receipt printers."""
    from django.http import HttpResponse, HttpResponseForbidden
    from wger.gym_operations_payroll.models import PayrollLedger, StaffShift
    from wger.membership.models import MemberProfile
    import calendar

    is_admin = request.user.is_superuser or request.user.groups.filter(name__in=['super_admin', 'admin']).exists()
    if not is_admin:
        return HttpResponseForbidden("Access denied. Only Super Admin and Admin can access staff payroll slips.")

    ledger = PayrollLedger.objects.select_related('staff_user').filter(id=ledger_id).first()
    if not ledger:
        return HttpResponse("Payroll ledger record not found.", status=404)

    first_day = ledger.month.replace(day=1)
    last_day_num = calendar.monthrange(first_day.year, first_day.month)[1]
    last_day = first_day.replace(day=last_day_num)

    # PT Coached Clients breakdown (strictly genuine members, deduplicated 1 payout per athlete)
    coached_profiles = MemberProfile.objects.filter(
        assigned_coach=ledger.staff_user,
        personal_trainer_needed=True,
        user__is_staff=False,
        user__is_superuser=False,
        user__is_active=True,
    ).select_related('user').prefetch_related('user__subscriptions')

    pt_clients = []
    seen_athletes = set()
    for cp in coached_profiles:
        if cp.user_id in seen_athletes:
            continue
        active_s = cp.user.subscriptions.filter(
            status='active',
            start_date__lte=last_day,
            end_date__gte=first_day
        ).order_by('-start_date').first()
        if active_s:
            seen_athletes.add(cp.user_id)
            pt_clients.append({
                'name': cp.user.get_full_name() or cp.user.username,
                'username': cp.user.username,
                'package_fee': 7000.0,
                'gym_share': 3000.0,
                'coach_share': 4000.0,
            })

    # Synchronize ledger pt_commissions if draft / unfinalized so take home matches breakdown
    computed_commissions = Decimal(len(pt_clients)) * Decimal('4000.00')
    if not ledger.is_finalized and ledger.pt_commissions != computed_commissions:
        ledger.pt_commissions = computed_commissions
        ledger.save(update_fields=['pt_commissions'])

    # Biometric duty attendance summary
    shifts = StaffShift.objects.filter(
        staff_user=ledger.staff_user,
        shift_date__range=[first_day, last_day]
    )
    attendance = {
        'scheduled': shifts.count(),
        'completed': shifts.filter(actual_first_in__isnull=False).count(),
        'late_minutes': sum(s.calculate_late_minutes() for s in shifts),
        'overtime_minutes': sum(s.overtime_minutes for s in shifts),
        'absence_minutes': sum(s.unapproved_absence_minutes for s in shifts),
    }

    context = {
        'ledger': ledger,
        'staff': ledger.staff_user,
        'pt_clients': pt_clients,
        'attendance': attendance,
        'club_info': {
            'name': 'FIT ME FITNESS',
            'tagline': 'TRAIN WITH PURPOSE',
            'address': 'New Town, Elpitiya Rd, Pitigala, 80420',
            'phone': '070 762 7878',
        },
        'issued_date': timezone.now().strftime('%Y-%m-%d %H:%M'),
    }
    return render(request, 'payroll_thermal_slip.html', context)


# ═════════════════════════════════════════════════════════════════
# STAFF ATTENDANCE & SHIFT ROSTER MANAGEMENT APIS
# ═════════════════════════════════════════════════════════════════

@login_required
@role_required('super_admin', 'admin', 'front_desk')
def admin_clock_staff_attendance_api(request):
    """
    Clocks a staff member IN or OUT at the biometric door turnstile,
    records the DoorAccessLog, and updates their active StaffShift (Morning or Evening session).
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    staff_id = data.get('staff_id')
    direction = data.get('direction', 'IN').upper()
    session = data.get('session', 'AUTO').upper()  # 'AUTO', 'MORNING', 'EVENING'
    notes = data.get('notes', 'Manual console biometric check-in')

    from django.contrib.auth import get_user_model
    from wger.gym_operations_payroll.models import StaffShift, StaffWorkSchedule
    from wger.zkbio_integration.models import DoorAccessLog

    User = get_user_model()
    staff_user = User.objects.filter(id=staff_id, is_staff=True).first()
    if not staff_user:
        return JsonResponse({'error': 'Staff member not found'}, status=404)

    now = timezone.now()
    today = now.date()

    # Find or auto-provision today's shift
    shift = StaffShift.objects.filter(staff_user=staff_user, shift_date=today).first()
    if not shift:
        work_sched = StaffWorkSchedule.objects.filter(staff_user=staff_user).first()
        if work_sched:
            is_active, s_type, s_start, s_end = work_sched.get_schedule_for_weekday(today.weekday())
        else:
            is_active = True
            s_type = 'FULL_SPLIT'
            s_start = timezone.datetime.strptime('05:00', '%H:%M').time()
            s_end = timezone.datetime.strptime('21:00', '%H:%M').time()

        shift = StaffShift.objects.create(
            staff_user=staff_user,
            shift_date=today,
            shift_type=s_type if is_active else 'REST_DAY',
            scheduled_start=s_start or timezone.datetime.strptime('05:00', '%H:%M').time(),
            scheduled_end=s_end or timezone.datetime.strptime('21:00', '%H:%M').time(),
            is_rest_day=(not is_active),
            status='REST_DAY' if not is_active else 'SCHEDULED'
        )

    # Resolve session
    if session == 'AUTO':
        session = 'MORNING' if now.hour < 14 else 'EVENING'

    event_type = 'ENTRY' if direction == 'IN' else 'EXIT'

    # Create DoorAccessLog
    DoorAccessLog.objects.create(
        user=staff_user,
        zk_pin=f"STAFF-{staff_user.id}",
        punch_time=now,
        event_type=event_type,
        verify_mode='BUZZER',
        device_ip='192.168.1.23',
        terminal_name='CONSOLE_MANUAL_ATTENDANCE',
        raw_payload={'clocked_by': request.user.username, 'session': session, 'notes': notes}
    )

    if session == 'MORNING':
        if direction == 'IN':
            if not shift.morning_in:
                shift.morning_in = now
            shift.status = 'ON_FLOOR'
            shift.is_off_floor = False
        else:
            shift.morning_out = now
            shift.status = 'OFF_FLOOR'
    else:  # EVENING
        if direction == 'IN':
            if not shift.evening_in:
                shift.evening_in = now
            shift.status = 'ON_FLOOR'
            shift.is_off_floor = False
        else:
            shift.evening_out = now
            shift.status = 'COMPLETED'

    # Sync legacy actual_first_in / actual_last_out & overtime
    if shift.morning_in and not shift.actual_first_in:
        shift.actual_first_in = shift.morning_in
    elif not shift.actual_first_in and shift.evening_in:
        shift.actual_first_in = shift.evening_in

    if shift.evening_out:
        shift.actual_last_out = shift.evening_out
    elif shift.morning_out and not shift.actual_last_out:
        shift.actual_last_out = shift.morning_out

    shift.overtime_minutes = shift.calculate_overtime_minutes()
    shift.save(update_fields=[
        'morning_in', 'morning_out', 'evening_in', 'evening_out',
        'actual_first_in', 'actual_last_out', 'overtime_minutes',
        'status', 'is_off_floor'
    ])

    try:
        from wger.zkbio_integration.views import _FLOOR_STATUS_CACHE
        _FLOOR_STATUS_CACHE['data'] = None
    except Exception:
        pass

    return JsonResponse({
        'success': True,
        'message': f"Clocked {direction} ({session}) for {staff_user.get_full_name() or staff_user.username}.",
        'shift': {
            'id': shift.id,
            'staff': staff_user.username,
            'shift_type': shift.shift_type,
            'status': shift.status,
            'morning_in': shift.morning_in.strftime('%H:%M') if shift.morning_in else None,
            'morning_out': shift.morning_out.strftime('%H:%M') if shift.morning_out else None,
            'evening_in': shift.evening_in.strftime('%H:%M') if shift.evening_in else None,
            'evening_out': shift.evening_out.strftime('%H:%M') if shift.evening_out else None,
            'late_minutes': shift.calculate_late_minutes(),
            'overtime_minutes': shift.overtime_minutes
        }
    })


@login_required
@role_required('super_admin', 'admin')
def admin_create_staff_shift_api(request):
    """Schedules a new staff shift roster record with split shift support."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    from django.contrib.auth import get_user_model
    from wger.gym_operations_payroll.models import StaffShift
    from decimal import Decimal

    User = get_user_model()
    staff_id = data.get('staff_id')
    shift_date_str = data.get('shift_date')
    shift_type = data.get('shift_type', 'FULL_SPLIT')
    start_str = data.get('scheduled_start', '')
    end_str = data.get('scheduled_end', '')
    rate_str = data.get('base_hourly_rate', '500.00')

    staff_user = User.objects.filter(id=staff_id, is_staff=True).first()
    if not staff_user:
        return JsonResponse({'error': 'Staff user not found'}, status=404)

    try:
        shift_date = timezone.datetime.strptime(shift_date_str, '%Y-%m-%d').date()
        if shift_type == 'FULL_SPLIT':
            s_start = timezone.datetime.strptime('05:00', '%H:%M').time()
            s_end = timezone.datetime.strptime('21:00', '%H:%M').time()
            is_rest = False
        elif shift_type == 'MORNING':
            s_start = timezone.datetime.strptime('05:00', '%H:%M').time()
            s_end = timezone.datetime.strptime('12:00', '%H:%M').time()
            is_rest = False
        elif shift_type == 'EVENING':
            s_start = timezone.datetime.strptime('15:00', '%H:%M').time()
            s_end = timezone.datetime.strptime('21:00', '%H:%M').time()
            is_rest = False
        elif shift_type == 'REST_DAY':
            s_start = timezone.datetime.strptime('05:00', '%H:%M').time()
            s_end = timezone.datetime.strptime('21:00', '%H:%M').time()
            is_rest = True
        else:
            s_start = timezone.datetime.strptime(start_str or '05:00', '%H:%M').time()
            s_end = timezone.datetime.strptime(end_str or '21:00', '%H:%M').time()
            is_rest = False

        rate = Decimal(str(rate_str))
    except Exception as e:
        return JsonResponse({'error': f"Invalid date or time format: {e}"}, status=400)

    shift, created = StaffShift.objects.update_or_create(
        staff_user=staff_user,
        shift_date=shift_date,
        defaults={
            'shift_type': shift_type,
            'scheduled_start': s_start,
            'scheduled_end': s_end,
            'base_hourly_rate': rate,
            'is_rest_day': is_rest,
            'status': 'REST_DAY' if is_rest else 'SCHEDULED'
        }
    )

    return JsonResponse({
        'success': True,
        'message': f"Shift ({shift.get_shift_type_display()}) scheduled for {staff_user.username} on {shift_date}.",
        'shift_id': shift.id
    })


@login_required
@role_required('super_admin', 'admin')
def admin_toggle_shift_leave_api(request, shift_id):
    """Toggles approved leave for a scheduled shift."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    reason = data.get('leave_reason', 'Approved medical or personal leave')

    from wger.gym_operations_payroll.models import StaffShift
    shift = StaffShift.objects.filter(id=shift_id).first()
    if not shift:
        return JsonResponse({'error': 'Shift not found'}, status=404)

    shift.approved_leave = not shift.approved_leave
    shift.leave_reason = reason if shift.approved_leave else ''
    shift.status = 'LEAVE' if shift.approved_leave else 'SCHEDULED'
    shift.save(update_fields=['approved_leave', 'leave_reason', 'status'])

    return JsonResponse({
        'success': True,
        'message': f"Shift leave {'approved' if shift.approved_leave else 'revoked'} for {shift.staff_user.username}.",
        'approved_leave': shift.approved_leave,
        'status': shift.status
    })


@login_required
@role_required('super_admin', 'admin')
def admin_enroll_staff_payroll_api(request):
    """Manually provisions or updates base salary for a staff member for a given month."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    from decimal import Decimal
    from django.contrib.auth import get_user_model
    from wger.gym_operations_payroll.models import PayrollLedger
    from wger.gym_operations_payroll.tasks import calculate_monthly_payroll

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    User = get_user_model()
    staff_id = data.get('staff_id')
    month_str = data.get('month', '')
    base_salary_str = data.get('base_salary', '75000.00')
    notes = data.get('notes', '')

    staff = User.objects.filter(id=staff_id, is_staff=True).first()
    if not staff:
        return JsonResponse({'error': 'Staff user not found.'}, status=404)

    try:
        if len(month_str) == 7:
            month_date = timezone.datetime.strptime(month_str, '%Y-%m').date().replace(day=1)
        else:
            month_date = timezone.datetime.strptime(month_str, '%Y-%m-%d').date().replace(day=1)
        base_salary = Decimal(str(base_salary_str))
    except Exception as e:
        return JsonResponse({'error': f"Invalid format: {e}"}, status=400)

    ledger, created = PayrollLedger.objects.get_or_create(
        staff_user=staff,
        month=month_date,
        defaults={
            'base_salary': base_salary,
            'notes': notes or f"Manual enrollment by {request.user.username}"
        }
    )
    if not created:
        ledger.base_salary = base_salary
        if notes:
            ledger.notes = notes
        ledger.save()

    # Recalculate dynamic components (commissions + attendance)
    calculate_monthly_payroll(month_date.year, month_date.month)

    return JsonResponse({
        'success': True,
        'message': f"Payroll ledger for {staff.get_full_name() or staff.username} saved for {month_date.strftime('%B %Y')} with Base LKR {base_salary:,.2f}.",
        'ledger_id': ledger.id
    })


@login_required
@role_required('super_admin', 'admin', 'coach')
def admin_get_pt_breakdown_api(request, ledger_id):
    """Returns JSON breakdown of coached athletes and the LKR 7000 / 3000 / 4000 split for a coach."""
    from wger.gym_operations_payroll.models import PayrollLedger
    from wger.membership.models import MemberProfile
    import calendar

    ledger = PayrollLedger.objects.select_related('staff_user').filter(id=ledger_id).first()
    if not ledger:
        return JsonResponse({'error': 'Ledger not found.'}, status=404)

    is_admin = request.user.is_superuser or request.user.groups.filter(name__in=['super_admin', 'admin']).exists()
    if not is_admin and request.user != ledger.staff_user:
        return JsonResponse({'error': 'Permission denied.'}, status=403)

    first_day = ledger.month
    last_day_num = calendar.monthrange(first_day.year, first_day.month)[1]
    last_day = first_day.replace(day=last_day_num)

    coached_profiles = MemberProfile.objects.filter(
        assigned_coach=ledger.staff_user,
        personal_trainer_needed=True,
        user__is_staff=False,
        user__is_superuser=False,
        user__is_active=True,
    ).select_related('user').prefetch_related('user__subscriptions')

    pt_list = []
    seen_athletes = set()
    for cp in coached_profiles:
        if cp.user_id in seen_athletes:
            continue
        active_s = cp.user.subscriptions.filter(
            status='active',
            start_date__lte=last_day,
            end_date__gte=first_day
        ).order_by('-start_date').first()
        if active_s:
            seen_athletes.add(cp.user_id)
            pt_list.append({
                'id': cp.user.id,
                'name': cp.user.get_full_name() or cp.user.username,
                'username': cp.user.username,
                'phone': cp.phone or '—',
                'plan_name': active_s.plan.name if active_s.plan else 'Personal Coaching Package',
                'package_fee': 7000.0,
                'gym_share': 3000.0,
                'coach_share': 4000.0,
                'sub_start': active_s.start_date.strftime('%d %b %Y'),
                'sub_end': active_s.end_date.strftime('%d %b %Y'),
                'status': 'Active'
            })

    # Synchronize unfinalized ledger pt_commissions so Net Salary stays synchronized
    computed_commissions = Decimal(len(pt_list)) * Decimal('4000.00')
    if not ledger.is_finalized and ledger.pt_commissions != computed_commissions:
        ledger.pt_commissions = computed_commissions
        ledger.save(update_fields=['pt_commissions'])

    return JsonResponse({
        'success': True,
        'coach_name': ledger.staff_user.get_full_name() or ledger.staff_user.username,
        'coach_username': ledger.staff_user.username,
        'month': ledger.month.strftime('%B %Y'),
        'total_clients': len(pt_list),
        'package_fee_unit': 7000.0,
        'gym_share_unit': 3000.0,
        'coach_share_unit': 4000.0,
        'total_gross_packages': len(pt_list) * 7000.0,
        'total_gym_revenue': len(pt_list) * 3000.0,
        'total_coach_commission': float(computed_commissions),
        'clients': pt_list
    })


# ═════════════════════════════════════════════════════════════════
# STAFF WORK SCHEDULE, BULK ROSTERING & SALARY ADVANCES APIS
# ═════════════════════════════════════════════════════════════════

@login_required
@role_required('super_admin', 'admin')
def admin_get_staff_work_schedule_api(request, staff_id):
    """Returns JSON of staff contract work schedule with split shift presets."""
    from django.contrib.auth import get_user_model
    from wger.gym_operations_payroll.models import StaffWorkSchedule
    User = get_user_model()
    staff = User.objects.filter(id=staff_id, is_staff=True).first()
    if not staff:
        return JsonResponse({'error': 'Staff user not found.'}, status=404)

    sched = StaffWorkSchedule.objects.filter(staff_user=staff).first()
    if sched:
        data = {
            'exists': True,
            'staff_id': staff.id,
            'staff_name': staff.get_full_name() or staff.username,
            'default_base_salary': float(sched.default_base_salary),
            'hourly_rate': float(sched.hourly_rate),
            'epf_etf_eligible': sched.epf_etf_eligible,
            'epf_number': sched.epf_number,
            'monday_active': sched.monday_active,
            'monday_shift_type': getattr(sched, 'monday_shift_type', 'FULL_SPLIT'),
            'monday_start': sched.monday_start.strftime('%H:%M'),
            'monday_end': sched.monday_end.strftime('%H:%M'),
            'tuesday_active': sched.tuesday_active,
            'tuesday_shift_type': getattr(sched, 'tuesday_shift_type', 'FULL_SPLIT'),
            'tuesday_start': sched.tuesday_start.strftime('%H:%M'),
            'tuesday_end': sched.tuesday_end.strftime('%H:%M'),
            'wednesday_active': sched.wednesday_active,
            'wednesday_shift_type': getattr(sched, 'wednesday_shift_type', 'FULL_SPLIT'),
            'wednesday_start': sched.wednesday_start.strftime('%H:%M'),
            'wednesday_end': sched.wednesday_end.strftime('%H:%M'),
            'thursday_active': sched.thursday_active,
            'thursday_shift_type': getattr(sched, 'thursday_shift_type', 'FULL_SPLIT'),
            'thursday_start': sched.thursday_start.strftime('%H:%M'),
            'thursday_end': sched.thursday_end.strftime('%H:%M'),
            'friday_active': sched.friday_active,
            'friday_shift_type': getattr(sched, 'friday_shift_type', 'FULL_SPLIT'),
            'friday_start': sched.friday_start.strftime('%H:%M'),
            'friday_end': sched.friday_end.strftime('%H:%M'),
            'saturday_active': sched.saturday_active,
            'saturday_shift_type': getattr(sched, 'saturday_shift_type', 'FULL_SPLIT'),
            'saturday_start': sched.saturday_start.strftime('%H:%M'),
            'saturday_end': sched.saturday_end.strftime('%H:%M'),
            'sunday_active': sched.sunday_active,
            'sunday_shift_type': getattr(sched, 'sunday_shift_type', 'REST_DAY'),
            'sunday_start': sched.sunday_start.strftime('%H:%M'),
            'sunday_end': sched.sunday_end.strftime('%H:%M'),
            'notes': sched.notes
        }
    else:
        data = {
            'exists': False,
            'staff_id': staff.id,
            'staff_name': staff.get_full_name() or staff.username,
            'default_base_salary': 75000.0,
            'hourly_rate': 500.0,
            'epf_etf_eligible': True,
            'epf_number': '',
            'monday_active': True,
            'monday_shift_type': 'FULL_SPLIT',
            'monday_start': '05:00',
            'monday_end': '21:00',
            'tuesday_active': True,
            'tuesday_shift_type': 'FULL_SPLIT',
            'tuesday_start': '05:00',
            'tuesday_end': '21:00',
            'wednesday_active': True,
            'wednesday_shift_type': 'FULL_SPLIT',
            'wednesday_start': '05:00',
            'wednesday_end': '21:00',
            'thursday_active': True,
            'thursday_shift_type': 'FULL_SPLIT',
            'thursday_start': '05:00',
            'thursday_end': '21:00',
            'friday_active': True,
            'friday_shift_type': 'FULL_SPLIT',
            'friday_start': '05:00',
            'friday_end': '21:00',
            'saturday_active': True,
            'saturday_shift_type': 'FULL_SPLIT',
            'saturday_start': '05:00',
            'saturday_end': '21:00',
            'sunday_active': False,
            'sunday_shift_type': 'REST_DAY',
            'sunday_start': '08:00',
            'sunday_end': '14:00',
            'notes': ''
        }
    return JsonResponse({'success': True, 'schedule': data})


@login_required
@role_required('super_admin', 'admin')
def admin_save_staff_work_schedule_api(request):
    """Saves or updates master weekly schedule for a staff member with split shift presets."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    from decimal import Decimal
    from django.contrib.auth import get_user_model
    from wger.gym_operations_payroll.models import StaffWorkSchedule

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    User = get_user_model()
    staff_id = data.get('staff_id')
    staff = User.objects.filter(id=staff_id, is_staff=True).first()
    if not staff:
        return JsonResponse({'error': 'Staff user not found.'}, status=404)

    try:
        sched, _ = StaffWorkSchedule.objects.get_or_create(staff_user=staff)
        sched.default_base_salary = Decimal(str(data.get('default_base_salary', '75000.00')))
        sched.hourly_rate = Decimal(str(data.get('hourly_rate', '500.00')))
        sched.epf_etf_eligible = bool(data.get('epf_etf_eligible', True))
        sched.epf_number = str(data.get('epf_number', '')).strip()

        # Days
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for d in days:
            s_type = data.get(f"{d}_shift_type")
            if s_type:
                setattr(sched, f"{d}_shift_type", s_type)
                if s_type == 'REST_DAY':
                    setattr(sched, f"{d}_active", False)
                else:
                    setattr(sched, f"{d}_active", True)
                    if s_type == 'FULL_SPLIT':
                        setattr(sched, f"{d}_start", timezone.datetime.strptime('05:00', '%H:%M').time())
                        setattr(sched, f"{d}_end", timezone.datetime.strptime('21:00', '%H:%M').time())
                    elif s_type == 'MORNING':
                        setattr(sched, f"{d}_start", timezone.datetime.strptime('05:00', '%H:%M').time())
                        setattr(sched, f"{d}_end", timezone.datetime.strptime('12:00', '%H:%M').time())
                    elif s_type == 'EVENING':
                        setattr(sched, f"{d}_start", timezone.datetime.strptime('15:00', '%H:%M').time())
                        setattr(sched, f"{d}_end", timezone.datetime.strptime('21:00', '%H:%M').time())
            else:
                setattr(sched, f"{d}_active", bool(data.get(f"{d}_active", False)))
                start_val = data.get(f"{d}_start", '05:00')
                end_val = data.get(f"{d}_end", '21:00')
                setattr(sched, f"{d}_start", timezone.datetime.strptime(start_val, '%H:%M').time())
                setattr(sched, f"{d}_end", timezone.datetime.strptime(end_val, '%H:%M').time())

        sched.notes = str(data.get('notes', '')).strip()
        sched.save()

        return JsonResponse({
            'success': True,
            'message': f"Work schedule saved for {staff.get_full_name() or staff.username}.",
            'schedule_id': sched.id
        })
    except Exception as e:
        return JsonResponse({'error': f"Error saving schedule: {e}"}, status=400)


@login_required
@role_required('super_admin', 'admin')
def admin_generate_bulk_roster_api(request):
    """
    1-Click Bulk Monthly Split Roster Generator.
    Reads each staff member's StaffWorkSchedule and auto-provisions StaffShift records
    for Morning 05:00-12:00 and Evening 15:00-21:00 split operations.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    import calendar
    from datetime import timedelta
    from decimal import Decimal
    from django.contrib.auth import get_user_model
    from wger.gym_operations_payroll.models import StaffShift, StaffWorkSchedule

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    User = get_user_model()
    month_str = data.get('month', '')  # 'YYYY-MM'
    staff_id = data.get('staff_id')
    include_rest_days = data.get('include_rest_days', True)

    now = timezone.now().date()
    if month_str:
        try:
            start_date = timezone.datetime.strptime(month_str, '%Y-%m').date().replace(day=1)
        except Exception:
            start_date = now.replace(day=1)
    else:
        start_date = now.replace(day=1)

    last_day_num = calendar.monthrange(start_date.year, start_date.month)[1]
    end_date = start_date.replace(day=last_day_num)

    staff_qs = User.objects.filter(is_staff=True, is_active=True)
    if staff_id:
        staff_qs = staff_qs.filter(id=staff_id)

    total_shifts_created = 0
    total_rest_days = 0

    curr_date = start_date
    while curr_date <= end_date:
        weekday_idx = curr_date.weekday()  # 0=Mon ... 6=Sun
        for staff in staff_qs:
            # Check if shift already scheduled for this staff on this day
            existing = StaffShift.objects.filter(staff_user=staff, shift_date=curr_date).first()
            if existing:
                continue

            sched = StaffWorkSchedule.objects.filter(staff_user=staff).first()
            if sched:
                is_active, s_type, s_start, s_end = sched.get_schedule_for_weekday(weekday_idx)
                rate = sched.hourly_rate
            else:
                # Default gym contract: Mon-Sat Split Shift (05:00-12:00 & 15:00-21:00), Sun Rest Day
                if weekday_idx < 6:
                    is_active = True
                    s_type = 'FULL_SPLIT'
                    s_start = timezone.datetime.strptime('05:00', '%H:%M').time()
                    s_end = timezone.datetime.strptime('21:00', '%H:%M').time()
                else:
                    is_active = False
                    s_type = 'REST_DAY'
                    s_start = timezone.datetime.strptime('05:00', '%H:%M').time()
                    s_end = timezone.datetime.strptime('21:00', '%H:%M').time()
                rate = Decimal('500.00')

            if is_active and s_type != 'REST_DAY':
                StaffShift.objects.create(
                    staff_user=staff,
                    shift_date=curr_date,
                    shift_type=s_type,
                    scheduled_start=s_start or timezone.datetime.strptime('05:00', '%H:%M').time(),
                    scheduled_end=s_end or timezone.datetime.strptime('21:00', '%H:%M').time(),
                    base_hourly_rate=rate,
                    status='SCHEDULED',
                    is_rest_day=False
                )
                total_shifts_created += 1
            elif include_rest_days:
                StaffShift.objects.create(
                    staff_user=staff,
                    shift_date=curr_date,
                    shift_type='REST_DAY',
                    scheduled_start=s_start or timezone.datetime.strptime('05:00', '%H:%M').time(),
                    scheduled_end=s_end or timezone.datetime.strptime('21:00', '%H:%M').time(),
                    base_hourly_rate=rate,
                    status='REST_DAY',
                    is_rest_day=True
                )
                total_rest_days += 1

        curr_date += timedelta(days=1)

    return JsonResponse({
        'success': True,
        'message': f"1-Click Split Roster generated for {start_date.strftime('%B %Y')}: {total_shifts_created} active split shifts and {total_rest_days} scheduled rest days created.",
        'month': start_date.strftime('%B %Y'),
        'shifts_created': total_shifts_created,
        'rest_days_created': total_rest_days
    })


@login_required
@role_required('super_admin', 'admin', 'front_desk')
def admin_issue_salary_advance_api(request):
    """
    Disburses a staff salary advance from the Front Desk till or bank transfer.
    Automatically creates a StaffSalaryAdvance and a linked ClubExpense (OPEX)
    so cash-in-hand, OPEX, and net profit sync immediately.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    from decimal import Decimal
    from django.contrib.auth import get_user_model
    from wger.gym_operations_payroll.models import StaffSalaryAdvance, ClubExpense
    from wger.gym_operations_payroll.tasks import calculate_monthly_payroll

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    User = get_user_model()
    staff_id = data.get('staff_id')
    amount_str = data.get('amount', '0.00')
    payout_method = data.get('payout_method', 'cash')
    reason = str(data.get('reason', '')).strip()

    staff = User.objects.filter(id=staff_id, is_staff=True).first()
    if not staff:
        return JsonResponse({'error': 'Staff user not found.'}, status=404)

    try:
        amount = Decimal(str(amount_str))
        if amount <= Decimal('0.00'):
            return JsonResponse({'error': 'Advance amount must be greater than zero.'}, status=400)
    except Exception:
        return JsonResponse({'error': 'Invalid amount provided.'}, status=400)

    now = timezone.now()
    today = now.date()

    # 1. Create StaffSalaryAdvance record
    advance = StaffSalaryAdvance.objects.create(
        staff_user=staff,
        amount=amount,
        request_date=today,
        payout_method=payout_method,
        reason=reason,
        approved_by=request.user
    )

    # 2. Automatically record in OPEX (ClubExpense) to instantly reflect in Till & Finance Telemetry
    exp_title = f"Staff Salary Advance: {staff.get_full_name() or staff.username}"
    opex_exp = ClubExpense.objects.create(
        title=exp_title,
        category='staff_salary',
        amount=amount,
        expense_date=today,
        payment_method=payout_method,
        recorded_by=request.user,
        receipt_ref=advance.receipt_voucher,
        notes=f"Mid-month advance disbursed to @{staff.username}. Reason: {reason or 'Personal advance'}. Voucher: {advance.receipt_voucher}"
    )

    advance.opex_expense = opex_exp
    advance.save(update_fields=['opex_expense'])

    # 3. Trigger payroll consolidation for this month to reflect the deduction immediately
    try:
        calculate_monthly_payroll(today.year, today.month)
    except Exception as exc:
        logger.warning(f"[Payroll] calculate_monthly_payroll failed following advance deduction: {exc}")

    return JsonResponse({
        'success': True,
        'message': f"Advance of LKR {amount:,.2f} disbursed for {staff.get_full_name() or staff.username} ({advance.receipt_voucher}).",
        'advance_id': advance.id,
        'voucher_code': advance.receipt_voucher,
        'staff_name': staff.get_full_name() or staff.username,
        'amount': float(amount),
        'voucher_url': f"/dashboard/advances/{advance.id}/thermal-voucher/"
    })


@login_required
def admin_advance_thermal_voucher_view(request, advance_id):
    """Renders 80mm POS Thermal Signature Slip for Staff Salary Advances."""
    from django.http import HttpResponse, HttpResponseForbidden
    from wger.gym_operations_payroll.models import StaffSalaryAdvance

    is_admin = request.user.is_superuser or request.user.groups.filter(name__in=['super_admin', 'admin', 'front_desk']).exists()
    if not is_admin:
        return HttpResponseForbidden("Access denied. Only Super Admin and Front Desk can access staff advance vouchers.")

    advance = StaffSalaryAdvance.objects.select_related('staff_user', 'approved_by', 'opex_expense').filter(id=advance_id).first()
    if not advance:
        return HttpResponse("Advance voucher not found.", status=404)

    context = {
        'advance': advance,
        'staff': advance.staff_user,
        'club_info': {
            'name': 'FIT ME FITNESS',
            'tagline': 'TRAIN WITH PURPOSE',
            'address': 'New Town, Elpitiya Rd, Pitigala, 80420',
            'phone': '070 762 7878',
        },
        'printed_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    return render(request, 'advance_thermal_voucher.html', context)


