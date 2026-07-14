from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .models import Attachment, ChatGroup, Message


@admin.register(ChatGroup)
class ChatGroupAdmin(ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    list_editable = ['is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        (None, {'fields': ('name', 'description', 'is_active')}),
        (_('Metadata'), {'fields': ('id', 'created_at', 'updated_at')}),
    )


@admin.register(Message)
class MessageAdmin(ModelAdmin):
    list_display = ['group', 'sender', 'message_type', 'is_edited', 'created_at']
    list_filter = ['message_type', 'is_edited', 'created_at']
    search_fields = ['content', 'sender__email', 'group__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'edited_at']
    autocomplete_fields = ['group', 'sender']
    date_hierarchy = 'created_at'

    fieldsets = (
        (None, {'fields': ('group', 'sender', 'message_type', 'content')}),
        (_('Flags'), {'fields': ('is_edited', 'edited_at')}),
        (_('Metadata'), {'fields': ('id', 'created_at', 'updated_at')}),
    )


@admin.register(Attachment)
class AttachmentAdmin(ModelAdmin):
    list_display = ['file_name', 'file_type', 'file_size', 'message', 'created_at']
    list_filter = ['file_type', 'created_at']
    search_fields = ['file_name', 'message__content']
    readonly_fields = ['id', 'created_at', 'updated_at']
    autocomplete_fields = ['message']
