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
                if file_field and file_field.name and file_field.name.startswith(('messages/', 'group_messages/', 'profile_pics/', 'posts/')):
                    local_path = os.path.join(settings.MEDIA_ROOT, file_field.name)
                    self.stdout.write(f'Checking {local_path} for {model_name} id={obj.id}')
                    if os.path.exists(local_path):
                        self.stdout.write(f'Uploading {local_path} to Cloudinary...')
                        result = cloudinary.uploader.upload(local_path, folder=field_name)
                        self.stdout.write(f'Cloudinary result: {result}')
                        file_field.name = result['public_id'] + '.' + result['format']
                        obj.save()
                        self.stdout.write(f'Updated {model_name} id={obj.id} media to {file_field.name}')
                        migrated += 1
                    else:
                        self.stdout.write(f'File does not exist: {local_path}')
        self.stdout.write(self.style.SUCCESS(f'Migrated {migrated} files to Cloudinary.'))