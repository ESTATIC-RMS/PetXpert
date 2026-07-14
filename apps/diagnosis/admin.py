from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .models import DiagnosisRecord


@admin.register(DiagnosisRecord)
class DiagnosisRecordAdmin(ModelAdmin):
    list_display = ['pet', 'requested_by', 'input_type', 'severity', 'status', 'risk_score', 'model_version', 'created_at']
    list_filter = ['input_type', 'severity', 'status', 'created_at']
    list_editable = ['severity', 'status']
    search_fields = ['pet__name', 'requested_by__email', 'requested_by__full_name', 'symptom_text', 'llm_explanation']
    readonly_fields = ['id', 'predicted_diseases', 'risk_score', 'inference_time_ms', 'model_version', 'created_at', 'updated_at']
    autocomplete_fields = ['pet', 'requested_by']
    ordering = ['-created_at']

    fieldsets = (
        (_('Request'), {'fields': ('pet', 'requested_by', 'input_type', 'image', 'symptom_text')}),
        (_('Results'), {'fields': ('predicted_diseases', 'severity', 'risk_score', 'status', 'llm_explanation')}),
        (_('Model'), {'fields': ('model_version', 'inference_time_ms', 'celery_task_id')}),
        (_('Metadata'), {'fields': ('id', 'created_at', 'updated_at')}),
    )
