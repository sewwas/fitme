"""
Fit Me — Membership App
Handles membership plans, subscriptions, and member profiles.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class MembershipPlan(models.Model):
    """Configurable gym membership plans (editable by Super Admin)."""
    PLAN_TYPES = [
        ('individual', 'Individual'),
        ('couples', 'Couples / Buddy'),
        ('student', 'Student'),
        ('off_peak', 'Off-Peak'),
    ]

    name = models.CharField(max_length=80)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, unique=True)
    price_monthly = models.DecimalField(max_digits=8, decimal_places=2)
    duration_days = models.IntegerField(default=30)
    max_members = models.IntegerField(default=1, help_text="2 for Couples plan")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['price_monthly']

    def __str__(self):
        return f"{self.name} — LKR {self.price_monthly}/mo"


class MemberProfile(models.Model):
    """Extended profile for gym members (linked 1:1 to Django User)."""
    GOAL_CHOICES = [
        ('weight_loss', 'Weight Loss'),
        ('muscle_gain', 'Muscle Gain'),
        ('endurance', 'Endurance & Cardio'),
        ('general_fitness', 'General Fitness'),
        ('rehabilitation', 'Rehabilitation'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='member_profile'
    )
    biometric_pin = models.CharField(
        max_length=10, unique=True, blank=True, null=True,
        help_text="ZKBio device PIN (auto-assigned)"
    )
    phone = models.CharField(max_length=20, blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    starting_weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    primary_goal = models.CharField(max_length=30, choices=GOAL_CHOICES, default='general_fitness')
    profile_photo = models.ImageField(upload_to='members/photos/', blank=True, null=True)
    onboarding_complete = models.BooleanField(default=False)
    assigned_coach = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='coached_members'
    )
    notes = models.TextField(blank=True, help_text="Staff internal notes")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Member: {self.user.get_full_name() or self.user.username}"

    def get_next_pin(self):
        """Auto-generate next available biometric PIN (1000–9999)."""
        last = MemberProfile.objects.filter(
            biometric_pin__isnull=False
        ).order_by('-biometric_pin').first()
        if last and last.biometric_pin:
            return str(int(last.biometric_pin) + 1)
        return '1000'


class Subscription(models.Model):
    """Active or historical membership subscription for a member."""
    STATUS_CHOICES = [
        ('pending_payment', 'Pending Payment'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('suspended', 'Suspended'),
    ]
    PAYMENT_METHODS = [
        ('cash', 'Cash at Counter'),
        ('card', 'Card / POS'),
        ('bank_transfer', 'Bank Transfer'),
        ('online', 'Online Payment'),
    ]

    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    plan = models.ForeignKey(MembershipPlan, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_payment')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, blank=True)
    amount_paid = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    payment_date = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approved_subscriptions'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.member.username} — {self.plan.name} ({self.status})"

    @property
    def is_active(self):
        return (
            self.status == 'active' and
            self.start_date <= timezone.now().date() <= self.end_date
        )

    @property
    def days_remaining(self):
        if self.is_active:
            return (self.end_date - timezone.now().date()).days
        return 0


class MemberApplication(models.Model):
    """Front desk application queue — new members apply before approval."""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    # Basic info submitted during application
    full_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    date_of_birth = models.DateField(null=True, blank=True)
    desired_plan = models.ForeignKey(MembershipPlan, on_delete=models.SET_NULL, null=True)
    primary_goal = models.CharField(max_length=30, blank=True)
    health_notes = models.TextField(blank=True, help_text="Any health conditions or special notes")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reviewed_applications'
    )
    review_notes = models.TextField(blank=True)
    created_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='member_application'
    )
    applied_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.full_name} — {self.status}"


class BodyCheckIn(models.Model):
    """Monthly body measurement check-ins for morph visualizer."""
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='body_checkins'
    )
    checkin_date = models.DateField()
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    body_fat_pct = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    muscle_mass_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    waist_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    chest_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    photo_front = models.ImageField(upload_to='checkins/front/', blank=True, null=True)
    photo_side = models.ImageField(upload_to='checkins/side/', blank=True, null=True)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='recorded_checkins'
    )

    class Meta:
        ordering = ['-checkin_date']
        unique_together = ['member', 'checkin_date']

    def __str__(self):
        return f"{self.member.username} check-in on {self.checkin_date}"
