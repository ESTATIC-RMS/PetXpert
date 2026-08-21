from rest_framework import serializers
import re
from .models import User, VeterinarianProfile, VeterinarianReview, SellerProfile

PHONE_REGEX = re.compile(r'^[\+]?[\d\s\-\(\)]{7,20}$')
LICENSE_REGEX = re.compile(r'^[A-Za-z0-9\-\/]{4,50}$')

class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'avatar', 'role']
        read_only_fields = ['id', 'email', 'role']

    def get_avatar(self, obj):
        request = self.context.get('request')
        if obj.avatar:
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None

class VeterinarianProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    is_profile_complete = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = VeterinarianProfile
        fields = [
            'id', 'user', 'profile_image', 'license_number', 'status', 'years_experience',
            'consultation_fee', 'bio', 'avg_rating', 'rating_count', 'total_consultations', 'location',
            'specialization', 'clinic_name', 'clinic_address', 'phone_number', 'qualification',
            'account_number', 'is_profile_complete',
        ]
        read_only_fields = ['id', 'user', 'status', 'avg_rating', 'rating_count', 'total_consultations', 'is_profile_complete']

    def get_is_profile_complete(self, obj):
        return obj.is_profile_complete()

    def get_profile_image(self, obj):
        request = self.context.get('request')
        if obj.profile_image:
            if request:
                return request.build_absolute_uri(obj.profile_image.url)
            return obj.profile_image.url
        return None


class VeterinarianProfileCompletionSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = VeterinarianProfile
        fields = [
            'profile_image', 'license_number', 'years_experience', 'consultation_fee', 'bio',
            'location', 'specialization', 'clinic_name', 'clinic_address', 'phone_number',
            'qualification', 'account_number',
        ]

    def _clean_text(self, value, field_label, min_len=1, max_len=None):
        value = (value or '').strip()
        if len(value) < min_len:
            raise serializers.ValidationError(f'{field_label} is required.')
        if max_len and len(value) > max_len:
            raise serializers.ValidationError(f'{field_label} cannot exceed {max_len} characters.')
        return value

    def validate_license_number(self, value):
        value = self._clean_text(value, 'License number', min_len=4, max_len=100)
        if not LICENSE_REGEX.match(value):
            raise serializers.ValidationError('Enter a valid license number (4-50 letters, numbers, hyphens, or slashes).')
        qs = VeterinarianProfile.objects.filter(license_number__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('This license number is already registered.')
        return value

    def validate_qualification(self, value):
        return self._clean_text(value, 'Qualification', min_len=2, max_len=255)

    def validate_specialization(self, value):
        return self._clean_text(value, 'Specialization', min_len=2, max_len=255)

    def validate_clinic_name(self, value):
        return self._clean_text(value, 'Clinic name', min_len=2, max_len=255)

    def validate_clinic_address(self, value):
        return self._clean_text(value, 'Clinic address', min_len=10, max_len=2000)

    def validate_location(self, value):
        return self._clean_text(value, 'City/location', min_len=2, max_len=255)

    def validate_phone_number(self, value):
        value = self._clean_text(value, 'Phone number', min_len=7, max_len=20)
        if not PHONE_REGEX.match(value):
            raise serializers.ValidationError('Enter a valid phone number (7-20 digits, may include +, spaces, or dashes).')
        return value

    def validate_bio(self, value):
        value = self._clean_text(value, 'Bio', min_len=20, max_len=1000)
        return value

    def validate_consultation_fee(self, value):
        if value is None or float(value) <= 0:
            raise serializers.ValidationError('Consultation fee must be greater than 0.')
        if float(value) > 1000000:
            raise serializers.ValidationError('Consultation fee is too high.')
        return value

    def validate_years_experience(self, value):
        if value is None or value < 0:
            raise serializers.ValidationError('Years of experience cannot be negative.')
        if value > 60:
            raise serializers.ValidationError('Please enter a realistic number of years of experience.')
        return value

    def validate_account_number(self, value):
        return self._clean_text(value, 'Account number', min_len=5, max_len=50)

    def validate_profile_image(self, value):
        if not value:
            return value
        if hasattr(value, 'size') and value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError('Profile photo must be smaller than 5 MB.')
        allowed = ('image/jpeg', 'image/png', 'image/webp', 'image/gif')
        if hasattr(value, 'content_type') and value.content_type not in allowed:
            raise serializers.ValidationError('Profile photo must be a JPEG, PNG, WebP, or GIF image.')
        return value

    def validate(self, attrs):
        profile = self.instance
        if not attrs.get('profile_image') and not (profile and profile.profile_image):
            raise serializers.ValidationError({'profile_image': 'Profile photo is required.'})
        return attrs


class VeterinarianReviewSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    patient_avatar = serializers.SerializerMethodField()
    veterinarian_name = serializers.CharField(source='veterinarian.user.full_name', read_only=True)

    class Meta:
        model = VeterinarianReview
        fields = [
            'id', 'veterinarian', 'patient', 'patient_name', 'patient_avatar',
            'veterinarian_name', 'appointment', 'rating', 'comment',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'patient', 'created_at', 'updated_at']

    def get_patient_avatar(self, obj):
        request = self.context.get('request')
        if obj.patient and obj.patient.avatar:
            if request:
                return request.build_absolute_uri(obj.patient.avatar.url)
            return obj.patient.avatar.url
        return None

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate(self, data):
        """
        Validate that:
        1. The patient has a completed appointment with the veterinarian.
        2. The patient is not reviewing themselves (if they are a veterinarian).
        3. The appointment has not already been reviewed.
        """
        veterinarian = data.get('veterinarian')
        appointment = data.get('appointment')
        patient = self.context['request'].user

        # Check if patient is reviewing themselves
        try:
            if patient.vet_profile.id == veterinarian.id:
                raise serializers.ValidationError("Veterinarians cannot review themselves.")
        except Exception:
            pass

        # Check if appointment belongs to the patient and veterinarian
        if appointment.pet_owner != patient:
            raise serializers.ValidationError("You can only review appointments you booked.")

        if appointment.veterinarian != veterinarian:
            raise serializers.ValidationError("This appointment is not with the specified veterinarian.")

        # Check if appointment is completed
        if appointment.status != 'COMPLETED':
            raise serializers.ValidationError("You can only review completed appointments.")

        # Check if review already exists for this appointment
        if self.instance is None:  # Only on create, not update
            if VeterinarianReview.objects.filter(appointment=appointment, patient=patient).exists():
                raise serializers.ValidationError("You have already reviewed this appointment.")

        return data


class SellerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    store_logo = serializers.SerializerMethodField()

    class Meta:
        model = SellerProfile
        fields = [
            'id', 'user', 'store_name', 'store_description', 'store_logo',
            'phone_number', 'address', 'account_number', 'is_verified',
            'total_products', 'total_sales', 'avg_rating',
        ]
        read_only_fields = ['id', 'user', 'is_verified', 'total_products', 'total_sales', 'avg_rating']

    def get_store_logo(self, obj):
        request = self.context.get('request')
        if obj.store_logo:
            if request:
                return request.build_absolute_uri(obj.store_logo.url)
            return obj.store_logo.url
        return None


class SellerProfileUpdateSerializer(serializers.ModelSerializer):
    store_logo = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = SellerProfile
        fields = [
            'store_name', 'store_description', 'store_logo',
            'phone_number', 'address', 'account_number',
        ]

    def to_internal_value(self, data):
        # Handle both QueryDict (from FormData) and dict (from JSON)
        if hasattr(data, 'getlist'):
            # This is FormData
            mutable_data = {}
            for key in data.keys():
                values = data.getlist(key)
                if len(values) == 1:
                    mutable_data[key] = values[0]
                else:
                    mutable_data[key] = values
            data = mutable_data
        return super().to_internal_value(data)

    def _clean_text(self, value, field_label, min_len=1, max_len=None):
        value = (value or '').strip()
        if len(value) < min_len:
            raise serializers.ValidationError(f'{field_label} is required.')
        if max_len and len(value) > max_len:
            raise serializers.ValidationError(f'{field_label} cannot exceed {max_len} characters.')
        return value

    def validate_store_name(self, value):
        value = self._clean_text(value, 'Store name', min_len=2, max_len=255)
        qs = SellerProfile.objects.filter(store_name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('This store name is already taken.')
        return value

    def validate_phone_number(self, value):
        if value:
            value = self._clean_text(value, 'Phone number', min_len=7, max_len=20)
            if not PHONE_REGEX.match(value):
                raise serializers.ValidationError('Enter a valid phone number (7-20 digits, may include +, spaces, or dashes).')
        return value

    def validate_account_number(self, value):
        if value:
            value = self._clean_text(value, 'Account number', min_len=5, max_len=50)
        return value

    def validate_store_logo(self, value):
        if not value:
            return value
        if hasattr(value, 'size') and value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError('Store logo must be smaller than 5 MB.')
        allowed = ('image/jpeg', 'image/png', 'image/webp', 'image/gif')
        if hasattr(value, 'content_type') and value.content_type not in allowed:
            raise serializers.ValidationError('Store logo must be a JPEG, PNG, WebP, or GIF image.')
        return value

