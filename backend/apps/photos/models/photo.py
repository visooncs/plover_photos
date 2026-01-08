import uuid
from django.db import models
from pgvector.django import VectorField

class Photo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file_path = models.CharField(max_length=512, unique=True, help_text="Physical path on disk")
    hash_md5 = models.CharField(max_length=32, unique=True, db_index=True)
    captured_at = models.DateTimeField(null=True, blank=True, db_index=True)
    
    # Live Photo / Motion Photo support
    is_live_photo = models.BooleanField(default=False)
    video_path = models.CharField(max_length=512, blank=True, null=True, help_text="Path to companion video")
    
    # GPS 信息
    latitude = models.FloatField(null=True, blank=True, verbose_name="纬度")
    longitude = models.FloatField(null=True, blank=True, verbose_name="经度")
    location_name = models.CharField(max_length=255, blank=True, verbose_name="地点名称")

    # EXIF 信息
    exif_camera_make = models.CharField(max_length=100, blank=True, null=True, verbose_name="相机厂商")
    exif_camera_model = models.CharField(max_length=100, blank=True, null=True, verbose_name="相机型号")
    exif_lens_model = models.CharField(max_length=100, blank=True, null=True, verbose_name="镜头型号")
    exif_iso = models.IntegerField(null=True, blank=True, verbose_name="ISO")
    exif_f_number = models.FloatField(null=True, blank=True, verbose_name="光圈")
    exif_exposure_time = models.CharField(max_length=50, blank=True, null=True, verbose_name="快门时间")
    exif_focal_length = models.FloatField(null=True, blank=True, verbose_name="焦距")
    
    # 聚类相关
    # CLIP 语义特征向量 (512维 for ViT-B-32)
    embedding_data = VectorField(dimensions=512, null=True, blank=True, verbose_name="语义向量")
    
    # 扫描标记
    face_scanned = models.BooleanField(default=False, db_index=True, verbose_name="已扫描人脸")
    
    # Metadata
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    size = models.PositiveBigIntegerField(null=True, blank=True, help_text="File size in bytes")
    duration = models.FloatField(null=True, blank=True, verbose_name="视频时长(秒)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name="删除时间")

    class Meta:
        ordering = ['-captured_at', '-created_at']
        indexes = [
            models.Index(fields=['captured_at']),
            models.Index(fields=['hash_md5']),
        ]

    def __str__(self):
        return f"{self.file_path} ({self.id})"

    @property
    def is_video(self):
        """是否是纯视频或包含视频的 Live Photo"""
        return bool(self.video_path) or self.is_live_photo

    @property
    def is_pure_video(self):
        """是否是纯视频文件 (不是 Live Photo)"""
        # is_video 包含了 live photo，所以这里要排除 live photo
        return (bool(self.video_path) and not self.is_live_photo)

    def set_embedding(self, embedding_array):
        """保存特征向量"""
        self.embedding_data = embedding_array

    def get_embedding(self):
        """获取特征向量"""
        return self.embedding_data
