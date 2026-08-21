from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .models import Pet


@admin.register(Pet)
class PetAdmin(ModelAdmin):
    list_display = ['name', 'get_owner_info', 'species', 'breed', 'gender', 'weight_kg', 'is_neutered', 'date_of_birth', 'created_at']
    list_filter = ['species', 'gender', 'is_neutered', 'created_at']
    search_fields = ['name', 'breed', 'owner__full_name', 'owner__email', 'microchip_number']
    readonly_fields = ['id', 'created_at', 'updated_at']
    autocomplete_fields = ['owner']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    fieldsets = (
        (_('Owner Information'), {'fields': ('owner',)}),
        (_('Basic Information'), {'fields': ('name', 'species', 'breed', 'picture')}),
        (_('Physical Details'), {'fields': ('date_of_birth', 'gender', 'weight_kg', 'is_neutered')}),
        (_('Medical Information'), {'fields': ('microchip_number', 'allergies', 'blood_type')}),
        (_('Metadata'), {'fields': ('id', 'created_at', 'updated_at')}),
    )

    def get_owner_info(self, obj):
        return f"{obj.owner.full_name} ({obj.owner.email})"
    get_owner_info.short_description = 'Owner'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('owner')
