# Generated by Django 4.2 on 2024-09-09 16:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0025_order_location_path'),
    ]

    operations = [
        migrations.AddField(
            model_name='telegramuser',
            name='tin',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='ИНН'),
        ),
    ]
