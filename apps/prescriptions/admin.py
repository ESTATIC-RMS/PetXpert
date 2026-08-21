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
    list_display = ['get_vet_info', 'get_pet_info', 'get_owner_info', 'is_finalized', 'valid_until', 'issued_at', 'created_at']
    list_filter = ['is_finalized', 'issued_at', 'created_at']
    list_editable = ['is_finalized']
    search_fields = ['pet__name', 'issuing_vet__user__full_name', 'issuing_vet__user__email', 'diagnosis_text']
    readonly_fields = ['id', 'created_at', 'updated_at']
    autocomplete_fields = ['appointment', 'issuing_vet', 'pet']
    inlines = [PrescriptionItemInline]
    date_hierarchy = 'issued_at'
    ordering = ['-issued_at']

    fieldsets = (
        (_('Prescription Details'), {'fields': ('appointment', 'issuing_vet', 'pet', 'is_finalized')}),
        (_('Clinical Information'), {'fields': ('diagnosis_text', 'instructions', 'issued_at', 'valid_until')}),
        (_('Metadata'), {'fields': ('id', 'created_at', 'updated_at')}),
    )

    def get_vet_info(self, obj):
        return f"{obj.issuing_vet.user.full_name} - {obj.issuing_vet.clinic_name or 'N/A'}"
    get_vet_info.short_description = 'Veterinarian'

    def get_pet_info(self, obj):
        return f"{obj.pet.name} ({obj.pet.species})"
    get_pet_info.short_description = 'Pet'

    def get_owner_info(self, obj):
        return f"{obj.pet.owner.full_name} ({obj.pet.owner.email})"
    get_owner_info.short_description = 'Owner'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('issuing_vet__user', 'pet__owner', 'appointment')


@admin.register(PrescriptionItem)
class PrescriptionItemAdmin(ModelAdmin):
    list_display = ['get_prescription_info', 'medicine_name', 'dosage', 'quantity', 'duration_days', 'created_at']
    search_fields = ['medicine_name', 'prescription__pet__name', 'prescription__issuing_vet__user__full_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'

    def get_prescription_info(self, obj):
        return f"{obj.prescription.pet.name} - {obj.prescription.issuing_vet.user.full_name}"
    get_prescription_info.short_description = 'Prescription'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('prescription__pet', 'prescription__issuing_vet__user')
