from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline

from .admin_forms import (
    PetXpertAdminPasswordChangeForm,
    PetXpertUserAddForm,
    PetXpertUserChangeForm,
)
from .models import SellerProfile, User, VeterinarianProfile, VeterinarianReview


class VeterinarianProfileInline(TabularInline):
    model = VeterinarianProfile
    can_delete = False
    verbose_name_plural = 'Veterinarian Profile'
    readonly_fields = ['license_number', 'status', 'clinic_name', 'phone_number', 'avg_rating']
    extra = 0


class SellerProfileInline(TabularInline):
    model = SellerProfile
    can_delete = False
    verbose_name_plural = 'Seller Profile'
    readonly_fields = ['store_name', 'is_verified', 'phone_number', 'total_products', 'total_sales']
    extra = 0


@admin.register(User)
class UserAdmin(DjangoUserAdmin, ModelAdmin):
    form = PetXpertUserChangeForm
    add_form = PetXpertUserAddForm
    change_password_form = PetXpertAdminPasswordChangeForm

    list_display = ['email', 'full_name', 'role', 'is_active', 'is_staff', 'is_email_verified', 'created_at', 'get_profile_info']
    list_filter = ['role', 'is_active', 'is_staff', 'is_email_verified', 'created_at']
    list_editable = ['is_active', 'role']
    search_fields = ['email', 'full_name']
    ordering = ['-created_at']
    readonly_fields = ['id', 'last_login', 'created_at', 'updated_at']
    inlines = [VeterinarianProfileInline, SellerProfileInline]

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

    def get_profile_info(self, obj):
        if obj.role == 'VETERINARIAN':
            try:
                vet = obj.vet_profile
                return f"Vet: {vet.clinic_name or 'N/A'} ({vet.status})"
            except:
                return "Vet: No Profile"
        elif obj.role == 'SELLER':
            try:
                seller = obj.seller_profile
                return f"Seller: {seller.store_name or 'N/A'} ({'Verified' if seller.is_verified else 'Unverified'})"
            except:
                return "Seller: No Profile"
        return "Pet Owner"
    get_profile_info.short_description = 'Profile Info'


@admin.register(VeterinarianProfile)
class VeterinarianProfileAdmin(ModelAdmin):
    list_display = ['get_user_info', 'license_number', 'status', 'clinic_name', 'location', 'phone_number', 'consultation_fee', 'avg_rating', 'total_consultations', 'created_at']
    list_filter = ['status', 'location', 'specialization', 'created_at']
    list_editable = ['status', 'consultation_fee']
    search_fields = ['user__full_name', 'user__email', 'license_number', 'clinic_name', 'specialization']
    readonly_fields = ['id', 'created_at', 'updated_at', 'avg_rating', 'rating_count', 'total_consultations']
    autocomplete_fields = ['user']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    fieldsets = (
        (_('User Account'), {'fields': ('user', 'profile_image', 'status')}),
        (_('Professional Credentials'), {'fields': ('license_number', 'qualification', 'specialization', 'years_experience')}),
        (_('Clinic Information'), {'fields': ('clinic_name', 'clinic_address', 'location', 'phone_number', 'consultation_fee', 'account_number')}),
        (_('Professional Profile'), {'fields': ('bio',)}),
        (_('Performance Statistics'), {'fields': ('avg_rating', 'rating_count', 'total_consultations')}),
        (_('Metadata'), {'fields': ('id', 'created_at', 'updated_at')}),
    )

    def get_user_info(self, obj):
        return f"{obj.user.full_name} ({obj.user.email})"
    get_user_info.short_description = 'Veterinarian'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')


@admin.register(SellerProfile)
class SellerProfileAdmin(ModelAdmin):
    list_display = ['store_name', 'get_user_info', 'is_verified', 'phone_number', 'total_products', 'total_sales', 'avg_rating', 'created_at']
    list_filter = ['is_verified', 'created_at']
    list_editable = ['is_verified']
    search_fields = ['store_name', 'user__email', 'user__full_name', 'address']
    readonly_fields = ['id', 'created_at', 'updated_at', 'total_products', 'total_sales', 'avg_rating']
    autocomplete_fields = ['user']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    fieldsets = (
        (_('User Account'), {'fields': ('user', 'store_logo', 'is_verified')}),
        (_('Store Information'), {'fields': ('store_name', 'store_description')}),
        (_('Contact Information'), {'fields': ('phone_number', 'address', 'account_number')}),
        (_('Business Statistics'), {'fields': ('total_products', 'total_sales', 'avg_rating')}),
        (_('Metadata'), {'fields': ('id', 'created_at', 'updated_at')}),
    )

    def get_user_info(self, obj):
        return f"{obj.user.full_name} ({obj.user.email})"
    get_user_info.short_description = 'Owner'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')


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
