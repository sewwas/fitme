"""
Fit Me — Habit & Streak Tracking API Views
"""
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from wger.habit.models import WorkoutStreak, HabitPing


@login_required
def my_streak_api(request):
    """Returns the authenticated member's streak stats."""
    streak, _ = WorkoutStreak.objects.get_or_create(member=request.user)
    return JsonResponse({
        'status': 'success',
        'current_streak': streak.current_streak,
        'longest_streak': streak.longest_streak,
        'total_checkins': streak.total_checkins,
        'last_checkin': streak.last_checkin_date.isoformat() if streak.last_checkin_date else None,
        'is_at_risk': streak.is_at_risk(),
    })


@login_required
def streak_leaderboard_api(request):
    """Returns top gym member workout streaks for community motivation."""
    top_streaks = WorkoutStreak.objects.select_related('member').order_by('-current_streak')[:10]
    leaderboard = []
    for s in top_streaks:
        leaderboard.append({
            'username': s.member.username,
            'name': s.member.get_full_name() or s.member.username,
            'current_streak': s.current_streak,
            'longest_streak': s.longest_streak,
            'total_checkins': s.total_checkins,
        })
    return JsonResponse({'status': 'success', 'leaderboard': leaderboard})


@login_required
def my_pings_api(request):
    """Returns coach motivational pings for the logged-in member."""
    pings = HabitPing.objects.filter(to_member=request.user).select_related('from_coach').order_by('-created_at')[:20]
    results = []
    for p in pings:
        results.append({
            'id': p.id,
            'coach_name': p.from_coach.get_full_name() or p.from_coach.username,
            'ping_type': p.ping_type,
            'ping_type_display': p.get_ping_type_display(),
            'message': p.message,
            'is_read': p.is_read,
            'created_at': p.created_at.strftime('%Y-%m-%d %H:%M'),
        })
    return JsonResponse({'status': 'success', 'pings': results})
