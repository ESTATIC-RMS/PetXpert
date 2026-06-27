from django.db import models
from django.conf import settings
from apps.core.models import BaseModel


class ChatGroup(BaseModel):
    name = models.CharField(max_length=255, unique=True, db_index=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = 'chat_chatgroup'
        verbose_name = 'Chat Group'
        verbose_name_plural = 'Chat Groups'

    def __str__(self):
        return self.name


class MessageType(models.TextChoices):
    TEXT = 'TEXT', 'Text'
    IMAGE = 'IMAGE', 'Image'
    DOCUMENT = 'DOCUMENT', 'Document'
    SYSTEM = 'SYSTEM', 'System'


class MessageManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class Message(BaseModel):
    group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE, related_name='messages', db_index=True)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages', db_index=True)
    message_type = models.CharField(max_length=20, choices=MessageType.choices, default=MessageType.TEXT, db_index=True)
    content = models.TextField(blank=True, null=True)
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)

    objects = MessageManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'chat_message'
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        indexes = [
            models.Index(fields=['group', '-created_at']),
            models.Index(fields=['sender']),
            models.Index(fields=['message_type']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.sender.email} - {self.message_type}'


class Attachment(BaseModel):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments', db_index=True)
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100)
    file_size = models.PositiveIntegerField()
    file = models.FileField(upload_to='chat/attachments/')

    class Meta:
        db_table = 'chat_attachment'
        verbose_name = 'Attachment'
        verbose_name_plural = 'Attachments'
        indexes = [
            models.Index(fields=['message']),
        ]

    def __str__(self):
        return self.file_name
