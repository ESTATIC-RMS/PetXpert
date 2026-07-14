from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = ['id', 'appointment', 'order', 'payer', 'amount', 'currency', 'payment_method', 'status', 'gateway', 'paid_at', 'created_at']
    list_filter = ['status', 'payment_method', 'gateway', 'paid_at', 'created_at']
    list_editable = ['status']
    search_fields = ['payer__full_name', 'payer__email', 'gateway_txn_id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    autocomplete_fields = ['appointment', 'order', 'payer']
    date_hierarchy = 'paid_at'
    ordering = ['-created_at']

    fieldsets = (
        (_('Payment'), {'fields': ('payer', 'appointment', 'order', 'amount', 'currency', 'payment_method', 'status')}),
        (_('Gateway'), {'fields': ('gateway', 'gateway_txn_id', 'paid_at')}),
        (_('Metadata'), {'fields': ('id', 'created_at', 'updated_at')}),
    )
