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
    list_display = ['pet_owner', 'veterinarian', 'pet', 'scheduled_at', 'status', 'fee_charged', 'created_at']
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
        (_('Schedule'), {'fields': ('scheduled_at', 'duration_minutes', 'status')}),
        (_('Details'), {'fields': ('reason', 'fee_charged', 'cancelled_by')}),
        (_('Metadata'), {'fields': ('id', 'created_at', 'updated_at')}),
    )
