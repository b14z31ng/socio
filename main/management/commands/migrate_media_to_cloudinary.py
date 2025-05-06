import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.apps import apps
import cloudinary.uploader

class Command(BaseCommand):
    help = 'Migrate local media files to Cloudinary and update model fields.'

    def handle(self, *args, **options):
        models_and_fields = [
            ('main', 'Profile', 'profile_pic'),
            ('main', 'Post', 'media'),
            ('main', 'Message', 'media'),
            ('main', 'GroupMessage', 'media'),
        ]
        migrated = 0
        for app_label, model_name, field_name in models_and_fields:
            model = apps.get_model(app_label, model_name)
            for obj in model.objects.all():
                file_field = getattr(obj, field_name, None)
                if file_field and file_field.name and not str(file_field.url).startswith('http'):
                    local_path = os.path.join(settings.MEDIA_ROOT, file_field.name)
                    if os.path.exists(local_path):
                        self.stdout.write(f'Uploading {local_path} to Cloudinary...')
                        result = cloudinary.uploader.upload(local_path, folder=field_name)
                        file_field.name = result['public_id'] + '.' + result['format']
                        obj.save()
                        migrated += 1
        self.stdout.write(self.style.SUCCESS(f'Migrated {migrated} files to Cloudinary.'))