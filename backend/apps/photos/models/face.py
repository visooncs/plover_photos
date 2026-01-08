import uuid
from django.db import models
from pgvector.django import VectorField

class Person(models.Model):
    """人物模型"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, db_index=True, verbose_name="姓名")
    avatar = models.ForeignKey('photos.Photo', on_delete=models.SET_NULL, null=True, blank=True, related_name='avatar_of', verbose_name="头像")
    photos = models.ManyToManyField('photos.Photo', related_name='people', verbose_name="照片")
    
    # 聚类标识，用于自动分组
    cluster_id = models.IntegerField(null=True, blank=True, db_index=True, verbose_name="聚类ID")
    is_hidden = models.BooleanField(default=False, db_index=True, verbose_name="是否隐藏")
    is_starred = models.BooleanField(default=False, db_index=True, verbose_name="是否标星")
    
    # 忽略的合并建议
    ignored_merges = models.ManyToManyField('self', symmetrical=True, blank=True, verbose_name="忽略的合并建议")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "人物"
        verbose_name_plural = "人物"

    def __str__(self):
        return self.name

    def sync_photos(self):
        """将所有通过 Face 关联的照片也同步到 photos ManyToMany 字段中"""
        face_photo_ids = self.faces.values_list('photo_id', flat=True).distinct()
        if face_photo_ids:
            self.photos.add(*face_photo_ids)
        return len(face_photo_ids)

    def ensure_avatar(self):
        """确保人物有头像，如果缺失则自动挑选一个"""
        if self.avatar:
            return self.avatar
            
        # 优先从关联的面孔中挑选
        best_face = self.faces.order_by('-prob').first()
        if best_face:
            self.avatar = best_face.photo
            self.save(update_fields=['avatar'])
            return self.avatar
            
        # 其次从关联的照片中挑选
        first_photo = self.photos.first()
        if first_photo:
            self.avatar = first_photo
            self.save(update_fields=['avatar'])
            return self.avatar
            
        return None

    @property
    def representative_face(self):
        """获取该人物的代表性人脸（优先选择置信度最高的人脸，如果设置了头像照片，则优先使用头像照片中的人脸）"""
        # 如果设置了头像照片，优先查找头像照片中的人脸
        if self.avatar_id:
            if hasattr(self, 'prefetched_faces'):
                 # 在预加载的列表中查找
                 for face in self.prefetched_faces:
                     if face.photo_id == self.avatar_id:
                         return face
            else:
                # 注意：这里假设一个人在同一张照片中只有一个 Face 归属自己
                # 如果有多个，可能需要更复杂的逻辑，但通常同一张照片不会有同一个人的多张脸
                avatar_face = self.faces.filter(photo_id=self.avatar_id).first()
                if avatar_face:
                    return avatar_face

        if hasattr(self, 'prefetched_faces'):
            return self.prefetched_faces[0] if self.prefetched_faces else None
        return self.faces.order_by('-prob').first()

    def merge_with(self, other_person):
        """将当前人物合并到另一个人物"""
        if self == other_person:
            return
            
        # 1. 批量转移所有照片关联 (使用 *args 批量添加)
        photo_ids = self.photos.values_list('id', flat=True)
        if photo_ids:
            other_person.photos.add(*photo_ids)
            
        # 2. 批量转移所有面孔关联 (直接 update)
        self.faces.update(person=other_person)
        
        # 3. 如果对方没有头像，把自己的头像给它
        if not other_person.avatar and self.avatar:
            other_person.avatar = self.avatar
            other_person.save(update_fields=['avatar'])
            
        # 4. 转移忽略的合并建议 (ManyToMany)
        # 获取对方已有的忽略列表
        other_ignored = set(other_person.ignored_merges.values_list('id', flat=True))
        self_ignored = self.ignored_merges.values_list('id', flat=True)
        # 过滤掉已有的和对方自己
        new_ignored = [pid for pid in self_ignored if pid != other_person.id and pid not in other_ignored]
        if new_ignored:
            other_person.ignored_merges.add(*new_ignored)

        # 5. 删除自己
        self.delete()

class Face(models.Model):
    """人脸模型：存储照片中检测到的人脸"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    photo = models.ForeignKey('photos.Photo', on_delete=models.CASCADE, related_name='faces', verbose_name="照片")
    person = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True, related_name='faces', verbose_name="所属人物")
    
    # 人脸在原图中的位置 [x1, y1, x2, y2]
    bbox = models.JSONField(verbose_name="边界框")
    
    # 检测置信度
    prob = models.FloatField(default=0.0, db_index=True, verbose_name="置信度")
    
    # 人脸特征向量 (通常为 128 或 512 维)
    embedding = VectorField(dimensions=512, null=True, blank=True, verbose_name="特征向量")
    
    # 视频相关
    timestamp = models.FloatField(null=True, blank=True, verbose_name="视频时间点(秒)")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "人脸"
        verbose_name_plural = "人脸"

    def set_embedding(self, embedding_array):
        """保存向量"""
        self.embedding = embedding_array

    def get_embedding(self):
        """获取向量"""
        return self.embedding
