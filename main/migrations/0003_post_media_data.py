# Generated by Django 5.2 on 2025-05-03 22:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0002_post_media_alter_post_content"),
    ]

    operations = [
        migrations.AddField(
            model_name="post",
            name="media_data",
            field=models.BinaryField(blank=True, editable=True, null=True),
        ),
    ]
