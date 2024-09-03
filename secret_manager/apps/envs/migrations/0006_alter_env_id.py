# Generated by Django 5.1 on 2024-08-31 16:07

import secret_manager.utili
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("envs", "0005_alter_env_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="env",
            name="id",
            field=models.CharField(
                default=secret_manager.utili.unique_id,
                editable=False,
                max_length=18,
                primary_key=True,
                serialize=False,
            ),
        ),
    ]
