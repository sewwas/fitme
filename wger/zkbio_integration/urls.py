from django.urls import path
from wger.zkbio_integration import views

app_name = 'zkbio_integration'

urlpatterns = [
    path('punches/', views.punches_ingest, name='punches_ingest'),
    path('pending-sync/', views.pending_sync_queue, name='pending_sync'),
    path('sync-status/', views.sync_status_callback, name='sync_status'),
    path('remote-buzzer/', views.remote_buzzer_trigger, name='remote_buzzer'),
    path('floor-status/', views.floor_status_api, name='floor_status'),
]
