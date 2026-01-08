import threading
import time
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class SchedulerThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.name = "PhotosScheduler"
        self.daemon = True

    def run(self):
        logger.info("Scheduler thread started")
        while True:
            try:
                self.check_schedule()
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
            time.sleep(60)

    def check_schedule(self):
        from .models import ScheduledTask, MaintenanceTask
        now = timezone.now()
        tasks = ScheduledTask.objects.filter(is_active=True)
        
        for task in tasks:
            should_run = False
            
            # 1. 简单间隔 (分钟)
            if task.schedule_type == 'interval':
                try:
                    val = task.schedule_value
                    # 兼容 "15:00" 这种格式，取冒号前的部分作为分钟数
                    if ':' in str(val):
                        minutes = int(str(val).split(':')[0])
                    else:
                        minutes = int(val)
                        
                    if not task.last_run_at or (now - task.last_run_at).total_seconds() / 60 >= minutes:
                        should_run = True
                except ValueError:
                    logger.error(f"Invalid interval value for task {task.id}: {task.schedule_value}")

            # 2. 每天 (HH:MM)
            elif task.schedule_type == 'daily':
                try:
                    hour, minute = map(int, task.schedule_value.split(':'))
                    # 如果今天还没运行过，且当前时间超过了设定时间
                    if not task.last_run_at or task.last_run_at.date() < now.date():
                        if now.hour > hour or (now.hour == hour and now.minute >= minute):
                            should_run = True
                except ValueError:
                    pass

            # 3. 每周 (d HH:MM) 0=周一
            elif task.schedule_type == 'weekly':
                try:
                    parts = task.schedule_value.split()
                    day_of_week = int(parts[0])
                    hour, minute = map(int, parts[1].split(':'))
                    
                    # 当前是指定的星期几
                    if now.weekday() == day_of_week:
                        # 检查今天是否运行过
                        if not task.last_run_at or task.last_run_at.date() < now.date():
                            if now.hour > hour or (now.hour == hour and now.minute >= minute):
                                should_run = True
                except ValueError:
                    pass

            if should_run:
                logger.info(f"Triggering scheduled task: {task.name}")
                # 创建并立即执行任务
                mt = MaintenanceTask.objects.create(
                    name=task.name,
                    params=task.params,
                    created_by="scheduler",
                    status='pending'
                )
                
                # 触发执行 (通过 API 的逻辑是调用 viewset，这里直接用线程启动或者等待轮询)
                # 为了简单，我们创建一个 MaintenanceTask 后，还需要触发它。
                # 可以在这里直接启动线程执行，或者 MaintenanceTask 模型 save 时触发? 不好。
                # 我们可以复用 api.py 中的 _run_task_thread 逻辑，或者调用 management command。
                
                self.execute_task(mt)
                
                task.last_run_at = now
                task.save()

    def execute_task(self, task):
        from django.core.management import call_command
        from io import StringIO
        
        class TaskLogger:
            def __init__(self, task_id):
                self.task_id = task_id
                self.buffer = []
                self.full_log = ""
                self.last_flush = time.time()
                
            def write(self, message):
                self.buffer.append(message)
                self.full_log += message
                if time.time() - self.last_flush > 0.5: # 0.5s flush interval
                    self.flush()
            
            def flush(self):
                if not self.buffer:
                    return
                
                from .models import MaintenanceTask
                try:
                    # Refresh task from DB to avoid overwriting other fields
                    t = MaintenanceTask.objects.get(id=self.task_id)
                    t.logs = self.full_log
                    t.save(update_fields=['logs'])
                    self.buffer = []
                    self.last_flush = time.time()
                except Exception as e:
                    logger.error(f"Error flushing logs: {e}")

            def getvalue(self):
                return self.full_log

        def run():
            task.status = 'running'
            task.started_at = timezone.now()
            task.save()
            
            # 使用自定义 Logger 实时更新 DB
            logger_out = TaskLogger(task.id)
            
            # stderr 也重定向到同一个 logger，或者分开？
            # 通常合并在一起看比较方便。
            # 如果分开，需要两个 logger 实例，并且要处理并发写入 full_log (或 DB)。
            # 为了简单，我们让 stderr 也写入同一个 logger_out。
            
            try:
                params = task.params or {}
                kwargs = {}
                for k, v in params.items():
                    if isinstance(v, bool):
                        if v: kwargs[k] = True
                    else:
                        kwargs[k] = v
                
                kwargs['task_id'] = str(task.id)
                
                # call_command 可能会同时写入 stdout 和 stderr
                # TaskLogger 不是线程安全的，但在单线程执行 call_command 时没问题。
                # 如果 call_command 内部有多线程写入 stdout，则需要锁。
                # 大部分管理命令是单线程打印日志。
                
                call_command(task.name, stdout=logger_out, stderr=logger_out, **kwargs)
                
                # 最后一次 flush
                logger_out.flush()
                
                task.status = 'completed'
                task.progress = 100
            except Exception as e:
                task.status = 'failed'
                task.error_message = str(e)
                import traceback
                # 记录 traceback
                tb = traceback.format_exc()
                logger_out.write("\n" + tb)
                logger_out.flush()
            finally:
                task.finished_at = timezone.now()
                # 确保日志完整保存
                task.logs = logger_out.getvalue()
                task.save()

        t = threading.Thread(target=run)
        t.start()
