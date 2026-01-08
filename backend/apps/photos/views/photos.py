from rest_framework import viewsets, filters, status, parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
import os

from ..models import Photo, Library
from ..serializers import PhotoSerializer
from ..services import process_single_file, search_photos_by_text

class PhotoViewSet(viewsets.ModelViewSet):
    queryset = Photo.objects.all().order_by('-captured_at')
    serializer_class = PhotoSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser] # 支持文件上传
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_live_photo', 'albums']
    search_fields = ['location_name', 'file_path']
    ordering_fields = ['captured_at', 'created_at']

    @action(detail=False, methods=['post'], parser_classes=[parsers.MultiPartParser])
    def upload(self, request):
        """Web 上传照片接口"""
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 确定保存路径
        library = Library.objects.first()
        if not library:
             # 如果没有库，创建一个默认的
             default_path = os.path.join(os.getcwd(), 'photos_library')
             os.makedirs(default_path, exist_ok=True)
             library = Library.objects.create(name="Default Library", path=default_path)
        
        # 在库目录下创建一个 'WebUploads' 文件夹
        upload_dir = os.path.join(library.path, 'WebUploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        # 防止文件名冲突
        file_name = file_obj.name
        base, ext = os.path.splitext(file_name)
        counter = 1
        save_path = os.path.join(upload_dir, file_name)
        while os.path.exists(save_path):
            save_path = os.path.join(upload_dir, f"{base}_{counter}{ext}")
            counter += 1
            
        # 保存文件
        try:
            with open(save_path, 'wb+') as destination:
                for chunk in file_obj.chunks():
                    destination.write(chunk)
            
            # 调用 process_single_file 进行导入处理
            # process_single_file 需要在线程安全或适当的上下文中运行，这里直接调用即可
            # 注意：这可能会阻塞请求，对于大文件或大量文件建议使用 Celery 异步任务
            # 但作为 MVP，同步处理是可以接受的
            process_single_file(save_path)
            
            # 查找刚创建的对象
            photo = Photo.objects.filter(file_path=save_path).first()
            if photo:
                serializer = self.get_serializer(photo)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                 return Response({'error': 'File saved but not processed correctly'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_queryset(self):
        """默认过滤掉已删除的照片"""
        qs = Photo.objects.all().order_by('-captured_at')
        
        # 自定义 people 过滤：使用 faces__person 而不是 people (ManyToMany)
        # 这样可以确保即使 Person.photos 字段没有同步，也能查出照片
        person_id = self.request.query_params.get('people')
        if person_id:
            qs = qs.filter(faces__person_id=person_id).distinct()

        # 如果是 trash action，则显示已删除的
        if self.action == 'trash':
            return Photo.objects.filter(deleted_at__isnull=False).order_by('-deleted_at')
        # 否则只显示未删除的
        return qs.filter(deleted_at__isnull=True)

    def perform_destroy(self, instance):
        """软删除：设置 deleted_at 而不是真正删除"""
        instance.deleted_at = timezone.now()
        instance.save()

    @action(detail=False, methods=['get'])
    def trash(self, request):
        """获取回收站中的照片"""
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """恢复已删除的照片"""
        # 注意：需要绕过 get_queryset 的过滤来找到已删除的对象
        try:
            photo = Photo.objects.get(pk=pk, deleted_at__isnull=False)
            photo.deleted_at = None
            photo.save()
            return Response({'status': 'restored'})
        except Photo.DoesNotExist:
            return Response({'error': 'Photo not found in trash'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['delete'])
    def permanent_delete(self, request, pk=None):
        """永久删除照片"""
        try:
            photo = Photo.objects.get(pk=pk, deleted_at__isnull=False)
            # 同时删除物理文件 (可选，根据需求)
            # 这里先只删除数据库记录
            photo.delete() 
            return Response({'status': 'permanently_deleted'})
        except Photo.DoesNotExist:
            return Response({'error': 'Photo not found in trash'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['delete'])
    def empty_trash(self, request):
        """清空回收站"""
        count, _ = Photo.objects.filter(deleted_at__isnull=False).delete()
        return Response({'status': 'trash_emptied', 'count': count})

    @action(detail=False, methods=['get'])
    def search(self, request):
        """语义搜索接口 (融合关键词匹配)"""
        query = request.query_params.get('q', '')
        if not query:
            return Response([])
            
        try:
            # 1. 关键词匹配 (Location, FilePath)
            keyword_results = Photo.objects.filter(
                Q(location_name__icontains=query) | 
                Q(file_path__icontains=query)
            ).order_by('-captured_at')[:100]
            
            # 2. 语义搜索 (尝试执行，如果失败则降级)
            semantic_results = []
            try:
                semantic_results = search_photos_by_text(query, limit=100)
            except Exception as e:
                print(f"Semantic search failed (downgrading to keyword only): {e}")
                # 语义搜索失败不影响主流程
            
            # 3. 合并去重 (优先显示关键词匹配结果)
            results = list(keyword_results)
            existing_ids = set(p.id for p in results)
            
            for p in semantic_results:
                if p.id not in existing_ids:
                    results.append(p)
            
            serializer = self.get_serializer(results, many=True)
            return Response(serializer.data)
        except Exception as e:
            # 如果完全失败 (如数据库连接断开)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
