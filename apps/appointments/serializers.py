from datetime import timedelta

from rest_framework import serializers
from .models import Appointment


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = [
            'id', 'veterinarian', 'pet', 'scheduled_at', 'duration_minutes',
            'status', 'fee_charged', 'reason', 'cancelled_by'
        ]
        read_only_fields = ['id', 'status', 'cancelled_by']
    
    def validate_scheduled_at(self, value):
        from django.utils import timezone
        if value <= timezone.now():
            raise serializers.ValidationError("Appointment must be scheduled in the future.")
        return value
    
    def validate_duration_minutes(self, value):
        if value != 60:
            raise serializers.ValidationError("Duration must be 60 minutes.")
        return value
    
    def validate_fee_charged(self, value):
        if value < 0:
            raise serializers.ValidationError("Fee cannot be negative.")
        return value

    def validate(self, data):
        """Reject a slot that is already taken for the same veterinarian."""
        veterinarian = data.get('veterinarian')
        scheduled_at = data.get('scheduled_at')

        if veterinarian and scheduled_at:
            # Treat appointments that start within the same hour as conflicting.
            slot_start = scheduled_at.replace(minute=0, second=0, microsecond=0)
            slot_end = slot_start + timedelta(hours=1)

            conflict = Appointment.objects.filter(
                veterinarian=veterinarian,
                scheduled_at__gte=slot_start,
                scheduled_at__lt=slot_end,
                status__in=['PENDING_PAYMENT', 'PENDING', 'CONFIRMED', 'IN_PROGRESS'],
            )
            if self.instance is not None:
                conflict = conflict.exclude(pk=self.instance.pk)

            if conflict.exists():
                raise serializers.ValidationError(
                    "This time slot is already booked. Please choose another time."
                )
        return data
