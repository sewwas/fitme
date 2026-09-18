from django.contrib import admin
from wger.zkbio_integration.models import BiometricProfile, DoorAccessLog


@admin.register(BiometricProfile)
class BiometricProfileAdmin(admin.ModelAdmin):
    list_display = ('zk_pin', 'user', 'sync_status', 'disabled', 'face_enrolled', 'fingerprint_enrolled', 'last_sync_time')
    list_filter = ('sync_status', 'disabled', 'face_enrolled', 'fingerprint_enrolled')
    search_fields = ('zk_pin', 'user__username', 'user__first_name', 'user__last_name', 'card_number')
    actions = ['force_sync_to_hardware', 'revoke_door_access', 'restore_door_access']

    def force_sync_to_hardware(self, request, queryset):
        queryset.update(sync_status='PENDING')
        self.message_user(request, f"{queryset.count()} biometric profiles queued for hardware sync.")
    force_sync_to_hardware.short_description = "Queue for ZKBio hardware sync"

    def revoke_door_access(self, request, queryset):
        queryset.update(disabled=True, sync_status='PENDING')
        self.message_user(request, f"Revoked door access for {queryset.count()} profiles.")
    revoke_door_access.short_description = "Revoke turnstile door permissions"

    def restore_door_access(self, request, queryset):
        queryset.update(disabled=False, sync_status='PENDING')
        self.message_user(request, f"Restored door access for {queryset.count()} profiles.")
    restore_door_access.short_description = "Restore turnstile door permissions"


@admin.register(DoorAccessLog)
class DoorAccessLogAdmin(admin.ModelAdmin):
    list_display = ('punch_time', 'user', 'zk_pin', 'event_type', 'device_ip', 'terminal_name')
    list_filter = ('event_type', 'punch_time', 'device_ip')
    search_fields = ('zk_pin', 'user__username', 'device_ip')
    readonly_fields = ('punch_time', 'user', 'zk_pin', 'event_type', 'device_ip', 'terminal_name', 'raw_payload', 'created_at')
