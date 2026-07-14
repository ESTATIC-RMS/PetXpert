from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline

from .models import Prescription, PrescriptionItem


class PrescriptionItemInline(TabularInline):
    model = PrescriptionItem
    extra = 0
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Prescription)
class PrescriptionAdmin(ModelAdmin):
    list_display = ['appointment', 'issuing_vet', 'pet', 'is_finalized', 'valid_until', 'issued_at', 'created_at']
    list_filter = ['is_finalized', 'issued_at', 'created_at']
    list_editable = ['is_finalized']
    search_fields = ['pet__name', 'issuing_vet__user__full_name', 'diagnosis_text']
    readonly_fields = ['id', 'created_at', 'updated_at']
    autocomplete_fields = ['appointment', 'issuing_vet', 'pet']
    inlines = [PrescriptionItemInline]
    date_hierarchy = 'issued_at'

    fieldsets = (
        (_('Prescription'), {'fields': ('appointment', 'issuing_vet', 'pet', 'is_finalized')}),
        (_('Clinical'), {'fields': ('diagnosis_text', 'instructions', 'issued_at', 'valid_until')}),
        (_('Metadata'), {'fields': ('id', 'created_at', 'updated_at')}),
    )


@admin.register(PrescriptionItem)
class PrescriptionItemAdmin(ModelAdmin):
    list_display = ['prescription', 'medicine_name', 'dosage', 'quantity', 'duration_days']
    search_fields = ['medicine_name', 'prescription__pet__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
