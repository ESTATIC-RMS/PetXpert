from django.contrib import admin
from .models import User, VeterinarianProfile, VeterinarianReview


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'email', 'full_name', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'created_at']
    search_fields = ['email', 'full_name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(VeterinarianProfile)
class VeterinarianProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'license_number', 'status', 'avg_rating', 'rating_count', 'total_consultations']
    list_filter = ['status', 'avg_rating', 'created_at']
    search_fields = ['user__full_name', 'license_number', 'clinic_name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(VeterinarianReview)
class VeterinarianReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'veterinarian', 'patient', 'rating', 'appointment', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['patient__full_name', 'veterinarian__user__full_name', 'comment']
    readonly_fields = ['id', 'created_at', 'updated_at']
