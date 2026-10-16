# -*- coding: utf-8 -*-

# This file is part of wger Workout Manager.
#
# wger Workout Manager is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# wger Workout Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Workout Manager.  If not, see <http://www.gnu.org/licenses/>.

# Django
from django.conf import settings
from django.conf.urls import include
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib.sitemaps.views import (
    index,
    sitemap,
)
import os
from django.contrib import admin
from django.urls import path, re_path

# Third Party
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)

from django.views.generic import RedirectView
from django.contrib.auth.views import (
    PasswordResetDoneView,
    PasswordResetCompleteView,
)
from wger.core.views.user import WgerPasswordResetConfirmView
from wger.core.views import assessment_apis as aa
from wger.core.views import fitme_dashboards as fd
from wger.zkbio_integration import views as zkbio_views


# wger
from wger.core.api import views as core_api_views
from wger.exercises.api import views as exercises_api_views
from wger.exercises.sitemap import ExercisesSitemap
from wger.gallery.api import views as gallery_api_views
from wger.manager.api import views as manager_api_views
from wger.measurements.api import views as measurements_api_views
from wger.nutrition.api import views as nutrition_api_views
from wger.trophies.api import views as trophies_api_views
from wger.utils import oidc_auth
from wger.utils.api_schema import CachedSchemaGenerator
from wger.utils.generic_views import TextTemplateView
from wger.weight.api import views as weight_api_views


#
# REST API
#
router = routers.DefaultRouter()

#
# Application
#

# Manager app
router.register(r'routine', manager_api_views.RoutineViewSet, basename='routine')
router.register(r'templates', manager_api_views.UserRoutineTemplateViewSet, basename='templates')
router.register(
    r'public-templates',
    manager_api_views.PublicRoutineTemplateViewSet,
    basename='public-templates',
)
router.register(
    r'workoutsession',
    manager_api_views.WorkoutSessionViewSet,
    basename='workoutsession',
)
router.register(
    r'day',
    manager_api_views.RoutineDayViewSet,
    basename='day',
)
router.register(
    r'slot',
    manager_api_views.SlotViewSet,
    basename='slot',
)
router.register(
    r'slot-entry',
    manager_api_views.SlotEntryViewSet,
    basename='slot-entry',
)
router.register(
    r'weight-config',
    manager_api_views.WeightConfigViewSet,
    basename='weight-config',
)
router.register(
    r'max-weight-config',
    manager_api_views.MaxWeightConfigViewSet,
    basename='max-weight-config',
)
router.register(
    r'repetitions-config',
    manager_api_views.RepetitionsConfigViewSet,
    basename='repetitions-config',
)
router.register(
    r'max-repetitions-config',
    manager_api_views.MaxRepetitionsConfigViewSet,
    basename='max-repetitions-config',
)
router.register(
    r'sets-config',
    manager_api_views.SetsConfigViewSet,
    basename='sets-config',
)
router.register(
    r'max-sets-config',
    manager_api_views.MaxSetsConfigViewSet,
    basename='max-sets-config',
)
router.register(
    r'rest-config',
    manager_api_views.RestConfigViewSet,
    basename='rest-config',
)
router.register(
    r'max-rest-config',
    manager_api_views.MaxRestConfigViewSet,
    basename='max-rest-config',
)
router.register(r'rir-config', manager_api_views.RiRConfigViewSet, basename='rir-config')
router.register(r'max-rir-config', manager_api_views.MaxRiRConfigViewSet, basename='max-rir-config')
router.register(r'workoutlog', manager_api_views.WorkoutLogViewSet, basename='workoutlog')

# Core app
router.register(r'language', core_api_views.LanguageViewSet, basename='language')
router.register(r'license', core_api_views.LicenseViewSet, basename='license')
# userprofile is not registered here: a user has exactly one profile, so it is
# a plain path without list or detail routes (see UserProfileView)
router.register(
    r'setting-repetitionunit',
    core_api_views.RepetitionUnitViewSet,
    basename='setting-repetition-unit',
)
router.register(
    r'setting-weightunit', core_api_views.RoutineWeightUnitViewSet, basename='setting-weight-unit'
)

# Exercises app
router.register(
    r'exerciseinfo',
    exercises_api_views.ExerciseInfoViewset,
    basename='exerciseinfo',
)

router.register(
    r'exercise-translation',
    exercises_api_views.ExerciseTranslationViewSet,
    basename='exercise-translation',
)
router.register(
    r'exercise',
    exercises_api_views.ExerciseViewSet,
    basename='exercise',
)
router.register(
    r'equipment',
    exercises_api_views.EquipmentViewSet,
    basename='equipment',
)
router.register(
    r'deletion-log',
    exercises_api_views.DeletionLogViewSet,
    basename='deletion-log',
)
router.register(
    r'exercisecategory',
    exercises_api_views.ExerciseCategoryViewSet,
    basename='exercisecategory',
)
router.register(
    r'video',
    exercises_api_views.ExerciseVideoViewSet,
    basename='video',
)
router.register(
    r'exerciseimage',
    exercises_api_views.ExerciseImageViewSet,
    basename='exerciseimage',
)
router.register(
    r'exercisecomment',
    exercises_api_views.ExerciseCommentViewSet,
    basename='exercisecomment',
)
router.register(
    r'exercisealias',
    exercises_api_views.ExerciseAliasViewSet,
    basename='exercisealias',
)
router.register(
    r'muscle',
    exercises_api_views.MuscleViewSet,
    basename='muscle',
)

# Nutrition app
router.register(r'ingredient', nutrition_api_views.IngredientViewSet, basename='api-ingredient')
router.register(
    r'ingredientinfo', nutrition_api_views.IngredientInfoViewSet, basename='api-ingredientinfo'
)
router.register(
    r'ingredient-sync',
    nutrition_api_views.IngredientSyncViewSet,
    basename='api-ingredient-sync',
)
router.register(
    r'ingredientweightunit',
    nutrition_api_views.IngredientWeightUnitViewSet,
    basename='ingredientweightunit',
)
router.register(
    r'nutritionplan', nutrition_api_views.NutritionPlanViewSet, basename='nutritionplan'
)
router.register(
    r'nutritionplaninfo', nutrition_api_views.NutritionPlanInfoViewSet, basename='nutritionplaninfo'
)
router.register(r'nutritiondiary', nutrition_api_views.LogItemViewSet, basename='nutritiondiary')
router.register(r'meal', nutrition_api_views.MealViewSet, basename='meal')
router.register(r'mealitem', nutrition_api_views.MealItemViewSet, basename='mealitem')
router.register(r'ingredient-image', nutrition_api_views.ImageViewSet, basename='ingredientimage')

# Weight app
router.register(r'weightentry', weight_api_views.WeightEntryViewSet, basename='weightentry')

# Gallery app
router.register(r'gallery', gallery_api_views.GalleryImageViewSet, basename='gallery')

# Measurements app
router.register(
    r'measurement',
    measurements_api_views.MeasurementViewSet,
    basename='measurement',
)
router.register(
    r'measurement-category',
    measurements_api_views.CategoryViewSet,
    basename='measurement-category',
)

# Trophies app
router.register(r'trophy', trophies_api_views.TrophyViewSet, basename='trophy')
router.register(r'user-trophy', trophies_api_views.UserTrophyViewSet, basename='user-trophy')
router.register(
    r'user-statistics',
    trophies_api_views.UserStatisticsViewSet,
    basename='user-statistics',
)

#
# Sitemaps
#
sitemaps = {
    'exercises': ExercisesSitemap,
}  # 'nutrition': NutritionSitemap}


def health_check_view(request):
    """
    Lightweight health check endpoint for container orchestrators (Render, Docker, Kubernetes).
    Returns 200 OK with JSON status and database connectivity indicator.
    """
    from django.http import JsonResponse
    from django.db import connection
    status = {"status": "ok"}
    http_status = 200
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
        status["database"] = "connected"
    except Exception as exc:
        status["database"] = "error"
        status["status"] = "degraded"
        status["detail"] = str(exc)
        http_status = 503
    return JsonResponse(status, status=http_status)


def protected_media_serve(request, path, document_root=None, show_indexes=False):
    """
    Ensure media files (member photos, receipts, documents) are accessible only
    to authenticated users (via session or Bearer JWT token).
    """
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            try:
                from rest_framework_simplejwt.authentication import JWTAuthentication
                validated = JWTAuthentication().authenticate(request)
                if validated:
                    request.user = validated[0]
            except Exception:
                pass

    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Authentication required to access media files.")

    from django.views.static import serve
    return serve(request, path, document_root=document_root, show_indexes=show_indexes)


#
# The actual URLs
#
urlpatterns = i18n_patterns(
    path('', include(('wger.core.urls', 'core'), namespace='core')),
    path('routine/', include(('wger.manager.urls', 'manager'), namespace='manager')),
    path('exercise/', include(('wger.exercises.urls', 'exercise'), namespace='exercise')),
    path('weight/', include(('wger.weight.urls', 'weight'), namespace='weight')),
    path('nutrition/', include(('wger.nutrition.urls', 'nutrition'), namespace='nutrition')),
    path('software/', include(('wger.software.urls', 'software'), namespace='software')),
    path('config/', include(('wger.config.urls', 'config'), namespace='config')),
    path('gym/', include(('wger.gym.urls', 'gym'), namespace='gym')),
    path('gallery/', include(('wger.gallery.urls', 'gallery'), namespace='gallery')),
    path('trophies/', include(('wger.trophies.urls', 'trophies'), namespace='trophies')),
    path(
        'measurement/',
        include(('wger.measurements.urls', 'measurements'), namespace='measurements'),
    ),
    path('email/', include(('wger.mailer.urls', 'email'), namespace='email')),
    path('sitemap.xml', index, {'sitemaps': sitemaps}, name='sitemap'),
    path(
        'sitemap-<section>.xml',
        sitemap,
        {'sitemaps': sitemaps},
        name='django.contrib.sitemaps.views.sitemap',
    ),
    prefix_default_language=False
)

#
# URLs without language prefix
#
urlpatterns += [
    # ── Django Admin Panel (/admin/) ──
    path('admin/', admin.site.urls),

    # ── Login Redirects ──
    path('login', RedirectView.as_view(url='/user/login', permanent=False)),
    path('login/', RedirectView.as_view(url='/user/login', permanent=False)),
    path('user/login/', RedirectView.as_view(url='/user/login', permanent=False)),
    path('en/user/login', RedirectView.as_view(url='/user/login', permanent=False)),
    path('en/user/login/', RedirectView.as_view(url='/user/login', permanent=False)),

    # ── Password Reset URLs (Root Aliases for Django auth & email links) ──
    path(
        'user/password/reset/check/<uidb64>/<token>/',
        WgerPasswordResetConfirmView.as_view(),
        name='password_reset_confirm',
    ),
    path(
        'user/password/reset/check/<uidb64>/<token>',
        WgerPasswordResetConfirmView.as_view(),
    ),
    path(
        'reset/<uidb64>/<token>/',
        WgerPasswordResetConfirmView.as_view(),
        name='password_reset_confirm_short',
    ),
    path(
        'reset/<uidb64>/<token>',
        WgerPasswordResetConfirmView.as_view(),
    ),
    path(
        'user/password/reset/done/',
        PasswordResetDoneView.as_view(),
        name='password_reset_done',
    ),
    path(
        'user/password/reset/complete/',
        PasswordResetCompleteView.as_view(),
        name='password_reset_complete',
    ),

    # ── Fit Me Role Dashboards (Clean URLs) ──
    path('dashboard/', include(([
        path('', fd.dashboard_redirect, name='fitme-dashboard'),
        path('admin/', fd.super_admin_dashboard, name='fitme-admin'),
        path('admin/users/', fd.admin_users_view, name='fitme-admin-users'),
        path('front-desk/', fd.front_desk_dashboard, name='fitme-front-desk'),
        path('coach/', fd.coach_dashboard, name='fitme-coach'),
        path('member/', fd.member_dashboard, name='fitme-member'),
        # Dynamic Actions
        path('api/applications/create/', fd.create_application_api, name='api-app-create'),
        path('api/applications/<int:app_id>/approve/', fd.approve_application_api, name='api-app-approve'),
        path('api/applications/<int:app_id>/reject/', fd.reject_application_api, name='api-app-reject'),
        path('api/record-payment/', fd.record_payment_api, name='api-record-payment'),
        path('api/desk/lookup/', fd.desk_member_lookup_api, name='api-desk-lookup'),
        path('api/members/<int:member_id>/profile/', fd.member_full_profile_api, name='api-member-profile'),
        path('api/meals/<int:meal_id>/review/', fd.review_meal_api, name='api-meal-review'),
        path('api/members/<int:member_id>/ping/', fd.ping_member_api, name='api-member-ping'),
        path('api/members/<int:member_id>/resend-invite/', fd.resend_member_invite_api, name='api-member-resend-invite'),
        path('api/quick-meal/', fd.log_quick_meal_api, name='api-quick-meal'),
        path('api/log-water/', fd.log_water_api, name='api-log-water'),
        path('api/alerts/<int:alert_id>/resolve/', fd.resolve_absence_alert_api, name='api-alert-resolve'),
        # New 31-Module Dynamic APIs
        path('api/log-workout/', fd.log_workout_api, name='api-log-workout'),
        path('api/log-measurement/', fd.log_measurement_api, name='api-log-measurement'),
        path('api/members/<int:member_id>/assign-plan/', fd.assign_program_api, name='api-member-assign-plan'),
        path('api/members/<int:member_id>/assign-coach/', fd.assign_coach_api, name='api-member-assign-coach'),
        path('api/members/<int:member_id>/set-nutrition/', fd.set_nutrition_target_api, name='api-member-set-nutrition'),
        path('api/members/<int:member_id>/toggle-access/', fd.toggle_member_access_api, name='api-member-toggle-access'),
        path('api/programs/create/', fd.admin_create_program_api, name='api-admin-create-program'),
        path('api/programs/<int:prog_id>/edit/', fd.admin_edit_program_api, name='api-admin-edit-program'),
        path('api/programs/<int:prog_id>/delete/', fd.admin_delete_program_api, name='api-admin-delete-program'),
        path('api/announcements/create/', fd.admin_create_announcement_api, name='api-admin-create-announcement'),
        path('api/testimonials/<int:testimonial_id>/toggle/', fd.admin_toggle_testimonial_api, name='api-admin-toggle-testimonial'),
        # Staff, User Creation & Role Management APIs
        path('api/users/create/', fd.admin_create_user_api, name='api-admin-create-user'),
        path('api/users/<int:user_id>/role/', fd.admin_update_user_role_api, name='api-admin-user-role'),
        path('api/users/<int:user_id>/toggle-active/', fd.admin_toggle_user_active_api, name='api-admin-user-toggle-active'),
        path('api/users/<int:user_id>/reset-password/', fd.admin_reset_user_password_api, name='api-admin-user-reset-password'),
        path('api/audit/align-roles/', fd.admin_audit_align_roles_api, name='api-audit-align-roles'),
        # Super Admin Dedicated: Plan Builder & Subscription Overrides
        path('api/plans/create/', fd.admin_create_plan_api, name='api-admin-create-plan'),
        path('api/plans/<int:plan_id>/edit/', fd.admin_edit_plan_api, name='api-admin-edit-plan'),
        path('api/plans/<int:plan_id>/toggle/', fd.admin_toggle_plan_api, name='api-admin-toggle-plan'),
        path('api/plans/<int:plan_id>/delete/', fd.admin_delete_plan_api, name='api-admin-delete-plan'),
        path('api/subscriptions/<int:sub_id>/override/', fd.admin_override_subscription_api, name='api-admin-sub-override'),
        # Financial Reports & Ledger Export
        path('admin/reports/export-csv/', fd.admin_export_financial_csv, name='admin-reports-export-csv'),
        path('admin/reports/export-members-csv/', fd.admin_export_members_csv, name='admin-reports-export-members-csv'),
        path('admin/reports/export-expenses-csv/', fd.admin_export_expenses_csv, name='admin-reports-export-expenses-csv'),
        path('admin/reports/export-payroll-csv/', fd.admin_export_payroll_csv, name='admin-reports-export-payroll-csv'),
        path('admin/reports/eod/', fd.admin_daily_eod_report, name='admin-daily-eod-report'),
        # Staff Payroll Management APIs
        path('api/payroll/recalculate/', fd.admin_recalculate_payroll_api, name='api-admin-payroll-recalculate'),
        path('api/payroll/enroll-staff/', fd.admin_enroll_staff_payroll_api, name='api-admin-payroll-enroll-staff'),
        path('api/payroll/<int:ledger_id>/pt-breakdown/', fd.admin_get_pt_breakdown_api, name='api-admin-payroll-pt-breakdown'),
        path('api/payroll/<int:ledger_id>/adjust/', fd.admin_adjust_payroll_ledger_api, name='api-admin-payroll-adjust'),
        path('api/payroll/<int:ledger_id>/delete/', fd.admin_delete_payroll_ledger_api, name='api-admin-payroll-delete'),
        path('api/payroll/<int:ledger_id>/finalize/', fd.admin_finalize_payroll_ledger_api, name='api-admin-payroll-finalize'),
        path('payroll/<int:ledger_id>/thermal-slip/', fd.admin_payroll_thermal_slip_view, name='payroll-thermal-slip'),
        # Staff Attendance & Shift Rosters
        path('api/staff-attendance/clock/', fd.admin_clock_staff_attendance_api, name='api-staff-attendance-clock'),
        path('api/staff-shifts/create/', fd.admin_create_staff_shift_api, name='api-staff-shifts-create'),
        path('api/staff-shifts/bulk-generate/', fd.admin_generate_bulk_roster_api, name='api-staff-shifts-bulk-generate'),
        path('api/staff-shifts/<int:shift_id>/toggle-leave/', fd.admin_toggle_shift_leave_api, name='api-staff-shifts-toggle-leave'),
        path('api/staff-schedule/<int:staff_id>/', fd.admin_get_staff_work_schedule_api, name='api-staff-schedule-get'),
        path('api/staff-schedule/save/', fd.admin_save_staff_work_schedule_api, name='api-staff-schedule-save'),
        path('api/payroll/issue-advance/', fd.admin_issue_salary_advance_api, name='api-payroll-issue-advance'),
        path('advances/<int:advance_id>/thermal-voucher/', fd.admin_advance_thermal_voucher_view, name='advance-thermal-voucher'),
        # Financial OPEX & Expenses APIs
        path('api/expenses/create/', fd.admin_create_expense_api, name='api-admin-create-expense'),
        path('api/expenses/<int:expense_id>/delete/', fd.admin_delete_expense_api, name='api-admin-delete-expense'),
        path('api/expenses/<int:expense_id>/upload-receipt/', fd.admin_upload_expense_receipt_api, name='api-admin-upload-expense-receipt'),
        # Member Self-Service Instant Renewal & Door Unlock
        path('api/member/self-renew/', fd.member_self_renew_api, name='api-member-self-renew'),
    ], 'fitme'))),

    path('api/member/self-renew/', fd.member_self_renew_api, name='api-direct-member-self-renew'),
    path('api/desk/lookup/', fd.desk_member_lookup_api, name='api-direct-desk-lookup'),
    path('api/members/<int:member_id>/profile/', fd.member_full_profile_api, name='api-direct-member-profile'),
    path('api/profile/update-photo/', zkbio_views.upload_face_api, name='api-profile-update-photo'),

    # ── Super Admin Dedicated: Plan Builder & Subscription Overrides (direct /api/ aliases) ──
    path('api/plans/create/', fd.admin_create_plan_api, name='api-direct-admin-create-plan'),
    path('api/plans/<int:plan_id>/edit/', fd.admin_edit_plan_api, name='api-direct-admin-edit-plan'),
    path('api/plans/<int:plan_id>/toggle/', fd.admin_toggle_plan_api, name='api-direct-admin-toggle-plan'),
    path('api/subscriptions/<int:sub_id>/override/', fd.admin_override_subscription_api, name='api-direct-admin-sub-override'),
    # Multi-User (Couples & Family) Partner Linking APIs
    path('api/subscriptions/<int:subscription_id>/link-partner/', fd.admin_link_partner_api, name='api-link-partner'),
    path('api/buddy-links/<int:link_id>/delete/', fd.admin_unlink_partner_api, name='api-unlink-partner'),
    path('api/payroll/issue-advance/', fd.admin_issue_salary_advance_api, name='api-direct-payroll-issue-advance'),
    path('api/payroll/enroll-staff/', fd.admin_enroll_staff_payroll_api, name='api-direct-payroll-enroll-staff'),
    # Direct expense API aliases
    path('api/expenses/create/', fd.admin_create_expense_api, name='api-direct-admin-create-expense'),
    path('api/expenses/<int:expense_id>/delete/', fd.admin_delete_expense_api, name='api-direct-admin-delete-expense'),
    path('api/expenses/<int:expense_id>/upload-receipt/', fd.admin_upload_expense_receipt_api, name='api-direct-admin-upload-expense-receipt'),
    path('dashboard/admin/reports/export-expenses-csv/', fd.admin_export_expenses_csv, name='admin-direct-reports-export-expenses-csv'),

    # ── Fit Me Point of Sale (POS) for Gym Drinks & Supplements ──
    path('pos/', include('wger.pos.urls', namespace='pos')),
    path('dashboard/pos/', RedirectView.as_view(url='/pos/', permanent=False)),

    # ── Fit Me Public Website Contact API ──
    path('api/public/contact/', fd.public_contact_api, name='public-contact-api'),


    # ── Legacy /fitme/ Redirects to clean routes ──
    path('fitme/dashboard/admin/', RedirectView.as_view(url='/dashboard/admin/', permanent=False)),
    path('fitme/dashboard/front-desk/', RedirectView.as_view(url='/dashboard/front-desk/', permanent=False)),
    path('fitme/dashboard/coach/', RedirectView.as_view(url='/dashboard/coach/', permanent=False)),
    path('fitme/dashboard/member/', RedirectView.as_view(url='/dashboard/member/', permanent=False)),
    path('fitme/dashboard/', RedirectView.as_view(url='/dashboard/', permanent=False)),
    path('fitme/register/', RedirectView.as_view(url='/register/', permanent=False)),
    path('fitme/receipt/<int:receipt_id>/', RedirectView.as_view(url='/receipt/%(receipt_id)s/', permanent=False)),

    # ── Fit Me 80mm Thermal Receipt View (Clean URL: /receipt/<id>/) ──
    path('receipt/<int:receipt_id>/', fd.view_receipt, name='receipt-view'),

    # ── Fit Me Official Membership Registration Form (Clean URL: /register/) ──
    path('register/', fd.public_registration_view, name='public-register'),

    # ── Fit Me Hardware & Operations Integrations ──
    path('api/zkbio/', include(('wger.zkbio_integration.urls', 'zkbio_integration'), namespace='zkbio_integration')),
    path('operations/', include(('wger.gym_operations_payroll.urls', 'gym_operations_payroll'), namespace='gym_operations_payroll')),
    path('api/nutrition-lk/', include(('wger.nutrition_lk.urls', 'nutrition_lk'), namespace='nutrition_lk')),
    path('api/habit/', include(('wger.habit.urls', 'habit'), namespace='habit')),

    # ── Fit Me Assessment Forms (Digital PDF equivalents) ──
    path('api/assessments/nutrition/submit/', aa.submit_nutrition_assessment_api, name='assessment-nutrition-submit'),
    path('api/assessments/workout/submit/', aa.submit_workout_assessment_api, name='assessment-workout-submit'),
    path('api/assessments/nutrition/<int:assessment_id>/review/', aa.coach_review_nutrition_assessment_api, name='assessment-nutrition-review'),
    path('api/assessments/workout/<int:assessment_id>/review/', aa.coach_review_workout_assessment_api, name='assessment-workout-review'),
    path('api/assessments/pending/', aa.list_pending_assessments_api, name='assessment-pending-list'),
    path('api/assessments/<str:assessment_type>/<int:assessment_id>/detail/', aa.get_assessment_detail_api, name='assessment-detail'),
    path('api/assessments/my/', aa.get_my_assessments_api, name='assessment-my'),
    # ── Media Uploads (Profile photos, receipts) ──
    re_path(r'^media/(?P<path>.*)$', protected_media_serve, {
        'document_root': settings.MEDIA_ROOT
    }),

    path('i18n/', include('django.conf.urls.i18n')),
    path('robots.txt', TextTemplateView.as_view(template_name='robots.txt'), name='robots'),
    # allauth account pages are mounted without a language prefix: the OAuth
    # callback's redirect_uri has to be stable
    path('account/', include('allauth.urls')),
    # REST auth API consumed by the Flutter app.
    path('allauth/', include('allauth.headless.urls')),
    # OAuth2/OIDC provider. Mounted at the root, the paths (/.well-known/... and
    # /identity/o/...) are part of the include. The authorization endpoint is
    # wrapped to keep the flow from starting when the provider isn't configured.
    path('identity/o/authorize', oidc_auth.authorization_view, name='oidc-authorize'),
    path('', include('allauth.idp.urls')),
    # API
    path(
        'api/v2/exercise-submission/',
        exercises_api_views.ExerciseSubmissionViewSet.as_view(),
        name='exercise-submission',
    ),
    path('api/v2/check-language/', core_api_views.check_language, name='check-language'),
    path(
        'api/v2/userprofile/',
        core_api_views.UserProfileView.as_view(),
        name='userprofile',
    ),
    path(
        'api/v2/userprofile/verify-email/',
        core_api_views.VerifyEmailView.as_view(),
        name='userprofile-verify-email',
    ),
    path('api/v2/', include(router.urls)),
    path('api/v2/token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v2/token/verify', TokenVerifyView.as_view(), name='token_verify'),
    # Others
    path(
        'api/v2/version/',
        core_api_views.ApplicationVersionView.as_view({'get': 'get'}),
        name='app_version',
    ),
    path(
        'api/v2/check-permission/',
        core_api_views.PermissionView.as_view({'get': 'get'}),
        name='permission',
    ),
    path(
        'api/v2/min-app-version/',
        core_api_views.RequiredApplicationVersionView.as_view({'get': 'get'}),
        name='min_app_version',
    ),
    path(
        'api/v2/min-server-version/',
        core_api_views.RequiredServerVersionView.as_view({'get': 'get'}),
        name='min_server_version',
    ),
    path(
        'api/v2/powersync-token',
        core_api_views.get_powersync_token,
        name='get_token',
    ),
    path(
        'api/v2/powersync-keys',
        core_api_views.get_powersync_keys,
        name='powersync-keys',
    ),
    path(
        'api/v2/upload-powersync-data',
        core_api_views.upload_powersync_data,
        name='powersync-data',
    ),
    # Api documentation
    #
    # metadata_class=None disables the OPTIONS handler on the HTML views: its
    # metadata response would otherwise be rendered through the UI template,
    # which requires context only the GET handler provides, and crash with 500.
    path(
        'api/v2/schema',
        SpectacularAPIView.as_view(generator_class=CachedSchemaGenerator),
        name='schema',
    ),
    path(
        'api/v2/schema/ui',
        SpectacularSwaggerView.as_view(url_name='schema', metadata_class=None),
        name='api-swagger-ui',
    ),
    path(
        'api/v2/schema/redoc',
        SpectacularRedocView.as_view(url_name='schema', metadata_class=None),
        name='api-redoc',
    ),
]


#
# URL for user uploaded files, served like this during development only
#
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # urlpatterns.append(path('__debug__/', include('debug_toolbar.urls')))

if settings.EXPOSE_PROMETHEUS_METRICS:
    urlpatterns += [path('prometheus/', include('django_prometheus.urls'))]

# Unprefixed routes for health checks and container probes
urlpatterns += [
    path('health/', health_check_view, name='health-check'),
]
