from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.shortcuts import get_object_or_404
from datetime import datetime, time
from .models import Appointment, AppointmentStatus
from .serializers import AppointmentSerializer
from apps.accounts.models import UserRole


@method_decorator(csrf_exempt, name='dispatch')
class AvailableTimeSlotsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get available time slots for a veterinarian on a specific date.
        Slots are from 9:00-13:00 and 14:00-16:00 in 1-hour intervals.
        Excludes slots with PENDING or CONFIRMED appointments.
        """
        veterinarian_id = request.GET.get('veterinarian_id')
        date_str = request.GET.get('date')
        
        if not veterinarian_id or not date_str:
            return Response(
                {'error': 'veterinarian_id and date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            morning_slots = self._generate_time_slots(time(9, 0), time(13, 0))
            afternoon_slots = self._generate_time_slots(time(14, 0), time(16, 0))
            all_slots = morning_slots + afternoon_slots
            
            existing_appointments = Appointment.objects.filter(
                veterinarian_id=veterinarian_id,
                scheduled_at__date=selected_date,
                status__in=['PENDING', 'CONFIRMED']
            )
            
            booked_times = set()
            for appointment in existing_appointments:
                appointment_time = appointment.scheduled_at.time()
                booked_time = time(appointment_time.hour, 0)
                booked_times.add(booked_time.strftime('%H:%M'))
            
            available_slots = []
            for slot_time in all_slots:
                is_available = slot_time not in booked_times
                hour = int(slot_time.split(':')[0])
                minute = int(slot_time.split(':')[1])
                if hour >= 12:
                    display_hour = hour - 12 if hour > 12 else 12
                    display_time = f"{display_hour}:{minute:02d} PM"
                else:
                    display_time = f"{hour}:{minute:02d} AM"
                
                available_slots.append({
                    'time': slot_time,
                    'display': display_time,
                    'available': is_available
                })
            
            return Response(available_slots)
            
        except ValueError as e:
            return Response(
                {'error': f'Invalid date format: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _generate_time_slots(self, start_time, end_time):
        """Generate 1-hour time slots between start and end time."""
        slots = []
        current = start_time
        while current < end_time:
            slots.append(current.strftime('%H:%M'))
            current = time(current.hour + 1, 0)
        return slots


def _serialize_appointment_full(appt, request):
    """Returns a rich dict with all appointment + related data."""
    vet_profile = appt.veterinarian
    owner = appt.pet
    pet = appt.pet

    vet_image = None
    if vet_profile and vet_profile.profile_image:
        vet_image = request.build_absolute_uri(vet_profile.profile_image.url)

    pet_picture = None
    if pet and pet.picture:
        pet_picture = request.build_absolute_uri(pet.picture.url)

    payment_info = None
    try:
        p = appt.payment
        payment_info = {
            'status': p.status,
            'amount': float(p.amount),
            'currency': p.currency,
            'gateway': p.gateway,
            'gateway_txn_id': p.gateway_txn_id,
            'paid_at': p.paid_at.isoformat() if p.paid_at else None,
        }
    except Exception:
        pass

    # Check if appointment has been reviewed
    has_review = False
    try:
        from apps.accounts.models import VeterinarianReview
        has_review = VeterinarianReview.objects.filter(appointment=appt).exists()
    except Exception:
        pass

    return {
        'id': str(appt.id),
        'has_review': has_review,
        'scheduled_at': appt.scheduled_at.isoformat(),
        'duration_minutes': appt.duration_minutes,
        'status': appt.status,
        'fee_charged': float(appt.fee_charged),
        'reason': appt.reason or '',
        'created_at': appt.created_at.isoformat() if hasattr(appt, 'created_at') else None,
        'vet': {
            'id': str(vet_profile.id) if vet_profile else None,
            'name': vet_profile.user.full_name if vet_profile and vet_profile.user else 'Unknown',
            'image': vet_image,
            'specialization': vet_profile.specialization or '' if vet_profile else '',
            'clinic_name': vet_profile.clinic_name or '' if vet_profile else '',
            'phone_number': vet_profile.phone_number or '' if vet_profile else '',
        },
        'pet': {
            'id': str(pet.id) if pet else None,
            'name': pet.name if pet else '',
            'species': pet.species if pet else '',
            'breed': pet.breed or '' if pet else '',
            'picture': pet_picture,
        },
        'owner': {
            'name': appt.pet_owner.full_name if appt.pet_owner else '',
            'email': appt.pet_owner.email if appt.pet_owner else '',
        },
        'payment': payment_info,
    }


@method_decorator(csrf_exempt, name='dispatch')
class AppointmentListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        List all appointments for the current user (pet owner or vet).
        Returns enriched appointment data.
        """
        try:
            user = request.user
            if user.role == UserRole.VETERINARIAN:
                try:
                    vet_profile = user.vet_profile
                    appointments = Appointment.objects.filter(
                        veterinarian=vet_profile
                    ).select_related('veterinarian__user', 'pet', 'pet_owner').order_by('-scheduled_at')
                except Exception:
                    appointments = Appointment.objects.none()
            else:
                appointments = Appointment.objects.filter(
                    pet_owner=user
                ).select_related('veterinarian__user', 'pet', 'pet_owner').order_by('-scheduled_at')

            data = [_serialize_appointment_full(a, request) for a in appointments]
            return Response(data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        """
        Create a new appointment.
        """
        try:
            serializer = AppointmentSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(pet_owner=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class AppointmentStatusUpdateView(APIView):
    """
    PATCH /api/appointments/<id>/status/
    Update appointment status with role-based permission checks.

    Pet Owner allowed transitions:
      CONFIRMED / PENDING / PENDING_PAYMENT → CANCELLED
      CANCELLED → CONFIRMED  (reactivate, only if future)

    Veterinarian allowed transitions:
      CONFIRMED → IN_PROGRESS  (activate / start)
      IN_PROGRESS → COMPLETED
      CONFIRMED / PENDING / PENDING_PAYMENT / IN_PROGRESS → CANCELLED
    """
    permission_classes = [IsAuthenticated]

    # Maps: (current_status, action) → new_status
    PET_OWNER_TRANSITIONS = {
        ('CONFIRMED', 'cancel'): 'CANCELLED',
        ('PENDING', 'cancel'): 'CANCELLED',
        ('PENDING_PAYMENT', 'cancel'): 'CANCELLED',
        ('CANCELLED', 'activate'): 'CONFIRMED',
    }

    VET_TRANSITIONS = {
        ('CONFIRMED', 'activate'): 'IN_PROGRESS',
        ('CONFIRMED', 'cancel'): 'CANCELLED',
        ('PENDING', 'cancel'): 'CANCELLED',
        ('PENDING_PAYMENT', 'cancel'): 'CANCELLED',
        ('IN_PROGRESS', 'complete'): 'COMPLETED',
        ('IN_PROGRESS', 'cancel'): 'CANCELLED',
    }

    def patch(self, request, appointment_id):
        action = request.data.get('action')  # 'cancel' | 'activate' | 'complete'
        if not action:
            return Response({'error': 'action is required'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        # Fetch appointment based on role
        try:
            if user.role == UserRole.VETERINARIAN:
                appointment = Appointment.objects.select_related(
                    'pet_owner', 'pet', 'veterinarian__user'
                ).get(id=appointment_id, veterinarian=user.vet_profile)
            else:
                appointment = Appointment.objects.select_related(
                    'pet_owner', 'pet', 'veterinarian__user'
                ).get(id=appointment_id, pet_owner=user)
        except Appointment.DoesNotExist:
            return Response({'error': 'Appointment not found'}, status=status.HTTP_404_NOT_FOUND)

        current = appointment.status
        key = (current, action)

        if user.role == UserRole.VETERINARIAN:
            transitions = self.VET_TRANSITIONS
        else:
            transitions = self.PET_OWNER_TRANSITIONS

        if key not in transitions:
            return Response(
                {'error': f"Cannot perform '{action}' on a '{current}' appointment."},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_status = transitions[key]

        # Extra guard: pet owner can only reactivate future appointments
        if user.role != UserRole.VETERINARIAN and action == 'activate':
            if appointment.scheduled_at <= timezone.now():
                return Response(
                    {'error': 'Cannot reactivate a past appointment.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Track who cancelled
        if new_status == 'CANCELLED':
            appointment.cancelled_by = user

        appointment.status = new_status

        # Auto-set paid_at / update total_consultations on complete
        if new_status == 'COMPLETED':
            try:
                vet_profile = user.vet_profile
                vet_profile.total_consultations += 1
                vet_profile.save(update_fields=['total_consultations'])
            except Exception:
                pass

        appointment.save()

        return Response({
            'success': True,
            'new_status': new_status,
            'appointment': _serialize_appointment_full(appointment, request),
        })
