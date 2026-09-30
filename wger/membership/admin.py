"""
Fit Me — Membership Admin Registration
Registers all membership models in the Django Admin panel.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone

from .models import (
    MembershipPlan,
    MemberProfile,
    Subscription,
    MemberApplication,
    BodyCheckIn,
    GymProgram,
    CoachProfile,
    ContactInquiry,
    Testimonial,
    Announcement,
    MemberWorkoutLog,
    MemberMeasurement,
)


@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'plan_type', 'price_monthly', 'duration_days', 'allowed_entry_start', 'allowed_entry_end', 'is_active')
    list_filter = ('plan_type', 'is_active')
    search_fields = ('name',)
    ordering = ('price_monthly',)


@admin.register(MemberProfile)
class MemberProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'biometric_pin', 'primary_goal', 'assigned_coach', 'onboarding_complete', 'created_at')
    list_filter = ('primary_goal', 'gender', 'onboarding_complete', 'personal_trainer_needed')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone', 'biometric_pin', 'nic_passport')
    raw_id_fields = ('user', 'assigned_coach')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('member', 'plan', 'status', 'start_date', 'end_date', 'amount_paid', 'payment_method', 'approved_by', 'is_active_display')
    list_filter = ('status', 'payment_method', 'plan')
    search_fields = ('member__username', 'member__first_name', 'member__last_name')
    raw_id_fields = ('member', 'approved_by')
    readonly_fields = ('created_at',)
    date_hierarchy = 'start_date'
    ordering = ('-created_at',)

    def is_active_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: #76C043; font-weight: bold;">✔ Active</span>')
        return format_html('<span style="color: #E63946;">✘ Inactive</span>')
    is_active_display.short_description = 'Live Status'


@admin.register(MemberApplication)
class MemberApplicationAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone', 'desired_plan', 'status', 'applied_at', 'reviewed_by')
    list_filter = ('status', 'gender', 'desired_plan', 'personal_trainer_needed')
    search_fields = ('full_name', 'email', 'phone', 'nic_passport')
    readonly_fields = ('applied_at', 'reviewed_at')
    raw_id_fields = ('reviewed_by', 'created_user')
    ordering = ('-applied_at',)
    actions = ['mark_approved', 'mark_rejected']

    def mark_approved(self, request, queryset):
        queryset.update(status='approved', reviewed_by=request.user, reviewed_at=timezone.now())
    mark_approved.short_description = 'Mark selected applications as Approved'

    def mark_rejected(self, request, queryset):
        queryset.update(status='rejected', reviewed_by=request.user, reviewed_at=timezone.now())
    mark_rejected.short_description = 'Mark selected applications as Rejected'


@admin.register(BodyCheckIn)
class BodyCheckInAdmin(admin.ModelAdmin):
    list_display = ('member', 'checkin_date', 'weight_kg', 'body_fat_pct', 'muscle_mass_kg', 'recorded_by')
    list_filter = ('checkin_date',)
    search_fields = ('member__username', 'member__first_name', 'member__last_name')
    raw_id_fields = ('member', 'recorded_by')
    date_hierarchy = 'checkin_date'
    ordering = ('-checkin_date',)


@admin.register(GymProgram)
class GymProgramAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'difficulty', 'duration_weeks', 'sessions_per_week', 'is_active')
    list_filter = ('category', 'difficulty', 'is_active')
    search_fields = ('title', 'description')
    ordering = ('title',)


@admin.register(CoachProfile)
class CoachProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'specialties', 'years_experience', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('user__username', 'user__first_name', 'specialties')
    raw_id_fields = ('user',)
    ordering = ('user__first_name',)


@admin.register(ContactInquiry)
class ContactInquiryAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'subject', 'is_resolved', 'created_at')
    list_filter = ('is_resolved',)
    search_fields = ('name', 'email', 'phone', 'subject')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    actions = ['mark_resolved']

    def mark_resolved(self, request, queryset):
        queryset.update(is_resolved=True)
    mark_resolved.short_description = 'Mark selected inquiries as Resolved'


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('member_name', 'program_name', 'weight_loss_kg', 'duration_months', 'is_featured', 'is_approved')
    list_filter = ('is_featured', 'is_approved')
    search_fields = ('member_name', 'program_name', 'quote')
    ordering = ('-created_at',)


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'priority', 'is_active', 'created_at')
    list_filter = ('priority', 'is_active')
    search_fields = ('title', 'content')
    ordering = ('-created_at',)


@admin.register(MemberWorkoutLog)
class MemberWorkoutLogAdmin(admin.ModelAdmin):
    list_display = ('member', 'workout_name', 'exercise_name', 'sets_completed', 'reps', 'weight_kg', 'logged_at')
    list_filter = ('workout_name',)
    search_fields = ('member__username', 'exercise_name', 'workout_name')
    raw_id_fields = ('member',)
    date_hierarchy = 'logged_at'
    ordering = ('-logged_at',)


@admin.register(MemberMeasurement)
class MemberMeasurementAdmin(admin.ModelAdmin):
    list_display = ('member', 'date', 'weight_kg', 'waist_cm', 'body_fat_pct')
    search_fields = ('member__username',)
    raw_id_fields = ('member',)
    date_hierarchy = 'date'
    ordering = ('-date',)
