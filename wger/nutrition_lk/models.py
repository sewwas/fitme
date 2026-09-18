"""
Fit Me — Nutrition LK App
Sri Lankan localized food database and meal logging engine.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class LocalFood(models.Model):
    """Sri Lankan localized food nutrition database."""
    CATEGORY_CHOICES = [
        ('rice_grains', 'Rice & Grains'),
        ('curry_stew', 'Curries & Stews'),
        ('protein', 'Protein / Meat / Fish / Eggs'),
        ('vegetables', 'Vegetables'),
        ('fruits', 'Fruits'),
        ('dairy', 'Dairy & Alternatives'),
        ('snacks', 'Snacks & Street Food'),
        ('beverages', 'Beverages'),
        ('supplements', 'Supplements & Powders'),
    ]

    name_en = models.CharField(max_length=120, help_text="English name")
    name_si = models.CharField(max_length=120, blank=True, help_text="Sinhala name (transliterated)")
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='rice_grains')
    # Macros per 100g
    calories_per_100g = models.DecimalField(max_digits=6, decimal_places=1)
    protein_g = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    carbs_g = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    fat_g = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    fiber_g = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    # Default serving size for quick logging
    default_serving_g = models.IntegerField(default=100)
    is_verified = models.BooleanField(default=True)

    class Meta:
        ordering = ['category', 'name_en']

    def __str__(self):
        return f"{self.name_en} ({self.calories_per_100g} kcal/100g)"

    def macros_for_serving(self, grams=None):
        """Returns macro dict for a given gram amount."""
        g = grams or self.default_serving_g
        ratio = g / 100
        return {
            'calories': float(self.calories_per_100g * ratio),
            'protein_g': float(self.protein_g * ratio),
            'carbs_g': float(self.carbs_g * ratio),
            'fat_g': float(self.fat_g * ratio),
            'fiber_g': float(self.fiber_g * ratio),
        }


class MealLogEntry(models.Model):
    """Individual food item within a meal log."""
    food = models.ForeignKey(LocalFood, on_delete=models.CASCADE)
    quantity_g = models.IntegerField(default=100)

    @property
    def macros(self):
        return self.food.macros_for_serving(self.quantity_g)

    def __str__(self):
        return f"{self.quantity_g}g of {self.food.name_en}"


class MealLog(models.Model):
    """Meal photo + food entries logged by a member."""
    MEAL_TYPES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
        ('pre_workout', 'Pre-Workout'),
        ('post_workout', 'Post-Workout'),
    ]

    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='meal_logs'
    )
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPES, default='lunch')
    logged_at = models.DateTimeField(default=timezone.now)
    photo = models.ImageField(upload_to='meals/photos/', blank=True, null=True)
    entries = models.ManyToManyField(MealLogEntry, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    coach_reviewed = models.BooleanField(default=False)
    coach_feedback = models.TextField(blank=True)

    # Cached totals (computed on save)
    total_calories = models.DecimalField(max_digits=7, decimal_places=1, default=0)
    total_protein_g = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    total_carbs_g = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    total_fat_g = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    class Meta:
        ordering = ['-logged_at']

    def __str__(self):
        return f"{self.member.username} — {self.meal_type} at {self.logged_at:%Y-%m-%d %H:%M}"

    def recalculate_totals(self):
        """Recalculate and cache macro totals from all entries."""
        totals = {'calories': 0, 'protein_g': 0, 'carbs_g': 0, 'fat_g': 0}
        for entry in self.entries.all():
            m = entry.macros
            for k in totals:
                totals[k] += m[k]
        self.total_calories = round(totals['calories'], 1)
        self.total_protein_g = round(totals['protein_g'], 2)
        self.total_carbs_g = round(totals['carbs_g'], 2)
        self.total_fat_g = round(totals['fat_g'], 2)
        self.save(update_fields=['total_calories', 'total_protein_g', 'total_carbs_g', 'total_fat_g'])


class DailyFuelTarget(models.Model):
    """Coach-set daily macro targets for a member."""
    member = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='fuel_target'
    )
    set_by_coach = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='set_targets'
    )
    target_calories = models.IntegerField(default=2000)
    target_protein_g = models.IntegerField(default=150)
    target_carbs_g = models.IntegerField(default=200)
    target_fat_g = models.IntegerField(default=65)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.member.username} fuel targets: {self.target_calories} kcal"

    def daily_progress(self, date=None):
        """Returns today's intake vs targets as percentages."""
        target_date = date or timezone.now().date()
        logs = MealLog.objects.filter(
            member=self.member,
            logged_at__date=target_date
        )
        consumed = {
            'calories': sum(float(l.total_calories) for l in logs),
            'protein_g': sum(float(l.total_protein_g) for l in logs),
            'carbs_g': sum(float(l.total_carbs_g) for l in logs),
            'fat_g': sum(float(l.total_fat_g) for l in logs),
        }
        return {
            'consumed': consumed,
            'targets': {
                'calories': self.target_calories,
                'protein_g': self.target_protein_g,
                'carbs_g': self.target_carbs_g,
                'fat_g': self.target_fat_g,
            },
            'pct_calories': min(100, round(consumed['calories'] / self.target_calories * 100)),
            'pct_protein': min(100, round(consumed['protein_g'] / self.target_protein_g * 100)),
            'pct_carbs': min(100, round(consumed['carbs_g'] / self.target_carbs_g * 100)),
            'pct_fat': min(100, round(consumed['fat_g'] / self.target_fat_g * 100)),
        }
