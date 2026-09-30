"""
Fit Me — Nutrition LK API Views
Endpoints for Sri Lankan food database lookup and member meal/hydration logging.
"""
import json
from decimal import Decimal
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q

from wger.nutrition_lk.models import LocalFood, MealLog, MealLogEntry, DailyFuelTarget, WaterLog


@login_required
def food_search_api(request):
    """Search Sri Lankan localized food database."""
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()

    foods = LocalFood.objects.all()
    if query:
        foods = foods.filter(
            Q(name_en__icontains=query) | Q(name_si__icontains=query)
        )
    if category:
        foods = foods.filter(category=category)

    results = []
    for f in foods[:50]:
        results.append({
            'id': f.id,
            'name_en': f.name_en,
            'name_si': f.name_si,
            'category': f.category,
            'category_display': f.get_category_display(),
            'calories_per_100g': float(f.calories_per_100g),
            'protein_g': float(f.protein_g),
            'carbs_g': float(f.carbs_g),
            'fat_g': float(f.fat_g),
            'fiber_g': float(f.fiber_g),
            'default_serving_g': f.default_serving_g,
        })

    return JsonResponse({'status': 'success', 'count': len(results), 'foods': results})


@login_required
def daily_fuel_api(request):
    """Returns the authenticated member's daily intake progress vs targets."""
    target, _ = DailyFuelTarget.objects.get_or_create(member=request.user)
    today = timezone.now().date()
    progress = target.daily_progress(date=today)

    recent_meals = []
    for m in MealLog.objects.filter(member=request.user, logged_at__date=today).order_by('-logged_at'):
        recent_meals.append({
            'id': m.id,
            'meal_type': m.meal_type,
            'meal_type_display': m.get_meal_type_display(),
            'logged_at': m.logged_at.strftime('%H:%M'),
            'calories': float(m.total_calories),
            'protein_g': float(m.total_protein_g),
            'carbs_g': float(m.total_carbs_g),
            'fat_g': float(m.total_fat_g),
            'notes': m.notes,
        })

    return JsonResponse({
        'status': 'success',
        'progress': progress,
        'today_meals': recent_meals,
    })
