from django.core.management.base import BaseCommand
from apps.photos.models import Photo
import time
import sys

class Command(BaseCommand):
    help = 'Update location names (City/District) for photos using reverse geocoding (Supports Chinese)'

    def add_arguments(self, parser):
        parser.add_argument('--task-id', type=str, help='系统维护任务 ID')
        parser.add_argument(
            '--provider',
            type=str,
            default='geopy',
            choices=['geopy', 'offline'],
            help='Geocoding provider: "geopy" (Online, Chinese supported) or "offline" (Fast, English only)'
        )

    def handle(self, *args, **options):
        task_id = options.get('task_id')
        from apps.photos.models import MaintenanceTask
        task = None
        if task_id:
            try:
                task = MaintenanceTask.objects.get(id=task_id)
            except MaintenanceTask.DoesNotExist:
                pass

        provider = options['provider']
        
        # 1. Get photos with GPS but no location name (or force update logic if needed)
        #    Currently we update all photos with GPS to ensure Chinese names if requested
        photos = Photo.objects.exclude(latitude=None).exclude(longitude=None)
        total = photos.count()
        
        if total == 0:
            self.stdout.write("No photos with GPS data found.")
            return

        self.stdout.write(f"Found {total} photos with GPS. Using provider: {provider}")
        
        updated_count = 0
        
        if provider == 'geopy':
            try:
                from geopy.geocoders import Nominatim
                from geopy.exc import GeocoderTimedOut, GeocoderServiceError
                
                # Initialize Geocoder
                geolocator = Nominatim(user_agent="plover_photos_app", timeout=10)
                
                for i, photo in enumerate(photos):
                    try:
                        # Add delay to respect Nominatim usage policy (1 request per second max recommended)
                        time.sleep(1.1)
                        
                        location = geolocator.reverse(
                            f"{photo.latitude}, {photo.longitude}", 
                            language='zh-cn',
                            exactly_one=True
                        )
                        
                        if location:
                            address = location.raw.get('address', {})
                            
                            # Construct location name: City, District
                            # e.g., "北京市, 朝阳区" or "南宁市, 青秀区"
                            city = address.get('city', '') or address.get('town', '') or address.get('village', '') or address.get('county', '')
                            district = address.get('district', '') or address.get('suburb', '')
                            province = address.get('state', '')
                            country = address.get('country', '')
                            
                            parts = []
                            if province and province != city: # avoid "Beijing, Beijing"
                                parts.append(province)
                            if city:
                                parts.append(city)
                            if district:
                                parts.append(district)
                                
                            # If no specific city/district, use country
                            if not parts and country:
                                parts.append(country)
                                
                            new_location_name = " ".join(parts)
                            
                            if photo.location_name != new_location_name:
                                photo.location_name = new_location_name
                                photo.save(update_fields=['location_name'])
                                updated_count += 1
                                self.stdout.write(f"[{i+1}/{total}] Updated: {new_location_name}")
                            else:
                                self.stdout.write(f"[{i+1}/{total}] Skipped (Unchanged): {new_location_name}")
                        else:
                            self.stdout.write(f"[{i+1}/{total}] No address found for {photo.latitude}, {photo.longitude}")
                            
                    except (GeocoderTimedOut, GeocoderServiceError) as e:
                        self.stdout.write(self.style.WARNING(f"[{i+1}/{total}] Geocoding error: {e}"))
                        time.sleep(5) # Wait longer on error
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"[{i+1}/{total}] Error processing photo {photo.id}: {e}"))

            except ImportError:
                self.stdout.write(self.style.ERROR("geopy not installed. Please run 'pip install geopy'"))
                return

        else: # offline (reverse_geocoder)
            import reverse_geocoder as rg
            
            # Batch processing for offline mode
            batch_size = 1000
            
            def chunked_queryset(queryset, chunk_size):
                start = 0
                while True:
                    chunk = list(queryset[start:start + chunk_size])
                    if not chunk:
                        break
                    yield chunk
                    start += chunk_size

            for chunk in chunked_queryset(photos, batch_size):
                coords = [(p.latitude, p.longitude) for p in chunk]
                results = rg.search(coords)
                
                for photo, result in zip(chunk, results):
                    city = result.get('name', '')
                    # district = result.get('admin2', '') 
                    
                    # reverse_geocoder is limited, usually gives English City
                    if photo.location_name != city:
                        photo.location_name = city
                        photo.save(update_fields=['location_name'])
                        updated_count += 1
                
                self.stdout.write(f"Processed batch. Total updated: {updated_count}")

        self.stdout.write(self.style.SUCCESS(f"Finished. Updated {updated_count} location names."))
