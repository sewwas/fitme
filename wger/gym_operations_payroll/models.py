from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone


# MembershipPlan is defined in wger.membership.models (single canonical model).
# Import it here for use in admin registrations and references within this app.
from wger.membership.models import MembershipPlan  # noqa: F401


class StaffShift(models.Model):
    """
    Staff Shift Roster & Attendance Tracking.
    Monitors shift times, punch timestamps, late arrivals, overtime, and off-floor status.
    """
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('ON_FLOOR', 'On Floor (Active)'),
        ('OFF_FLOOR', 'Off Floor — Unapproved Departure'),
        ('LEAVE', 'Approved Leave'),
        ('COMPLETED', 'Shift Completed'),
    ]

    staff_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'is_staff': True},
        related_name='staff_shifts'
    )
    shift_date = models.DateField(db_index=True)
    scheduled_start = models.TimeField()
    scheduled_end = models.TimeField()

    actual_first_in = models.DateTimeField(null=True, blank=True)
    actual_last_out = models.DateTimeField(null=True, blank=True)

    unapproved_absence_minutes = models.IntegerField(default=0)
    overtime_minutes = models.IntegerField(default=0)
    is_off_floor = models.BooleanField(default=False, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')

    approved_leave = models.BooleanField(default=False)
    leave_reason = models.TextField(blank=True)
    base_hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('500.00'))

    class Meta:
        verbose_name = 'Staff Shift'
        verbose_name_plural = 'Staff Shifts'
        ordering = ['-shift_date', 'scheduled_start']

    def __str__(self):
        return f"{self.staff_user.username} - {self.shift_date} ({self.scheduled_start} - {self.scheduled_end}) [{self.status}]"

    def calculate_late_minutes(self):
        """Computes minutes late based on scheduled start and actual first punch."""
        if not self.actual_first_in:
            return 0
        scheduled_dt = timezone.make_aware(
            timezone.datetime.combine(self.shift_date, self.scheduled_start)
        )
        if self.actual_first_in > scheduled_dt:
            delta = self.actual_first_in - scheduled_dt
            return int(delta.total_seconds() / 60)
        return 0


class SuddenAbsenceAlert(models.Model):
    """
    Triggered when an on-shift staff member punches out during working hours
    without an approved leave request for >20 minutes. Alerts the Super Admin.
    """
    shift = models.ForeignKey(
        StaffShift,
        on_delete=models.CASCADE,
        related_name='absence_alerts'
    )
    staff_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='staff_absence_alerts'
    )
    exit_time = models.DateTimeField(default=timezone.now)
    minutes_off_floor = models.IntegerField(default=20)
    is_resolved = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Sudden Absence Alert'
        verbose_name_plural = 'Sudden Absence Alerts'
        ordering = ['-created_at']

    def __str__(self):
        return f"CRITICAL: {self.staff_user.username} departed floor @ {self.exit_time:%H:%M} ({self.minutes_off_floor}m off floor)"


class PayrollLedger(models.Model):
    """
    Automated Monthly Net Salary Ledger:
    Net = Base_Salary + Overtime_Pay + PT_Commissions - (Late_Minutes_Penalty + Sudden_Absence_Penalty)
    """
    staff_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payroll_ledgers'
    )
    month = models.DateField(help_text="First day of payroll month, e.g. 2026-09-01")
    base_salary = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    overtime_pay = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    pt_commissions = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Personal Training session commissions")
    late_minutes_penalty = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    sudden_absence_penalty = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    is_finalized = models.BooleanField(default=False)
    finalized_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Payroll Ledger'
        verbose_name_plural = 'Payroll Ledgers'
        unique_together = ['staff_user', 'month']
        ordering = ['-month', 'staff_user']

    def __str__(self):
        return f"Payroll: {self.staff_user.username} — {self.month:%B %Y} (Net: LKR {self.net_salary:,.2f})"

    @property
    def net_salary(self):
        """
        Net = Base_Salary + Overtime_Pay + PT_Commissions - (Late_Minutes_Penalty + Sudden_Absence_Penalty)
        """
        earnings = self.base_salary + self.overtime_pay + self.pt_commissions
        deductions = self.late_minutes_penalty + self.sudden_absence_penalty
        return max(Decimal('0.00'), earnings - deductions)


class PaymentReceipt(models.Model):
    """
    Fit Me POS & Membership 80mm Thermal Receipt / Invoice Record.
    Auto-generates sequential receipt number: FM-RCP-YYYY-XXXX.
    """
    receipt_number = models.CharField(max_length=30, unique=True, db_index=True)
    subscription = models.ForeignKey(
        'membership.Subscription',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='receipts'
    )
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payment_receipts'
    )
    plan_name = models.CharField(max_length=100)
    duration_days = models.IntegerField(default=30)
    validity_start = models.DateField()
    validity_end = models.DateField()
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    payment_method = models.CharField(max_length=30, default='cash')
    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='issued_receipts'
    )
    member_pin = models.CharField(max_length=20, blank=True, help_text="Assigned hardware turnstile PIN")
    notes = models.TextField(blank=True)
    issued_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Payment Receipt'
        verbose_name_plural = 'Payment Receipts'
        ordering = ['-issued_at']

    def __str__(self):
        return f"{self.receipt_number} — {self.member.username} (LKR {self.amount_paid})"

    @classmethod
    def generate_next_receipt_number(cls):
        year = timezone.now().year
        prefix = f"FM-RCP-{year}-"
        last = cls.objects.filter(receipt_number__startswith=prefix).order_by('-receipt_number').first()
        if last:
            try:
                seq = int(last.receipt_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"


class BuddyMembership(models.Model):
    """
    Links two members under a single Couples / Buddy membership billing subscription.
    Both members receive independent biometric hardware PINs for turnstile access.
    """
    primary_member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='primary_buddy_memberships'
    )
    partner_member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='partner_buddy_memberships'
    )
    subscription = models.ForeignKey(
        'membership.Subscription',
        on_delete=models.CASCADE,
        related_name='buddy_links'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Buddy Membership'
        verbose_name_plural = 'Buddy Memberships'
        unique_together = ['primary_member', 'partner_member']

    def __str__(self):
        return f"Buddy: {self.primary_member.username} & {self.partner_member.username}"

