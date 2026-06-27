from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'appointment', 'payer', 'amount', 'currency', 'status', 'gateway', 'paid_at', 'created_at']
    list_filter = ['status', 'gateway', 'paid_at', 'created_at']
    search_fields = ['payer__full_name', 'gateway_txn_id', 'appointment__id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'paid_at'
