from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.photos.models import Photo

class Command(BaseCommand):
    help = 'Delete photos that have been in trash for more than 30 days'

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

        threshold = timezone.now() - timedelta(days=30)
        
        # Filter photos deleted before threshold
        photos_to_delete = Photo.objects.filter(deleted_at__lt=threshold)
        count = photos_to_delete.count()
        
        if count > 0:
            self.stdout.write(f'Found {count} photos in trash older than 30 days. Deleting...')
            if task: MaintenanceTask.objects.filter(id=task.id).update(progress=10)
            photos_to_delete.delete() # This performs hard delete
            self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} photos.'))
        else:
            self.stdout.write('No photos found in trash older than 30 days.')
            
        if task: MaintenanceTask.objects.filter(id=task.id).update(progress=100)
