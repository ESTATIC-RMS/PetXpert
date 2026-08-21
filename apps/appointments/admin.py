from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .models import Appointment, AppointmentStatus


@admin.action(description='Mark selected as Confirmed')
def mark_confirmed(modeladmin, request, queryset):
    queryset.update(status=AppointmentStatus.CONFIRMED)


@admin.action(description='Mark selected as In Progress')
def mark_in_progress(modeladmin, request, queryset):
    queryset.update(status=AppointmentStatus.IN_PROGRESS)


@admin.action(description='Mark selected as Completed')
def mark_completed(modeladmin, request, queryset):
    queryset.update(status=AppointmentStatus.COMPLETED)


@admin.action(description='Mark selected as Cancelled')
def mark_cancelled(modeladmin, request, queryset):
    queryset.update(status=AppointmentStatus.CANCELLED)


@admin.register(Appointment)
class AppointmentAdmin(ModelAdmin):
    list_display = ['get_pet_owner_info', 'get_vet_info', 'get_pet_info', 'scheduled_at', 'status', 'fee_charged', 'duration_minutes', 'created_at']
    list_filter = ['status', 'scheduled_at', 'created_at']
    list_editable = ['status', 'fee_charged']
    search_fields = ['pet_owner__full_name', 'pet_owner__email', 'veterinarian__user__full_name', 'pet__name', 'reason']
    readonly_fields = ['id', 'created_at', 'updated_at']
    autocomplete_fields = ['pet_owner', 'veterinarian', 'pet', 'cancelled_by']
    date_hierarchy = 'scheduled_at'
    ordering = ['-scheduled_at']
    actions = [mark_confirmed, mark_in_progress, mark_completed, mark_cancelled]

    fieldsets = (
        (_('Participants'), {'fields': ('pet_owner', 'veterinarian', 'pet')}),
        (_('Schedule Information'), {'fields': ('scheduled_at', 'duration_minutes', 'status')}),
        (_('Appointment Details'), {'fields': ('reason', 'fee_charged', 'cancelled_by')}),
        (_('Metadata'), {'fields': ('id', 'created_at', 'updated_at')}),
    )

    def get_pet_owner_info(self, obj):
        return f"{obj.pet_owner.full_name} ({obj.pet_owner.email})"
    get_pet_owner_info.short_description = 'Pet Owner'

    def get_vet_info(self, obj):
        return f"{obj.veterinarian.user.full_name} - {obj.veterinarian.clinic_name or 'N/A'}"
    get_vet_info.short_description = 'Veterinarian'

    def get_pet_info(self, obj):
        return f"{obj.pet.name} ({obj.pet.species})"
    get_pet_info.short_description = 'Pet'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('pet_owner', 'veterinarian__user', 'pet')
