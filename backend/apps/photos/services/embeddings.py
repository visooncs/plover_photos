import os
import threading
import time
from PIL import Image
from django.db import close_old_connections, connections
from django.db.utils import InterfaceError, OperationalError
from apps.photos.models import Photo
from .hardware import check_gpu_availability
from .video import extract_video_frame
from pgvector.django import CosineDistance

_clip_model = None
_clip_lock = threading.Lock()

def get_clip_model(silent=True):
    """获取 CLIP 模型单例"""
    global _clip_model
    if _clip_model is None:
        with _clip_lock:
            if _clip_model is None:
                try:
                    from sentence_transformers import SentenceTransformer
                    
                    # 针对国内环境优化
                    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
                    
                    # 获取设备
                    gpu_info = check_gpu_availability(silent=True)
                    device = "cuda" if gpu_info["available"] else "cpu"
                    
                    # 模型名称和可能的本地路径
                    model_name = 'clip-ViT-B-32'
                    # 优先从环境变量获取路径，否则使用相对于当前工作目录的路径
                    local_base = os.environ.get('SENTENCE_TRANSFORMERS_HOME', os.path.join(os.getcwd(), "models", "huggingface"))
                    
                    possible_paths = [
                        os.path.join(local_base, f"sentence-transformers_{model_name}"),
                        os.path.join(local_base, model_name),
                    ]
                    
                    _clip_model = None
                    for local_path in possible_paths:
                        if os.path.exists(os.path.join(local_path, "config.json")):
                            if not silent: print(f"Loading CLIP model from local path: {local_path}")
                            try:
                                _clip_model = SentenceTransformer(local_path, device=device)
                                break
                            except Exception as e:
                                if not silent: print(f"Failed to load from {local_path}: {e}")
                    
                    if _clip_model is None:
                        # 最后尝试通过名称加载（如果设置了镜像站，这一步在 Docker 内会很快）
                        if not silent: print(f"No valid local path found, trying by name: {model_name}")
                        _clip_model = SentenceTransformer(model_name, device=device)
                    
                    if not silent:
                        print(f"CLIP 模型已加载 (Device: {device})")
                except Exception as e:
                    if not silent:
                        print(f"无法加载 CLIP 模型: {e}")
                    return None
    return _clip_model

def search_photos_by_text(query, limit=100):
    """根据文本进行语义搜索"""
    # 获取 CLIP 模型
    model = get_clip_model(silent=True)
    if not model:
        return []
    
    try:
        # 编码文本
        text_emb = model.encode(query)
        
        # 使用 pgvector 进行高效搜索
        photos = Photo.objects.annotate(
            distance=CosineDistance('embedding_data', text_emb)
        ).filter(distance__lt=0.8).order_by('distance')[:limit]
        
        return list(photos)
    except Exception as e:
        print(f"语义搜索失败: {e}")
        return []

def db_execute_with_retry(func, max_retries=3):
    """带强力重连机制的数据库操作"""
    from django.db import transaction
    
    for i in range(max_retries):
        try:
            # 如果不在事务中，才尝试清理失效连接
            if not transaction.get_connection().in_atomic_block:
                close_old_connections()
            return func()
        except (InterfaceError, OperationalError) as e:
            # 如果在事务中，无法通过重连修复，只能抛出错误
            if transaction.get_connection().in_atomic_block:
                raise e
                
            error_str = str(e).lower()
            if "closed" in error_str or "client" in error_str or "terminat" in error_str:
                try:
                    connections['default'].close()
                    connections['default'].connection = None
                except:
                    pass
                
                if i < max_retries - 1:
                    time.sleep(0.5 * (i + 1))
                    continue
            raise e
    return func()

def generate_photo_embedding(photo_id):
    """生成照片的 CLIP 语义向量"""
    try:
        # 获取基础信息后立即释放连接
        photo = db_execute_with_retry(lambda: Photo.objects.get(id=photo_id))
        file_path = photo.file_path
        is_pure_video = photo.is_pure_video
        is_video = photo.is_video
        
        if not os.path.exists(file_path):
            return False
            
        model = get_clip_model(silent=True)
        if not model:
            return False
        
        if is_pure_video:
            image = extract_video_frame(file_path)
            if not image:
                return False
        else:
            try:
                img = Image.open(file_path)
                image = img.convert('RGB')
            except Exception:
                if is_video:
                     image = extract_video_frame(file_path)
                     if not image: return False
                else:
                     return False

        def process_embedding():
            # 如果不在事务中，才彻底关闭连接，AI 推理期间不持有任何 DB 资源
            try:
                from django.db import transaction, connections
                if not transaction.get_connection().in_atomic_block:
                    for conn in connections.all():
                        conn.close()
                        conn.connection = None # 强力清除
            except:
                pass
                
            # CLIP 推理
            try:
                # 确保传入的是列表，以避免某些版本的 sentence-transformers 报错
                embeddings = model.encode([image], convert_to_numpy=True)
                embedding = embeddings[0]
            except Exception as e:
                import sys, traceback
                sys.stdout.write(f"\n[Error] CLIP 推理崩溃: {str(e)}\n")
                traceback.print_exc(file=sys.stdout)
                sys.stdout.flush()
                raise e
                
            # 推理结束后，使用 db_execute_with_retry 保存数据
            def save_embedding():
                p = Photo.objects.get(id=photo_id)
                p.embedding_data = embedding.tolist()
                p.save(update_fields=['embedding_data'])
                
            db_execute_with_retry(save_embedding)

        process_embedding()
        
        # Close image if it was opened via PIL
        if hasattr(image, 'close'):
             image.close()
             
        return True
    except Exception as e:
        print(f"Embedding generation failed for {photo_id}: {e}")
        return False
    finally:
        # 在每个任务结束时主动关闭连接
        try:
            from django.db import connections
            connections.close_all()
        except:
            pass
