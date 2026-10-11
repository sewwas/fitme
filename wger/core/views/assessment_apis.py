"""
Fit Me — Assessment Form API Views
Members fill the digital assessment forms; coaches review and attach personalised plans.
"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone

from wger.core.views.fitme_dashboards import role_required


# ─── Helper functions ─────────────────────────────────────────────────────────

def _make_helpers(data):
    """Return (str_fn, int_fn, dec_fn, bool_fn, list_fn) helpers for a data dict."""
    def _str(key, default=''):
        return str(data.get(key, default)).strip()

    def _int(key):
        try:
            return int(data.get(key)) if data.get(key) not in (None, '', 'null') else None
        except (ValueError, TypeError):
            return None

    def _dec(key):
        try:
            from decimal import Decimal
            return Decimal(str(data.get(key))) if data.get(key) not in (None, '', 'null') else None
        except Exception:
            return None

    def _bool(key):
        v = data.get(key)
        if isinstance(v, bool):
            return v
        return str(v).lower() in ('true', '1', 'yes', 'on')

    def _list(key):
        v = data.get(key)
        if isinstance(v, list):
            return ','.join(str(x) for x in v)
        return str(v).strip() if v else ''

    return _str, _int, _dec, _bool, _list


def _parse_data(request):
    import json
    try:
        return json.loads(request.body.decode('utf-8'))
    except Exception:
        return request.POST.dict()


def _resolve_target_user(request, data):
    """If a coach passes member_id, resolve to that user; else use request.user."""
    target_user = request.user
    member_id = data.get('member_id')
    if member_id and request.user.groups.filter(
        name__in=['coach', 'gym_trainer', 'gym_manager', 'general_gym_manager']
    ).exists():
        from django.contrib.auth import get_user_model
        User = get_user_model()
        target_user = User.objects.filter(id=member_id).first() or request.user
    return target_user


def _get_registration_profile_defaults(user):
    """
    Extract personal, contact, and emergency info already collected during membership registration
    so members never have to re-enter this same data in their assessment forms.
    """
    from wger.membership.models import MemberProfile, MemberApplication
    from datetime import date
    profile = MemberProfile.objects.filter(user=user).first()
    app = MemberApplication.objects.filter(email=user.email).order_by('-applied_at').first()

    full_name = user.get_full_name() or (app.full_name if app else '') or user.username
    email = user.email or (app.email if app else '')
    phone = (profile.phone if profile else '') or (app.phone if app else '')

    dob = None
    if profile and profile.date_of_birth:
        dob = profile.date_of_birth
    elif app and app.date_of_birth:
        dob = app.date_of_birth

    age = None
    if dob:
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    elif app and app.age:
        age = app.age

    gender = (profile.gender if profile and profile.gender else '') or (app.gender if app else '')

    # Emergency Contact
    em_name = (profile.emergency_contact_name if profile else '') or (app.emergency_name if app else '')
    em_rel = (profile.emergency_relationship if profile else '') or (app.emergency_relationship if app else '')
    em_phone = (profile.emergency_contact_phone if profile else '') or (app.emergency_phone if app else '')

    em_parts = []
    if em_name:
        em_parts.append(em_name)
    if em_rel:
        em_parts.append(f"({em_rel})")
    if em_phone:
        em_parts.append(f"— {em_phone}")
    emergency_contact = " ".join(em_parts)

    height_cm = float(profile.height_cm) if (profile and profile.height_cm) else None
    starting_weight_kg = float(profile.starting_weight_kg) if (profile and profile.starting_weight_kg) else None

    medical_conditions = (profile.medical_conditions if profile else '') or (app.medical_condition_details if app else '')
    under_medication = (profile.under_medication if profile else '') or (app.medication_details if app else '')

    return {
        'full_name': full_name,
        'email': email,
        'phone': phone,
        'date_of_birth': dob.isoformat() if dob else '',
        'age': age,
        'gender': gender,
        'emergency_contact': emergency_contact,
        'emergency_name': em_name,
        'emergency_relationship': em_rel,
        'emergency_phone': em_phone,
        'height_cm': height_cm,
        'starting_weight_kg': starting_weight_kg,
        'medical_conditions': medical_conditions,
        'under_medication': under_medication,
    }


# ─── Member: Submit Nutrition Assessment ─────────────────────────────────────

@login_required
@role_required('member', 'super_admin', 'coach', 'manager', 'front_desk')
def submit_nutrition_assessment_api(request):
    """Member submits (or updates) their Nutrition Assessment Form."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    data = _parse_data(request)
    target_user = _resolve_target_user(request, data)
    _str, _int, _dec, _bool, _list = _make_helpers(data)
    defaults = _get_registration_profile_defaults(target_user)

    from decimal import Decimal
    from wger.membership.models import NutritionAssessment
    assessment = NutritionAssessment.objects.filter(member=target_user, status='pending').first()
    if not assessment:
        assessment = NutritionAssessment(member=target_user)

    # Section 1 – Basic Personal Info (Auto-populated from registration profile if empty)
    assessment.full_name = _str('full_name') or defaults['full_name']
    dob_val = data.get('date_of_birth') or defaults['date_of_birth']
    if dob_val:
        try:
            from datetime import date
            assessment.date_of_birth = date.fromisoformat(str(dob_val))
        except Exception:
            pass
    assessment.age = _int('age') or defaults['age']
    assessment.gender = _str('gender') or defaults['gender']
    assessment.height_cm = _dec('height_cm') or (Decimal(str(defaults['height_cm'])) if defaults['height_cm'] else None)
    assessment.waist_cm = _dec('waist_cm')
    assessment.phone = _str('phone') or defaults['phone']
    assessment.email = _str('email') or defaults['email']
    assessment.occupation = _str('occupation')
    assessment.emergency_contact = _str('emergency_contact') or defaults['emergency_contact']
    if data.get('assessment_date'):
        try:
            from datetime import date
            assessment.assessment_date = date.fromisoformat(str(data['assessment_date']))
        except Exception:
            pass
    elif not assessment.assessment_date:
        assessment.assessment_date = timezone.now().date()

    # Section 2 – Goals
    assessment.current_weight_kg = _dec('current_weight_kg')
    assessment.target_weight_kg = _dec('target_weight_kg')
    assessment.goal_timeline_weeks = _int('goal_timeline_weeks')
    assessment.goal_importance = _int('goal_importance')
    assessment.primary_goals = _list('primary_goals')
    assessment.primary_goals_other = _str('primary_goals_other')

    # Section 3 – Weight & Diet History
    assessment.highest_adult_weight_kg = _dec('highest_adult_weight_kg')
    assessment.lowest_adult_weight_kg = _dec('lowest_adult_weight_kg')
    assessment.previous_diet_plan = _bool('previous_diet_plan')
    assessment.previous_diet_types = _list('previous_diet_types')
    assessment.previous_diet_types_other = _str('previous_diet_types_other')
    assessment.diet_stop_reasons = _list('diet_stop_reasons')
    assessment.diet_stop_reasons_other = _str('diet_stop_reasons_other')

    # Section 4 – Daily Activity
    assessment.activity_level = _str('activity_level')
    assessment.work_hours_per_day = _int('work_hours_per_day')
    assessment.sitting_hours_per_day = _int('sitting_hours_per_day')
    assessment.daily_commute_minutes = _int('daily_commute_minutes')
    assessment.shift_type = _str('shift_type')
    assessment.daily_steps = _str('daily_steps')

    # Section 5 – Exercise History
    assessment.currently_exercising = _bool('currently_exercising')
    assessment.exercise_days_per_week = _int('exercise_days_per_week')
    assessment.session_duration_minutes = _int('session_duration_minutes')
    assessment.usual_workout_time = _str('usual_workout_time')

    # Section 6 – Food Preferences
    assessment.dietary_preference = _str('dietary_preference')
    assessment.disliked_foods = _str('disliked_foods')
    assessment.allergies = _str('allergies')
    assessment.cultural_restrictions = _str('cultural_restrictions')
    assessment.meal_pattern = _list('meal_pattern')
    assessment.meals_per_day = _int('meals_per_day')

    # Section 7 – Typical Day Eating
    assessment.typical_breakfast = _str('typical_breakfast')
    assessment.typical_lunch = _str('typical_lunch')
    assessment.typical_dinner = _str('typical_dinner')
    assessment.typical_snacks = _str('typical_snacks')
    assessment.daily_water_ml = _int('daily_water_ml')
    assessment.daily_tea_coffee_cups = _int('daily_tea_coffee_cups')
    assessment.sugar_in_tea = _bool('sugar_in_tea')
    assessment.alcohol_frequency = _str('alcohol_frequency')

    # Section 8 – Eating Habits
    assessment.eats_outside_frequently = _bool('eats_outside_frequently')
    assessment.outside_food_frequency = _str('outside_food_frequency')
    assessment.stress_eating = _bool('stress_eating')
    assessment.night_eating = _bool('night_eating')
    assessment.emotional_eating = _bool('emotional_eating')
    assessment.binge_eating = _bool('binge_eating')
    assessment.skip_meals_often = _bool('skip_meals_often')

    # Section 9 – Supplements & Meds
    assessment.current_supplements = _str('current_supplements')
    assessment.current_medications = _str('current_medications')
    assessment.vitamin_d_tested = _bool('vitamin_d_tested')
    assessment.iron_tested = _bool('iron_tested')

    # Section 10 – Medical
    assessment.medical_conditions = _str('medical_conditions')
    assessment.digestive_issues = _bool('digestive_issues')
    assessment.hormonal_issues = _bool('hormonal_issues')
    assessment.thyroid_issues = _bool('thyroid_issues')
    assessment.pcos = _bool('pcos')
    assessment.diabetes = _bool('diabetes')
    assessment.blood_pressure_issues = _bool('blood_pressure_issues')

    # Section 11 – Sleep & Stress
    assessment.sleep_hours_per_night = _dec('sleep_hours_per_night')
    assessment.sleep_quality = _str('sleep_quality')
    assessment.stress_level = _int('stress_level')
    assessment.stress_causes = _str('stress_causes')

    # Section 12 – Notes
    assessment.member_notes = _str('member_notes')

    assessment.save()
    return JsonResponse({
        'success': True,
        'assessment_id': assessment.id,
        'message': 'Nutrition assessment saved! Your coach will review it shortly.',
    })


# ─── Member: Submit Workout Assessment ───────────────────────────────────────

@login_required
@role_required('member', 'super_admin', 'coach', 'manager', 'front_desk')
def submit_workout_assessment_api(request):
    """Member submits (or updates) their Workout Assessment Form."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    data = _parse_data(request)
    target_user = _resolve_target_user(request, data)
    _str, _int, _dec, _bool, _list = _make_helpers(data)

    from decimal import Decimal
    from wger.membership.models import WorkoutAssessment
    defaults = _get_registration_profile_defaults(target_user)
    assessment = WorkoutAssessment.objects.filter(member=target_user, status='pending').first()
    if not assessment:
        assessment = WorkoutAssessment(member=target_user)

    # Section 1 – Basic Personal Info (Auto-populated from registration profile if empty)
    assessment.full_name = _str('full_name') or defaults['full_name']
    dob_val = data.get('date_of_birth') or defaults['date_of_birth']
    if dob_val:
        try:
            from datetime import date
            assessment.date_of_birth = date.fromisoformat(str(dob_val))
        except Exception:
            pass
    assessment.age = _int('age') or defaults['age']
    assessment.gender = _str('gender') or defaults['gender']
    assessment.height_cm = _dec('height_cm') or (Decimal(str(defaults['height_cm'])) if defaults['height_cm'] else None)
    assessment.current_weight_kg = _dec('current_weight_kg') or (Decimal(str(defaults['starting_weight_kg'])) if defaults['starting_weight_kg'] else None)
    assessment.phone = _str('phone') or defaults['phone']
    assessment.email = _str('email') or defaults['email']
    assessment.occupation = _str('occupation')
    assessment.emergency_contact = _str('emergency_contact') or defaults['emergency_contact']
    if data.get('assessment_date'):
        try:
            from datetime import date
            assessment.assessment_date = date.fromisoformat(str(data['assessment_date']))
        except Exception:
            pass
    elif not assessment.assessment_date:
        assessment.assessment_date = timezone.now().date()

    # Section 2
    assessment.target_weight_kg = _dec('target_weight_kg')
    assessment.goal_timeline_weeks = _int('goal_timeline_weeks')
    assessment.primary_goals = _list('primary_goals')
    assessment.primary_goals_other = _str('primary_goals_other')
    assessment.motivation_level = _int('motivation_level')

    # Section 3
    assessment.training_experience = _str('training_experience')
    assessment.currently_training = _bool('currently_training')
    assessment.training_days_per_week = _int('training_days_per_week')
    assessment.session_duration_minutes = _int('session_duration_minutes')
    assessment.preferred_training_time = _str('preferred_training_time')
    assessment.previous_training_types = _list('previous_training_types')
    assessment.previous_training_other = _str('previous_training_other')
    assessment.longest_training_streak_months = _int('longest_training_streak_months')
    assessment.reason_stopped_training = _str('reason_stopped_training')

    # Section 4
    assessment.body_fat_pct = _dec('body_fat_pct')
    assessment.waist_cm = _dec('waist_cm')
    assessment.hip_cm = _dec('hip_cm')
    assessment.chest_cm = _dec('chest_cm')
    assessment.bicep_cm = _dec('bicep_cm')
    assessment.thigh_cm = _dec('thigh_cm')
    assessment.strength_self_rating = _int('strength_self_rating')
    assessment.endurance_self_rating = _int('endurance_self_rating')
    assessment.flexibility_self_rating = _int('flexibility_self_rating')
    assessment.pushups_reps = _int('pushups_reps')
    assessment.squats_reps = _int('squats_reps')
    assessment.plank_seconds = _int('plank_seconds')

    # Section 5
    assessment.gym_access = _bool('gym_access')
    assessment.home_equipment = _list('home_equipment')
    assessment.preferred_gym_area = _list('preferred_gym_area')

    # Section 6
    assessment.sleep_hours_per_night = _dec('sleep_hours_per_night')
    assessment.sleep_quality = _str('sleep_quality')
    assessment.stress_level = _int('stress_level')
    assessment.recovery_days_per_week = _int('recovery_days_per_week')
    assessment.active_rest_activities = _str('active_rest_activities')

    # Section 7
    assessment.current_injuries = _str('current_injuries')
    assessment.past_injuries = _str('past_injuries')
    assessment.chronic_conditions = _str('chronic_conditions')
    assessment.physical_limitations = _str('physical_limitations')
    assessment.cleared_by_doctor = _bool('cleared_by_doctor')
    assessment.is_under_medication = _bool('is_under_medication')
    assessment.medication_details = _str('medication_details')

    # Section 8
    assessment.exercises_to_avoid = _str('exercises_to_avoid')
    assessment.preferred_exercises = _str('preferred_exercises')
    assessment.training_split_preference = _str('training_split_preference')
    assessment.cardio_preference = _str('cardio_preference')
    assessment.member_notes = _str('member_notes')

    assessment.save()
    return JsonResponse({
        'success': True,
        'assessment_id': assessment.id,
        'message': 'Workout assessment saved! Your coach will review it shortly.',
    })


# ─── Coach: Review Nutrition Assessment + Attach Plan ────────────────────────

@login_required
@role_required('coach', 'super_admin', 'manager')
def coach_review_nutrition_assessment_api(request, assessment_id):
    """Coach reviews a nutrition assessment and attaches a personalised plan."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    data = _parse_data(request)
    _, _int, _, _, _ = _make_helpers(data)

    from wger.membership.models import NutritionAssessment
    assessment = NutritionAssessment.objects.filter(id=assessment_id).first()
    if not assessment:
        return JsonResponse({'error': 'Assessment not found'}, status=404)

    assessment.coach_plan_notes = str(data.get('coach_plan_notes', '')).strip()
    assessment.coach_calorie_target = _int('coach_calorie_target')
    assessment.coach_protein_target_g = _int('coach_protein_target_g')
    assessment.coach_carbs_target_g = _int('coach_carbs_target_g')
    assessment.coach_fat_target_g = _int('coach_fat_target_g')
    assessment.coach_water_target_ml = _int('coach_water_target_ml')
    assessment.status = 'reviewed'
    assessment.reviewed_by = request.user
    assessment.reviewed_at = timezone.now()
    assessment.save()

    # Sync targets to DailyFuelTarget if numbers are set
    if any([assessment.coach_calorie_target, assessment.coach_protein_target_g]):
        try:
            from wger.nutrition_lk.models import DailyFuelTarget
            defaults = {}
            mapping = {
                'target_calories': assessment.coach_calorie_target,
                'target_protein_g': assessment.coach_protein_target_g,
                'target_carbs_g': assessment.coach_carbs_target_g,
                'target_fat_g': assessment.coach_fat_target_g,
                'target_water_ml': assessment.coach_water_target_ml,
            }
            defaults = {k: v for k, v in mapping.items() if v is not None}
            target, _ = DailyFuelTarget.objects.get_or_create(member=assessment.member, defaults=defaults)
            for k, v in defaults.items():
                setattr(target, k, v)
            target.save()
        except Exception:
            pass

    member_name = assessment.member.get_full_name() or assessment.member.username
    return JsonResponse({
        'success': True,
        'message': f'Nutrition plan saved for {member_name}!',
        'assessment_id': assessment.id,
        'status': assessment.status,
    })


# ─── Coach: Review Workout Assessment + Attach Plan ──────────────────────────

@login_required
@role_required('coach', 'super_admin', 'manager')
def coach_review_workout_assessment_api(request, assessment_id):
    """Coach reviews a workout assessment and attaches a personalised training plan."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    data = _parse_data(request)
    _, _int, _, _, _ = _make_helpers(data)

    from wger.membership.models import WorkoutAssessment, GymProgram
    assessment = WorkoutAssessment.objects.filter(id=assessment_id).first()
    if not assessment:
        return JsonResponse({'error': 'Assessment not found'}, status=404)

    assessment.coach_plan_notes = str(data.get('coach_plan_notes', '')).strip()
    assessment.coach_training_days_per_week = _int('coach_training_days_per_week')
    assessment.coach_session_duration_minutes = _int('coach_session_duration_minutes')
    assessment.coach_cardio_recommendation = str(data.get('coach_cardio_recommendation', '')).strip()

    program_id = _int('assigned_program_id')
    if program_id:
        program = GymProgram.objects.filter(id=program_id).first()
        if program:
            assessment.assigned_program = program
            # Also update member profile
            try:
                from wger.membership.models import MemberProfile
                profile, _ = MemberProfile.objects.get_or_create(user=assessment.member)
                profile.assigned_program = program
                profile.save(update_fields=['assigned_program'])
            except Exception:
                pass

    assessment.status = 'reviewed'
    assessment.reviewed_by = request.user
    assessment.reviewed_at = timezone.now()
    assessment.save()

    member_name = assessment.member.get_full_name() or assessment.member.username
    return JsonResponse({
        'success': True,
        'message': f'Workout plan saved for {member_name}!',
        'assessment_id': assessment.id,
        'status': assessment.status,
    })


# ─── Coach: List Pending Assessments ─────────────────────────────────────────

@login_required
@role_required('coach', 'super_admin', 'manager')
def list_pending_assessments_api(request):
    """Returns all pending assessments for the coach's members (or all if manager/admin)."""
    from wger.membership.models import NutritionAssessment, WorkoutAssessment, MemberProfile

    if request.user.is_superuser or request.user.groups.filter(
        name__in=['gym_manager', 'general_gym_manager']
    ).exists():
        member_ids = None
    else:
        member_ids = list(
            MemberProfile.objects.filter(assigned_coach=request.user).values_list('user_id', flat=True)
        )
        if not member_ids:
            member_ids = None  # fallback: show all pending

    nut_qs = NutritionAssessment.objects.filter(status='pending')
    wrk_qs = WorkoutAssessment.objects.filter(status='pending')
    if member_ids is not None:
        nut_qs = nut_qs.filter(member_id__in=member_ids)
        wrk_qs = wrk_qs.filter(member_id__in=member_ids)

    nut_qs = nut_qs.select_related('member').order_by('-submitted_at')[:50]
    wrk_qs = wrk_qs.select_related('member').order_by('-submitted_at')[:50]

    return JsonResponse({
        'success': True,
        'nutrition': [
            {
                'id': a.id,
                'member_id': a.member_id,
                'member_name': a.member.get_full_name() or a.member.username,
                'submitted_at': a.submitted_at.isoformat(),
                'primary_goals': a.primary_goals,
                'current_weight_kg': str(a.current_weight_kg or ''),
                'target_weight_kg': str(a.target_weight_kg or ''),
                'activity_level': a.activity_level,
                'medical_conditions': a.medical_conditions,
            }
            for a in nut_qs
        ],
        'workout': [
            {
                'id': a.id,
                'member_id': a.member_id,
                'member_name': a.member.get_full_name() or a.member.username,
                'submitted_at': a.submitted_at.isoformat(),
                'primary_goals': a.primary_goals,
                'training_experience': a.training_experience,
                'current_weight_kg': str(a.current_weight_kg or ''),
                'target_weight_kg': str(a.target_weight_kg or ''),
                'injuries': a.current_injuries,
            }
            for a in wrk_qs
        ],
    })


# ─── Serializers ─────────────────────────────────────────────────────────────

def _serialize_nutrition(a):
    if not a:
        return None
    return {
        'id': a.id,
        'status': a.status,
        'submitted_at': a.submitted_at.isoformat() if a.submitted_at else None,
        'reviewed_at': a.reviewed_at.isoformat() if a.reviewed_at else None,
        'reviewed_by': (a.reviewed_by.get_full_name() or a.reviewed_by.username) if a.reviewed_by else None,
        'coach_plan_notes': a.coach_plan_notes or '',
        'coach_calorie_target': a.coach_calorie_target,
        'coach_protein_target_g': a.coach_protein_target_g,
        'coach_carbs_target_g': a.coach_carbs_target_g,
        'coach_fat_target_g': a.coach_fat_target_g,
        'coach_water_target_ml': a.coach_water_target_ml,
        'full_name': a.full_name or '',
        'date_of_birth': a.date_of_birth.isoformat() if a.date_of_birth else '',
        'age': a.age,
        'gender': a.gender or '',
        'height_cm': str(a.height_cm or ''),
        'waist_cm': str(a.waist_cm or ''),
        'phone': a.phone or '',
        'email': a.email or '',
        'occupation': a.occupation or '',
        'emergency_contact': a.emergency_contact or '',
        'assessment_date': a.assessment_date.isoformat() if a.assessment_date else '',
        'current_weight_kg': str(a.current_weight_kg or ''),
        'target_weight_kg': str(a.target_weight_kg or ''),
        'goal_timeline_weeks': a.goal_timeline_weeks,
        'goal_importance': a.goal_importance,
        'primary_goals': a.primary_goals or '',
        'primary_goals_other': a.primary_goals_other or '',
        'highest_adult_weight_kg': str(a.highest_adult_weight_kg or ''),
        'lowest_adult_weight_kg': str(a.lowest_adult_weight_kg or ''),
        'previous_diet_plan': a.previous_diet_plan,
        'previous_diet_types': a.previous_diet_types or '',
        'previous_diet_types_other': a.previous_diet_types_other or '',
        'diet_stop_reasons': a.diet_stop_reasons or '',
        'diet_stop_reasons_other': a.diet_stop_reasons_other or '',
        'activity_level': a.activity_level or '',
        'work_hours_per_day': a.work_hours_per_day,
        'sitting_hours_per_day': a.sitting_hours_per_day,
        'daily_commute_minutes': a.daily_commute_minutes,
        'shift_type': a.shift_type or '',
        'daily_steps': a.daily_steps or '',
        'currently_exercising': a.currently_exercising,
        'exercise_days_per_week': a.exercise_days_per_week,
        'session_duration_minutes': a.session_duration_minutes,
        'usual_workout_time': a.usual_workout_time or '',
        'dietary_preference': a.dietary_preference or '',
        'disliked_foods': a.disliked_foods or '',
        'allergies': a.allergies or '',
        'cultural_restrictions': a.cultural_restrictions or '',
        'meal_pattern': a.meal_pattern or '',
        'meals_per_day': a.meals_per_day,
        'typical_breakfast': a.typical_breakfast or '',
        'typical_lunch': a.typical_lunch or '',
        'typical_dinner': a.typical_dinner or '',
        'typical_snacks': a.typical_snacks or '',
        'daily_water_ml': a.daily_water_ml,
        'daily_tea_coffee_cups': a.daily_tea_coffee_cups,
        'sugar_in_tea': a.sugar_in_tea,
        'alcohol_frequency': a.alcohol_frequency or '',
        'eats_outside_frequently': a.eats_outside_frequently,
        'outside_food_frequency': a.outside_food_frequency or '',
        'stress_eating': a.stress_eating,
        'night_eating': a.night_eating,
        'emotional_eating': a.emotional_eating,
        'binge_eating': a.binge_eating,
        'skip_meals_often': a.skip_meals_often,
        'current_supplements': a.current_supplements or '',
        'current_medications': a.current_medications or '',
        'vitamin_d_tested': a.vitamin_d_tested,
        'iron_tested': a.iron_tested,
        'medical_conditions': a.medical_conditions or '',
        'digestive_issues': a.digestive_issues,
        'hormonal_issues': a.hormonal_issues,
        'thyroid_issues': a.thyroid_issues,
        'pcos': a.pcos,
        'diabetes': a.diabetes,
        'blood_pressure_issues': a.blood_pressure_issues,
        'sleep_hours_per_night': str(a.sleep_hours_per_night or ''),
        'sleep_quality': a.sleep_quality or '',
        'stress_level': a.stress_level,
        'stress_causes': a.stress_causes or '',
        'member_notes': a.member_notes or '',
    }


def _serialize_workout(a):
    if not a:
        return None
    return {
        'id': a.id,
        'status': a.status,
        'submitted_at': a.submitted_at.isoformat() if a.submitted_at else None,
        'reviewed_at': a.reviewed_at.isoformat() if a.reviewed_at else None,
        'reviewed_by': (a.reviewed_by.get_full_name() or a.reviewed_by.username) if a.reviewed_by else None,
        'coach_plan_notes': a.coach_plan_notes or '',
        'coach_training_days_per_week': a.coach_training_days_per_week,
        'coach_session_duration_minutes': a.coach_session_duration_minutes,
        'coach_cardio_recommendation': a.coach_cardio_recommendation or '',
        'assigned_program': {
            'id': a.assigned_program.id,
            'title': a.assigned_program.title
        } if a.assigned_program else None,
        'full_name': a.full_name or '',
        'date_of_birth': a.date_of_birth.isoformat() if a.date_of_birth else '',
        'age': a.age,
        'gender': a.gender or '',
        'height_cm': str(a.height_cm or ''),
        'current_weight_kg': str(a.current_weight_kg or ''),
        'phone': a.phone or '',
        'email': a.email or '',
        'occupation': a.occupation or '',
        'emergency_contact': a.emergency_contact or '',
        'assessment_date': a.assessment_date.isoformat() if a.assessment_date else '',
        'target_weight_kg': str(a.target_weight_kg or ''),
        'goal_timeline_weeks': a.goal_timeline_weeks,
        'primary_goals': a.primary_goals or '',
        'primary_goals_other': a.primary_goals_other or '',
        'motivation_level': a.motivation_level,
        'training_experience': a.training_experience or '',
        'currently_training': a.currently_training,
        'training_days_per_week': a.training_days_per_week,
        'session_duration_minutes': a.session_duration_minutes,
        'preferred_training_time': a.preferred_training_time or '',
        'previous_training_types': a.previous_training_types or '',
        'previous_training_other': a.previous_training_other or '',
        'longest_training_streak_months': a.longest_training_streak_months,
        'reason_stopped_training': a.reason_stopped_training or '',
        'body_fat_pct': str(a.body_fat_pct or ''),
        'waist_cm': str(a.waist_cm or ''),
        'hip_cm': str(a.hip_cm or ''),
        'chest_cm': str(a.chest_cm or ''),
        'bicep_cm': str(a.bicep_cm or ''),
        'thigh_cm': str(a.thigh_cm or ''),
        'strength_self_rating': a.strength_self_rating,
        'endurance_self_rating': a.endurance_self_rating,
        'flexibility_self_rating': a.flexibility_self_rating,
        'pushups_reps': a.pushups_reps,
        'squats_reps': a.squats_reps,
        'plank_seconds': a.plank_seconds,
        'gym_access': a.gym_access,
        'home_equipment': a.home_equipment or '',
        'preferred_gym_area': a.preferred_gym_area or '',
        'sleep_hours_per_night': str(a.sleep_hours_per_night or ''),
        'sleep_quality': a.sleep_quality or '',
        'stress_level': a.stress_level,
        'recovery_days_per_week': a.recovery_days_per_week,
        'active_rest_activities': a.active_rest_activities or '',
        'current_injuries': a.current_injuries or '',
        'past_injuries': a.past_injuries or '',
        'chronic_conditions': a.chronic_conditions or '',
        'physical_limitations': a.physical_limitations or '',
        'cleared_by_doctor': a.cleared_by_doctor,
        'is_under_medication': a.is_under_medication,
        'medication_details': a.medication_details or '',
        'exercises_to_avoid': a.exercises_to_avoid or '',
        'preferred_exercises': a.preferred_exercises or '',
        'training_split_preference': a.training_split_preference or '',
        'cardio_preference': a.cardio_preference or '',
        'member_notes': a.member_notes or '',
    }


# ─── Coach: Get Single Assessment Detail ─────────────────────────────────────

@login_required
@role_required('coach', 'super_admin', 'manager')
def get_assessment_detail_api(request, assessment_type, assessment_id):
    """Coach retrieves full answers & details for an assessment."""
    from wger.membership.models import NutritionAssessment, WorkoutAssessment, GymProgram
    programs_list = [
        {'id': p.id, 'title': p.title, 'category': p.get_category_display()}
        for p in GymProgram.objects.all().order_by('title')
    ]

    if assessment_type == 'nutrition':
        a = NutritionAssessment.objects.filter(id=assessment_id).first()
        if not a:
            return JsonResponse({'error': 'Assessment not found'}, status=404)
        return JsonResponse({
            'success': True,
            'type': 'nutrition',
            'assessment': _serialize_nutrition(a),
            'programs': programs_list,
        })
    elif assessment_type == 'workout':
        a = WorkoutAssessment.objects.filter(id=assessment_id).first()
        if not a:
            return JsonResponse({'error': 'Assessment not found'}, status=404)
        return JsonResponse({
            'success': True,
            'type': 'workout',
            'assessment': _serialize_workout(a),
            'programs': programs_list,
        })
    return JsonResponse({'error': 'Invalid assessment type'}, status=400)


# ─── Member: Get My Assessment Status & Coach Plan ───────────────────────────

@login_required
def get_my_assessments_api(request):
    """Member fetches their own latest assessment status, coach plan, and registration defaults."""
    from wger.membership.models import NutritionAssessment, WorkoutAssessment

    user = request.user
    nut = NutritionAssessment.objects.filter(member=user).order_by('-submitted_at').first()
    wrk = WorkoutAssessment.objects.filter(member=user).order_by('-submitted_at').first()
    profile_defaults = _get_registration_profile_defaults(user)

    return JsonResponse({
        'success': True,
        'profile_defaults': profile_defaults,
        'nutrition_assessment': _serialize_nutrition(nut),
        'workout_assessment': _serialize_workout(wrk),
    })
