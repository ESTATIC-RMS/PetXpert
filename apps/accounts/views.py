from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.db.models import Avg, Count
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import User, UserRole, VeterinarianProfile, VeterinarianReview, SellerProfile
from .serializers import UserSerializer, VeterinarianProfileSerializer, VeterinarianProfileCompletionSerializer, VeterinarianReviewSerializer, SellerProfileSerializer, SellerProfileUpdateSerializer
from apps.core.permissions import IsPetOwner, IsVeterinarian, IsPetOwnerOrVeterinarian, IsCommunityMember


def _recalculate_vet_rating(veterinarian):
    """Recalculate and save avg_rating and rating_count for a VeterinarianProfile."""
    agg = VeterinarianReview.objects.filter(veterinarian=veterinarian).aggregate(
        avg=Avg('rating'),
        count=Count('id')
    )
    veterinarian.avg_rating = round(agg['avg'] or 0, 2)
    veterinarian.rating_count = agg['count'] or 0
    veterinarian.save(update_fields=['avg_rating', 'rating_count'])

@method_decorator(csrf_exempt, name='dispatch')
class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        full_name = request.data.get('full_name')
        password = request.data.get('password')
        role = request.data.get('role', UserRole.PET_OWNER)

        if not email or not password:
            return Response({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            email=email,
            full_name=full_name,
            password=password,
            role=role
        )

        if role == UserRole.VETERINARIAN:
            VeterinarianProfile.objects.create(user=user)
        elif role == UserRole.SELLER:
            store_name = request.data.get('store_name', '') or f"{full_name}'s Store"
            SellerProfile.objects.create(user=user, store_name=store_name)

        refresh = RefreshToken.for_user(user)

        user_payload = UserSerializer(user, context={'request': request}).data
        if role == UserRole.VETERINARIAN:
            user_payload['is_profile_complete'] = False
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': user_payload,
        }, status=status.HTTP_201_CREATED)

from django.contrib.auth import authenticate

class SigninView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(email=email, password=password)

        if user:
            refresh = RefreshToken.for_user(user)
            
            is_profile_complete = False
            if user.role == UserRole.VETERINARIAN:
                try:
                    is_profile_complete = user.vet_profile.is_profile_complete()
                except VeterinarianProfile.DoesNotExist:
                    is_profile_complete = False

            user_payload = UserSerializer(user, context={'request': request}).data
            user_payload['is_profile_complete'] = is_profile_complete

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': user_payload,
            })
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


@method_decorator(csrf_exempt, name='dispatch')
class ProfileImageUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        
        if 'avatar' not in request.FILES:
            return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        user.avatar = request.FILES['avatar']
        user.save()
        
        serializer = UserSerializer(user, context={'request': request})
        return Response({
            'message': 'Profile image updated successfully',
            'user': serializer.data
        }, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class ProfileImageDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        
        if user.avatar:
            user.avatar.delete()
            user.avatar = None
            user.save()
            return Response({'message': 'Profile image deleted successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'No image to delete'}, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user, context={'request': request})
        data = serializer.data
        
        # Add profile image for veterinarians
        if user.role == UserRole.VETERINARIAN:
            try:
                vet_profile = user.vet_profile
                if vet_profile.profile_image:
                    data['profile_image'] = request.build_absolute_uri(vet_profile.profile_image.url)
                else:
                    data['profile_image'] = None
            except VeterinarianProfile.DoesNotExist:
                data['profile_image'] = None
        
        return Response(data, status=status.HTTP_200_OK)

    def put(self, request):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class VeterinarianProfileImageUploadView(APIView):
    permission_classes = [IsVeterinarian]

    def post(self, request):
        user = request.user
        
        if user.role != UserRole.VETERINARIAN:
            return Response({'error': 'Only veterinarians can upload profile images'}, status=status.HTTP_403_FORBIDDEN)
        
        if 'profile_image' not in request.FILES:
            return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        vet_profile = user.vet_profile
        vet_profile.profile_image = request.FILES['profile_image']
        vet_profile.save()
        
        serializer = VeterinarianProfileSerializer(vet_profile)
        return Response({
            'message': 'Profile image updated successfully',
            'profile': serializer.data
        }, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class VeterinarianProfileImageDeleteView(APIView):
    permission_classes = [IsVeterinarian]

    def delete(self, request):
        user = request.user
        
        if user.role != UserRole.VETERINARIAN:
            return Response({'error': 'Only veterinarians can delete profile images'}, status=status.HTTP_403_FORBIDDEN)
        
        vet_profile = user.vet_profile
        
        if vet_profile.profile_image:
            vet_profile.profile_image.delete()
            vet_profile.profile_image = None
            vet_profile.save()
            return Response({'message': 'Profile image deleted successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'No image to delete'}, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class VeterinarianProfileUpdateView(APIView):
    permission_classes = [IsVeterinarian]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get(self, request):
        user = request.user
        if user.role != UserRole.VETERINARIAN:
            return Response({'error': 'Only veterinarians can access this profile'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            profile = user.vet_profile
        except VeterinarianProfile.DoesNotExist:
            profile = VeterinarianProfile.objects.create(user=user)
            
        serializer = VeterinarianProfileSerializer(profile)
        return Response(serializer.data)

    def put(self, request):
        user = request.user
        if user.role != UserRole.VETERINARIAN:
            return Response({'error': 'Only veterinarians can update this profile'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            profile = user.vet_profile
        except VeterinarianProfile.DoesNotExist:
            profile = VeterinarianProfile.objects.create(user=user)

        complete_mode = request.query_params.get('complete', '').lower() in ('1', 'true', 'yes')
        if complete_mode or not profile.is_profile_complete():
            serializer = VeterinarianProfileCompletionSerializer(profile, data=request.data, partial=False)
        else:
            serializer = VeterinarianProfileSerializer(profile, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            profile.refresh_from_db()
            response_serializer = VeterinarianProfileSerializer(profile)
            return Response(response_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VeterinarianListView(APIView):
    permission_classes = [IsPetOwnerOrVeterinarian]

    def get(self, request):
        # Only list verified veterinarians (or all for now for testing)
        vets = VeterinarianProfile.objects.select_related('user').all()
        serializer = VeterinarianProfileSerializer(vets, many=True)
        return Response(serializer.data)


class SellerProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        user = request.user
        if user.role != UserRole.SELLER:
            return Response({'error': 'Only sellers can access this profile'}, status=status.HTTP_403_FORBIDDEN)

        try:
            profile = user.seller_profile
        except SellerProfile.DoesNotExist:
            profile = SellerProfile.objects.create(user=user)

        serializer = SellerProfileSerializer(profile)
        return Response(serializer.data)

    def put(self, request):
        user = request.user
        if user.role != UserRole.SELLER:
            return Response({'error': 'Only sellers can update this profile'}, status=status.HTTP_403_FORBIDDEN)

        try:
            profile = user.seller_profile
        except SellerProfile.DoesNotExist:
            profile = SellerProfile.objects.create(user=user)

        # Handle both JSON and FormData requests
        if request.content_type.startswith('multipart/form-data'):
            serializer = SellerProfileUpdateSerializer(profile, data=request.data, partial=True)
        else:
            serializer = SellerProfileUpdateSerializer(profile, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            profile.refresh_from_db()
            response_serializer = SellerProfileSerializer(profile)
            return Response(response_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VeterinarianReviewListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsPetOwner()]
        return [IsAuthenticated()]

    def get(self, request, veterinarian_id):
        """
        List all reviews for a specific veterinarian.
        """
        try:
            veterinarian = VeterinarianProfile.objects.get(id=veterinarian_id)
        except VeterinarianProfile.DoesNotExist:
            return Response({'error': 'Veterinarian not found'}, status=status.HTTP_404_NOT_FOUND)
        
        reviews = VeterinarianReview.objects.filter(veterinarian=veterinarian).select_related('patient', 'appointment')
        serializer = VeterinarianReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    def post(self, request, veterinarian_id):
        """
        Create a new review for a veterinarian.
        """
        try:
            veterinarian = VeterinarianProfile.objects.get(id=veterinarian_id)
        except VeterinarianProfile.DoesNotExist:
            return Response({'error': 'Veterinarian not found'}, status=status.HTTP_404_NOT_FOUND)

        # Add veterinarian to the data
        request.data['veterinarian'] = veterinarian.id

        serializer = VeterinarianReviewSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            review = serializer.save(patient=request.user)
            # Recalculate avg_rating on the vet profile
            _recalculate_vet_rating(veterinarian)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VeterinarianReviewDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, review_id):
        """
        Get a specific review.
        """
        try:
            review = VeterinarianReview.objects.get(id=review_id)
        except VeterinarianReview.DoesNotExist:
            return Response({'error': 'Review not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Only allow the reviewer or the veterinarian being reviewed to see the review
        if review.patient != request.user and review.veterinarian.user != request.user:
            return Response({'error': 'You do not have permission to view this review'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = VeterinarianReviewSerializer(review)
        return Response(serializer.data)

    def put(self, request, review_id):
        """
        Update a review (only by the original reviewer).
        """
        try:
            review = VeterinarianReview.objects.get(id=review_id)
        except VeterinarianReview.DoesNotExist:
            return Response({'error': 'Review not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Only allow the original reviewer to update
        if review.patient != request.user:
            return Response({'error': 'You can only update your own reviews'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = VeterinarianReviewSerializer(review, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, review_id):
        """
        Delete a review (only by the original reviewer).
        """
        try:
            review = VeterinarianReview.objects.get(id=review_id)
        except VeterinarianReview.DoesNotExist:
            return Response({'error': 'Review not found'}, status=status.HTTP_404_NOT_FOUND)

        # Only allow the original reviewer to delete
        if review.patient != request.user:
            return Response({'error': 'You can only delete your own reviews'}, status=status.HTTP_403_FORBIDDEN)

        veterinarian = review.veterinarian
        review.delete()
        # Recalculate avg_rating after deletion
        _recalculate_vet_rating(veterinarian)
        return Response({'message': 'Review deleted successfully'}, status=status.HTTP_200_OK)


class UserReviewListView(APIView):
    permission_classes = [IsPetOwner]

    def get(self, request):
        """
        List all reviews by the current user.
        """
        reviews = VeterinarianReview.objects.filter(patient=request.user).select_related('veterinarian__user', 'appointment')
        serializer = VeterinarianReviewSerializer(reviews, many=True)
        return Response(serializer.data)


class PublicStatsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """
        Get public statistics for the landing page.
        """
        from apps.pets.models import Pet
        
        user_count = User.objects.count()
        pet_count = Pet.objects.count()
        vet_count = VeterinarianProfile.objects.count()
        
        return Response({
            'user_count': user_count,
            'pet_count': pet_count,
            'vet_count': vet_count
        }, status=status.HTTP_200_OK)


class AppointmentReviewView(APIView):
    permission_classes = [IsPetOwnerOrVeterinarian]

    def get(self, request, appointment_id):
        """
        Get the review for a specific appointment (if it exists).
        """
        try:
            review = VeterinarianReview.objects.get(appointment_id=appointment_id)
        except VeterinarianReview.DoesNotExist:
            return Response({'review': None}, status=status.HTTP_200_OK)
        
        # Only allow the reviewer or the veterinarian being reviewed to see the review
        if review.patient != request.user and review.veterinarian.user != request.user:
            return Response({'error': 'You do not have permission to view this review'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = VeterinarianReviewSerializer(review)
        return Response(serializer.data)


def veterinarian_detail_page(request, veterinarian_id):
    veterinarian = get_object_or_404(VeterinarianProfile, id=veterinarian_id)
    return render(request, 'veterinarians/detail.html', {'veterinarian': veterinarian})


def book_appointment_page(request, veterinarian_id):
    veterinarian = get_object_or_404(VeterinarianProfile, id=veterinarian_id)
    return render(request, 'appointments/book.html', {'veterinarian': veterinarian})


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.utils import timezone
        from apps.appointments.models import Appointment
        from apps.payments.models import Payment, PaymentStatus

        user = request.user
        now = timezone.now()
        today = now.date()

        if user.role == UserRole.PET_OWNER:
            # --- Pet Owner Stats ---
            from apps.pets.models import Pet

            pets = Pet.objects.filter(owner=user).values('id', 'name', 'species', 'breed', 'picture', 'date_of_birth')
            pets_list = []
            for pet in pets:
                picture_url = None
                if pet['picture']:
                    picture_url = f"{settings.MEDIA_URL}{pet['picture']}"
                pets_list.append({
                    'id': str(pet['id']),
                    'name': pet['name'],
                    'species': pet['species'],
                    'breed': pet['breed'] or '',
                    'picture': picture_url,
                    'date_of_birth': str(pet['date_of_birth']) if pet['date_of_birth'] else None,
                })

            appointments = Appointment.objects.filter(
                pet_owner=user
            ).select_related('veterinarian__user', 'pet').order_by('scheduled_at')

            upcoming = []
            past = []
            for appt in appointments:
                vet_profile = appt.veterinarian
                vet_name = vet_profile.user.full_name if vet_profile and vet_profile.user else 'Unknown'
                vet_image = None
                if vet_profile and vet_profile.profile_image:
                    vet_image = request.build_absolute_uri(vet_profile.profile_image.url)

                entry = {
                    'id': str(appt.id),
                    'scheduled_at': appt.scheduled_at.isoformat(),
                    'status': appt.status,
                    'pet_name': appt.pet.name if appt.pet else '',
                    'vet_name': vet_name,
                    'vet_image': vet_image,
                    'fee_charged': float(appt.fee_charged),
                    'reason': appt.reason or '',
                }
                if appt.status in ('COMPLETED', 'CANCELLED', 'NO_SHOW'):
                    past.append(entry)
                elif appt.status in ('CONFIRMED', 'PENDING_PAYMENT', 'PENDING', 'IN_PROGRESS') and appt.scheduled_at >= now:
                    upcoming.append(entry)
                else:
                    past.append(entry)

            # Total spent — sum of completed payments
            total_spent = 0.0
            try:
                payments = Payment.objects.filter(
                    appointment__pet_owner=user,
                    status=PaymentStatus.COMPLETED
                )
                total_spent = float(sum(p.amount for p in payments))
            except Exception:
                pass

            return Response({
                'role': 'PET_OWNER',
                'stats': {
                    'pets_count': len(pets_list),
                    'upcoming_appointments_count': len(upcoming),
                    'total_spent': total_spent,
                    'total_appointments': appointments.count(),
                },
                'pets': pets_list[:4],  # Show up to 4 on dashboard
                'upcoming_appointments': upcoming[:5],
                'recent_appointments': sorted(past, key=lambda x: x['scheduled_at'], reverse=True)[:3],
            })

        elif user.role == UserRole.VETERINARIAN:
            # --- Veterinarian Stats ---
            try:
                vet_profile = user.vet_profile
            except VeterinarianProfile.DoesNotExist:
                vet_profile = None

            appointments = Appointment.objects.filter(
                veterinarian=vet_profile
            ).select_related('pet_owner', 'pet').order_by('scheduled_at') if vet_profile else Appointment.objects.none()

            today_appointments = []
            upcoming_appointments = []
            pending_appointments = []

            for appt in appointments:
                owner = appt.pet_owner
                entry = {
                    'id': str(appt.id),
                    'scheduled_at': appt.scheduled_at.isoformat(),
                    'status': appt.status,
                    'pet_name': appt.pet.name if appt.pet else '',
                    'pet_species': appt.pet.species if appt.pet else '',
                    'owner_name': owner.full_name if owner else 'Unknown',
                    'owner_email': owner.email if owner else '',
                    'fee_charged': float(appt.fee_charged),
                    'reason': appt.reason or '',
                }
                if appt.scheduled_at.date() == today and appt.status == 'CONFIRMED':
                    today_appointments.append(entry)
                if appt.scheduled_at >= now and appt.status == 'CONFIRMED':
                    upcoming_appointments.append(entry)
                if appt.status in ('PENDING_PAYMENT', 'PENDING'):
                    pending_appointments.append(entry)

            # Earnings — sum of consultation fees from completed appointments (not including tax)
            total_earnings = 0.0
            try:
                from apps.appointments.models import Appointment
                earnings_qs = Appointment.objects.filter(
                    veterinarian=vet_profile,
                    status='COMPLETED'
                )
                total_earnings = float(sum(appt.fee_charged for appt in earnings_qs))
            except Exception:
                pass

            profile_complete = bool(vet_profile and vet_profile.is_profile_complete())

            return Response({
                'role': 'VETERINARIAN',
                'stats': {
                    'today_count': len(today_appointments),
                    'upcoming_count': len(upcoming_appointments),
                    'pending_count': len(pending_appointments),
                    'total_consultations': vet_profile.total_consultations if vet_profile else 0,
                    'avg_rating': float(vet_profile.avg_rating) if vet_profile else 0.0,
                    'rating_count': vet_profile.rating_count if vet_profile else 0,
                    'total_earnings': total_earnings,
                },
                'profile_complete': profile_complete,
                'today_appointments': today_appointments,
                'upcoming_appointments': upcoming_appointments[:5],
                'pending_appointments': pending_appointments[:5],
            })

        elif user.role == UserRole.SELLER:
            return Response({'role': 'SELLER', 'stats': {}})
        return Response({'error': 'Unsupported role'}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        new_password = request.data.get('new_password')
        
        if not email or not new_password:
            return Response({'error': 'Email and new password are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'No account found with this email'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password directly
        user.set_password(new_password)
        user.save()
        
        return Response({'message': 'Password has been reset successfully'}, status=status.HTTP_200_OK)
