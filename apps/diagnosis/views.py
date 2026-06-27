from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.models import Notification, NotificationType
from . import llm_service, ml_engine
from .models import DiagnosisInputType, DiagnosisRecord, DiagnosisSeverity, DiagnosisStatus
from .serializers import (
    DiagnosisChatSerializer,
    DiagnosisRecordSerializer,
    DiagnosisRequestSerializer,
)


def _decimal_score(value):
    value = min(max(float(value or 0), 0.0), 1.0)
    return Decimal(str(value)).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)


def _create_notification(record):
    disease = 'Unknown'
    if record.predicted_diseases:
        disease = record.predicted_diseases[0].get('disease', 'Unknown')
    Notification.objects.create(
        recipient=record.requested_by,
        title='AI diagnosis completed',
        content=f'{record.pet.name}: {disease} ({record.get_severity_display()})',
        notification_type=NotificationType.GENERAL,
        related_id=record.id,
        related_type='diagnosis',
    )


@method_decorator(csrf_exempt, name='dispatch')
class DiagnoseImageView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def post(self, request):
        serializer = DiagnosisRequestSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        pet = serializer.validated_data['pet']
        symptom_text = serializer.validated_data.get('symptom_text') or ''
        input_type = DiagnosisInputType.BOTH if symptom_text else DiagnosisInputType.IMAGE

        record = DiagnosisRecord.objects.create(
            pet=pet,
            requested_by=request.user,
            input_type=input_type,
            image=serializer.validated_data['image'],
            symptom_text=symptom_text,
            predicted_diseases=[],
            severity=DiagnosisSeverity.LOW,
            risk_score=Decimal('0.000'),
            status=DiagnosisStatus.PROCESSING,
            model_version=getattr(settings, 'ML_MODEL_VERSION', '1.0.0'),
            inference_time_ms=0,
        )

        prediction = ml_engine.predict(record.image.path)
        disease = prediction.get('disease', 'Unknown')
        similarity = prediction.get('similarity', prediction.get('risk_score', 0.0))
        explanation = ''

        if prediction.get('success') and disease != 'Unknown':
            explanation = llm_service.explain_disease(
                disease,
                severity=prediction.get('severity', DiagnosisSeverity.LOW),
                similarity=float(similarity or 0.0),
            )

        record.predicted_diseases = prediction.get('predicted_diseases', [])
        if disease == 'Unknown':
            record.predicted_diseases = [{'disease': 'Unknown', 'similarity': similarity}]
        elif disease and not record.predicted_diseases:
            record.predicted_diseases = [{'disease': disease, 'similarity': similarity}]
        record.severity = prediction.get('severity', DiagnosisSeverity.LOW)
        record.risk_score = _decimal_score(prediction.get('risk_score', similarity))
        record.status = DiagnosisStatus.COMPLETED if prediction.get('success') else DiagnosisStatus.FAILED
        record.model_version = prediction.get('model_version', getattr(settings, 'ML_MODEL_VERSION', '1.0.0'))
        record.inference_time_ms = prediction.get('inference_time_ms')
        record.llm_explanation = explanation
        record.save()

        if record.status == DiagnosisStatus.COMPLETED:
            _create_notification(record)

        return Response({
            'record': DiagnosisRecordSerializer(record).data,
            'result': prediction,
        }, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class DiagnosisChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DiagnosisChatSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        answer = llm_service.pet_chat(serializer.validated_data['question'])
        return Response({'answer': answer})


@method_decorator(csrf_exempt, name='dispatch')
class DiagnosisAssistantView(APIView):
    """Unified chat endpoint: optional image (runs detector) + optional text."""

    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def post(self, request):
        message = (request.data.get('message') or '').strip()
        image = request.FILES.get('image')

        if not message and not image:
            return Response(
                {'error': 'Please type a message or attach an image.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        detection = None
        if image is not None:
            detection = ml_engine.predict(image)

        answer = llm_service.assistant_reply(message, detection)

        summary = None
        if detection is not None:
            summary = {
                'is_dog': detection.get('is_dog', False),
                'disease': detection.get('disease', 'Unknown'),
                'similarity': detection.get('similarity'),
                'severity': detection.get('severity', 'LOW'),
                'message': detection.get('message', ''),
                'feature_unavailable': detection.get('feature_unavailable', False),
            }

        return Response({'answer': answer, 'detection': summary})


class DiagnosisHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        records = DiagnosisRecord.objects.filter(
            requested_by=request.user,
            is_deleted=False,
        ).select_related('pet').order_by('-created_at')
        return Response(DiagnosisRecordSerializer(records, many=True).data)


class DiagnosisDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, diagnosis_id):
        try:
            record = DiagnosisRecord.objects.select_related('pet').get(
                id=diagnosis_id,
                requested_by=request.user,
                is_deleted=False,
            )
        except DiagnosisRecord.DoesNotExist:
            return Response({'error': 'Diagnosis record not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(DiagnosisRecordSerializer(record).data)
