# Generated by Django 4.1.6 on 2023-08-30 19:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cowork", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="room",
            name="is_private",
            field=models.BooleanField(default=True),
        ),
    ]