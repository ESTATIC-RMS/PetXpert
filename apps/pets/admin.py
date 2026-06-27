from django.contrib import admin
from .models import Pet


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ['id', 'owner', 'name', 'species', 'breed', 'date_of_birth', 'created_at']
    list_filter = ['species', 'created_at']
    search_fields = ['name', 'breed', 'owner__full_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
