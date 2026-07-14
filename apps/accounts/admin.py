from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .admin_forms import (
    PetXpertAdminPasswordChangeForm,
    PetXpertUserAddForm,
    PetXpertUserChangeForm,
)
from .models import SellerProfile, User, VeterinarianProfile, VeterinarianReview


@admin.register(User)
class UserAdmin(DjangoUserAdmin, ModelAdmin):
    form = PetXpertUserChangeForm
    add_form = PetXpertUserAddForm
    change_password_form = PetXpertAdminPasswordChangeForm

    list_display = ['email', 'full_name', 'role', 'is_active', 'is_staff', 'is_email_verified', 'created_at']
    list_filter = ['role', 'is_active', 'is_staff', 'is_email_verified', 'created_at']
    list_editable = ['is_active', 'role']
    search_fields = ['email', 'full_name']
    ordering = ['-created_at']
    readonly_fields = ['id', 'last_login', 'created_at', 'updated_at']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Profile'), {'fields': ('full_name', 'avatar', 'role')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_email_verified', 'groups', 'user_permissions'),
        }),
        (_('Metadata'), {'fields': ('id', 'last_login', 'created_at', 'updated_at')}),
    )
    filter_horizontal = ('groups', 'user_permissions')
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'full_name', 'role', 'is_active', 'is_staff', 'is_superuser'),
        }),
    )


@admin.register(VeterinarianProfile)
class VeterinarianProfileAdmin(ModelAdmin):
    list_display = ['user', 'license_number', 'status', 'avg_rating', 'rating_count', 'total_consultations', 'clinic_name']
    list_filter = ['status', 'created_at']
    list_editable = ['status']
    search_fields = ['user__full_name', 'user__email', 'license_number', 'clinic_name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'avg_rating', 'rating_count', 'total_consultations']
    autocomplete_fields = ['user']

    fieldsets = (
        (_('Account'), {'fields': ('user', 'profile_image', 'status')}),
        (_('Credentials'), {'fields': ('license_number', 'qualification', 'specialization', 'years_experience')}),
        (_('Clinic'), {'fields': ('clinic_name', 'clinic_address', 'location', 'phone_number', 'consultation_fee', 'account_number')}),
        (_('Profile'), {'fields': ('bio',)}),
        (_('Stats'), {'fields': ('avg_rating', 'rating_count', 'total_consultations')}),
        (_('Metadata'), {'fields': ('id', 'created_at', 'updated_at')}),
    )


@admin.register(SellerProfile)
class SellerProfileAdmin(ModelAdmin):
    list_display = ['store_name', 'user', 'is_verified', 'total_products', 'total_sales', 'avg_rating', 'created_at']
    list_filter = ['is_verified', 'created_at']
    list_editable = ['is_verified']
    search_fields = ['store_name', 'user__email', 'user__full_name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'total_products', 'total_sales', 'avg_rating']
    autocomplete_fields = ['user']

    fieldsets = (
        (_('Store'), {'fields': ('user', 'store_name', 'store_description', 'store_logo', 'is_verified')}),
        (_('Contact'), {'fields': ('phone_number', 'address')}),
        (_('Stats'), {'fields': ('total_products', 'total_sales', 'avg_rating')}),
        (_('Metadata'), {'fields': ('id', 'created_at', 'updated_at')}),
    )


@admin.register(VeterinarianReview)
class VeterinarianReviewAdmin(ModelAdmin):
    list_display = ['veterinarian', 'patient', 'rating', 'appointment', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['patient__full_name', 'veterinarian__user__full_name', 'comment']
    readonly_fields = ['id', 'created_at', 'updated_at']
    autocomplete_fields = ['veterinarian', 'patient', 'appointment']

    fieldsets = (
        (None, {'fields': ('veterinarian', 'patient', 'appointment', 'rating', 'comment')}),
        (_('Metadata'), {'fields': ('id', 'created_at', 'updated_at')}),
    )
