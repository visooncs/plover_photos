import uuid
from django.db import models

class Album(models.Model):
    """相册模型"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name="相册名称")
    description = models.TextField(blank=True, verbose_name="描述")
    cover = models.ForeignKey('photos.Photo', on_delete=models.SET_NULL, null=True, blank=True, related_name='covered_albums', verbose_name="封面")
    photos = models.ManyToManyField('photos.Photo', related_name='albums', verbose_name="照片")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "相册"
        verbose_name_plural = "相册"
        ordering = ['-created_at']

    def __str__(self):
        return self.name
