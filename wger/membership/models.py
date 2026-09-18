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
    # Official Registration Form Extensions
    nic_passport = models.CharField(max_length=30, blank=True, verbose_name="NIC / Passport No")
    address = models.TextField(blank=True)
    gender = models.CharField(max_length=15, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], blank=True)
    blood_group = models.CharField(max_length=10, blank=True)
    emergency_relationship = models.CharField(max_length=50, blank=True)
    medical_conditions = models.TextField(blank=True)
    under_medication = models.TextField(blank=True)
    personal_trainer_needed = models.BooleanField(default=False)
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
    """
    Official Fit Me Fitness Club — Membership Registration Intake Queue.
    Matches the official physical 2-page registration form across all 8 sections.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    # Section 1: Personal Information
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=15, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], default='male')
    nic_passport = models.CharField(max_length=30, blank=True, verbose_name="NIC / Passport No")

    # Section 2: Emergency Contact Details
    emergency_name = models.CharField(max_length=100, blank=True)
    emergency_relationship = models.CharField(max_length=50, blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)

    # Section 3: Payment Plan
    desired_plan = models.ForeignKey(MembershipPlan, on_delete=models.SET_NULL, null=True, blank=True)
    plan_duration = models.CharField(max_length=20, choices=[
        ('monthly', 'Monthly'),
        ('3_months', '3 Months'),
        ('6_months', '6 Months'),
        ('annual', 'Annual'),
    ], default='monthly')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    # Section 4: Fitness Goals
    primary_goal = models.CharField(max_length=50, blank=True)
    fitness_goals_other = models.CharField(max_length=150, blank=True)

    # Section 5: Medical Information
    has_medical_conditions = models.BooleanField(default=False)
    medical_condition_details = models.TextField(blank=True)
    is_under_medication = models.BooleanField(default=False)
    medication_details = models.TextField(blank=True)
    blood_group = models.CharField(max_length=10, blank=True)

    # Section 6: Trainer Requirement
    personal_trainer_needed = models.BooleanField(default=False)

    # Section 7: Payment Details
    admission_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    payment_method = models.CharField(max_length=20, choices=[
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('online', 'Online'),
    ], default='cash')

    # Section 8: Terms & Conditions
    agreed_to_rules = models.BooleanField(default=True)

    # Review Status
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
        return f"{self.full_name} ({self.nic_passport}) — {self.status}"


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


class GymProgram(models.Model):
    """Catalog of Training Programs available at Fit Me."""
    CATEGORY_CHOICES = [
        ('hypertrophy', 'Hypertrophy & Muscle Build'),
        ('fat_loss', 'Fat Loss & Shred'),
        ('strength', 'Power & Strength'),
        ('hiit', 'HIIT & Conditioning'),
        ('calisthenics', 'Bodyweight & Calisthenics'),
        ('personal_training', '1-on-1 Personal Training'),
    ]
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced / Athlete'),
    ]

    title = models.CharField(max_length=120)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='hypertrophy')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='intermediate')
    duration_weeks = models.IntegerField(default=8)
    sessions_per_week = models.IntegerField(default=4)
    description = models.TextField()
    key_features = models.TextField(help_text="Comma-separated or newline list of features")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"


class CoachProfile(models.Model):
    """Trainer & Coach Details for public directory and coach portal."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='coach_profile'
    )
    title = models.CharField(max_length=100, default="Certified Strength & Conditioning Coach")
    specialties = models.CharField(max_length=200, help_text="e.g. Hypertrophy, Sri Lankan Nutrition, Powerlifting")
    certifications = models.CharField(max_length=250, blank=True)
    years_experience = models.IntegerField(default=5)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='coaches/avatars/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Coach: {self.user.get_full_name() or self.user.username} — {self.title}"


class ContactInquiry(models.Model):
    """Inquiries submitted via the public website contact form."""
    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=25)
    subject = models.CharField(max_length=150, default="Membership / Training Inquiry")
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Inquiry from {self.name} ({self.phone}) - {self.subject}"


class Testimonial(models.Model):
    """Member transformation stories showcased on the public website and admin."""
    member_name = models.CharField(max_length=100)
    program_name = models.CharField(max_length=100, default="Fit Me 12-Week Transformation")
    quote = models.TextField()
    weight_loss_kg = models.DecimalField(max_digits=5, decimal_places=1, default=Decimal('0.0'))
    muscle_gain_kg = models.DecimalField(max_digits=5, decimal_places=1, default=Decimal('0.0'))
    duration_months = models.IntegerField(default=3)
    before_photo = models.ImageField(upload_to='testimonials/before/', blank=True, null=True)
    after_photo = models.ImageField(upload_to='testimonials/after/', blank=True, null=True)
    is_featured = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.member_name} ({self.program_name})"


class Announcement(models.Model):
    """Gym-wide notices and broadcast messages."""
    PRIORITY_CHOICES = [
        ('info', 'Information'),
        ('warning', 'Operational Notice'),
        ('critical', 'Urgent / Important'),
    ]
    title = models.CharField(max_length=150)
    content = models.TextField()
    priority = models.CharField(max_length=15, choices=PRIORITY_CHOICES, default='info')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.priority.upper()}] {self.title}"


class MemberWorkoutLog(models.Model):
    """Real-time workout logging for member and coach review."""
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='fitme_workout_logs'
    )
    workout_name = models.CharField(max_length=100, default="Push Day")
    exercise_name = models.CharField(max_length=100)
    sets_completed = models.IntegerField(default=3)
    reps = models.IntegerField(default=10)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    notes = models.CharField(max_length=200, blank=True)
    logged_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-logged_at']

    def __str__(self):
        return f"{self.member.username} - {self.exercise_name}: {self.sets_completed}x{self.reps} @ {self.weight_kg}kg"


class MemberMeasurement(models.Model):
    """Body circumference and metric log for progress tracking."""
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='fitme_measurements'
    )
    date = models.DateField(default=timezone.now)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2)
    chest_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    waist_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    biceps_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    thighs_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    body_fat_pct = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.member.username} metrics on {self.date}: {self.weight_kg}kg"

