from django.contrib import admin
from wger.gym_operations_payroll.models import (
    StaffShift, SuddenAbsenceAlert, PayrollLedger,
    ShiftTemplate, StaffWorkSchedule, StaffSalaryAdvance
)


@admin.register(ShiftTemplate)
class ShiftTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_time', 'end_time', 'color_hex', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(StaffWorkSchedule)
class StaffWorkScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'staff_user', 'default_base_salary', 'hourly_rate', 'epf_etf_eligible', 'epf_number',
        'monday_active', 'tuesday_active', 'wednesday_active', 'thursday_active', 'friday_active', 'saturday_active', 'sunday_active'
    )
    search_fields = ('staff_user__username', 'epf_number')


@admin.register(StaffSalaryAdvance)
class StaffSalaryAdvanceAdmin(admin.ModelAdmin):
    list_display = ('receipt_voucher', 'staff_user', 'amount', 'request_date', 'payout_method', 'is_deducted', 'approved_by')
    list_filter = ('is_deducted', 'payout_method', 'request_date')
    search_fields = ('receipt_voucher', 'staff_user__username', 'reason')


@admin.register(StaffShift)
class StaffShiftAdmin(admin.ModelAdmin):
    list_display = ('staff_user', 'shift_date', 'scheduled_start', 'scheduled_end', 'actual_first_in', 'actual_last_out', 'status', 'is_rest_day', 'is_off_floor')
    list_filter = ('shift_date', 'status', 'is_rest_day', 'is_off_floor', 'approved_leave')
    search_fields = ('staff_user__username', 'staff_user__first_name', 'staff_user__last_name')


@admin.register(SuddenAbsenceAlert)
class SuddenAbsenceAlertAdmin(admin.ModelAdmin):
    list_display = ('staff_user', 'exit_time', 'minutes_off_floor', 'is_resolved', 'created_at')
    list_filter = ('is_resolved', 'created_at')
    search_fields = ('staff_user__username',)
    actions = ['resolve_alerts']

    def resolve_alerts(self, request, queryset):
        queryset.update(is_resolved=True)
        self.message_user(request, f"Marked {queryset.count()} absence alerts as resolved.")
    resolve_alerts.short_description = "Mark selected alerts as resolved"


@admin.register(PayrollLedger)
class PayrollLedgerAdmin(admin.ModelAdmin):
    list_display = ('staff_user', 'month', 'base_salary', 'overtime_pay', 'pt_commissions', 'epf_employee_8', 'salary_advance_deduction', 'get_net_salary', 'is_finalized')
    list_filter = ('month', 'is_finalized')
    search_fields = ('staff_user__username',)

    def get_net_salary(self, obj):
        return f"LKR {obj.net_salary:,.2f}"
    get_net_salary.short_description = 'Net Salary'

