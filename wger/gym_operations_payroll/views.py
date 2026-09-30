from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum

from wger.gym_operations_payroll.models import StaffShift, SuddenAbsenceAlert, PayrollLedger


@staff_member_required
def sudden_absence_alerts_api(request):
    """Returns unresolved sudden absence alerts for the top bar."""
    unresolved = SuddenAbsenceAlert.objects.filter(is_resolved=False).select_related('staff_user', 'shift')
    alerts_data = []
    for a in unresolved:
        alerts_data.append({
            'id': a.id,
            'staff_name': a.staff_user.get_full_name() or a.staff_user.username,
            'exit_time': a.exit_time.strftime('%H:%M'),
            'minutes_off_floor': a.minutes_off_floor,
            'shift_id': a.shift.id if a.shift else None,
        })
    return JsonResponse({'alerts': alerts_data, 'count': len(alerts_data)})


@staff_member_required
def payroll_summary_api(request):
    """Returns summary of monthly payroll ledgers."""
    month_str = request.GET.get('month')
    if month_str:
        try:
            target_month = timezone.datetime.strptime(month_str, '%Y-%m').date()
        except ValueError:
            target_month = timezone.now().date().replace(day=1)
    else:
        target_month = timezone.now().date().replace(day=1)

    ledgers = PayrollLedger.objects.filter(month=target_month).select_related('staff_user')
    total_base = sum(l.base_salary for l in ledgers)
    total_overtime = sum(l.overtime_pay for l in ledgers)
    total_commissions = sum(l.pt_commissions for l in ledgers)
    total_penalties = sum(l.late_minutes_penalty + l.sudden_absence_penalty for l in ledgers)
    total_net = sum(l.net_salary for l in ledgers)

    return JsonResponse({
        'month': target_month.strftime('%B %Y'),
        'total_staff': ledgers.count(),
        'total_base': float(total_base),
        'total_overtime': float(total_overtime),
        'total_commissions': float(total_commissions),
        'total_penalties': float(total_penalties),
        'total_net_payout': float(total_net),
    })
