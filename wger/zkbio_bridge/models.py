from django.db import models
from django.conf import settings

class AccessState(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='zkbio_access')
    is_synced = models.BooleanField(default=False)
    pin = models.CharField(max_length=10, unique=True)
    last_sync_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - Synced: {self.is_synced}"

class DoorPunch(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='door_punches')
    punch_time = models.DateTimeField()
    terminal_id = models.CharField(max_length=50, default="MAIN_GATE")
    direction = models.CharField(max_length=10, choices=[('IN', 'In'), ('OUT', 'Out')], default='IN')
    
    def __str__(self):
        return f"{self.user.username} punched {self.direction} at {self.punch_time}"
