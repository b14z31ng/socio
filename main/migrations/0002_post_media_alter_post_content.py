# Generated by Django 5.2 on 2025-05-03 22:25

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="post",
            name="media",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="media/",
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=[
                            "jpg",
                            "jpeg",
                            "png",
                            "gif",
                            "mp4",
                            "mov",
                            "avi",
                        ]
                    )
                ],
            ),
        ),
        migrations.AlterField(
            model_name="post",
            name="content",
            field=models.TextField(blank=True),
        ),
    ]
