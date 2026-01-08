from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import Memory
from ..serializers import MemorySerializer, PhotoSerializer
from ..services import MemoryService

class MemoryViewSet(viewsets.ModelViewSet):
    queryset = Memory.objects.all().order_by('-is_favorite', '-created_at')
    serializer_class = MemorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'description']

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """触发回忆生成"""
        try:
            stats = MemoryService.generate_all()
            return Response(stats)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def photos(self, request, pk=None):
        """获取回忆包含的照片"""
        memory = self.get_object()
        photos = memory.photos.all().order_by('captured_at')
        serializer = PhotoSerializer(photos, many=True)
        return Response(serializer.data)
