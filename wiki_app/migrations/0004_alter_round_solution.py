# Generated by Django 3.2.9 on 2021-12-11 22:39

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wiki_app", "0003_alter_round_start_time"),
    ]

    operations = [
        migrations.AlterField(
            model_name="round",
            name="solution",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=100), null=True, size=None
            ),
        ),
    ]