from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .models import DiagnosisRecord


@admin.register(DiagnosisRecord)
class DiagnosisRecordAdmin(ModelAdmin):
    list_display = ['get_pet_info', 'get_user_info', 'input_type', 'severity', 'status', 'risk_score', 'predicted_disease_preview', 'created_at']
    list_filter = ['input_type', 'severity', 'status', 'created_at']
    list_editable = ['severity', 'status']
    search_fields = ['pet__name', 'requested_by__email', 'requested_by__full_name', 'symptom_text', 'llm_explanation']
    readonly_fields = ['id', 'predicted_diseases', 'risk_score', 'inference_time_ms', 'model_version', 'created_at', 'updated_at']
    autocomplete_fields = ['pet', 'requested_by']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    fieldsets = (
        (_('Request Information'), {'fields': ('pet', 'requested_by', 'input_type', 'image', 'symptom_text')}),
        (_('Diagnosis Results'), {'fields': ('predicted_diseases', 'severity', 'risk_score', 'status', 'llm_explanation')}),
        (_('Model Information'), {'fields': ('model_version', 'inference_time_ms', 'celery_task_id')}),
        (_('Metadata'), {'fields': ('id', 'created_at', 'updated_at')}),
    )

    def get_pet_info(self, obj):
        return f"{obj.pet.name} ({obj.pet.species})"
    get_pet_info.short_description = 'Pet'

    def get_user_info(self, obj):
        return f"{obj.requested_by.full_name} ({obj.requested_by.email})"
    get_user_info.short_description = 'Requested By'

    def predicted_disease_preview(self, obj):
        if obj.predicted_diseases:
            diseases = obj.predicted_diseases[:3] if isinstance(obj.predicted_diseases, list) else str(obj.predicted_diseases)[:50]
            return str(diseases) + '...' if len(str(diseases)) > 47 else str(diseases)
        return 'N/A'
    predicted_disease_preview.short_description = 'Predicted Disease'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('pet', 'requested_by')
