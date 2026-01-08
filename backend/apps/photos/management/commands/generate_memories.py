from django.core.management.base import BaseCommand
from apps.photos.memory_service import MemoryService
import time

class Command(BaseCommand):
    help = '分析照片数据并自动生成回忆合集'

    def add_arguments(self, parser):
        parser.add_argument('--task-id', type=str, help='系统维护任务 ID')
        parser.add_argument(
            '--clear',
            action='store_true',
            help='生成前清除所有现有的非收藏回忆',
        )

    def handle(self, *args, **options):
        start_time = time.time()
        self.stdout.write(self.style.SUCCESS('正在启动回忆生成系统...'))
        
        task_id = options.get('task_id')
        from apps.photos.models import MaintenanceTask
        task = None
        if task_id:
            try:
                task = MaintenanceTask.objects.get(id=task_id)
            except MaintenanceTask.DoesNotExist:
                pass

        from apps.photos.models import Photo, Person, Memory
        
        # 基础数据检查
        photo_count = Photo.objects.count()
        person_count = Person.objects.exclude(name="未命名").count()
        location_count = Photo.objects.exclude(location_name="").values('location_name').distinct().count()

        self.stdout.write(f"当前库中共有 {photo_count} 张照片")
        self.stdout.write(f"已识别并命名的角色: {person_count} 位")
        self.stdout.write(f"包含地理位置信息的地点: {location_count} 个")

        if options['clear']:
            deleted_count = Memory.objects.filter(is_favorite=False).delete()[0]
            self.stdout.write(self.style.WARNING(f'已清除 {deleted_count} 个非收藏回忆'))

        # 执行生成逻辑
        if task: MaintenanceTask.objects.filter(id=task.id).update(progress=10)
        results = MemoryService.generate_all()
        if task: MaintenanceTask.objects.filter(id=task.id).update(progress=90)
        
        # 输出统计结果
        self.stdout.write("\n" + "="*30)
        self.stdout.write(self.style.SUCCESS('回忆生成完成！统计信息如下：'))
        for key, count in results.items():
            self.stdout.write(f"- {key}: {count} 个")
        
        # 提供建议
        self.stdout.write("\n" + "温馨提示：")
        if results.get("那年今日", 0) == 0:
            self.stdout.write("- “那年今日”需要照片包含历史年份中今天的拍摄记录。")
        if results.get("旅行足迹", 0) == 0:
            self.stdout.write("- “旅行足迹”需要照片包含 GPS 信息且已被解析为地点名称（同一个城市超过 5 张）。")
        if results.get("人物重聚", 0) == 0:
            self.stdout.write("- “人物重聚”需要您在“人物”页面为角色命名，且照片中同时出现 2 位及以上已命名角色。")
        if results.get("人物特辑", 0) == 0:
            self.stdout.write("- “人物特辑”会自动为照片较多（>10张）的已命名角色生成。")
        
        duration = time.time() - start_time
        self.stdout.write("="*30)
        self.stdout.write(self.style.SUCCESS(f'总耗时: {duration:.2f} 秒'))
        self.stdout.write(self.style.SUCCESS('您现在可以前往“回忆”页面查看最新生成的精彩内容。'))
