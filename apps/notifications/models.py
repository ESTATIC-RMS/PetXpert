from django.db import models
from django.conf import settings
from apps.core.models import BaseModel

class NotificationType(models.TextChoices):
    APPOINTMENT_CREATED = 'APPOINTMENT_CREATED', 'Appointment Created'
    APPOINTMENT_CANCELLED = 'APPOINTMENT_CANCELLED', 'Appointment Cancelled'
    APPOINTMENT_STARTED = 'APPOINTMENT_STARTED', 'Appointment Started'
    APPOINTMENT_COMPLETED = 'APPOINTMENT_COMPLETED', 'Appointment Completed'
    PAYMENT_RECEIVED = 'PAYMENT_RECEIVED', 'Payment Received'
    REVIEW_RECEIVED = 'REVIEW_RECEIVED', 'Review Received'
    ORDER_CONFIRMED = 'ORDER_CONFIRMED', 'Order Confirmed'
    ORDER_CANCELLED = 'ORDER_CANCELLED', 'Order Cancelled'
    ORDER_SHIPPED = 'ORDER_SHIPPED', 'Order Shipped'
    ORDER_DELIVERED = 'ORDER_DELIVERED', 'Order Delivered'
    ORDER_PAYMENT_SUCCESS = 'ORDER_PAYMENT_SUCCESS', 'Order Payment Success'
    SELLER_NEW_ORDER = 'SELLER_NEW_ORDER', 'Seller New Order'
    GENERAL = 'GENERAL', 'General Notification'

class Notification(BaseModel):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        db_index=True
    )
    title = models.CharField(max_length=255)
    content = models.TextField()
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        default=NotificationType.GENERAL,
        db_index=True
    )
    is_read = models.BooleanField(default=False, db_index=True)
    related_id = models.UUIDField(null=True, blank=True)
    related_type = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'notifications_notification'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recipient.email} - {self.title} - Read: {self.is_read}"
