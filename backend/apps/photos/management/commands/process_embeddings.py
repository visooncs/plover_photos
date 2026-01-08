from django.core.management.base import BaseCommand
from apps.photos.models import Photo
from sentence_transformers import SentenceTransformer
from PIL import Image
import os
import torch
from apps.photos.services import check_gpu_availability
from apps.photos.services.video import extract_video_frame

class Command(BaseCommand):
    help = 'Generate embeddings for photos using CLIP (GPU Accelerated)'

    def add_arguments(self, parser):
        parser.add_argument('--task-id', type=str, help='系统维护任务 ID')
        parser.add_argument('--batch-size', type=int, default=32, help='Batch size for processing')

    def handle(self, *args, **options):
        task_id = options.get('task_id')
        from apps.photos.models import MaintenanceTask
        task = None
        if task_id:
            try:
                task = MaintenanceTask.objects.get(id=task_id)
            except MaintenanceTask.DoesNotExist:
                pass

        # 针对国内网络环境，提前强制设置环境变量
        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
        # 强制 transformers 不去检查远程版本，优先使用本地缓存
        os.environ["TRANSFORMERS_OFFLINE"] = "0" 
        
        # 查找还未生成语义向量的照片
        photos = Photo.objects.filter(embedding_data__isnull=True).order_by('created_at')
        
        # 现在视频也支持生成向量，不再过滤
        valid_photo_list = list(photos)
        count = len(valid_photo_list)

        if count == 0:
            self.stdout.write(self.style.SUCCESS("No photos to process."))
            return

        # 检测设备
        gpu_info = check_gpu_availability()
        device = "cpu"
        
        if gpu_info["available"]:
            self.stdout.write(self.style.SUCCESS(f"Detected GPU: {gpu_info['type']} - {gpu_info['details']}"))
            if "CUDA" in gpu_info["type"]:
                device = "cuda"
            else:
                self.stdout.write(self.style.WARNING("Torch CUDA not available. Falling back to CPU for embedding generation."))
        else:
            self.stdout.write("No GPU detected, using CPU.")

        # 设置 HuggingFace 镜像 (针对国内网络优化)
        self.stdout.write("Note: Using HF-Mirror for model downloads.")

        # 尝试忽略 transformers 的 use_fast 警告
        import warnings
        warnings.filterwarnings("ignore", message=".*use_fast.*")

        self.stdout.write(f"Loading CLIP model... (Total: {count} photos)")
        
        model_name = 'clip-ViT-B-32'
        try:
            # 1. 首先尝试完全离线加载 (如果已经下载过)
            try:
                model = SentenceTransformer(model_name, device=device, local_files_only=True)
                self.stdout.write(self.style.SUCCESS("Successfully loaded model from local cache (Offline Mode)."))
            except Exception:
                # 2. 如果离线加载失败，再尝试联网下载 (使用镜像)
                self.stdout.write("Model not found in cache. Attempting to download from mirror...")
                model = SentenceTransformer(model_name, device=device)
                self.stdout.write(self.style.SUCCESS("Model downloaded and loaded successfully."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to load model: {e}"))
            self.stdout.write(self.style.NOTICE("Tip: Check your internet connection or try running again to resume download."))
            return
        
        processed_count = 0
        batch_size = options.get('batch_size', 32) # 批处理以进一步提高效率
        
        # 将照片分批处理以提高 GPU 利用率
        total_batches = (count + batch_size - 1) // batch_size
        for i in range(0, count, batch_size):
            # 每一批次处理前，先清理可能失效的连接
            from django.db import connections
            for conn in connections.all():
                conn.close()
            
            batch_photos = valid_photo_list[i:i+batch_size]
            images = []
            valid_batch_photos = []
            
            # 更新任务进度
            if task:
                progress = int((i / count) * 100)
                MaintenanceTask.objects.filter(id=task.id).update(progress=progress)

            for photo in batch_photos:
                if not os.path.exists(photo.file_path):
                    continue
                
                try:
                    img_obj = None
                    img = None
                    
                    if photo.is_pure_video:
                         img = extract_video_frame(photo.file_path)
                         if img:
                             images.append(img.convert('RGB'))
                             valid_batch_photos.append(photo)
                    else:
                        try:
                            img = Image.open(photo.file_path)
                            # 确保图片模式正确
                            images.append(img.convert('RGB'))
                            valid_batch_photos.append(photo)
                        except Exception:
                            # 尝试作为视频处理
                             if photo.is_video:
                                 img = extract_video_frame(photo.file_path)
                                 if img:
                                     images.append(img.convert('RGB'))
                                     valid_batch_photos.append(photo)
                    
                    # 注意：Image.open 返回的对象在 append 后由列表持有引用
                    # 对于 extract_video_frame 返回的也是 Image 对象
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error opening {photo.file_path}: {e}"))

            if not images:
                continue

            try:
                # 批量生成向量
                embeddings = model.encode(images, convert_to_numpy=True, show_progress_bar=False, batch_size=batch_size)
                
                # 保存
                for photo, embedding in zip(valid_batch_photos, embeddings):
                    photo.set_embedding(embedding)
                    photo.save()
                
                processed_count += len(images)
                if processed_count % (batch_size * 5) == 0 or processed_count == count:
                    self.stdout.write(f"Progress: {processed_count}/{count} photos processed.")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing batch: {e}"))
                
        self.stdout.write(self.style.SUCCESS(f"Done! Processed {processed_count} photos."))
