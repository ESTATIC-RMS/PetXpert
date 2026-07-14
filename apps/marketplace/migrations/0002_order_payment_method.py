from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_method',
            field=models.CharField(
                choices=[('COD', 'Cash on Delivery'), ('STRIPE', 'Stripe Online')],
                db_index=True,
                default='COD',
                max_length=20,
            ),
        ),
    ]
