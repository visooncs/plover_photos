from django.core.management.base import BaseCommand
from apps.photos.models import Person, Photo, Face
from django.db.models import Count

class Command(BaseCommand):
    help = 'Diagnostic tool for missing photos in person details'

    def add_arguments(self, parser):
        parser.add_argument('person_name', type=str, help='Name of the person to diagnose')

    def handle(self, *args, **options):
        person_name = options['person_name']
        self.stdout.write(f"Diagnosing for person: {person_name}")

        people = Person.objects.filter(name=person_name)
        if not people.exists():
            self.stdout.write(self.style.ERROR(f"No person found with name: {person_name}"))
            return

        for person in people:
            self.stdout.write(self.style.SUCCESS(f"\n--- Person ID: {person.id} (Hidden: {person.is_hidden}) ---"))
            
            # 1. Check ManyToMany relation
            m2m_count = person.photos.count()
            self.stdout.write(f"Direct ManyToMany count: {m2m_count}")
            
            # 2. Check Face relation
            face_photos = Face.objects.filter(person=person).values_list('photo_id', flat=True).distinct()
            face_count = len(face_photos)
            self.stdout.write(f"Face relation count: {face_count}")
            
            # 3. Find mismatch
            m2m_ids = set(person.photos.values_list('id', flat=True))
            face_ids = set(face_photos)
            
            missing_in_m2m = face_ids - m2m_ids
            if missing_in_m2m:
                self.stdout.write(self.style.WARNING(f"Photos in Face but missing in M2M: {len(missing_in_m2m)}"))
                for pid in list(missing_in_m2m)[:5]:
                    self.stdout.write(f"  - Photo ID: {pid}")
            else:
                 self.stdout.write(self.style.SUCCESS("All Face photos are in M2M."))

            # 4. Check API Visibility Logic
            # Simulate API filter
            api_qs = Photo.objects.filter(deleted_at__isnull=True, faces__person=person).distinct()
            api_count = api_qs.count()
            self.stdout.write(f"API Visible count (deleted_at=Null): {api_count}")

            # Simulate API Response (First Page)
            from rest_framework.test import APIRequestFactory
            from apps.photos.views import PhotoViewSet
            
            factory = APIRequestFactory()
            request = factory.get(f'/api/photos/?people={person.id}', HTTP_HOST='127.0.0.1:8200')
            view = PhotoViewSet.as_view({'get': 'list'})
            response = view(request)
            
            if hasattr(response, 'data'):
                results = response.data.get('results', []) if isinstance(response.data, dict) else response.data
                self.stdout.write(f"API Response Count (Page 1): {len(results)}")
                
                # Check if target photos are in Page 1
                # Check for the photo ID found in previous step (the one created recently)
                target_id = "2c92e265-1aea-44dd-a814-193989363eda" # From previous shell output
                found = any(str(p['id']) == target_id for p in results)
                self.stdout.write(f"Is target photo {target_id} in Page 1? {found}")
                
                self.stdout.write("Top 5 photos in Page 1:")
                for p in results[:5]:
                    self.stdout.write(f"  ID: {p['id']}, Captured: {p.get('captured_at')}")
            
            if api_count < face_count:
                self.stdout.write(self.style.WARNING(f"Diff: {face_count - api_count} photos are hidden by API filter (probably deleted)"))
                
                # Check deleted ones
                deleted_qs = Photo.objects.filter(deleted_at__isnull=False, faces__person=person).distinct()
                self.stdout.write(f"Deleted photos count: {deleted_qs.count()}")
                for p in deleted_qs[:5]:
                     self.stdout.write(f"  - Deleted Photo: {p.id} at {p.deleted_at}")
