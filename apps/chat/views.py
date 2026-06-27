from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.exceptions import ValidationError
from .models import ChatGroup, Message, Attachment
from .serializers import (
    MessageSerializer, MessageCreateSerializer, MessageEditSerializer, ChatGroupSerializer
)
from .services import create_message, edit_message, delete_message, get_message_history


class MessageViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def list(self, request, group_id=None):
        """Get message history for a group with cursor-based pagination."""
        cursor = request.query_params.get('cursor')
        page_size = request.query_params.get('page_size')
        
        if page_size:
            try:
                page_size = int(page_size)
            except ValueError:
                page_size = None
        
        try:
            result = get_message_history(group_id, cursor, page_size)
            serializer = MessageSerializer(result['results'], many=True, context={'request': request})
            return Response({
                'results': serializer.data,
                'next_cursor': result['next_cursor'],
                'has_more': result['has_more']
            })
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, group_id=None):
        """Create a new message in a group."""
        try:
            group = ChatGroup.objects.get(id=group_id, is_active=True)
        except ChatGroup.DoesNotExist:
            return Response({'error': 'Chat group not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = MessageCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                message = create_message(
                    user=request.user,
                    group=group,
                    content=serializer.validated_data.get('content'),
                    message_type=serializer.validated_data.get('message_type', 'TEXT')
                )
                response_serializer = MessageSerializer(message)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            except ValidationError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        """Get a single message by ID."""
        try:
            message = Message.objects.get(id=pk, is_deleted=False)
            serializer = MessageSerializer(message)
            return Response(serializer.data)
        except Message.DoesNotExist:
            return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)

    def partial_update(self, request, pk=None):
        """Edit a message."""
        serializer = MessageEditSerializer(data=request.data)
        if serializer.is_valid():
            try:
                message = edit_message(
                    user=request.user,
                    message_id=pk,
                    new_content=serializer.validated_data.get('content')
                )
                response_serializer = MessageSerializer(message)
                return Response(response_serializer.data)
            except ValidationError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except PermissionDenied as e:
                return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """Delete a message (soft-delete)."""
        try:
            delete_message(user=request.user, message_id=pk)
            return Response({'message': 'Message deleted successfully'}, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)

    @action(detail=False, methods=['post'], url_path='upload')
    def upload_file(self, request, group_id=None):
        """Upload a file attachment."""
        try:
            group = ChatGroup.objects.get(id=group_id, is_active=True)
        except ChatGroup.DoesNotExist:
            return Response({'error': 'Chat group not found'}, status=status.HTTP_404_NOT_FOUND)
        
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate file type / extension
        import os
        allowed_extensions = ['.jpg', '.jpeg', '.png']
        allowed_content_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/pjpeg', 'image/x-png']
        
        _, ext = os.path.splitext(file.name.lower())
        is_valid = ext in allowed_extensions
        if file.content_type:
            content_type_lower = file.content_type.lower()
            is_valid = is_valid and (content_type_lower in allowed_content_types or content_type_lower.startswith('image/'))
            
        if not is_valid:
            return Response(
                {'error': 'Only JPG, JPEG, and PNG images are allowed.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Create attachment
        attachment = Attachment.objects.create(
            file_name=file.name,
            file_type=file.content_type,
            file_size=file.size,
            file=file
        )
        
        return Response({
            'id': str(attachment.id),
            'file_name': attachment.file_name,
            'file_type': attachment.file_type,
            'file_size': attachment.file_size,
            'file_url': attachment.file.url
        }, status=status.HTTP_201_CREATED)


class ChatGroupViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ChatGroupSerializer
    queryset = ChatGroup.objects.filter(is_active=True)
