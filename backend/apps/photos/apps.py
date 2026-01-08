from django.apps import AppConfig
import sys

class PhotosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.photos'

    def ready(self):
        # 注册 HEIF 支持
        try:
            from pillow_heif import register_heif_opener
            register_heif_opener()
        except ImportError:
            pass

        # 使用信号在数据库就绪后执行清理逻辑，避免 ready() 中的 RuntimeWarning
        from django.db.models.signals import post_migrate
        post_migrate.connect(reset_scanning_status, sender=self)
        
        # 启动定时任务调度器 (仅在 RunServer 的主进程或 WSGI 中启动)
        import os
        if os.environ.get('RUN_MAIN') == 'true':
            from .scheduler import SchedulerThread
            import threading
            # 防止重复启动
            if not any(t.name == "PhotosScheduler" for t in threading.enumerate()):
                SchedulerThread().start()

def reset_scanning_status(sender, **kwargs):
    """重启或迁移后重置扫描状态"""
    try:
        from .models import Library, MaintenanceTask
        Library.objects.filter(scan_status='SCANNING').update(scan_status='READY')
        
        # 重置因服务重启而中断的任务
        MaintenanceTask.objects.filter(status='running').update(
            status='failed',
            error_message='服务异常重启，任务中断'
        )
    except Exception:
        pass
