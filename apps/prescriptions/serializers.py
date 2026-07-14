from rest_framework import serializers
from django.db import transaction
from django.utils import timezone
from .models import Prescription, PrescriptionItem
from apps.appointments.models import Appointment


class PrescriptionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionItem
        fields = ['medicine_name', 'dosage', 'quantity', 'duration_days', 'notes']

    def validate_medicine_name(self, value):
        value = (value or '').strip()
        if len(value) < 2:
            raise serializers.ValidationError('Medicine name must be at least 2 characters.')
        if len(value) > 200:
            raise serializers.ValidationError('Medicine name cannot exceed 200 characters.')
        return value

    def validate_dosage(self, value):
        value = (value or '').strip()
        if len(value) < 2:
            raise serializers.ValidationError('Dosage instruction must be at least 2 characters.')
        if len(value) > 200:
            raise serializers.ValidationError('Dosage instruction cannot exceed 200 characters.')
        return value

    def validate_quantity(self, value):
        if value is None or value < 1:
            raise serializers.ValidationError('Quantity must be at least 1.')
        if value > 9999:
            raise serializers.ValidationError('Quantity is too high.')
        return value

    def validate_duration_days(self, value):
        if value is None or value < 1:
            raise serializers.ValidationError('Duration must be at least 1 day.')
        if value > 365:
            raise serializers.ValidationError('Duration cannot exceed 365 days.')
        return value

    def validate_notes(self, value):
        if value is None:
            return ''
        value = value.strip()
        if len(value) > 500:
            raise serializers.ValidationError('Notes cannot exceed 500 characters.')
        return value


class PrescriptionDetailSerializer(serializers.ModelSerializer):
    items = PrescriptionItemSerializer(many=True, read_only=True)
    vet_name = serializers.ReadOnlyField(source='issuing_vet.user.full_name')
    vet_specialization = serializers.ReadOnlyField(source='issuing_vet.specialization')
    pet_name = serializers.ReadOnlyField(source='pet.name')
    pet_species = serializers.ReadOnlyField(source='pet.species')
    appointment_date = serializers.ReadOnlyField(source='appointment.scheduled_at')

    class Meta:
        model = Prescription
        fields = [
            'id', 'appointment', 'issuing_vet', 'pet', 'diagnosis_text',
            'instructions', 'issued_at', 'valid_until', 'is_finalized',
            'items', 'vet_name', 'vet_specialization', 'pet_name',
            'pet_species', 'appointment_date'
        ]


class PrescriptionCreateSerializer(serializers.ModelSerializer):
    items = PrescriptionItemSerializer(many=True, required=True)
    appointment = serializers.PrimaryKeyRelatedField(queryset=Appointment.objects.all())
    valid_until = serializers.DateField(required=False, allow_null=True, input_formats=['%Y-%m-%d'])

    class Meta:
        model = Prescription
        fields = ['appointment', 'diagnosis_text', 'instructions', 'valid_until', 'items']

    def validate_diagnosis_text(self, value):
        value = (value or '').strip()
        if len(value) < 5:
            raise serializers.ValidationError('Diagnosis must be at least 5 characters.')
        if len(value) > 5000:
            raise serializers.ValidationError('Diagnosis cannot exceed 5000 characters.')
        return value

    def validate_instructions(self, value):
        value = (value or '').strip()
        if len(value) < 5:
            raise serializers.ValidationError('Instructions must be at least 5 characters.')
        if len(value) > 5000:
            raise serializers.ValidationError('Instructions cannot exceed 5000 characters.')
        return value

    def validate_valid_until(self, value):
        if value is None:
            return value
        if value < timezone.localdate():
            raise serializers.ValidationError('Valid until date cannot be in the past.')
        return value

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError('At least one prescription item is required.')
        if len(value) > 20:
            raise serializers.ValidationError('A prescription cannot include more than 20 medicines.')
        medicine_names = [item.get('medicine_name', '').strip().lower() for item in value]
        if len(medicine_names) != len(set(medicine_names)):
            raise serializers.ValidationError('Duplicate medicine names are not allowed in the same prescription.')
        return value

    def validate(self, attrs):
        appointment = attrs.get('appointment')
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError('Authentication required.')

        try:
            vet_profile = request.user.vet_profile
        except Exception:
            raise serializers.ValidationError('Only veterinarians with a profile can issue prescriptions.')

        if not vet_profile.is_profile_complete():
            raise serializers.ValidationError('Complete your veterinarian profile before issuing prescriptions.')

        if appointment.veterinarian != vet_profile:
            raise serializers.ValidationError('You are not the veterinarian for this appointment.')

        if appointment.status not in ['CONFIRMED', 'COMPLETED']:
            raise serializers.ValidationError('Can only issue prescriptions for CONFIRMED or COMPLETED appointments.')

        if Prescription.objects.filter(appointment=appointment, is_deleted=False).exists():
            raise serializers.ValidationError('A prescription already exists for this appointment.')

        return attrs

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        appointment = validated_data.pop('appointment')
        request = self.context.get('request')
        vet_profile = request.user.vet_profile

        with transaction.atomic():
            prescription = Prescription.objects.create(
                appointment=appointment,
                issuing_vet=vet_profile,
                pet=appointment.pet,
                **validated_data
            )
            for item_data in items_data:
                PrescriptionItem.objects.create(prescription=prescription, **item_data)
            return prescription
