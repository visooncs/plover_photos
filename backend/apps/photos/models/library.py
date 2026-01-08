import uuid
from django.db import models

class Library(models.Model):
    """照片库：管理本地文件夹入口"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, help_text="库名称")
    path = models.CharField(max_length=512, unique=True, help_text="本地目录绝对路径")
    last_scanned_at = models.DateTimeField(null=True, blank=True)
    
    # 扫描进度追踪
    class ScanStatus(models.TextChoices):
        IDLE = 'idle', '空闲'
        SCANNING = 'scanning', '扫描中'
        PAUSED = 'paused', '已暂停'
        COMPLETED = 'completed', '已完成'
        FAILED = 'failed', '失败'

    scan_status = models.CharField(max_length=20, choices=ScanStatus.choices, default=ScanStatus.IDLE)
    total_files = models.PositiveIntegerField(default=0)
    processed_files = models.PositiveIntegerField(default=0)
    scan_error = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def scan_progress_percent(self):
        if self.total_files > 0:
            return int((self.processed_files / self.total_files) * 100)
        return 0

    class Meta:
        verbose_name = "照片库"
        verbose_name_plural = "照片库"

    def __str__(self):
        return f"{self.name} ({self.path})"
