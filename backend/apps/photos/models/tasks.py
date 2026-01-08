import uuid
from django.db import models

class MaintenanceTask(models.Model):
    """System maintenance tasks (scan, analysis, cleanup)"""
    TASK_TYPES = [
        ('scan_photos', '扫描照片'),
        ('process_faces', '人脸识别'),
        ('cluster_people', '人脸聚类'),
        ('generate_memories', '生成回忆'),
        ('cleanup_trash', '清空回收站'),
        ('update_gps', '更新GPS信息'),
        ('process_embeddings', '生成语义向量'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '等待中'),
        ('running', '进行中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, choices=TASK_TYPES)
    params = models.JSONField(default=dict, blank=True, verbose_name="参数")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress = models.IntegerField(default=0, help_text="进度 0-100")
    logs = models.TextField(blank=True, default="")
    error_message = models.TextField(blank=True, null=True)
    
    created_by = models.CharField(max_length=100, blank=True, default="system")
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "维护任务"
        verbose_name_plural = "维护任务"

    def __str__(self):
        return f"{self.get_name_display()} ({self.status})"

class ScheduledTask(models.Model):
    """定时维护任务配置"""
    TASK_TYPES = MaintenanceTask.TASK_TYPES
    
    SCHEDULE_TYPE_CHOICES = [
        ('daily', '每天'),
        ('weekly', '每周'),
        ('interval', '间隔'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, choices=TASK_TYPES, verbose_name="任务类型")
    params = models.JSONField(default=dict, blank=True, verbose_name="参数")
    
    schedule_type = models.CharField(max_length=20, choices=SCHEDULE_TYPE_CHOICES, default='daily', verbose_name="调度类型")
    # For daily: "HH:MM", for weekly: "d HH:MM" (0=Mon), for interval: minutes
    schedule_value = models.CharField(max_length=50, help_text="格式：每天 HH:MM，每周 d HH:MM (0=周一)，间隔 分钟数", verbose_name="调度值")
    
    is_active = models.BooleanField(default=True, verbose_name="启用")
    last_run_at = models.DateTimeField(null=True, blank=True, verbose_name="上次运行时间")
    next_run_at = models.DateTimeField(null=True, blank=True, verbose_name="下次运行时间")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "定时任务"
        verbose_name_plural = "定时任务"
        ordering = ['created_at']
        
    def __str__(self):
        return f"{self.get_name_display()} ({self.get_schedule_type_display()})"
