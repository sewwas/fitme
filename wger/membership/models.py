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
        ('individual', 'Monthly Package'),
        ('three_months', '3 Months Package'),
        ('six_months', '6 Months Package'),
        ('couples', 'Couple Monthly Package'),
        ('family_3', '3 Persons Family Monthly Package'),
        ('student', 'Student Package'),
        ('off_peak', 'Off-Peak Package'),
        ('personal_coaching', 'Personal Coaching Package'),
    ]

    name = models.CharField(max_length=80)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, unique=True)
    price_monthly = models.DecimalField(max_digits=8, decimal_places=2, help_text="Effective / payable price")
    original_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Original price before discount")
    discount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'), help_text="Promotional discount amount")
    registration_fee = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('1000.00'), help_text="Yearly fee for new/renewing members (Rs. 0 for students)")
    duration_days = models.IntegerField(default=30)
    max_members = models.IntegerField(default=1, help_text="2 for Couples, 3 for Family plan")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    # Entry time window (e.g. Off-Peak: 09:00–17:00 only)
    allowed_entry_start = models.TimeField(
        null=True, blank=True,
        help_text="Earliest allowed entry time (leave blank for unrestricted)"
    )
    allowed_entry_end = models.TimeField(
        null=True, blank=True,
        help_text="Latest allowed entry time (leave blank for unrestricted)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['price_monthly']

    def __str__(self):
        return f"{self.name} — LKR {self.price_monthly}/mo"

    @property
    def is_student_plan(self):
        """Returns True if this plan is a student package."""
        return self.plan_type == 'student' or 'student' in (self.name or '').lower()



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
    assigned_program = models.ForeignKey(
        'GymProgram',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_members',
        help_text="Currently active gym training program assigned by coach"
    )
    join_date = models.DateField(
        null=True, blank=True,
        verbose_name="Join Date",
        help_text="Official date the member joined Fit Me"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Member: {self.user.get_full_name() or self.user.username}"

    @property
    def effective_join_date(self):
        """Returns the member's official join date, fallback to first subscription or user.date_joined."""
        if self.join_date:
            return self.join_date
        first_sub = self.user.subscriptions.order_by('start_date').first()
        if first_sub and first_sub.start_date:
            return first_sub.start_date
        if self.user and self.user.date_joined:
            return self.user.date_joined.date()
        return None


    def get_next_pin(self):
        """Auto-generate next available biometric PIN (1000–9999)."""
        last = MemberProfile.objects.filter(
            biometric_pin__isnull=False
        ).order_by('-biometric_pin').first()
        if last and last.biometric_pin:
            return str(int(last.biometric_pin) + 1)
        return '1000'

    @property
    def age(self):
        """Calculates current age from date_of_birth."""
        if not self.date_of_birth:
            return None
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @property
    def is_student_eligible(self):
        """
        Student package is strictly for students aged 18 and under.
        When reaching 19, a general package is required.
        """
        current_age = self.age
        if current_age is None:
            return None
        return current_age <= 18



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

    @property
    def linked_partners(self):
        """Returns linked secondary/partner members for multi-user subscriptions."""
        if hasattr(self, 'buddy_links'):
            return self.buddy_links.all()
        return []

    @property
    def can_add_partner(self):
        """True if plan allows multiple users and slots are still open."""
        if self.plan.max_members <= 1:
            return False
        return len(self.linked_partners) < (self.plan.max_members - 1)

    @property
    def open_slots_count(self):
        """Number of open secondary member slots left to assign."""
        if self.plan.max_members <= 1:
            return 0
        return max(0, (self.plan.max_members - 1) - len(self.linked_partners))


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
    preferred_coach = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='intake_coached_applications'
    )

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

    @property
    def calculated_age(self):
        """Calculates current age from date_of_birth, fallback to stored age."""
        if self.date_of_birth:
            today = timezone.now().date()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return self.age

    @property
    def is_student_eligible(self):
        """
        Student package is strictly for applicants aged 18 and under.
        When reaching 19, a general package is required.
        """
        current_age = self.calculated_age
        if current_age is None:
            return None
        return current_age <= 18



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


# ─────────────────────────────────────────────────────────────────────────────
# Assessment Forms (Digital versions of the physical PDF forms)
# Members fill these in; coaches review and create plans.
# ─────────────────────────────────────────────────────────────────────────────

class NutritionAssessment(models.Model):
    """
    Digital version of 'Fitness with Dhananjaya — Nutrition Assessment Form'.
    Member fills this, coach reviews and attaches a nutrition plan + notes.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('reviewed', 'Reviewed — Plan Created'),
        ('completed', 'Completed'),
    ]

    # ── Member reference ──
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='nutrition_assessments',
    )

    # ── Section 1: Basic Personal Information ──
    full_name = models.CharField(max_length=150, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        blank=True,
    )
    height_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    waist_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    emergency_contact = models.CharField(max_length=150, blank=True)
    assessment_date = models.DateField(null=True, blank=True)

    # ── Section 2: Primary Fitness / Body Goals ──
    current_weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    target_weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    goal_timeline_weeks = models.IntegerField(null=True, blank=True)
    goal_importance = models.IntegerField(null=True, blank=True, help_text="0-10 importance rating")
    # Checkboxes stored as comma-separated keys
    primary_goals = models.CharField(
        max_length=500, blank=True,
        help_text="Comma-sep: fat_loss,muscle_gain,lean_muscle,body_recomposition,weight_gain,"
                  "general_health,maintenance,strength,athletic_perf,diet_habits,blood_sugar,"
                  "cholesterol,fitness_endurance,daily_energy,other"
    )
    primary_goals_other = models.CharField(max_length=200, blank=True)

    # ── Section 3: Weight & Diet History ──
    highest_adult_weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    lowest_adult_weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    previous_diet_plan = models.BooleanField(default=False)
    previous_diet_types = models.CharField(
        max_length=500, blank=True,
        help_text="Comma-sep: calorie_restrict,intermittent_fasting,low_carb,keto,meal_replacement,"
                  "high_protein,vegetarian,low_fat,online_plan,coach_plan,self_made,other"
    )
    previous_diet_types_other = models.CharField(max_length=200, blank=True)
    diet_stop_reasons = models.CharField(
        max_length=500, blank=True,
        help_text="Comma-sep: hunger,too_restrictive,cravings,tea_sugar,meal_prep_time,"
                  "work_schedule,food_cost,cooking_difficulty,social_meals,disliked_food,"
                  "eating_out,cannot_stop_sugar,weekend_eating,slow_results,other"
    )
    diet_stop_reasons_other = models.CharField(max_length=200, blank=True)

    # ── Section 4: Daily Activity Level ──
    activity_level = models.CharField(
        max_length=20,
        choices=[
            ('sedentary', 'Sedentary (mostly sitting)'),
            ('lightly_active', 'Lightly Active'),
            ('moderately_active', 'Moderately Active'),
            ('very_active', 'Very Active'),
            ('extra_active', 'Extra Active / Heavy Labor'),
        ],
        blank=True,
    )
    work_hours_per_day = models.IntegerField(null=True, blank=True)
    sitting_hours_per_day = models.IntegerField(null=True, blank=True)
    daily_commute_minutes = models.IntegerField(null=True, blank=True)
    shift_type = models.CharField(
        max_length=15,
        choices=[('day', 'Day Shift'), ('night', 'Night Shift'), ('rotating', 'Rotating Shift'), ('none', 'None')],
        blank=True,
    )
    daily_steps = models.CharField(
        max_length=20,
        choices=[
            ('under_3000', '< 3,000'),
            ('3000_5000', '3,000 – 5,000'),
            ('5000_7500', '5,000 – 7,500'),
            ('7500_10000', '7,500 – 10,000'),
            ('over_10000', '10,000+'),
            ('unknown', 'Not sure'),
        ],
        blank=True,
    )

    # ── Section 5: Exercise / Gym History ──
    currently_exercising = models.BooleanField(default=False)
    exercise_days_per_week = models.IntegerField(null=True, blank=True)
    session_duration_minutes = models.IntegerField(null=True, blank=True)
    usual_workout_time = models.CharField(max_length=50, blank=True, help_text="e.g. Morning / Evening")

    # ── Section 6: Food Preferences ──
    dietary_preference = models.CharField(
        max_length=20,
        choices=[
            ('omnivore', 'Omnivore (Eat everything)'),
            ('vegetarian', 'Vegetarian'),
            ('vegan', 'Vegan'),
            ('pescatarian', 'Pescatarian'),
        ],
        blank=True,
    )
    disliked_foods = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    cultural_restrictions = models.TextField(blank=True)
    # Meal timing checkboxes
    meal_pattern = models.CharField(
        max_length=200, blank=True,
        help_text="Comma-sep: breakfast,mid_morning,lunch,afternoon,dinner,before_bed,post_workout,pre_workout"
    )
    meals_per_day = models.IntegerField(null=True, blank=True)

    # ── Section 7: Current Typical Day Eating ──
    typical_breakfast = models.TextField(blank=True)
    typical_lunch = models.TextField(blank=True)
    typical_dinner = models.TextField(blank=True)
    typical_snacks = models.TextField(blank=True)
    daily_water_ml = models.IntegerField(null=True, blank=True, help_text="Estimated ml/day")
    daily_tea_coffee_cups = models.IntegerField(null=True, blank=True)
    sugar_in_tea = models.BooleanField(default=False)
    alcohol_frequency = models.CharField(
        max_length=20,
        choices=[('none', 'None'), ('rare', 'Rarely'), ('weekly', 'Weekly'), ('daily', 'Daily')],
        blank=True,
    )

    # ── Section 8: Eating Habits & Challenges ──
    eats_outside_frequently = models.BooleanField(default=False)
    outside_food_frequency = models.CharField(
        max_length=20,
        choices=[('never', 'Never'), ('once_week', '1x/week'), ('2_3_week', '2-3x/week'), ('daily', 'Daily')],
        blank=True,
    )
    stress_eating = models.BooleanField(default=False)
    night_eating = models.BooleanField(default=False)
    emotional_eating = models.BooleanField(default=False)
    binge_eating = models.BooleanField(default=False)
    skip_meals_often = models.BooleanField(default=False)

    # ── Section 9: Supplement & Medication History ──
    current_supplements = models.TextField(blank=True)
    current_medications = models.TextField(blank=True)
    vitamin_d_tested = models.BooleanField(default=False)
    iron_tested = models.BooleanField(default=False)

    # ── Section 10: Medical Conditions ──
    medical_conditions = models.TextField(blank=True)
    digestive_issues = models.BooleanField(default=False)
    hormonal_issues = models.BooleanField(default=False)
    thyroid_issues = models.BooleanField(default=False)
    pcos = models.BooleanField(default=False)
    diabetes = models.BooleanField(default=False)
    blood_pressure_issues = models.BooleanField(default=False)

    # ── Section 11: Sleep & Stress ──
    sleep_hours_per_night = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    sleep_quality = models.CharField(
        max_length=15,
        choices=[('poor', 'Poor'), ('average', 'Average'), ('good', 'Good'), ('excellent', 'Excellent')],
        blank=True,
    )
    stress_level = models.IntegerField(null=True, blank=True, help_text="1-10 stress scale")
    stress_causes = models.TextField(blank=True)

    # ── Section 12: Additional Notes from Member ──
    member_notes = models.TextField(blank=True)

    # ── Review & Status ──
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reviewed_nutrition_assessments',
    )
    coach_plan_notes = models.TextField(
        blank=True,
        help_text="Coach-written personalised nutrition plan / recommendations for this member"
    )
    coach_calorie_target = models.IntegerField(null=True, blank=True)
    coach_protein_target_g = models.IntegerField(null=True, blank=True)
    coach_carbs_target_g = models.IntegerField(null=True, blank=True)
    coach_fat_target_g = models.IntegerField(null=True, blank=True)
    coach_water_target_ml = models.IntegerField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Nutrition Assessment — {self.member.get_full_name() or self.member.username} ({self.status})"


class WorkoutAssessment(models.Model):
    """
    Digital version of 'Fitness with Dhananjaya — Workout Assessment Form'.
    Member fills this, coach reviews and attaches a workout plan + notes.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('reviewed', 'Reviewed — Plan Created'),
        ('completed', 'Completed'),
    ]

    # ── Member reference ──
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='workout_assessments',
    )

    # ── Section 1: Basic Personal Information ──
    full_name = models.CharField(max_length=150, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        blank=True,
    )
    height_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    current_weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    emergency_contact = models.CharField(max_length=150, blank=True)
    assessment_date = models.DateField(null=True, blank=True)

    # ── Section 2: Primary Fitness Goals ──
    target_weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    goal_timeline_weeks = models.IntegerField(null=True, blank=True)
    primary_goals = models.CharField(
        max_length=500, blank=True,
        help_text="Comma-sep: fat_loss,muscle_gain,lean_muscle,strength,endurance,flexibility,"
                  "sports_performance,rehabilitation,general_fitness,body_recomposition,other"
    )
    primary_goals_other = models.CharField(max_length=200, blank=True)
    motivation_level = models.IntegerField(null=True, blank=True, help_text="1-10 motivation rating")

    # ── Section 3: Gym / Exercise History ──
    training_experience = models.CharField(
        max_length=20,
        choices=[
            ('none', 'No Experience'),
            ('beginner', 'Beginner (< 6 months)'),
            ('intermediate', 'Intermediate (6m – 2 years)'),
            ('advanced', 'Advanced (2+ years)'),
            ('athlete', 'Competitive Athlete'),
        ],
        blank=True,
    )
    currently_training = models.BooleanField(default=False)
    training_days_per_week = models.IntegerField(null=True, blank=True)
    session_duration_minutes = models.IntegerField(null=True, blank=True)
    preferred_training_time = models.CharField(max_length=50, blank=True)
    previous_training_types = models.CharField(
        max_length=500, blank=True,
        help_text="Comma-sep: weight_training,cardio,crossfit,yoga,pilates,martial_arts,team_sport,other"
    )
    previous_training_other = models.CharField(max_length=200, blank=True)
    longest_training_streak_months = models.IntegerField(null=True, blank=True)
    reason_stopped_training = models.TextField(blank=True)

    # ── Section 4: Physical Assessment / Current Fitness Level ──
    body_fat_pct = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    waist_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    hip_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    chest_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    bicep_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    thigh_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    # Self-assessment (1-5 scale)
    strength_self_rating = models.IntegerField(null=True, blank=True, help_text="1-5 scale")
    endurance_self_rating = models.IntegerField(null=True, blank=True, help_text="1-5 scale")
    flexibility_self_rating = models.IntegerField(null=True, blank=True, help_text="1-5 scale")
    # Functional tests (reps/seconds recorded by coach)
    pushups_reps = models.IntegerField(null=True, blank=True)
    squats_reps = models.IntegerField(null=True, blank=True)
    plank_seconds = models.IntegerField(null=True, blank=True)

    # ── Section 5: Equipment & Gym Access ──
    gym_access = models.BooleanField(default=True)
    home_equipment = models.CharField(
        max_length=500, blank=True,
        help_text="Comma-sep: dumbbells,barbell,resistance_bands,pull_up_bar,bench,cables,none"
    )
    preferred_gym_area = models.CharField(
        max_length=200, blank=True,
        help_text="Comma-sep: free_weights,machines,cardio_zone,functional_area,outdoor"
    )

    # ── Section 6: Lifestyle & Recovery ──
    sleep_hours_per_night = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    sleep_quality = models.CharField(
        max_length=15,
        choices=[('poor', 'Poor'), ('average', 'Average'), ('good', 'Good'), ('excellent', 'Excellent')],
        blank=True,
    )
    stress_level = models.IntegerField(null=True, blank=True, help_text="1-10")
    recovery_days_per_week = models.IntegerField(null=True, blank=True)
    active_rest_activities = models.TextField(blank=True)

    # ── Section 7: Injuries & Medical History ──
    current_injuries = models.TextField(blank=True)
    past_injuries = models.TextField(blank=True)
    chronic_conditions = models.TextField(blank=True)
    physical_limitations = models.TextField(blank=True)
    cleared_by_doctor = models.BooleanField(default=True)
    is_under_medication = models.BooleanField(default=False)
    medication_details = models.TextField(blank=True)

    # ── Section 8: Preferences & Constraints ──
    exercises_to_avoid = models.TextField(blank=True)
    preferred_exercises = models.TextField(blank=True)
    training_split_preference = models.CharField(
        max_length=30,
        choices=[
            ('full_body', 'Full Body'),
            ('upper_lower', 'Upper / Lower Split'),
            ('push_pull_legs', 'Push / Pull / Legs'),
            ('body_part_split', 'Body Part Split'),
            ('no_preference', 'No Preference'),
        ],
        blank=True,
    )
    cardio_preference = models.CharField(
        max_length=30,
        choices=[
            ('none', 'None'),
            ('liss', 'LISS (Low Intensity Steady State)'),
            ('hiit', 'HIIT'),
            ('moderate', 'Moderate'),
            ('no_preference', 'No Preference'),
        ],
        blank=True,
    )

    # ── Member Notes ──
    member_notes = models.TextField(blank=True)

    # ── Coach Review & Plan ──
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reviewed_workout_assessments',
    )
    # Coach-created workout plan
    coach_plan_notes = models.TextField(
        blank=True,
        help_text="Coach-written personalised workout plan / recommendations"
    )
    assigned_program = models.ForeignKey(
        'GymProgram',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assessment_assigned_members',
        help_text="Gym Program assigned based on this assessment",
    )
    coach_training_days_per_week = models.IntegerField(null=True, blank=True)
    coach_session_duration_minutes = models.IntegerField(null=True, blank=True)
    coach_cardio_recommendation = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Workout Assessment — {self.member.get_full_name() or self.member.username} ({self.status})"

