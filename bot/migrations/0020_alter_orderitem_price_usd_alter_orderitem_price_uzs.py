# Generated by Django 4.2 on 2024-09-02 06:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0019_order_agent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderitem',
            name='price_usd',
            field=models.CharField(max_length=255, verbose_name='Цена USD'),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='price_uzs',
            field=models.CharField(max_length=255, verbose_name='Цена sum'),
        ),
    ]
