from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0003_alter_notification_notification_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(
                choices=[
                    ('APPOINTMENT_CREATED', 'Appointment Created'),
                    ('APPOINTMENT_CANCELLED', 'Appointment Cancelled'),
                    ('APPOINTMENT_STARTED', 'Appointment Started'),
                    ('APPOINTMENT_COMPLETED', 'Appointment Completed'),
                    ('PAYMENT_RECEIVED', 'Payment Received'),
                    ('REVIEW_RECEIVED', 'Review Received'),
                    ('ORDER_CONFIRMED', 'Order Confirmed'),
                    ('ORDER_CANCELLED', 'Order Cancelled'),
                    ('ORDER_SHIPPED', 'Order Shipped'),
                    ('ORDER_DELIVERED', 'Order Delivered'),
                    ('ORDER_PAYMENT_SUCCESS', 'Order Payment Success'),
                    ('SELLER_NEW_ORDER', 'Seller New Order'),
                    ('GENERAL', 'General Notification'),
                ],
                db_index=True,
                default='GENERAL',
                max_length=50,
            ),
        ),
    ]
