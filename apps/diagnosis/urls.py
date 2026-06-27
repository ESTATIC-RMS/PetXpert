from django.urls import path

from .views import (
    DiagnoseImageView,
    DiagnosisAssistantView,
    DiagnosisChatView,
    DiagnosisDetailView,
    DiagnosisHistoryView,
)


urlpatterns = [
    path('analyze/', DiagnoseImageView.as_view(), name='diagnosis_analyze'),
    path('assistant/', DiagnosisAssistantView.as_view(), name='diagnosis_assistant'),
    path('chat/', DiagnosisChatView.as_view(), name='diagnosis_chat'),
    path('history/', DiagnosisHistoryView.as_view(), name='diagnosis_history'),
    path('<uuid:diagnosis_id>/', DiagnosisDetailView.as_view(), name='diagnosis_detail'),
]
