from django.contrib import admin
from .models import ChatGroup, Message, Attachment


@admin.register(ChatGroup)
class ChatGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'group', 'sender', 'message_type', 'is_edited', 'created_at']
    list_filter = ['message_type', 'is_edited', 'is_deleted', 'created_at']
    search_fields = ['content', 'sender__email', 'group__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'edited_at']
    date_hierarchy = 'created_at'


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'file_type', 'file_size', 'message', 'created_at']
    list_filter = ['file_type', 'created_at']
    search_fields = ['file_name', 'message__content']
    readonly_fields = ['id', 'created_at', 'updated_at']
