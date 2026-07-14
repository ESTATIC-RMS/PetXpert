from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .models import Pet


@admin.register(Pet)
class PetAdmin(ModelAdmin):
    list_display = ['name', 'owner', 'species', 'breed', 'gender', 'weight_kg', 'date_of_birth', 'created_at']
    list_filter = ['species', 'gender', 'is_neutered', 'created_at']
    search_fields = ['name', 'breed', 'owner__full_name', 'owner__email', 'microchip_number']
    readonly_fields = ['id', 'created_at', 'updated_at']
    autocomplete_fields = ['owner']
    ordering = ['-created_at']

    fieldsets = (
        (_('Basic Info'), {'fields': ('owner', 'name', 'species', 'breed', 'picture')}),
        (_('Details'), {'fields': ('date_of_birth', 'gender', 'weight_kg', 'is_neutered')}),
        (_('Medical'), {'fields': ('microchip_number', 'allergies', 'blood_type')}),
        (_('Metadata'), {'fields': ('id', 'created_at', 'updated_at')}),
    )
