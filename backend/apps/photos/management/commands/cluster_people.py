from django.core.management.base import BaseCommand
from apps.photos.services.people import PersonService
from apps.photos.models import Person

class Command(BaseCommand):
    help = '对人物进行自动聚类和合并'

    def add_arguments(self, parser):
        parser.add_argument('--task-id', type=str, help='系统维护任务 ID')
        parser.add_argument('--threshold', type=float, default=0.2, help='相似度阈值 (0-1)，越小越严格')
        parser.add_argument('--dry-run', action='store_true', help='仅显示合并建议，不执行合并')
        # 保留旧参数以兼容现有调用，但逻辑上默认都会合并
        parser.add_argument('--auto-merge', action='store_true', help='(已废弃，默认自动合并) 是否自动合并极高相似度的人物')
        parser.add_argument('--merge-all', action='store_true', help='(已废弃，默认自动合并) 强制合并所有发现的建议')

    def handle(self, *args, **options):
        threshold = options['threshold']
        dry_run = options['dry_run']
        task_id = options.get('task_id')
        
        from apps.photos.models import MaintenanceTask
        task = None
        if task_id:
            try:
                task = MaintenanceTask.objects.get(id=task_id)
            except MaintenanceTask.DoesNotExist:
                pass

        self.stdout.write(self.style.SUCCESS(f'正在开始聚类分析，阈值: {threshold}'))
        
        # 0. 预检：检查是否有大量缺失特征向量的人脸
        from apps.photos.models import Face
        missing_vecs = Face.objects.filter(embedding__isnull=True).count()
        if missing_vecs > 0:
            self.stdout.write(self.style.WARNING(f'警告: 发现 {missing_vecs} 张人脸缺少特征向量。'))
            self.stdout.write(self.style.NOTICE('请先运行 python manage.py extract_face_embeddings 来补全特征，否则聚类效果会大打折扣。'))

        # 1. 对未标记人脸进行归类 (DBSCAN 自动发现新人物)
        self.stdout.write('正在处理未标记人脸...')
        if task: MaintenanceTask.objects.filter(id=task.id).update(progress=10)
        labeled_count = PersonService.auto_cluster_unlabeled_faces(threshold=threshold)
        self.stdout.write(self.style.SUCCESS(f'成功自动归类了 {labeled_count} 张脸。'))

        # 1.5 同步所有人物的照片关联
        self.stdout.write('正在同步人物照片关联...')
        if task: MaintenanceTask.objects.filter(id=task.id).update(progress=40)
        all_people = Person.objects.all()
        for person in all_people:
            person.sync_photos()
        self.stdout.write(self.style.SUCCESS(f'已同步 {all_people.count()} 个人物的照片关联。'))

        # 2. 寻找并自动合并相似人物 (包含自动生成的“人物_N”)
        self.stdout.write('正在分析相似人物并进行聚合...')
        if task: MaintenanceTask.objects.filter(id=task.id).update(progress=70)
        suggestions = PersonService.get_merge_suggestions(threshold=threshold)
        
        if not suggestions:
            self.stdout.write('未发现可进一步聚合的人物。')
            return

        self.stdout.write(f'发现 {len(suggestions)} 组相似人物：')
        merge_count = 0
        merged_ids = set()  # 记录在本轮中已被合并（删除）的人物ID

        for sug in suggestions:
            p1 = sug['person1']
            p2 = sug['person2']
            conf = sug['confidence']
            
            # 检查人物是否在本轮中已被处理过
            if p1.id in merged_ids or p2.id in merged_ids:
                continue
            
            # 再次确认数据库中对象仍然存在（双重保险）
            if not Person.objects.filter(id=p1.id).exists() or not Person.objects.filter(id=p2.id).exists():
                continue

            # 对于自动生成的名字，我们采取更激进的合并策略
            is_unnamed = p1.name.startswith('人物_') or p2.name.startswith('人物_')
            
            self.stdout.write(f'  - {p1.name} 与 {p2.name} (相似度: {conf}%)')
            
            # 自动合并逻辑：
            # 默认合并所有发现的建议，除非指定了 --dry-run
            if dry_run:
                self.stdout.write(f'    [预览合并] {p1.name} -> {p2.name} (未执行)')
                continue

            self.stdout.write(self.style.WARNING(f'    [执行合并] {p1.name} -> {p2.name}'))
            try:
                # 将 p1 合并到 p2 (保持 p2)
                p1.merge_with(p2)
                merged_ids.add(p1.id) # p1 被删除了
                merge_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    合并失败: {e}'))
        
        if merge_count > 0:
            # 清理缓存
            from django.core.cache import cache
            cache.delete('merge_suggestions_all')
            self.stdout.write(self.style.SUCCESS(f'聚类聚合分析完成，共合并了 {merge_count} 组人物。'))
        else:
            self.stdout.write(self.style.SUCCESS('聚类聚合分析完成，没有执行任何合并。'))
