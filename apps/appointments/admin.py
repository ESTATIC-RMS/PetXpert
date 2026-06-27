from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'pet_owner', 'veterinarian', 'pet', 'scheduled_at', 'status', 'fee_charged', 'created_at']
    list_filter = ['status', 'scheduled_at', 'created_at']
    search_fields = ['pet_owner__full_name', 'veterinarian__user__full_name', 'pet__name', 'reason']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'scheduled_at'
