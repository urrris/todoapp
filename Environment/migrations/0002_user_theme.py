# Generated by Django 5.0.1 on 2024-05-29 15:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Environment', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='theme',
            field=models.BooleanField(default=False, verbose_name='Тема рабочего пространства'),
        ),
    ]
