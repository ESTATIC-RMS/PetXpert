import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0004_alter_appointment_status'),
        ('marketplace', '0002_order_payment_method'),
        ('payments', '0002_alter_payment_appointment'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='order',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='payment',
                to='marketplace.order',
            ),
        ),
        migrations.AddField(
            model_name='payment',
            name='payment_method',
            field=models.CharField(
                choices=[('COD', 'Cash on Delivery'), ('STRIPE', 'Stripe')],
                db_index=True,
                default='STRIPE',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='payment',
            name='appointment',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='payment',
                to='appointments.appointment',
            ),
        ),
        migrations.AddConstraint(
            model_name='payment',
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ('appointment__isnull', False),
                    ('order__isnull', True),
                ) | models.Q(
                    ('appointment__isnull', True),
                    ('order__isnull', False),
                ),
                name='chk_payment_single_target',
            ),
        ),
    ]
