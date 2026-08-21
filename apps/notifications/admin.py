from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    list_display = ['get_recipient_info', 'title', 'notification_type', 'content_preview', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    list_editable = ['is_read']
    search_fields = ['recipient__email', 'recipient__full_name', 'title', 'content']
    readonly_fields = ['id', 'created_at', 'updated_at']
    autocomplete_fields = ['recipient']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    fieldsets = (
        (_('Recipient Information'), {'fields': ('recipient',)}),
        (_('Notification Content'), {'fields': ('title', 'content', 'notification_type', 'is_read')}),
        (_('Related Information'), {'fields': ('related_id', 'related_type')}),
        (_('Metadata'), {'fields': ('id', 'created_at', 'updated_at')}),
    )

    def get_recipient_info(self, obj):
        return f"{obj.recipient.full_name} ({obj.recipient.email})"
    get_recipient_info.short_description = 'Recipient'

    def content_preview(self, obj):
        return obj.content[:50] + '...' if obj.content and len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('recipient')
