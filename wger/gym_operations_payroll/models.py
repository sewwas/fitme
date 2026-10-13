from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone


# MembershipPlan is defined in wger.membership.models (single canonical model).
# Import it here for use in admin registrations and references within this app.
from wger.membership.models import MembershipPlan  # noqa: F401


class ShiftTemplate(models.Model):
    """
    Standard reusable shift templates for gym operations.
    e.g. Morning Shift, Evening Shift, Full Day Weekend, Split Shift.
    """
    name = models.CharField(max_length=60, unique=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    color_hex = models.CharField(max_length=10, default='#10B981')
    description = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Shift Template'
        verbose_name_plural = 'Shift Templates'
        ordering = ['start_time', 'name']

    def __str__(self):
        return f"{self.name} ({self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')})"


class StaffWorkSchedule(models.Model):
    """
    Master Employment Schedule & Contract Hours for Staff.
    Defines default working days (Mon-Sun), shift times, standard salary, and EPF/ETF enrollment.
    """
    staff_user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'is_staff': True},
        related_name='work_schedule'
    )
    default_base_salary = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('75000.00'))
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('500.00'))
    epf_etf_eligible = models.BooleanField(default=True, help_text="Sri Lankan EPF (8% employee, 12% employer) & ETF (3% employer)")
    epf_number = models.CharField(max_length=30, blank=True, help_text="Employee EPF Registration Number")

    # Standard Gym Shift Presets per Day
    DEFAULT_SHIFT_CHOICES = [
        ('FULL_SPLIT', 'Split Shift (05:00-12:00 & 15:00-21:00)'),
        ('MORNING', 'Morning Shift (05:00-12:00)'),
        ('EVENING', 'Evening Shift (15:00-21:00)'),
        ('REST_DAY', 'Scheduled Rest Day'),
    ]
    monday_shift_type = models.CharField(max_length=20, choices=DEFAULT_SHIFT_CHOICES, default='FULL_SPLIT')
    tuesday_shift_type = models.CharField(max_length=20, choices=DEFAULT_SHIFT_CHOICES, default='FULL_SPLIT')
    wednesday_shift_type = models.CharField(max_length=20, choices=DEFAULT_SHIFT_CHOICES, default='FULL_SPLIT')
    thursday_shift_type = models.CharField(max_length=20, choices=DEFAULT_SHIFT_CHOICES, default='FULL_SPLIT')
    friday_shift_type = models.CharField(max_length=20, choices=DEFAULT_SHIFT_CHOICES, default='FULL_SPLIT')
    saturday_shift_type = models.CharField(max_length=20, choices=DEFAULT_SHIFT_CHOICES, default='FULL_SPLIT')
    sunday_shift_type = models.CharField(max_length=20, choices=DEFAULT_SHIFT_CHOICES, default='REST_DAY')

    # Working Day Toggles & Daily Shift Times (for backwards compatibility & custom overrides)
    monday_active = models.BooleanField(default=True)
    monday_start = models.TimeField(default='05:00')
    monday_end = models.TimeField(default='21:00')

    tuesday_active = models.BooleanField(default=True)
    tuesday_start = models.TimeField(default='05:00')
    tuesday_end = models.TimeField(default='21:00')

    wednesday_active = models.BooleanField(default=True)
    wednesday_start = models.TimeField(default='05:00')
    wednesday_end = models.TimeField(default='21:00')

    thursday_active = models.BooleanField(default=True)
    thursday_start = models.TimeField(default='05:00')
    thursday_end = models.TimeField(default='21:00')

    friday_active = models.BooleanField(default=True)
    friday_start = models.TimeField(default='05:00')
    friday_end = models.TimeField(default='21:00')

    saturday_active = models.BooleanField(default=True)
    saturday_start = models.TimeField(default='05:00')
    saturday_end = models.TimeField(default='21:00')

    sunday_active = models.BooleanField(default=False)
    sunday_start = models.TimeField(default='08:00')
    sunday_end = models.TimeField(default='14:00')

    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Staff Work Schedule'
        verbose_name_plural = 'Staff Work Schedules'

    def __str__(self):
        return f"Schedule: {self.staff_user.username} (Base: LKR {self.default_base_salary:,.2f})"

    def get_schedule_for_weekday(self, weekday_int):
        """
        weekday_int: 0=Monday, ..., 6=Sunday.
        Returns: (is_active, shift_type, default_start, default_end)
        """
        mapping = {
            0: (self.monday_active, self.monday_shift_type, self.monday_start, self.monday_end),
            1: (self.tuesday_active, self.tuesday_shift_type, self.tuesday_start, self.tuesday_end),
            2: (self.wednesday_active, self.wednesday_shift_type, self.wednesday_start, self.wednesday_end),
            3: (self.thursday_active, self.thursday_shift_type, self.thursday_start, self.thursday_end),
            4: (self.friday_active, self.friday_shift_type, self.friday_start, self.friday_end),
            5: (self.saturday_active, self.saturday_shift_type, self.saturday_start, self.saturday_end),
            6: (self.sunday_active, self.sunday_shift_type, self.sunday_start, self.sunday_end),
        }
        active, s_type, s_start, s_end = mapping.get(weekday_int, (False, 'REST_DAY', None, None))
        if s_type == 'REST_DAY':
            active = False
        return (active, s_type, s_start, s_end)


class StaffShift(models.Model):
    """
    Staff Shift Roster & Attendance Tracking.
    Supports Fit Me split shift model (Morning 05:00-12:00 and Evening 15:00-21:00).
    Monitors shift times, session punch timestamps, late arrivals, overtime, and off-floor status.
    """
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('ON_FLOOR', 'On Floor (Active)'),
        ('OFF_FLOOR', 'Off Floor — Unapproved Departure'),
        ('LEAVE', 'Approved Leave'),
        ('REST_DAY', 'Scheduled Rest Day'),
        ('COMPLETED', 'Shift Completed'),
    ]

    SHIFT_TYPE_CHOICES = [
        ('FULL_SPLIT', 'Split Shift (05:00-12:00 & 15:00-21:00)'),
        ('MORNING', 'Morning Shift (05:00-12:00)'),
        ('EVENING', 'Evening Shift (15:00-21:00)'),
        ('CUSTOM', 'Custom Hours'),
        ('REST_DAY', 'Scheduled Rest Day'),
    ]

    staff_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'is_staff': True},
        related_name='staff_shifts'
    )
    shift_template = models.ForeignKey(
        ShiftTemplate,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='shifts'
    )
    shift_date = models.DateField(db_index=True)
    shift_type = models.CharField(
        max_length=20,
        choices=SHIFT_TYPE_CHOICES,
        default='FULL_SPLIT',
        db_index=True,
        help_text="Standard gym shift type (Split 5-12 & 3-9, Morning 5-12, Evening 3-9)"
    )
    scheduled_start = models.TimeField(default='05:00')
    scheduled_end = models.TimeField(default='21:00')

    # Granular punch timestamps for split shifts (Morning & Evening sessions)
    morning_in = models.DateTimeField(null=True, blank=True, help_text="Morning check-in punch (05:00 session)")
    morning_out = models.DateTimeField(null=True, blank=True, help_text="Morning departure punch (12:00 closure)")
    evening_in = models.DateTimeField(null=True, blank=True, help_text="Evening check-in punch (15:00 session)")
    evening_out = models.DateTimeField(null=True, blank=True, help_text="Evening departure punch (21:00 closure)")

    # Legacy & aggregate timestamps (synced with morning/evening punches)
    actual_first_in = models.DateTimeField(null=True, blank=True)
    actual_last_out = models.DateTimeField(null=True, blank=True)

    unapproved_absence_minutes = models.IntegerField(default=0)
    overtime_minutes = models.IntegerField(default=0)
    is_off_floor = models.BooleanField(default=False, db_index=True)
    is_rest_day = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')

    approved_leave = models.BooleanField(default=False)
    leave_reason = models.TextField(blank=True)
    base_hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('500.00'))

    class Meta:
        verbose_name = 'Staff Shift'
        verbose_name_plural = 'Staff Shifts'
        ordering = ['-shift_date', 'scheduled_start']

    def __str__(self):
        return f"{self.staff_user.username} - {self.shift_date} ({self.get_shift_type_display()}) [{self.status}]"

    def save(self, *args, **kwargs):
        # Sync aggregate punches
        if self.morning_in and not self.actual_first_in:
            self.actual_first_in = self.morning_in
        elif not self.actual_first_in and self.evening_in:
            self.actual_first_in = self.evening_in

        if self.evening_out:
            self.actual_last_out = self.evening_out
        elif self.morning_out and not self.actual_last_out:
            self.actual_last_out = self.morning_out

        if self.shift_type == 'REST_DAY':
            self.is_rest_day = True
            self.status = 'REST_DAY'
        super().save(*args, **kwargs)

    def calculate_late_minutes(self):
        """Computes minutes late based on scheduled morning and evening session starts."""
        if self.is_rest_day or self.approved_leave:
            return 0
        total_late = 0

        # Morning session late check (scheduled 05:00)
        if self.shift_type in ['FULL_SPLIT', 'MORNING']:
            sched_m_time = timezone.datetime.strptime('05:00', '%H:%M').time()
            sched_m_dt = timezone.make_aware(timezone.datetime.combine(self.shift_date, sched_m_time))
            m_punch = self.morning_in or (self.actual_first_in if self.actual_first_in and self.actual_first_in.time() < timezone.datetime.strptime('13:00', '%H:%M').time() else None)
            if m_punch and m_punch > sched_m_dt:
                delta = m_punch - sched_m_dt
                total_late += int(delta.total_seconds() / 60)

        # Evening session late check (scheduled 15:00)
        if self.shift_type in ['FULL_SPLIT', 'EVENING']:
            sched_e_time = timezone.datetime.strptime('15:00', '%H:%M').time()
            sched_e_dt = timezone.make_aware(timezone.datetime.combine(self.shift_date, sched_e_time))
            e_punch = self.evening_in or (self.actual_first_in if self.actual_first_in and self.actual_first_in.time() >= timezone.datetime.strptime('13:00', '%H:%M').time() else None)
            if e_punch and e_punch > sched_e_dt:
                delta = e_punch - sched_e_dt
                total_late += int(delta.total_seconds() / 60)

        # Fallback for CUSTOM shifts
        if self.shift_type == 'CUSTOM' and self.actual_first_in:
            scheduled_dt = timezone.make_aware(timezone.datetime.combine(self.shift_date, self.scheduled_start))
            if self.actual_first_in > scheduled_dt:
                delta = self.actual_first_in - scheduled_dt
                total_late += int(delta.total_seconds() / 60)

        return total_late

    def calculate_overtime_minutes(self):
        """Computes overtime minutes worked beyond 12:00 (morning) or 21:00 (evening)."""
        if self.is_rest_day or self.approved_leave:
            return 0
        total_ot = 0
        if self.shift_type in ['FULL_SPLIT', 'MORNING'] and self.morning_out:
            sched_m_end = timezone.make_aware(timezone.datetime.combine(self.shift_date, timezone.datetime.strptime('12:00', '%H:%M').time()))
            if self.morning_out > sched_m_end:
                total_ot += int((self.morning_out - sched_m_end).total_seconds() / 60)
        if self.shift_type in ['FULL_SPLIT', 'EVENING'] and self.evening_out:
            sched_e_end = timezone.make_aware(timezone.datetime.combine(self.shift_date, timezone.datetime.strptime('21:00', '%H:%M').time()))
            if self.evening_out > sched_e_end:
                total_ot += int((self.evening_out - sched_e_end).total_seconds() / 60)
        return max(total_ot, self.overtime_minutes or 0)


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


class StaffSalaryAdvance(models.Model):
    """
    Staff Salary Advances & Till Loans.
    Mid-month cash taken from the front desk till or company bank transfer,
    automatically deducted during monthly payroll ledger consolidation.
    """
    PAYOUT_METHODS = [
        ('cash', 'Cash from Till'),
        ('bank_transfer', 'Bank Transfer'),
    ]

    staff_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'is_staff': True},
        related_name='salary_advances'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    request_date = models.DateField(default=timezone.now)
    payout_method = models.CharField(max_length=20, choices=PAYOUT_METHODS, default='cash')
    reason = models.CharField(max_length=255, blank=True)
    receipt_voucher = models.CharField(max_length=40, unique=True, db_index=True, blank=True)
    is_deducted = models.BooleanField(default=False, db_index=True)
    ledger = models.ForeignKey(
        'PayrollLedger',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='advances_included'
    )
    opex_expense = models.ForeignKey(
        'ClubExpense',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='linked_advances'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approved_advances'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Staff Salary Advance'
        verbose_name_plural = 'Staff Salary Advances'
        ordering = ['-request_date', '-created_at']

    def __str__(self):
        return f"Advance: {self.staff_user.username} - LKR {self.amount:,.2f} on {self.request_date} ({'Deducted' if self.is_deducted else 'Pending'})"

    def save(self, *args, **kwargs):
        if not self.receipt_voucher:
            year = timezone.now().year
            prefix = f"FM-ADV-{year}-"
            last = StaffSalaryAdvance.objects.filter(receipt_voucher__startswith=prefix).order_by('-id').first()
            if last and last.receipt_voucher:
                try:
                    seq = int(last.receipt_voucher.split('-')[-1]) + 1
                except Exception:
                    seq = 1
            else:
                seq = 1
            self.receipt_voucher = f"{prefix}{seq:04d}"
        super().save(*args, **kwargs)


class PayrollLedger(models.Model):
    """
    Automated Monthly Net Salary Ledger:
    Net = (Base_Salary + Overtime_Pay + PT_Commissions) - (Late_Penalty + Absence_Penalty + EPF_8% + Salary_Advances)
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

    # Sri Lankan Statutory Deductions & Contributions
    epf_employee_8 = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="8% Employee EPF Contribution (Deducted)")
    epf_employer_12 = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="12% Employer EPF Contribution (Gym Cost)")
    etf_employer_3 = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="3% Employer ETF Contribution (Gym Cost)")

    # Till Cash Advances & Mid-Month Loan Deductions
    salary_advance_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Till Cash Advances Deducted")

    is_finalized = models.BooleanField(default=False)
    finalized_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Payroll Ledger'
        verbose_name_plural = 'Payroll Ledgers'
        unique_together = ['staff_user', 'month']
        ordering = ['-month', 'staff_user']

    def save(self, *args, **kwargs):
        if self.month:
            self.month = self.month.replace(day=1)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Payroll: {self.staff_user.username} — {self.month:%B %Y} (Net: LKR {self.net_salary:,.2f})"

    @property
    def gross_earnings(self):
        return self.base_salary + self.overtime_pay + self.pt_commissions

    @property
    def total_deductions(self):
        return (
            self.late_minutes_penalty
            + self.sudden_absence_penalty
            + self.epf_employee_8
            + self.salary_advance_deduction
        )

    @property
    def net_salary(self):
        """
        Net = Gross Earnings - Total Deductions
        """
        return max(Decimal('0.00'), self.gross_earnings - self.total_deductions)

    @property
    def gym_total_cost(self):
        """
        Total employer operational liability including Employer EPF (12%) and ETF (3%).
        """
        return self.gross_earnings + self.epf_employer_12 + self.etf_employer_3


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
    package_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Base membership plan fee")
    coaching_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Personal coaching fee / add-on")
    annual_fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Annual registration / renewal fee")
    coach_name = models.CharField(max_length=100, blank=True, default='', help_text="Assigned personal coach if applicable")
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

    def get_line_items(self):
        """
        Returns structured list of billing line items for 80mm thermal receipt & invoices.
        Handles both new granularly recorded receipts and existing historical receipts.
        """
        items = []

        has_granular = (
            (self.package_amount and self.package_amount > 0) or
            (self.coaching_amount and self.coaching_amount > 0) or
            (self.annual_fee_amount and self.annual_fee_amount > 0)
        )

        val_start_str = self.validity_start.strftime('%d/%m/%Y') if self.validity_start else ''
        val_end_str = self.validity_end.strftime('%d/%m/%Y') if self.validity_end else ''
        val_range = f"{val_start_str} - {val_end_str}" if val_start_str and val_end_str else ''

        if has_granular:
            if self.package_amount and self.package_amount > 0:
                detail_str = f"{self.duration_days} Days Access"
                if val_range:
                    detail_str += f" ({val_range})"
                items.append({
                    'name': self.plan_name,
                    'detail': detail_str,
                    'amount': self.package_amount,
                    'badge': 'Package',
                })
            elif self.coaching_amount > 0 and self.package_amount == 0:
                # Coaching-only payment (monthly pass already active)
                detail_str = f"Pass valid until {val_end_str} (Fee Waived: LKR 0.00)" if val_end_str else "Fee Waived (Active Pass)"
                items.append({
                    'name': f"{self.plan_name} (Active Pass)",
                    'detail': detail_str,
                    'amount': Decimal('0.00'),
                    'badge': 'Active Pass',
                })

            if self.coaching_amount and self.coaching_amount > 0:
                coach_label = f"Assigned Coach: {self.coach_name}" if self.coach_name else "1-on-1 Dedicated Trainer"
                items.append({
                    'name': 'Personal Coaching (1-on-1)',
                    'detail': coach_label,
                    'amount': self.coaching_amount,
                    'badge': 'Coaching',
                })

            if self.annual_fee_amount and self.annual_fee_amount > 0:
                items.append({
                    'name': 'Annual Registration / Renewal Fee',
                    'detail': f"Registration Period: {self.issued_at.year}",
                    'amount': self.annual_fee_amount,
                    'badge': 'Annual Fee',
                })
        else:
            # Parse from notes or intelligent fallback for historical receipts
            import re
            notes_str = self.notes or ''
            annual_fee = Decimal('0.00')
            coaching_fee = Decimal('0.00')

            ann_match = re.search(r'Annual Registration/Renewal Fee:\s*LKR\s*([\d,]+(?:\.\d+)?)', notes_str, re.IGNORECASE)
            if ann_match:
                try:
                    annual_fee = Decimal(ann_match.group(1).replace(',', ''))
                except Exception:
                    annual_fee = Decimal('0.00')
            elif 'annual' in notes_str.lower() and '1000' in notes_str:
                annual_fee = Decimal('1000.00')

            coach_label = "1-on-1 Dedicated Trainer"
            c_match = re.search(r'Coach\s*\(([^)]+)\)', notes_str)
            if c_match:
                coach_label = f"Assigned Coach: {c_match.group(1)}"

            if 'Personal Coaching' in notes_str or 'Coaching' in self.plan_name:
                if 'Coaching Add-on' in notes_str or 'Personal Coaching Split' in notes_str:
                    coaching_fee = Decimal('7000.00')
                elif 'coaching' in self.plan_name.lower():
                    coaching_fee = Decimal('7000.00')

            total = self.amount_paid or Decimal('0.00')
            base_pkg = total - annual_fee - coaching_fee

            detail_str = f"{self.duration_days} Days Access"
            if val_range:
                detail_str += f" ({val_range})"

            if base_pkg > Decimal('0.00'):
                items.append({
                    'name': self.plan_name,
                    'detail': detail_str,
                    'amount': base_pkg,
                    'badge': 'Package',
                })
            elif coaching_fee == Decimal('0.00') and (total - annual_fee) > Decimal('0.00'):
                items.append({
                    'name': self.plan_name,
                    'detail': detail_str,
                    'amount': total - annual_fee,
                    'badge': 'Package',
                })
            elif coaching_fee > 0 and ('Coaching Add-on' in notes_str or 'Monthly Active' in notes_str):
                items.append({
                    'name': f"{self.plan_name} (Active Pass)",
                    'detail': f"Pass valid until {val_end_str} (Fee Waived: LKR 0.00)" if val_end_str else "Fee Waived (Active Pass)",
                    'amount': Decimal('0.00'),
                    'badge': 'Active Pass',
                })

            if coaching_fee > 0:
                items.append({
                    'name': 'Personal Coaching (1-on-1)',
                    'detail': coach_label,
                    'amount': coaching_fee,
                    'badge': 'Coaching',
                })

            if annual_fee > 0:
                items.append({
                    'name': 'Annual Registration / Renewal Fee',
                    'detail': f"Registration Period: {self.issued_at.year}",
                    'amount': annual_fee,
                    'badge': 'Annual Fee',
                })

        if not items:
            items.append({
                'name': self.plan_name or 'Gym Membership Package',
                'detail': f"{self.duration_days} Days Access ({val_range})",
                'amount': self.amount_paid,
                'badge': 'Package',
            })

        return items

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


class ClubExpense(models.Model):
    """
    Operating Expenses (OPEX) for Pitigala Gym Facility.
    Tracks utility bills (CEB, Water), building rent, equipment repairs, staff payroll, supplements stock, and cleaning.
    """
    CATEGORY_CHOICES = [
        ('rent', 'Facility & Building Rent'),
        ('electricity', 'Electricity (CEB)'),
        ('water', 'Water Utility'),
        ('maintenance', 'Equipment Maintenance & Repairs'),
        ('staff_salary', 'Staff & Coach Payroll / Commissions'),
        ('supplements_stock', 'POS Bar & Supplement Inventory'),
        ('cleaning', 'Hygiene & Cleaning Supplies'),
        ('internet', 'Internet & Security CCTV'),
        ('marketing', 'Marketing, Social & Print Ads'),
        ('other', 'Other Operational Expenses'),
    ]

    title = models.CharField(max_length=150)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='other')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    expense_date = models.DateField(default=timezone.now)
    payment_method = models.CharField(max_length=30, default='cash', choices=[
        ('cash', 'Cash from Till'),
        ('bank_transfer', 'Bank Transfer / Cheque'),
        ('card', 'Company Debit/Credit Card'),
    ])
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='recorded_expenses'
    )
    receipt_ref = models.CharField(max_length=80, blank=True, help_text="Bill / Invoice / Receipt number")
    receipt_image = models.FileField(
        upload_to='expenses/receipts/%Y/%m/',
        null=True, blank=True,
        help_text="Uploaded photo or PDF scan of the physical bill/receipt"
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Club Expense'
        verbose_name_plural = 'Club Expenses'
        ordering = ['-expense_date', '-created_at']

    def __str__(self):
        return f"{self.title} — LKR {self.amount} ({self.get_category_display()})"

