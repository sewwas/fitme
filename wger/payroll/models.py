from django.db import models
from django.conf import settings
from django.utils import timezone


class StaffShift(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'is_staff': True})
    date = models.DateField()
    expected_start = models.TimeField()
    expected_end = models.TimeField()
    base_hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.user.username} shift on {self.date}"


class Attendance(models.Model):
    shift = models.OneToOneField(StaffShift, on_delete=models.CASCADE, related_name='attendance')
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    late_minutes = models.IntegerField(default=0)
    unapproved_absence_minutes = models.IntegerField(default=0)
    overtime_minutes = models.IntegerField(default=0)
    is_off_floor = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    def calculate_deductions(self):
        """Hook into door punch logs to compute late + absence deductions."""
        hourly_rate = float(self.shift.base_hourly_rate)
        late_deduction = (self.late_minutes / 60) * hourly_rate
        absence_deduction = (self.unapproved_absence_minutes / 60) * hourly_rate
        return late_deduction + absence_deduction


class SuddenAbsenceAlert(models.Model):
    """Raised when a staff member exits mid-shift without approval."""
    STATUS_CHOICES = [
        ('open', 'Open — Not Returned'),
        ('returned', 'Returned'),
        ('approved', 'Approved Leave'),
        ('penalised', 'Penalised'),
    ]
    staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='absence_alerts')
    shift = models.ForeignKey(StaffShift, on_delete=models.CASCADE, related_name='absence_alerts', null=True, blank=True)
    flagged_at = models.DateTimeField(default=timezone.now)
    returned_at = models.DateTimeField(null=True, blank=True)
    absence_minutes = models.IntegerField(default=0)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='open')
    admin_note = models.TextField(blank=True)
    notified_admin = models.BooleanField(default=False)

    class Meta:
        ordering = ['-flagged_at']

    def __str__(self):
        return f"Absence alert: {self.staff.username} @ {self.flagged_at:%Y-%m-%d %H:%M}"

    def duration_minutes(self):
        if self.returned_at:
            delta = self.returned_at - self.flagged_at
            return int(delta.total_seconds() / 60)
        elapsed = timezone.now() - self.flagged_at
        return int(elapsed.total_seconds() / 60)


class Payslip(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    month = models.DateField()  # Store the first day of the month
    base_pay = models.DecimalField(max_digits=10, decimal_places=2)
    overtime_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    commissions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    penalty_minutes = models.IntegerField(default=0)
    generated_at = models.DateTimeField(auto_now_add=True)
    pdf_path = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ['user', 'month']
        ordering = ['-month']

    @property
    def net_salary(self):
        return (self.base_pay + self.overtime_pay + self.commissions) - self.deductions

    def __str__(self):
        return f"Payslip: {self.user.username} — {self.month:%B %Y}"

