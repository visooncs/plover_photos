import uuid
from django.db import models

class Memory(models.Model):
    """回忆模型：自动生成的照片聚合"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, verbose_name="标题")
    description = models.TextField(blank=True, verbose_name="描述")
    
    class MemoryType(models.TextChoices):
        ON_THIS_DAY = 'on_this_day', '那年今日'
        TRAVEL = 'travel', '旅行足迹'
        PEOPLE = 'people', '人物重聚'
        MOOD = 'mood', '心境氛围'
        FESTIVAL = 'festival', '节日庆典'
        CUSTOM = 'custom', '自定义回忆'

    memory_type = models.CharField(max_length=20, choices=MemoryType.choices, verbose_name="回忆类型")
    
    # 回忆关联的照片
    photos = models.ManyToManyField('photos.Photo', related_name='memories', verbose_name="关联照片")
    
    # 回忆封面图
    cover = models.ForeignKey('photos.Photo', on_delete=models.SET_NULL, null=True, blank=True, related_name='+', verbose_name="封面")
    
    # 存储生成回忆的相关元数据 (例如: 地点名, 人物ID列表, 情感标签等)
    metadata = models.JSONField(default=dict, blank=True, verbose_name="元数据")
    
    # 是否置顶或收藏
    is_favorite = models.BooleanField(default=False, verbose_name="收藏")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "回忆"
        verbose_name_plural = "回忆"
        ordering = ['-is_favorite', '-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_memory_type_display()})"
