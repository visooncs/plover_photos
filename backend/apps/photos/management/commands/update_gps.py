from django.core.management.base import BaseCommand
from apps.photos.models import Photo
from apps.photos.services import get_gps_data
from PIL import Image, ImageOps
import os

class Command(BaseCommand):
    help = 'Update GPS information for all photos'

    def add_arguments(self, parser):
        parser.add_argument('--task-id', type=str, help='系统维护任务 ID')

    def handle(self, *args, **options):
        task_id = options.get('task_id')
        from apps.photos.models import MaintenanceTask
        task = None
        if task_id:
            try:
                task = MaintenanceTask.objects.get(id=task_id)
            except MaintenanceTask.DoesNotExist:
                pass

        photos = Photo.objects.all()
        total = photos.count()
        updated_count = 0
        
        self.stdout.write(f"Scanning {total} photos for GPS data...")
        
        for i, photo in enumerate(photos):
            if not os.path.exists(photo.file_path):
                continue
                
            try:
                # Use standard Image.open to get EXIF
                with Image.open(photo.file_path) as img:
                    exif = img.getexif()
                    lat, lon = get_gps_data(exif)
                    
                    if lat is not None and lon is not None:
                        # Update if changed or missing
                        if photo.latitude != lat or photo.longitude != lon:
                            photo.latitude = lat
                            photo.longitude = lon
                            photo.location_name = "" # Reset location name to trigger reverse geocoding if needed
                            photo.save(update_fields=['latitude', 'longitude', 'location_name'])
                            updated_count += 1
                            self.stdout.write(f"Updated GPS for {os.path.basename(photo.file_path)}: {lat}, {lon}")
                            
            except Exception as e:
                # self.stdout.write(self.style.WARNING(f"Error processing {photo.file_path}: {e}"))
                pass
                
            if (i + 1) % 100 == 0:
                self.stdout.write(f"Processed {i + 1}/{total} photos...")
                if task:
                    progress = int(((i + 1) / total) * 100)
                    MaintenanceTask.objects.filter(id=task.id).update(progress=progress)

        self.stdout.write(self.style.SUCCESS(f"Successfully updated GPS for {updated_count} photos."))
