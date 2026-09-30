"""
Fit Me — Nutrition LK URL Configuration
"""
from django.urls import path
from wger.nutrition_lk import views

app_name = 'nutrition_lk'

urlpatterns = [
    path('foods/', views.food_search_api, name='food-search'),
    path('fuel/', views.daily_fuel_api, name='daily-fuel'),
]
