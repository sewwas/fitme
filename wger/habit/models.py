"""
Fit Me — Habit App
Workout streaks, coach habit pings, and consecutive miss detection.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class WorkoutStreak(models.Model):
    """Tracks gym attendance streaks per member (updated on each door punch-in)."""
    member = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='workout_streak'
    )
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_checkin_date = models.DateField(null=True, blank=True)
    total_checkins = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.member.username} — 🔥 {self.current_streak}-day streak"

    def record_checkin(self):
        """Called when member punches IN. Updates streak logic."""
        today = timezone.now().date()
        if self.last_checkin_date == today:
            return  # Already checked in today

        yesterday = today - timezone.timedelta(days=1)
        if self.last_checkin_date == yesterday:
            self.current_streak += 1
        elif self.last_checkin_date is None or self.last_checkin_date < yesterday:
            self.current_streak = 1  # Streak broken or first checkin

        self.longest_streak = max(self.current_streak, self.longest_streak)
        self.last_checkin_date = today
        self.total_checkins += 1
        self.save()

    def is_at_risk(self):
        """Returns True if member hasn't checked in for 2+ days (trigger nudge)."""
        if not self.last_checkin_date:
            return False
        days_since = (timezone.now().date() - self.last_checkin_date).days
        return days_since >= 2


class HabitPing(models.Model):
    """Coach-to-member motivational messages, voice notes, and nudges."""
    PING_TYPES = [
        ('text', 'Text Message'),
        ('voice', 'Voice Note'),
        ('nudge', 'Auto Nudge (Missed Workout)'),
        ('feedback', 'Meal Feedback'),
        ('achievement', 'Achievement Badge'),
    ]

    from_coach = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_pings'
    )
    to_member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_pings'
    )
    ping_type = models.CharField(max_length=15, choices=PING_TYPES, default='text')
    message = models.TextField(blank=True)
    audio_file = models.FileField(upload_to='habit/voice_notes/', blank=True, null=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.ping_type}] {self.from_coach.username} → {self.to_member.username}"

    def mark_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
