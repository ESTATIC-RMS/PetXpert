from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    list_display = ['recipient', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    list_editable = ['is_read']
    search_fields = ['recipient__email', 'recipient__full_name', 'title', 'content']
    readonly_fields = ['id', 'created_at', 'updated_at']
    autocomplete_fields = ['recipient']
    ordering = ['-created_at']

    fieldsets = (
        (_('Recipient'), {'fields': ('recipient',)}),
        (_('Content'), {'fields': ('title', 'content', 'notification_type', 'is_read')}),
        (_('Related'), {'fields': ('related_id', 'related_type')}),
        (_('Metadata'), {'fields': ('id', 'created_at', 'updated_at')}),
    )
