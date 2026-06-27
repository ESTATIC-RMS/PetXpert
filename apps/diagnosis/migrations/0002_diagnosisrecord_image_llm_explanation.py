from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('diagnosis', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='diagnosisrecord',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='diagnosis/'),
        ),
        migrations.AddField(
            model_name='diagnosisrecord',
            name='llm_explanation',
            field=models.TextField(blank=True),
        ),
    ]
