from django.contrib import admin
from wger.gym_operations_payroll.models import MembershipPlan, StaffShift, SuddenAbsenceAlert, PayrollLedger


@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'plan_type', 'price_monthly', 'max_members', 'allowed_entry_start', 'allowed_entry_end', 'is_active')
    list_filter = ('plan_type', 'is_active')
    search_fields = ('name', 'primary_member__username', 'secondary_member__username')


@admin.register(StaffShift)
class StaffShiftAdmin(admin.ModelAdmin):
    list_display = ('staff_user', 'shift_date', 'scheduled_start', 'scheduled_end', 'actual_first_in', 'actual_last_out', 'status', 'is_off_floor')
    list_filter = ('shift_date', 'status', 'is_off_floor', 'approved_leave')
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
    list_display = ('staff_user', 'month', 'base_salary', 'overtime_pay', 'pt_commissions', 'late_minutes_penalty', 'sudden_absence_penalty', 'get_net_salary', 'is_finalized')
    list_filter = ('month', 'is_finalized')
    search_fields = ('staff_user__username',)

    def get_net_salary(self, obj):
        return f"LKR {obj.net_salary:,.2f}"
    get_net_salary.short_description = 'Net Salary'
