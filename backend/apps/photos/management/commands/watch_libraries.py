import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from django.core.management.base import BaseCommand
from apps.photos.models import Library
from apps.photos.services import scan_directory
import threading

class LibraryHandler(FileSystemEventHandler):
    def __init__(self, library_id, logger):
        self.library_id = library_id
        self.logger = logger
        # Simple debounce mechanism could be added here
        
    def on_created(self, event):
        if event.is_directory:
            return
        self.logger(f"File created: {event.src_path}")
        # Trigger scan or single file import
        # For simplicity, we re-scan the library (scan_directory is optimized to skip existing)
        # In a production env, we should process just this file.
        # But scan_directory handles everything safely.
        # We run it in a separate thread to not block the observer
        threading.Thread(target=self.trigger_scan).start()

    def on_moved(self, event):
        if event.is_directory:
            return
        self.logger(f"File moved: {event.src_path} -> {event.dest_path}")
        threading.Thread(target=self.trigger_scan).start()

    def trigger_scan(self):
        try:
            # Re-fetch library to get current path
            library = Library.objects.get(id=self.library_id)
            scan_directory(library.path, library_id=library.id)
        except Exception as e:
            self.logger(f"Error scanning library {self.library_id}: {e}")

class Command(BaseCommand):
    help = 'Monitors library directories for changes and auto-scans them'

    def handle(self, *args, **options):
        self.stdout.write("Starting library monitor...")
        
        observer = Observer()
        
        # Initial setup
        self.update_observers(observer)
        
        observer.start()
        
        try:
            while True:
                # Check for new libraries every 10 seconds
                # In a real system, we might use database signals to update observers dynamically
                time.sleep(10)
                self.update_observers(observer)
        except KeyboardInterrupt:
            observer.stop()
        
        observer.join()

    def update_observers(self, observer):
        # This is a simplified logic. 
        # Ideally we should map paths to handlers and add/remove as needed.
        # For now, we just ensure all active libraries are watched.
        # Warning: This simple implementation might add duplicate watches if not careful,
        # but watchdog handles existing watches on the same path gracefully usually, 
        # or we should track them.
        
        # Let's track watched paths
        if not hasattr(self, 'watched_paths'):
            self.watched_paths = set()
            
        libraries = Library.objects.all()
        for lib in libraries:
            if lib.path not in self.watched_paths and os.path.exists(lib.path):
                self.stdout.write(f"Watching new library: {lib.path}")
                event_handler = LibraryHandler(lib.id, self.stdout.write)
                observer.schedule(event_handler, lib.path, recursive=True)
                self.watched_paths.add(lib.path)
