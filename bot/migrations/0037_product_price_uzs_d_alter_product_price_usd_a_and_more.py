# Generated by Django 4.2 on 2024-09-18 19:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0036_orderitem_product_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='price_uzs_d',
            field=models.FloatField(default=0, verbose_name='Оптовик Цена (сум) C'),
        ),
        migrations.AlterField(
            model_name='product',
            name='price_usd_a',
            field=models.FloatField(default=0, verbose_name='Стандарт Цена (долл. США) A'),
        ),
        migrations.AlterField(
            model_name='product',
            name='price_usd_b',
            field=models.FloatField(default=0, verbose_name='-4% Цена (долл. США) B'),
        ),
        migrations.AlterField(
            model_name='product',
            name='price_usd_c',
            field=models.FloatField(default=0, verbose_name='Хорека Цена (долл. США) C'),
        ),
        migrations.AlterField(
            model_name='product',
            name='price_uzs_a',
            field=models.FloatField(default=0, verbose_name='Стандарт Цена (сум) A'),
        ),
        migrations.AlterField(
            model_name='product',
            name='price_uzs_b',
            field=models.FloatField(default=0, verbose_name='-4% Цена (сум) B'),
        ),
        migrations.AlterField(
            model_name='product',
            name='price_uzs_c',
            field=models.FloatField(default=0, verbose_name='Хорека Цена (сум) C'),
        ),
        migrations.AlterField(
            model_name='telegramuser',
            name='category',
            field=models.CharField(blank=True, choices=[('a', 'Стандарт'), ('b', '-4%'), ('c', 'Хорека'), ('d', 'Оптовик')], max_length=255, null=True, verbose_name='Категория клиента'),
        ),
    ]
