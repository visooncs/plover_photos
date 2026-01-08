from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.management import call_command
from django.utils import timezone
from django import db
import threading
import time
from io import StringIO
import traceback

from ..models import ScheduledTask, MaintenanceTask
from ..serializers import ScheduledTaskSerializer, MaintenanceTaskSerializer

class ScheduledTaskViewSet(viewsets.ModelViewSet):
    queryset = ScheduledTask.objects.all().order_by('created_at')
    serializer_class = ScheduledTaskSerializer

class MaintenanceTaskViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceTask.objects.all().order_by('-created_at')
    serializer_class = MaintenanceTaskSerializer
    pagination_class = None

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action == 'list':
            return qs[:10]
        return qs
    
    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        task = self.get_object()
        if task.status == 'running':
            return Response({'error': 'Task is already running'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Reset task status
        task.status = 'pending'
        task.progress = 0
        task.logs = ""
        task.error_message = None
        task.started_at = None
        task.finished_at = None
        task.save()
        
        # Run in thread
        thread = threading.Thread(target=self._run_task_thread, args=(task,))
        thread.start()
        
        return Response({'status': 'started'})

    def _run_task_thread(self, task):
        # 确保线程开始时关闭旧的、可能失效的连接
        db.close_old_connections()
        
        task.status = 'running'
        task.started_at = timezone.now()
        task.save()
        
        # Capture stdout
        out = StringIO()
        err = StringIO()
        
        # 启动日志同步线程 (单实例，更稳健)
        def sync_logs_worker():
            # 内部导入以避免循环依赖
            from ..models import MaintenanceTask
            while True:
                try:
                    # 检查任务是否还在运行
                    t = MaintenanceTask.objects.filter(id=task.id).first()
                    if not t or t.status != 'running':
                        break
                        
                    # 获取当前输出并更新
                    current_logs = out.getvalue() + "\n" + err.getvalue()
                    if current_logs.strip() and current_logs != t.logs:
                        # 使用 update 减少冲突
                        MaintenanceTask.objects.filter(id=task.id).update(logs=current_logs)
                    
                    time.sleep(2) # 每 2 秒同步一次
                except Exception:
                    # 如果连接丢失，尝试关闭并等待下一次
                    try:
                        db.close_old_connections()
                    except:
                        pass
                    time.sleep(5)
        
        log_sync_thread = threading.Thread(target=sync_logs_worker, daemon=True)
        log_sync_thread.start()
        
        try:
            # Prepare arguments
            params = task.params or {}
            kwargs = {}
            
            for k, v in params.items():
                if isinstance(v, bool):
                    if v: kwargs[k] = True
                else:
                    kwargs[k] = v
            
            kwargs['task_id'] = str(task.id)
            
            # 执行命令
            call_command(task.name, stdout=out, stderr=err, **kwargs)
            
            task.status = 'completed'
            task.progress = 100
        except Exception as e:
            task.status = 'failed'
            task.error_message = str(e)
            err.write(traceback.format_exc())
        finally:
            task.finished_at = timezone.now()
            # 最终合并所有日志
            task.logs = out.getvalue() + "\n" + err.getvalue()
            task.save()
            db.close_old_connections()
