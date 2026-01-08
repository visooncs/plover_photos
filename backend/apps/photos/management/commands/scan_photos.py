import os
import hashlib
from datetime import datetime
from PIL import Image
from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware
from apps.photos.services import scan_directory
from apps.photos.models import Library

class Command(BaseCommand):
    help = 'Scan a directory for photos'

    def add_arguments(self, parser):
        parser.add_argument('path', type=str, nargs='?', help='Path to scan (optional if libraries are configured)')
        parser.add_argument('--task-id', type=str, help='系统维护任务 ID')

    def handle(self, *args, **options):
        path = options.get('path')
        task_id = options.get('task_id')
        
        if path:
            # Check if this path corresponds to a library
            library = Library.objects.filter(path=path).first()
            library_id = library.id if library else None
            scan_directory(path, logger=self.stdout.write, library_id=library_id, task_id=task_id)
        else:
            # Scan all libraries
            libraries = Library.objects.all()
            if not libraries.exists():
                self.stdout.write("No libraries configured and no path provided.")
                return

            self.stdout.write(f"Scanning {libraries.count()} libraries...")
            for lib in libraries:
                self.stdout.write(f"Scanning library: {lib.name} ({lib.path})")
                scan_directory(lib.path, logger=self.stdout.write, library_id=lib.id, task_id=task_id)

