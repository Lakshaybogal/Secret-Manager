# Generated by Django 5.1 on 2024-08-31 10:31

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_alter_user_createdat'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='lastLogin',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
