from django.urls import path
from wger.zkbio_integration import views

app_name = 'zkbio_integration'

urlpatterns = [
    path('punches/', views.punches_ingest, name='punches_ingest'),
    path('recent-punches/', views.recent_punches_api, name='recent_punches'),
    path('pending-sync/', views.pending_sync_queue, name='pending_sync'),
    path('sync-status/', views.sync_status_callback, name='sync_status'),
    path('upload-face/', views.upload_face_api, name='upload_face'),
    path('enroll-fingerprint/', views.enroll_fingerprint_api, name='enroll_fingerprint'),
    path('command-status/<int:command_id>/', views.check_command_status_api, name='command_status'),
    path('pending-commands/', views.pending_commands_api, name='pending_commands'),
    path('update-command/', views.update_command_status_api, name='update_command'),
    path('remote-buzzer/', views.remote_buzzer_trigger, name='remote_buzzer'),
    path('floor-status/', views.floor_status_api, name='floor_status'),
]
