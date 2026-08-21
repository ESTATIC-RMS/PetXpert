from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = ['id', 'get_payer_info', 'get_related_info', 'amount', 'currency', 'payment_method', 'status', 'gateway', 'paid_at', 'created_at']
    list_filter = ['status', 'payment_method', 'gateway', 'paid_at', 'created_at']
    list_editable = ['status']
    search_fields = ['payer__full_name', 'payer__email', 'gateway_txn_id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    autocomplete_fields = ['appointment', 'order', 'payer']
    date_hierarchy = 'paid_at'
    ordering = ['-created_at']

    fieldsets = (
        (_('Payment Information'), {'fields': ('payer', 'appointment', 'order', 'amount', 'currency', 'payment_method', 'status')}),
        (_('Gateway Information'), {'fields': ('gateway', 'gateway_txn_id', 'paid_at')}),
        (_('Metadata'), {'fields': ('id', 'created_at', 'updated_at')}),
    )

    def get_payer_info(self, obj):
        return f"{obj.payer.full_name} ({obj.payer.email})"
    get_payer_info.short_description = 'Payer'

    def get_related_info(self, obj):
        if obj.appointment:
            return f"Appointment: {obj.appointment.pet.name}"
        elif obj.order:
            return f"Order: {obj.order.id}"
        return 'N/A'
    get_related_info.short_description = 'Related To'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('payer', 'appointment', 'order')
