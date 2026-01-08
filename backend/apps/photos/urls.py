from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PhotoViewSet, AlbumViewSet, PersonViewSet, LibraryViewSet, 
    SystemViewSet, MemoryViewSet, MaintenanceTaskViewSet, ScheduledTaskViewSet,
    places_list, photo_serve, photo_video_serve, face_crop_serve, map_markers
)

router = DefaultRouter()
router.register(r'photos', PhotoViewSet)
router.register(r'albums', AlbumViewSet)
router.register(r'memories', MemoryViewSet)
router.register(r'people', PersonViewSet)
router.register(r'libraries', LibraryViewSet)
router.register(r'maintenance', MaintenanceTaskViewSet)
router.register(r'schedules', ScheduledTaskViewSet)
router.register(r'system', SystemViewSet, basename='system')

urlpatterns = [
    path('api/photos/places/', places_list, name='places_list'),
    path('api/', include(router.urls)),
    
    # Serve views
    path('photo/<uuid:pk>/serve/', photo_serve, name='photo_serve'),
    path('photo/<uuid:pk>/video/', photo_video_serve, name='photo_video_serve'),
    path('face/<uuid:pk>/crop/', face_crop_serve, name='face_crop_serve'),
    path('map/markers/', map_markers, name='map_markers'),
]
