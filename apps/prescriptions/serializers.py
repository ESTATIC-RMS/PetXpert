from rest_framework import serializers
from django.db import transaction
from .models import Prescription, PrescriptionItem
from apps.appointments.models import Appointment

class PrescriptionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionItem
        fields = ['medicine_name', 'dosage', 'quantity', 'duration_days', 'notes']

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

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one prescription item is required.")
        return value

    def validate(self, attrs):
        appointment = attrs.get('appointment')
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError("Authentication required.")

        # Verify veterinarian is the logged in user
        try:
            vet_profile = request.user.vet_profile
        except Exception:
            raise serializers.ValidationError("Only veterinarians with a profile can issue prescriptions.")

        if appointment.veterinarian != vet_profile:
            raise serializers.ValidationError("You are not the veterinarian for this appointment.")

        # Allow prescriptions for CONFIRMED or COMPLETED appointments
        if appointment.status not in ['CONFIRMED', 'COMPLETED']:
            raise serializers.ValidationError("Can only issue prescriptions for CONFIRMED or COMPLETED appointments.")

        if Prescription.objects.filter(appointment=appointment, is_deleted=False).exists():
            raise serializers.ValidationError("A prescription already exists for this appointment.")

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
