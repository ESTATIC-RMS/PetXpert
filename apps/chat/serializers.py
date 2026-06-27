from rest_framework import serializers
from .models import ChatGroup, Message, Attachment, MessageType


class UUIDField(serializers.Field):
    """Custom UUID field that serializes to string."""
    def to_representation(self, value):
        if value is None:
            return None
        return str(value)


class AttachmentSerializer(serializers.ModelSerializer):
    id = UUIDField(read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = ['id', 'file_name', 'file_type', 'file_size', 'file', 'file_url']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None


class MessageSerializer(serializers.ModelSerializer):
    id = UUIDField(read_only=True)
    group = UUIDField(read_only=True)
    sender = UUIDField(read_only=True)
    sender_info = serializers.SerializerMethodField()
    attachments = AttachmentSerializer(many=True, read_only=True)
    message_type_display = serializers.CharField(source='get_message_type_display', read_only=True)

    class Meta:
        model = Message
        fields = [
            'id', 'group', 'sender', 'sender_info', 'message_type', 'message_type_display',
            'content', 'is_edited', 'edited_at', 'attachments', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'edited_at']

    def get_sender_info(self, obj):
        request = self.context.get('request')
        avatar_url = None
        
        image_field = None
        if obj.sender.role == 'VETERINARIAN':
            try:
                if hasattr(obj.sender, 'vet_profile') and obj.sender.vet_profile and obj.sender.vet_profile.profile_image:
                    image_field = obj.sender.vet_profile.profile_image
            except Exception:
                pass
        
        if not image_field and obj.sender.avatar:
            image_field = obj.sender.avatar

        if image_field:
            if request:
                avatar_url = request.build_absolute_uri(image_field.url)
            else:
                # Build absolute URI using settings if no request context
                from django.conf import settings
                base_url = getattr(settings, 'BASE_URL', 'http://127.0.0.1:8000')
                avatar_url = f'{base_url}{image_field.url}'
        
        return {
            'id': str(obj.sender.id),
            'email': obj.sender.email,
            'full_name': obj.sender.full_name,
            'avatar': avatar_url,
            'role': obj.sender.role
        }


class MessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['content', 'message_type']

    def validate_content(self, value):
        from django.conf import settings
        max_length = getattr(settings, 'CHAT_MAX_MESSAGE_LENGTH', 5000)
        if value and len(value) > max_length:
            raise serializers.ValidationError(
                f'Message content exceeds maximum length of {max_length} characters'
            )
        return value

    def validate_message_type(self, value):
        valid_types = [choice[0] for choice in MessageType.choices]
        if value not in valid_types:
            raise serializers.ValidationError(f'Invalid message type. Must be one of: {valid_types}')
        return value


class MessageEditSerializer(serializers.Serializer):
    content = serializers.CharField(required=False, allow_blank=True)

    def validate_content(self, value):
        from django.conf import settings
        max_length = getattr(settings, 'CHAT_MAX_MESSAGE_LENGTH', 5000)
        if value and len(value) > max_length:
            raise serializers.ValidationError(
                f'Message content exceeds maximum length of {max_length} characters'
            )
        return value


class ChatGroupSerializer(serializers.ModelSerializer):
    id = UUIDField(read_only=True)

    class Meta:
        model = ChatGroup
        fields = ['id', 'name', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
