from django.core.management.base import BaseCommand
from apps.photos.models import Photo, Face
from apps.photos.services import detect_faces_in_photo, get_face_detector
from apps.photos.services.people import PersonService
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time
import os

class Command(BaseCommand):
    help = '一键完成人脸识别与聚类 (包括扫描、特征提取、自动归类和合并)'

    def add_arguments(self, parser):
        # 扫描相关参数
        parser.add_argument(
            '--workers',
            type=int,
            default=multiprocessing.cpu_count(),
            help='并发线程数 (默认: CPU 核心数)'
        )
        parser.add_argument(
            '--re-scan',
            action='store_true',
            help='清空已有数据并重新扫描所有人脸'
        )
        # 聚类相关参数
        parser.add_argument(
            '--threshold',
            type=float,
            default=0.15,
            help='聚类阈值 (默认: 0.15)'
        )
        parser.add_argument(
            '--min-samples',
            type=int,
            default=3,
            help='形成一个人物所需的最小面孔数 (默认: 3)。设为 1 可将所有面孔归类。'
        )
        parser.add_argument(
            '--skip-cluster',
            action='store_true',
            help='只扫描人脸，不进行自动聚类'
        )
        parser.add_argument(
            '--task-id',
            type=str,
            help='系统维护任务 ID (用于更新进度)'
        )

    def handle(self, *args, **options):
        # AI 推理任务，Docker 环境下限制默认并发数，防止数据库连接爆炸
        is_docker = os.path.exists('/.dockerenv')
        default_workers = 1 if is_docker else multiprocessing.cpu_count()
        
        workers = options.get('workers', default_workers)
        if is_docker and workers > 2:
            self.stdout.write(self.style.WARNING(f"检测到 Docker 环境，强制将 workers 从 {workers} 降低到 2 以保证数据库连接稳定。"))
            workers = 2
            
        re_scan = options['re_scan']
        threshold = options['threshold']
        min_samples = options['min_samples']
        skip_cluster = options['skip_cluster']
        task_id = options.get('task_id')
        
        from apps.photos.models import MaintenanceTask
        task = None
        if task_id:
            try:
                task = MaintenanceTask.objects.get(id=task_id)
            except MaintenanceTask.DoesNotExist:
                pass

        # --- 第一步：扫描人脸 ---
        self.stdout.write(self.style.MIGRATE_HEADING("=== 第一步：正在扫描并识别照片中的人脸 ==="))
        
        if re_scan:
            self.stdout.write(self.style.WARNING("正在按要求清空旧的人脸数据..."))
            Face.objects.all().delete()
            Photo.objects.update(face_scanned=False)
            self.stdout.write(self.style.SUCCESS("数据已清空。"))

        # 同步状态
        Photo.objects.filter(faces__isnull=False, face_scanned=False).update(face_scanned=True)
        
        # 统计
        total_photos = Photo.objects.count()
        scanned_count = Photo.objects.filter(face_scanned=True).count()
        photo_ids = list(Photo.objects.filter(face_scanned=False).values_list('id', flat=True))
        total = len(photo_ids)

        if total > 0:
            self.stdout.write(f"总照片数: {total_photos}, 已处理: {scanned_count}, 待处理: {total}")
            self.stdout.write(f"正在增量识别 {total} 张新照片，使用 {workers} 个线程进行处理...")
            # 显示硬件加速状态 (现在已被静音，如果需要确认状态，可以在日志中查看)
            # get_face_detector(silent=False) 
            self.stdout.write("正在初始化人脸检测模型...")
            get_face_detector(silent=False)
            self.stdout.write("模型初始化完成，开始处理...")

            count = 0
            face_count = 0
            with tqdm(total=total, desc="人脸扫描中", unit="photo") as pbar:
                with ThreadPoolExecutor(max_workers=workers) as executor:
                    batch_size = workers * 2
                    for i in range(0, total, batch_size):
                        batch_ids = photo_ids[i:i + batch_size]
                        future_to_photo = {executor.submit(detect_faces_in_photo, pid): pid for pid in batch_ids}
                        for future in as_completed(future_to_photo):
                            try:
                                num = future.result()
                                face_count += num
                                count += 1
                                pbar.update(1)
                                if count % 50 == 0:
                                    pbar.set_postfix({"已发现人脸": face_count})
                                
                                # 更新任务进度 (0-80% 给人脸扫描)
                                if task and count % 10 == 0:
                                    progress = int((count / total) * 80)
                                    MaintenanceTask.objects.filter(id=task.id).update(progress=progress)
                                    
                            except Exception as e:
                                self.stdout.write(self.style.ERROR(f"处理照片失败: {e}"))
                        time.sleep(0.1)
            self.stdout.write(self.style.SUCCESS(f"人脸扫描完成：共处理 {count} 张照片，发现 {face_count} 张人脸。"))
        else:
            self.stdout.write(f"总照片数: {total_photos}, 已处理: {scanned_count}, 待处理: {total}")
            self.stdout.write(self.style.SUCCESS("所有照片均已处理，无需增量识别。"))

        # --- 第二步：自动聚类 ---
        if skip_cluster:
            self.stdout.write(self.style.NOTICE("已跳过自动聚类。"))
            return

        self.stdout.write("\n" + self.style.MIGRATE_HEADING("=== 第二步：正在进行人脸聚类与人物合并 ==="))
        
        # 1. 自动聚类
        self.stdout.write("正在识别并聚合新人物...")
        if task:
            MaintenanceTask.objects.filter(id=task.id).update(progress=85)
            
        labeled_count = PersonService.auto_cluster_unlabeled_faces(threshold=threshold, min_samples=min_samples)
        self.stdout.write(self.style.SUCCESS(f"成功自动归类了 {labeled_count} 张人脸。"))

        # 2. 自动合并建议
        self.stdout.write("正在分析相似人物并进行自动合并...")
        if task:
            MaintenanceTask.objects.filter(id=task.id).update(progress=90)
            
        suggestions = PersonService.get_merge_suggestions(threshold=threshold)
        
        if not suggestions:
            self.stdout.write(self.style.SUCCESS("未发现可进一步合并的人物。"))
        else:
            merge_count = 0
            for sug in suggestions:
                p1, p2 = sug['person1'], sug['person2']
                conf = sug['confidence']
                
                # 自动合并策略：相似度 > 95% 或者 包含自动生成名称且相似度 > 85%
                is_unnamed = p1.name.startswith('人物_') or p2.name.startswith('人物_')
                if conf > 95 or (is_unnamed and conf > 85):
                    try:
                        p1.merge_with(p2)
                        merge_count += 1
                        self.stdout.write(f"  [自动合并] {p1.name} -> {p2.name} (相似度: {conf}%)")
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  合并失败 {p1.name}: {e}"))
            
            self.stdout.write(self.style.SUCCESS(f"自动合并完成：共合并了 {merge_count} 组人物。"))

        self.stdout.write("\n" + self.style.SUCCESS("✨ 所有人脸处理任务已全部完成！"))
