from django.contrib import admin
from .models import Prescription, PrescriptionItem


class PrescriptionItemInline(admin.TabularInline):
    model = PrescriptionItem
    extra = 0
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'appointment', 'issuing_vet', 'pet', 'is_finalized', 'valid_until', 'issued_at', 'created_at']
    list_filter = ['is_finalized', 'issued_at', 'created_at']
    search_fields = ['pet__name', 'issuing_vet__user__full_name', 'diagnosis_text']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [PrescriptionItemInline]
    date_hierarchy = 'issued_at'


@admin.register(PrescriptionItem)
class PrescriptionItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'prescription', 'medicine_name', 'dosage', 'quantity', 'duration_days']
    search_fields = ['medicine_name', 'prescription__pet__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
