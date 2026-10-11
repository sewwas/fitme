import logging
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from celery import shared_task

logger = logging.getLogger('wger')


@shared_task(name='gym_operations_payroll.tasks.inspect_staff_punch_continuity')
def inspect_staff_punch_continuity():
    """
    Sudden Leaving Detection Task (runs every 5-10 minutes via Celery Beat).
    Inspects staff punch logs. If an on-shift staff member punches out during working
    hours without an approved leave request for >20 minutes, flag shift as OFF_FLOOR
    and alert the Super Admin.
    """
    from wger.gym_operations_payroll.models import StaffShift, SuddenAbsenceAlert
    from wger.zkbio_integration.models import DoorAccessLog

    now = timezone.now()
    today = now.date()
    current_time = now.time()

    # Find shifts scheduled for today where shift has started and not finished
    active_shifts = StaffShift.objects.filter(
        shift_date=today,
        scheduled_start__lte=current_time,
        scheduled_end__gte=current_time,
        approved_leave=False
    ).select_related('staff_user')

    alerts_triggered = 0

    for shift in active_shifts:
        user = shift.staff_user

        # Get latest punch for this user today
        latest_punch = DoorAccessLog.objects.filter(
            user=user,
            punch_time__date=today,
            event_type__in=['ENTRY', 'EXIT']
        ).order_by('-punch_time').first()

        if not latest_punch:
            # Staff never showed up yet, check if late
            continue

        if latest_punch.event_type == 'EXIT':
            elapsed_minutes = int((now - latest_punch.punch_time).total_seconds() / 60)

            # If absent for > 20 minutes without leave
            if elapsed_minutes >= 20:
                if not shift.is_off_floor:
                    shift.is_off_floor = True
                    shift.status = 'OFF_FLOOR'
                    shift.unapproved_absence_minutes += elapsed_minutes
                    shift.save(update_fields=['is_off_floor', 'status', 'unapproved_absence_minutes'])

                    # Check or create SuddenAbsenceAlert
                    alert, created = SuddenAbsenceAlert.objects.get_or_create(
                        shift=shift,
                        staff_user=user,
                        is_resolved=False,
                        defaults={
                            'exit_time': latest_punch.punch_time,
                            'minutes_off_floor': elapsed_minutes,
                            'admin_notes': f"Automated flag: {user.username} departed floor without approved leave. Absent {elapsed_minutes} mins."
                        }
                    )
                    if not created:
                        alert.minutes_off_floor = elapsed_minutes
                        alert.save(update_fields=['minutes_off_floor'])

                    alerts_triggered += 1
                    logger.warning(
                        f"[Staff Floor Alert] Staff {user.username} has been OFF FLOOR for {elapsed_minutes}m! Shift ID: {shift.id}"
                    )
        elif latest_punch.event_type == 'ENTRY':
            # Staff returned
            if shift.is_off_floor:
                shift.is_off_floor = False
                shift.status = 'ON_FLOOR'
                shift.save(update_fields=['is_off_floor', 'status'])
                # Resolve active alerts
                SuddenAbsenceAlert.objects.filter(
                    shift=shift,
                    is_resolved=False
                ).update(is_resolved=True)
                logger.info(f"[Staff Floor Alert] Staff {user.username} has RETURNED to floor.")

    return f"Inspected {active_shifts.count()} shifts. Triggered {alerts_triggered} sudden absence alerts."


@shared_task(name='gym_operations_payroll.tasks.calculate_monthly_payroll')
def calculate_monthly_payroll(year=None, month=None):
    """
    Monthly payroll consolidation task.
    Calculates monthly net salary:
    Net = Base_Salary + Overtime_Pay + PT_Commissions - (Late_Minutes_Penalty + Sudden_Absence_Penalty)
    """
    from wger.gym_operations_payroll.models import (
        StaffShift, PayrollLedger, SuddenAbsenceAlert,
        StaffWorkSchedule, StaffSalaryAdvance
    )
    from django.contrib.auth import get_user_model
    User = get_user_model()

    now = timezone.now()
    if not year or not month:
        # Default to current month
        year = now.year
        month = now.month

    first_day = timezone.datetime(year, month, 1).date()
    # Next month first day minus 1 day
    if month == 12:
        last_day = timezone.datetime(year + 1, 1, 1).date() - timedelta(days=1)
    else:
        last_day = timezone.datetime(year, month + 1, 1).date() - timedelta(days=1)

    staff_users = User.objects.filter(is_staff=True, is_active=True)
    generated = 0

    for staff in staff_users:
        # Check if staff has a customized StaffWorkSchedule contract
        work_sched = StaffWorkSchedule.objects.filter(staff_user=staff).first()
        base_salary_val = work_sched.default_base_salary if work_sched else Decimal('75000.00')
        hourly_rate = work_sched.hourly_rate if work_sched else Decimal('500.00')
        minute_rate = hourly_rate / Decimal('60.0')

        shifts = StaffShift.objects.filter(
            staff_user=staff,
            shift_date__range=[first_day, last_day]
        )

        total_late_minutes = sum(s.calculate_late_minutes() for s in shifts)
        total_absence_minutes = sum(s.unapproved_absence_minutes for s in shifts)
        total_overtime_minutes = sum(s.overtime_minutes for s in shifts)

        overtime_pay = (Decimal(total_overtime_minutes) * minute_rate * Decimal('1.5')).quantize(Decimal('0.01'))
        late_penalty = (Decimal(total_late_minutes) * minute_rate).quantize(Decimal('0.01'))
        absence_penalty = (Decimal(total_absence_minutes) * minute_rate * Decimal('1.25')).quantize(Decimal('0.01'))

        # Calculate dynamic PT coaching commissions (LKR 4,000 per active coached client)
        from wger.membership.models import MemberProfile
        coached_count = MemberProfile.objects.filter(
            assigned_coach=staff,
            personal_trainer_needed=True,
            user__subscriptions__status='active',
            user__subscriptions__start_date__lte=last_day,
            user__subscriptions__end_date__gte=first_day
        ).distinct().count()
        computed_pt_commission = Decimal(coached_count) * Decimal('4000.00')

        # Calculate EPF & ETF (Sri Lankan Statutory Compliance)
        epf_eligible = work_sched.epf_etf_eligible if work_sched else True
        epf_employee_8 = (base_salary_val * Decimal('0.08')).quantize(Decimal('0.01')) if epf_eligible else Decimal('0.00')
        epf_employer_12 = (base_salary_val * Decimal('0.12')).quantize(Decimal('0.01')) if epf_eligible else Decimal('0.00')
        etf_employer_3 = (base_salary_val * Decimal('0.03')).quantize(Decimal('0.01')) if epf_eligible else Decimal('0.00')

        # Calculate mid-month Staff Salary Advances disbursed in this period
        advances_qs = StaffSalaryAdvance.objects.filter(
            staff_user=staff,
            request_date__range=[first_day, last_day]
        )
        total_advances = sum((a.amount for a in advances_qs), Decimal('0.00'))

        # Fetch or initialize ledger
        ledger, created = PayrollLedger.objects.get_or_create(
            staff_user=staff,
            month=first_day,
            defaults={
                'base_salary': base_salary_val,
                'overtime_pay': overtime_pay,
                'pt_commissions': computed_pt_commission,
                'late_minutes_penalty': late_penalty,
                'sudden_absence_penalty': absence_penalty,
                'epf_employee_8': epf_employee_8,
                'epf_employer_12': epf_employer_12,
                'etf_employer_3': etf_employer_3,
                'salary_advance_deduction': total_advances,
                'notes': f"Auto-computed: {coached_count} coached clients (LKR {computed_pt_commission:,.2f}), {total_late_minutes}m late, {total_absence_minutes}m unapproved absence, {total_overtime_minutes}m overtime, advances: LKR {total_advances:,.2f}."
            }
        )

        if not ledger.is_finalized:
            if not created and ledger.base_salary == Decimal('0.00'):
                ledger.base_salary = base_salary_val
            ledger.overtime_pay = overtime_pay
            ledger.late_minutes_penalty = late_penalty
            ledger.sudden_absence_penalty = absence_penalty
            ledger.epf_employee_8 = epf_employee_8
            ledger.epf_employer_12 = epf_employer_12
            ledger.etf_employer_3 = etf_employer_3
            ledger.salary_advance_deduction = total_advances

            if created or (ledger.pt_commissions or Decimal('0.00')) < computed_pt_commission:
                ledger.pt_commissions = computed_pt_commission

            ledger.notes = f"Auto-computed: {coached_count} coached client(s) (LKR {computed_pt_commission:,.2f}), {total_late_minutes}m late, {total_absence_minutes}m absence, {total_overtime_minutes}m OT, advances: LKR {total_advances:,.2f}."
            ledger.save()

            # Associate advances with ledger
            advances_qs.filter(ledger__isnull=True).update(ledger=ledger)
            generated += 1

    return f"Consolidated payroll for {generated} staff members for month {first_day}."
