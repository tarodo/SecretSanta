# Generated by Django 4.0 on 2021-12-17 13:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0011_alter_wishlist_options_remove_wishlist_item_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='gameuser',
            name='interest_raw',
            field=models.CharField(blank=True, max_length=2000, verbose_name='Интерес от игрока'),
        ),
        migrations.AddField(
            model_name='gameuser',
            name='wishlist_raw',
            field=models.CharField(blank=True, max_length=2000, verbose_name='Подарок от игрока'),
        ),
    ]