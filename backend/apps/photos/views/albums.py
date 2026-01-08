from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import Album, Photo
from ..serializers import AlbumSerializer
from ..services import get_all_recommendations

class AlbumViewSet(viewsets.ModelViewSet):
    queryset = Album.objects.all().order_by('-created_at')
    serializer_class = AlbumSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        """获取智能相册推荐"""
        try:
            recs = get_all_recommendations()
            # Serialize cover photos manually or use a simple serializer
            # For simplicity, we just return the raw data, but we need valid image URLs for covers
            
            # Helper to get thumbnail URL
            def get_thumb(photo_id):
                if not photo_id: return None
                return f"/photo/{photo_id}/serve/?size=300&crop=1"

            for rec in recs:
                rec['cover_url'] = get_thumb(rec.get('cover_id'))
                
            return Response(recs)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def save_recommendation(self, request):
        """保存推荐为正式相册"""
        title = request.data.get('title')
        rec_type = request.data.get('type')
        query_params = request.data.get('query_params', {})
        
        if not title:
            return Response({'error': 'Title is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Create Album
        album = Album.objects.create(name=title, description=f"From {rec_type} recommendation")
        
        # Add photos based on type/query
        photos = Photo.objects.none()
        
        if rec_type == 'person':
            person_id = query_params.get('people')
            if person_id:
                photos = Photo.objects.filter(people__id=person_id)
                
        elif rec_type == 'location':
            location = query_params.get('location')
            if location:
                photos = Photo.objects.filter(location_name=location)
                
        elif rec_type == 'event':
            date_after = query_params.get('date_after')
            date_before = query_params.get('date_before')
            if date_after:
                photos = Photo.objects.filter(captured_at__gte=date_after, captured_at__lt=date_before)
                
        if photos.exists():
            album.photos.add(*photos)
            album.cover = photos.first()
            album.save()
            
        return Response(AlbumSerializer(album).data)

    @action(detail=True, methods=['post'])
    def add_photos(self, request, pk=None):
        """添加照片到相册"""
        album = self.get_object()
        photo_ids = request.data.get('photo_ids', [])
        
        if not photo_ids:
            return Response({'error': 'No photo_ids provided'}, status=status.HTTP_400_BAD_REQUEST)
            
        photos = Photo.objects.filter(id__in=photo_ids)
        album.photos.add(*photos)
        
        # 如果相册没有封面，自动设置第一张
        if not album.cover and photos.exists():
            album.cover = photos.first()
            album.save()
            
        return Response({'status': 'added', 'count': photos.count()})

    @action(detail=True, methods=['post'])
    def remove_photos(self, request, pk=None):
        """从相册移除照片"""
        album = self.get_object()
        photo_ids = request.data.get('photo_ids', [])
        
        if not photo_ids:
            return Response({'error': 'No photo_ids provided'}, status=status.HTTP_400_BAD_REQUEST)
            
        photos = Photo.objects.filter(id__in=photo_ids)
        album.photos.remove(*photos)
        
        # 如果封面被移除，重置封面
        if album.cover_id in photo_ids:
            first_photo = album.photos.first()
            album.cover = first_photo
            album.save()
            
        return Response({'status': 'removed'})

    @action(detail=True, methods=['post'])
    def set_cover(self, request, pk=None):
        """设置相册封面"""
        album = self.get_object()
        photo_id = request.data.get('photo_id')
        
        if not photo_id:
            return Response({'error': 'photo_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            photo = Photo.objects.get(id=photo_id)
            album.cover = photo
            album.save()
            return Response({'status': 'updated'})
        except Photo.DoesNotExist:
             return Response({'error': 'Photo not found'}, status=status.HTTP_404_NOT_FOUND)
