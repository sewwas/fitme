from django.db import models
from django.conf import settings
from django.utils import timezone


class BiometricProfile(models.Model):
    """
    Maps Wger User / UserProfile to ZKTeco Biometric Turnstile Controller hardware context.
    Controller IP: 192.168.1.23, ZKBio CVAccess service: localhost:8098
    """
    SYNC_STATUS_CHOICES = [
        ('PENDING', 'Pending Sync'),
        ('SYNCED', 'Synced with Hardware'),
        ('FAILED', 'Hardware Sync Failed'),
        ('REVOKED', 'Revoked / Disabled'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='biometric_profile'
    )
    zk_pin = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text="Unique ZKTeco hardware PIN"
    )
    card_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="RFID / Proximity card number"
    )
    face_enrolled = models.BooleanField(
        default=False,
        help_text="Face template enrolled on terminal"
    )
    fingerprint_enrolled = models.BooleanField(
        default=False,
        help_text="Fingerprint template enrolled"
    )
    door_group_id = models.IntegerField(
        default=1,
        help_text="ZKBio access level / door group ID"
    )
    sync_status = models.CharField(
        max_length=20,
        choices=SYNC_STATUS_CHOICES,
        default='PENDING',
        db_index=True
    )
    disabled = models.BooleanField(
        default=False,
        help_text="Hardware door permission revoked if subscription expires or user suspended"
    )
    liveu_id = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        db_index=True,
        help_text="LiveU Cloud MongoDB _id for cloud-managed hardware sync"
    )
    last_sync_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Biometric Profile'
        verbose_name_plural = 'Biometric Profiles'
        ordering = ['zk_pin']

    def __str__(self):
        status = "DISABLED" if self.disabled else self.sync_status
        return f"{self.user.username} (PIN: {self.zk_pin}) — [{status}]"

    @property
    def user_profile(self):
        """Helper to access core UserProfile if present."""
        return getattr(self.user, 'userprofile', None)


class DoorAccessLog(models.Model):
    """
    Real-time log of turnstile door punch events received from local bridge daemon.
    Enforces anti-passback cooldown (60 seconds) and powers live gym floor tracking.
    """
    EVENT_CHOICES = [
        ('ENTRY', 'Entry Granted'),
        ('EXIT', 'Exit Granted'),
        ('DENIED', 'Access Denied'),
        ('ANTI_PASSBACK', 'Anti-Passback Blocked'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='door_access_logs'
    )
    zk_pin = models.CharField(max_length=20, db_index=True, blank=True)
    punch_time = models.DateTimeField(default=timezone.now, db_index=True)
    event_type = models.CharField(max_length=20, choices=EVENT_CHOICES, db_index=True)
    verify_mode = models.CharField(
        max_length=20,
        default='FACE_ID',
        choices=[
            ('FACE_ID', 'Face Recognition'),
            ('FINGERPRINT', 'Fingerprint'),
            ('BUZZER', 'Manual Override'),
            ('CARD', 'RFID Card'),
        ]
    )
    device_ip = models.GenericIPAddressField(default='192.168.1.23')
    terminal_name = models.CharField(max_length=100, default='MAIN_TURNSTILE')
    liveu_attendance_id = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        unique=True,
        db_index=True,
        help_text="LiveU attendance record _id"
    )
    raw_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Door Access Log'
        verbose_name_plural = 'Door Access Logs'
        ordering = ['-punch_time']

    def __str__(self):
        username = self.user.username if self.user else f"PIN:{self.zk_pin}"
        return f"{username} - {self.event_type} ({self.verify_mode}) at {self.punch_time:%Y-%m-%d %H:%M:%S}"


class BiometricCommand(models.Model):
    """
    Commands queued from the Fit Me cloud/dashboard to the local ZKBio bridge daemon
    (e.g., initiating 3-tap fingerprint enrollment on turnstile, pushing face photos, revoking access).
    """
    COMMAND_CHOICES = [
        ('ENROLL_FP', 'Enroll Fingerprint on Turnstile Terminal'),
        ('UPLOAD_FACE', 'Upload Face Template / Photo to Terminal'),
        ('REMOTE_BUZZ', 'Pulse Turnstile Relay Open (5s)'),
        ('REVOKE_USER', 'Revoke Access & Delete from Terminal'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending Execution'),
        ('IN_PROGRESS', 'Executing on Device'),
        ('COMPLETED', 'Successfully Completed'),
        ('FAILED', 'Execution Failed'),
    ]

    command_type = models.CharField(max_length=30, choices=COMMAND_CHOICES)
    zk_pin = models.CharField(max_length=20, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='biometric_commands'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    device_ip = models.GenericIPAddressField(default='192.168.1.23')
    payload = models.JSONField(default=dict, blank=True)
    result_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    executed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Biometric Command'
        verbose_name_plural = 'Biometric Commands'
        ordering = ['-created_at']

    def __str__(self):
        return f"Cmd {self.command_type} for PIN {self.zk_pin} [{self.status}]"

