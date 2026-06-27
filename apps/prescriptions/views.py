from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404

from .models import Prescription
from .serializers import PrescriptionDetailSerializer, PrescriptionCreateSerializer
from apps.accounts.models import UserRole

@method_decorator(csrf_exempt, name='dispatch')
class PrescriptionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            if user.role == UserRole.VETERINARIAN:
                try:
                    vet_profile = user.vet_profile
                    prescriptions = Prescription.objects.filter(
                        issuing_vet=vet_profile,
                        is_deleted=False
                    ).select_related(
                        'appointment',
                        'issuing_vet__user',
                        'pet'
                    ).prefetch_related('items').order_by('-issued_at')
                except Exception:
                    prescriptions = Prescription.objects.none()
            else:
                prescriptions = Prescription.objects.filter(
                    pet__owner=user,
                    is_deleted=False
                ).select_related(
                    'appointment',
                    'issuing_vet__user',
                    'pet'
                ).prefetch_related('items').order_by('-issued_at')

            serializer = PrescriptionDetailSerializer(prescriptions, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        user = request.user
        if user.role != UserRole.VETERINARIAN:
            return Response(
                {'error': 'Only veterinarians can create prescriptions.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            serializer = PrescriptionCreateSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                prescription = serializer.save()
                # Serialize the new prescription with the detail serializer
                detail_serializer = PrescriptionDetailSerializer(prescription)
                return Response(detail_serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            import traceback
            error_details = {
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            return Response(error_details, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(csrf_exempt, name='dispatch')
class PrescriptionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            user = request.user
            prescription = get_object_or_404(Prescription, id=pk, is_deleted=False)
            
            # Access control
            if user.role == UserRole.VETERINARIAN:
                try:
                    vet_profile = user.vet_profile
                    if prescription.issuing_vet != vet_profile:
                        return Response(
                            {'error': 'You do not have access to this prescription.'},
                            status=status.HTTP_403_FORBIDDEN
                        )
                except Exception:
                    return Response(
                        {'error': 'Veterinarian profile not found.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            else:
                if prescription.pet.owner != user:
                    return Response(
                        {'error': 'You do not have access to this prescription.'},
                        status=status.HTTP_403_FORBIDDEN
                    )

            serializer = PrescriptionDetailSerializer(prescription)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
