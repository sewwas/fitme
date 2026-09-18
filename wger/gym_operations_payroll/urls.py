from django.urls import path
from wger.gym_operations_payroll import views

app_name = 'gym_operations_payroll'

urlpatterns = [
    path('api/absence-alerts/', views.sudden_absence_alerts_api, name='absence_alerts_api'),
    path('api/payroll-summary/', views.payroll_summary_api, name='payroll_summary_api'),
]
