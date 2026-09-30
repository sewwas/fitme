"""
Fit Me — Habit App URL Configuration
"""
from django.urls import path
from wger.habit import views

app_name = 'habit'

urlpatterns = [
    path('streak/', views.my_streak_api, name='my-streak'),
    path('leaderboard/', views.streak_leaderboard_api, name='streak-leaderboard'),
    path('pings/', views.my_pings_api, name='my-pings'),
]
