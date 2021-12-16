# Generated by Django 4.0 on 2021-12-16 04:32

from django.db import migrations, models
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0005_alter_game_options_alter_gameuser_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gameuser',
            name='letter',
            field=models.TextField(blank=True, verbose_name='Письмо Санте'),
        ),
        migrations.AlterField(
            model_name='gameuser',
            name='phone',
            field=phonenumber_field.modelfields.PhoneNumberField(max_length=128, region=None, verbose_name='Номер владельца'),
        ),
    ]
