from rest_framework import serializers

from apps.pets.models import Pet, PetSpecies
from .models import DiagnosisRecord


class DiagnosisRecordSerializer(serializers.ModelSerializer):
    pet_name = serializers.ReadOnlyField(source='pet.name')
    pet_species = serializers.ReadOnlyField(source='pet.species')

    class Meta:
        model = DiagnosisRecord
        fields = [
            'id', 'pet', 'pet_name', 'pet_species', 'input_type', 'image',
            'symptom_text', 'predicted_diseases', 'severity', 'risk_score',
            'status', 'model_version', 'inference_time_ms', 'llm_explanation',
            'created_at',
        ]
        read_only_fields = fields


class DiagnosisRequestSerializer(serializers.Serializer):
    pet_id = serializers.UUIDField()
    image = serializers.ImageField(required=True)
    symptom_text = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate_pet_id(self, value):
        request = self.context.get('request')
        try:
            pet = Pet.objects.get(id=value, owner=request.user, is_deleted=False)
        except Pet.DoesNotExist:
            raise serializers.ValidationError('Pet not found.')

        if pet.species != PetSpecies.DOG:
            raise serializers.ValidationError('AI image diagnosis currently supports dog profiles only.')

        self.context['pet'] = pet
        return value

    def validate(self, attrs):
        attrs['pet'] = self.context['pet']
        return attrs


class DiagnosisChatSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=2000)
