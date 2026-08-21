from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .models import Attachment, ChatGroup, Message


@admin.register(ChatGroup)
class ChatGroupAdmin(ModelAdmin):
    list_display = ['name', 'get_member_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    list_editable = ['is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        (None, {'fields': ('name', 'description', 'is_active')}),
        (_('Metadata'), {'fields': ('id', 'created_at', 'updated_at')}),
    )

    def get_member_count(self, obj):
        return obj.members.count()
    get_member_count.short_description = 'Members'


@admin.register(Message)
class MessageAdmin(ModelAdmin):
    list_display = ['group', 'get_sender_info', 'message_type', 'content_preview', 'is_edited', 'created_at']
    list_filter = ['message_type', 'is_edited', 'created_at']
    search_fields = ['content', 'sender__email', 'sender__full_name', 'group__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'edited_at']
    autocomplete_fields = ['group', 'sender']
    date_hierarchy = 'created_at'

    fieldsets = (
        (None, {'fields': ('group', 'sender', 'message_type', 'content')}),
        (_('Editing Information'), {'fields': ('is_edited', 'edited_at')}),
        (_('Metadata'), {'fields': ('id', 'created_at', 'updated_at')}),
    )

    def get_sender_info(self, obj):
        return f"{obj.sender.full_name} ({obj.sender.email})"
    get_sender_info.short_description = 'Sender'

    def content_preview(self, obj):
        return obj.content[:50] + '...' if obj.content and len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('sender', 'group')


@admin.register(Attachment)
class AttachmentAdmin(ModelAdmin):
    list_display = ['file_name', 'file_type', 'get_file_size_mb', 'get_message_info', 'created_at']
    list_filter = ['file_type', 'created_at']
    search_fields = ['file_name', 'message__content', 'message__sender__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    autocomplete_fields = ['message']
    date_hierarchy = 'created_at'

    def get_file_size_mb(self, obj):
        size_mb = obj.file_size / (1024 * 1024) if obj.file_size else 0
        return f"{size_mb:.2f} MB"
    get_file_size_mb.short_description = 'Size'

    def get_message_info(self, obj):
        if obj.message:
            return f"{obj.message.sender.full_name}: {obj.message.content[:30]}..."
        return 'N/A'
    get_message_info.short_description = 'Message'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('message__sender')
