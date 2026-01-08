from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
import shutil
import os
from ..models import Photo, Library

class SystemViewSet(viewsets.ViewSet):
    """
    系统相关 API
    """
    @action(detail=False, methods=['get'])
    def storage(self, request):
        # 1. 计算照片总占用空间
        total_size = Photo.objects.aggregate(total=Sum('size'))['total'] or 0
        
        # 2. 获取磁盘空间信息
        # 优先使用 Library 的路径，如果没有则使用当前工作目录
        library = Library.objects.first()
        check_path = library.path if library and os.path.exists(library.path) else os.getcwd()
        
        try:
            usage = shutil.disk_usage(check_path)
            return Response({
                'used_bytes': total_size,
                'disk_total': usage.total,
                'disk_used': usage.used,
                'disk_free': usage.free,
                'path': check_path
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
