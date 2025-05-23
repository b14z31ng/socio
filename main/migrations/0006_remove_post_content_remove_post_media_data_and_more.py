# Generated by Django 5.2 on 2025-05-03 23:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0005_auto_20250504_0550"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="post",
            name="content",
        ),
        migrations.RemoveField(
            model_name="post",
            name="media_data",
        ),
        migrations.AddField(
            model_name="post",
            name="content_mac",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="post",
            name="encrypted_content",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="profile",
            name="bio_mac",
            field=models.CharField(blank=True, default="", max_length=64, null=True),
        ),
        migrations.AddField(
            model_name="profile",
            name="encrypted_username",
            field=models.CharField(blank=True, default="", max_length=256),
        ),
        migrations.AlterField(
            model_name="profile",
            name="bio",
            field=models.TextField(blank=True, default="", null=True),
        ),
    ]
