import bleach
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError, PermissionDenied
from .models import ChatGroup, Message, Attachment, MessageType


def create_message(user, group, content=None, message_type=MessageType.TEXT, attachments=None):
    """
    Create a new message with sanitized content.
    
    Args:
        user: The user sending the message
        group: ChatGroup instance
        content: Message content (text)
        message_type: MessageType enum value
        attachments: List of file paths or Attachment instances
    
    Returns:
        Message instance
    """
    # Validate content length
    max_length = getattr(settings, 'CHAT_MAX_MESSAGE_LENGTH', 5000)
    if content and len(content) > max_length:
        raise ValidationError(f'Message content exceeds maximum length of {max_length} characters')
    
    # Sanitize content
    sanitized_content = None
    if content:
        sanitized_content = bleach.clean(
            content,
            tags=[],
            attributes={},
            strip=True
        )
    
    # Create message
    message = Message.objects.create(
        group=group,
        sender=user,
        message_type=message_type,
        content=sanitized_content
    )
    
    # Handle attachments
    if attachments:
        for attachment_data in attachments:
            if isinstance(attachment_data, Attachment):
                attachment_data.message = message
                attachment_data.save()
            elif isinstance(attachment_data, dict):
                Attachment.objects.create(
                    message=message,
                    file_name=attachment_data.get('file_name'),
                    file_type=attachment_data.get('file_type'),
                    file_size=attachment_data.get('file_size'),
                    file=attachment_data.get('file')
                )
    
    return message


def edit_message(user, message_id, new_content):
    """
    Edit an existing message.
    
    Args:
        user: The user editing the message
        message_id: UUID of the message
        new_content: New message content
    
    Returns:
        Updated Message instance
    
    Raises:
        PermissionDenied: If user is not the message sender
        ValidationError: If content is invalid
    """
    try:
        message = Message.objects.get(id=message_id, is_deleted=False)
    except Message.DoesNotExist:
        raise ValidationError('Message not found')
    
    # Check ownership
    if message.sender != user:
        raise PermissionDenied('You can only edit your own messages')
    
    # Validate content length
    max_length = getattr(settings, 'CHAT_MAX_MESSAGE_LENGTH', 5000)
    if new_content and len(new_content) > max_length:
        raise ValidationError(f'Message content exceeds maximum length of {max_length} characters')
    
    # Sanitize content
    sanitized_content = None
    if new_content:
        sanitized_content = bleach.clean(
            new_content,
            tags=[],
            attributes={},
            strip=True
        )
    
    # Update message
    message.content = sanitized_content
    message.is_edited = True
    message.edited_at = timezone.now()
    message.save()
    
    return message


def delete_message(user, message_id):
    """
    Soft-delete a message.
    
    Args:
        user: The user deleting the message
        message_id: UUID of the message
    
    Returns:
        The deleted Message instance
    
    Raises:
        PermissionDenied: If user is not the message sender and not an admin
        ValidationError: If message not found
    """
    try:
        message = Message.objects.get(id=message_id, is_deleted=False)
    except Message.DoesNotExist:
        raise ValidationError('Message not found')
    
    # Check ownership or admin status
    if message.sender != user and not user.is_staff:
        raise PermissionDenied('You can only delete your own messages')
    
    # Soft delete
    message.is_deleted = True
    message.save()
    
    return message


def get_message_history(group_id, cursor=None, page_size=None):
    """
    Get paginated message history for a group.
    
    Args:
        group_id: UUID of the chat group
        cursor: Timestamp cursor for pagination (ISO format string)
        page_size: Number of messages per page
    
    Returns:
        dict with 'results', 'next_cursor', 'has_more'
    """
    if page_size is None:
        page_size = getattr(settings, 'CHAT_PAGE_SIZE', 50)
    
    try:
        group = ChatGroup.objects.get(id=group_id, is_active=True)
    except ChatGroup.DoesNotExist:
        raise ValidationError('Chat group not found')
    
    queryset = Message.objects.filter(group=group)
    
    # Apply cursor pagination
    if cursor:
        try:
            from datetime import datetime
            cursor_time = datetime.fromisoformat(cursor)
            queryset = queryset.filter(created_at__lt=cursor_time)
        except (ValueError, TypeError):
            pass
    
    messages = queryset.order_by('-created_at')[:page_size + 1]
    messages_list = list(messages)
    
    # Determine if there are more results
    has_more = len(messages_list) > page_size
    results = messages_list[:page_size]
    
    # Calculate next cursor
    next_cursor = None
    if has_more and results:
        next_cursor = results[-1].created_at.isoformat()
    
    # Reverse to get chronological order
    results.reverse()
    
    return {
        'results': results,
        'next_cursor': next_cursor,
        'has_more': has_more
    }
