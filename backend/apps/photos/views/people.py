from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Prefetch, Count, Case, When, Value, IntegerField
from pgvector.django import CosineDistance
from django.core.management import call_command
import threading

from ..models import Person, Face, Photo
from ..serializers import PersonSerializer
from ..services import scan_all_faces, generate_photo_embedding

class PersonViewSet(viewsets.ModelViewSet):
    queryset = Person.objects.all() # Satisfy DRF router introspection
    serializer_class = PersonSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def get_queryset(self):
        show_hidden = self.request.query_params.get('show_hidden') == 'true'
        
        if show_hidden:
            queryset = Person.objects.filter(is_hidden=True)
        else:
            queryset = Person.objects.filter(is_hidden=False)
        
        # 预加载人脸以优化 representative_face 获取
        queryset = queryset.prefetch_related(
            Prefetch('faces', queryset=Face.objects.order_by('-prob'), to_attr='prefetched_faces')
        )
        
        # 1. 注解照片数量
        # 使用 faces__photo 进行计数，确保与详情页查询逻辑一致（不依赖 ManyToMany 同步）
        queryset = queryset.annotate(photo_count=Count('faces__photo', distinct=True))
        
        # 2. 区分已命名和默认命名 (默认命名格式: 人物_数字)
        # is_default_name: 1 (是默认), 0 (是已命名)
        queryset = queryset.annotate(
            is_default_name=Case(
                When(name__regex=r'^人物_\d+$', then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        )
        
        # 3. 排序: 标星优先(True > False), 已命名优先(0 < 1), 然后按照片数量降序, 最后按创建时间
        return queryset.order_by('-is_starred', 'is_default_name', '-photo_count', '-created_at')

    @action(detail=True, methods=['post'])
    def star(self, request, pk=None):
        """标星人物"""
        person = self.get_object()
        person.is_starred = True
        person.save()
        return Response({'status': 'starred'})

    @action(detail=True, methods=['post'])
    def unstar(self, request, pk=None):
        """取消标星"""
        person = self.get_object()
        person.is_starred = False
        person.save()
        return Response({'status': 'unstarred'})

    @action(detail=True, methods=['post'])
    def remove_photo(self, request, pk=None):
        """从人物中移除照片"""
        person = self.get_object()
        photo_id = request.data.get('photo_id')
        
        if not photo_id:
            return Response({'error': 'No photo_id provided'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            photo = Photo.objects.get(id=photo_id)
        except Photo.DoesNotExist:
            return Response({'error': 'Photo not found'}, status=status.HTTP_404_NOT_FOUND)

        # 1. 解除 Face 关联
        faces = Face.objects.filter(photo=photo, person=person)
        if faces.exists():
            faces.update(person=None)
            
        # 2. 解除 ManyToMany 关联
        person.photos.remove(photo)
        
        # 3. 如果是头像，清除头像
        if person.avatar_id == photo.id:
            person.avatar = None
            person.ensure_avatar() # 尝试找一个新的头像
            person.save()
            
        return Response({'status': 'removed'})

    @action(detail=True, methods=['post'])
    def hide(self, request, pk=None):
        person = self.get_object()
        person.is_hidden = True
        person.save()
        return Response({'status': 'hidden'})

    @action(detail=True, methods=['post'])
    def unhide(self, request, pk=None):
        """取消隐藏人物"""
        person = self.get_object()
        person.is_hidden = False
        person.save()
        return Response({'status': 'unhidden'})

    @action(detail=True, methods=['post'])
    def merge(self, request, pk=None):
        """合并人物: 将其他人合并到当前人物"""
        target_person = self.get_object()
        source_ids = request.data.get('source_ids', [])
        
        if not source_ids:
            return Response({'error': 'No source ids provided'}, status=status.HTTP_400_BAD_REQUEST)
            
        source_people = Person.objects.filter(id__in=source_ids)
        merged_count = 0
        
        for source_person in source_people:
            if source_person.id != target_person.id:
                source_person.merge_with(target_person)
                merged_count += 1
                
        return Response({'status': 'merged', 'count': merged_count})

    @action(detail=True, methods=['post'])
    def set_cover(self, request, pk=None):
        """设置人物封面 (头像)"""
        person = self.get_object()
        photo_id = request.data.get('photo_id')
        if not photo_id:
             return Response({'error': 'photo_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            photo = Photo.objects.get(id=photo_id)
            # Verify the photo has a face belonging to this person
            # 注意：这里我们放宽一点限制，只要照片有关联的 Face 且归属该 Person 即可
            # 如果只是照片在 Person.photos 中但没有检测出 Face，可能无法正确截取头像
            if not person.faces.filter(photo=photo).exists():
                 return Response({'error': 'This photo does not contain a face assigned to this person'}, status=status.HTTP_400_BAD_REQUEST)
            
            person.avatar = photo
            person.save()
            return Response({'status': 'updated', 'face_url': PersonSerializer(person).data['face_url']})
        except Photo.DoesNotExist:
            return Response({'error': 'Photo not found'}, status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request, *args, **kwargs):
        """
        删除人物：释放关联的所有人脸（变为未标记），并删除该人物实体。
        """
        person = self.get_object()
        # 释放所有关联的人脸
        person.faces.all().update(person=None)
        # 正常删除
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def reset(self, request, pk=None):
        """
        重置人物：释放关联的所有人脸（变为未标记），并删除该人物实体。
        这允许这些照片重新进入聚类流程。
        """
        person = self.get_object()
        
        # 1. 释放所有关联的人脸 (将 person 字段置为 NULL)
        # 这样它们就会变成 "未标记人脸"，可以被下次聚类重新扫描
        updated_count = person.faces.all().update(person=None)
        
        # 2. 删除人物实体
        # 注意：由于 on_delete 通常是 SET_NULL 或 CASCADE，但我们已经手动处理了 faces。
        # 对于 photos (ManyToMany)，删除 person 会自动移除关联表记录，不会删照片。
        person_id = person.id
        person_name = person.name
        person.delete()
        
        return Response({
            'status': 'reset', 
            'message': f'人物 "{person_name}" 已重置，{updated_count} 张人脸已释放待重新聚类。',
            'released_faces': updated_count
        })

    @action(detail=True, methods=['get'])
    def similar(self, request, pk=None):
        """查找相似人物"""
        person = self.get_object()
        face = person.representative_face
        if not face or face.embedding is None:
            return Response([])

        try:
            threshold = float(request.query_params.get('threshold', 0.5))
        except ValueError:
            threshold = 0.5
        
        # Find similar faces belonging to OTHER people
        similar_faces = Face.objects.filter(
            person__isnull=False,
            embedding__isnull=False
        ).exclude(
            person=person
        ).annotate(
            distance=CosineDistance('embedding', face.embedding)
        ).filter(
            distance__lt=threshold
        ).order_by('distance')[:200] # 限制数量以防过大

        # Group by person, keeping the best match per person
        similar_people_map = {}
        for f in similar_faces:
            if f.person_id not in similar_people_map:
                similar_people_map[f.person_id] = {
                    'person': f.person,
                    'distance': f.distance,
                }
        
        # Convert to list and sort
        results = []
        for item in similar_people_map.values():
            p = item['person']
            results.append({
                'id': p.id,
                'name': p.name,
                'face_url': f"/face/{p.representative_face.id}/crop/" if p.representative_face else None,
                'distance': item['distance'],
                'photo_count': p.photos.count()
            })
        
        results.sort(key=lambda x: x['distance'])
        return Response(results)

    @action(detail=False, methods=['post'])
    def scan_faces(self, request):
        """触发全量人脸扫描与聚类"""
        
        def run_task():
            scan_all_faces()
            
        thread = threading.Thread(target=run_task)
        thread.daemon = True
        thread.start()
        
        return Response({'status': 'face_scan_started'})

    @action(detail=False, methods=['post'])
    def process_embeddings(self, request):
        """生成语义搜索索引"""
        
        def run_task():
            photos = Photo.objects.filter(embedding_data__isnull=True)
            for photo in photos:
                try:
                    generate_photo_embedding(photo.id)
                except Exception as e:
                    print(f"Error processing embedding for {photo.id}: {e}")
                    
        thread = threading.Thread(target=run_task)
        thread.daemon = True
        thread.start()
        return Response({'status': 'embedding_processing_started'})

    @action(detail=False, methods=['post'])
    def generate_memories(self, request):
        """生成智能回忆"""
        
        def run_task():
            call_command('generate_memories')
            
        thread = threading.Thread(target=run_task)
        thread.daemon = True
        thread.start()
        return Response({'status': 'memory_generation_started'})

    @action(detail=False, methods=['post'])
    def update_locations(self, request):
        """更新地点信息"""
        provider = request.data.get('provider', 'geopy')
        
        def run_task():
            call_command('update_locations', provider=provider)
            
        thread = threading.Thread(target=run_task)
        thread.daemon = True
        thread.start()
        return Response({'status': 'location_update_started'})
