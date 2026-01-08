import os
import sys
import threading
import time
import random
import numpy as np
import contextlib
import io
from PIL import Image, ImageOps
from django.db import close_old_connections, connections
from django.db.utils import InterfaceError, OperationalError

from apps.photos.models import Photo, Face
from .hardware import check_gpu_availability
from .video import extract_video_frame, extract_video_frames_generator

# 全局单例，避免多线程重复加载模型导致显存爆炸
_global_detector = None
# 初始化锁，防止多线程并发初始化导致日志混乱或资源竞争
_init_lock = threading.Lock()

class SuppressOutput:
    """
    上下文管理器：已禁用，用于排查崩溃问题
    """
    def __init__(self, suppress_stdout=True, suppress_stderr=True):
        pass
    def __enter__(self):
        return
    def __exit__(self, exc_type, exc_value, traceback):
        pass

class FaceDetectorWrapper:
    """
    人脸检测与特征提取包装类 (仅使用强力的 InsightFace 模型)
    """
    def __init__(self, silent=False):
        # 已经在 get_face_detector 中通过锁保证了单例初始化的安全性
        self._init_impl(silent)

    def _init_impl(self, silent=False):
        self.insightface_app = None
        
        # 国内加速
        if not os.environ.get("HF_ENDPOINT"):
            os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
            
        # 确保模型存放路径
        insightface_home = os.environ.get("INSIGHTFACE_HOME")
        if not insightface_home:
            insightface_home = os.path.join(os.getcwd(), "models", "insightface")
            os.environ["INSIGHTFACE_HOME"] = insightface_home

        # 初始化 InsightFace (RetinaFace + ArcFace)
        try:
            import insightface
            from insightface.app import FaceAnalysis
            import onnxruntime as ort
            
            # 减少 ONNX Runtime 的日志输出 (仅显示 Error)
            try:
                ort.set_default_logger_severity(3)
            except Exception:
                pass
            
            # 检查模型是否已下载 (优先检查 INSIGHTFACE_HOME)
            model_path = os.path.join(insightface_home, 'models', 'buffalo_l')
            if not os.path.exists(model_path):
                # 如果环境变量指定的路径不存在，再检查默认路径
                model_path = os.path.expanduser('~/.insightface/models/buffalo_l')
            
            # 使用 hardware.py 中的 check_gpu_availability 进行更完善的检测
            gpu_info = check_gpu_availability(silent=True)
            use_cuda = gpu_info.get("onnx_cuda", False)
            
            success = False
            
            # 1. 尝试 GPU 初始化
            if use_cuda:
                try:
                    if not silent:
                        sys.stdout.write(f"[Init] 准备初始化 GPU 模型: {gpu_info.get('details')}\n")
                        sys.stdout.flush()
                    
                    providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
                    
                    # 彻底放弃日志屏蔽，看看底层的输出到底是什么
                    if not silent:
                        sys.stdout.write("[Init] 正在调用 FaceAnalysis()...\n")
                        sys.stdout.flush()
                    
                    app = FaceAnalysis(name='buffalo_l', root=insightface_home, providers=providers)
                    
                    if not silent:
                        sys.stdout.write("[Init] FaceAnalysis 实例创建成功，正在调用 app.prepare()...\n")
                        sys.stdout.flush()
                        
                    # ctx_id=0 使用第一个 GPU
                    app.prepare(ctx_id=0, det_size=(640, 640))
                    
                    if not silent:
                        sys.stdout.write("[Init] app.prepare() 执行成功！\n")
                        sys.stdout.flush()
                    
                    self.insightface_app = app
                    self.device = "cuda"
                    success = True
                except Exception as e:
                    if not silent:
                        sys.stdout.write(f"[Init] GPU 初始化异常 (被捕获): {e}\n")
                        import traceback
                        traceback.print_exc()
                        sys.stdout.flush()
                    self.insightface_app = None

            # 2. 如果 GPU 失败或不可用，使用 CPU 初始化
            if not success:
                if not silent:
                    sys.stdout.write("[Init] 正在回退到 CPU 模式...\n")
                    sys.stdout.flush()
                
                providers = ['CPUExecutionProvider']
                app = FaceAnalysis(name='buffalo_l', root=insightface_home, providers=providers)
                app.prepare(ctx_id=-1, det_size=(640, 640))
                
                self.insightface_app = app
                self.device = "cpu"
                if not silent:
                    sys.stdout.write("[Init] CPU 模式加载完成\n")
                    sys.stdout.flush()

        except ImportError:
            if not silent: print("未安装 insightface 库")
            self.insightface_app = None
        except Exception as e:
            if not silent:
                print(f"InsightFace 初始化顶级异常: {e}")
                import traceback
                traceback.print_exc()
            self.insightface_app = None

    def process(self, image_rgb):
        """
        处理图片，返回检测到的人脸及其特征
        """
        if self.insightface_app is None:
            return []
            
        try:
            # InsightFace 的 get 方法会同时进行检测、对齐和特征提取
            faces = self.insightface_app.get(image_rgb)
        except Exception as e:
            # 打印详细错误到标准输出，以便我们在任务日志中看到
            import sys, traceback
            sys.stdout.write(f"\n[Error] InsightFace 推理崩溃: {str(e)}\n")
            traceback.print_exc(file=sys.stdout)
            sys.stdout.flush()
            raise e

        detections = []
        for face in faces:
            x1, y1, x2, y2 = face.bbox.astype(int)
            detections.append({
                'bbox': [int(x1), int(y1), int(x2-x1), int(y2-y1)],
                'score': float(face.det_score),
                'embedding': face.embedding, # 预存特征向量
                'gender': face.gender,       # 性别 (0: 女性, 1: 男性)
                'age': face.age              # 年龄
            })
        return detections

    def extract_embedding(self, face_image_rgb):
        """
        为单个裁剪后的人脸图片提取特征向量 (通常 process 已包含)
        """
        if self.insightface_app is None:
            return None
            
        faces = self.insightface_app.get(face_image_rgb)
        if faces:
            # 返回最大的那张脸的向量
            faces.sort(key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]), reverse=True)
            return faces[0].embedding
        return None

def get_face_detector(silent=True):
    """获取全局共享的人脸检测器实例"""
    global _global_detector
    
    if _global_detector is None:
        # 使用双重检查锁定 (Double-Checked Locking) 确保线程安全
        with _init_lock:
            if _global_detector is None:
                _global_detector = FaceDetectorWrapper(silent=silent)
                
    return _global_detector

def cluster_faces():
    """
    对未分配的人脸进行聚类 (调用 PersonService)
    """
    try:
        from .people import PersonService
        return PersonService.auto_cluster_unlabeled_faces()
    except Exception as e:
        print(f"Clustering failed: {e}")
        return 0

def scan_all_faces(limit=None):
    """
    扫描所有未扫描照片的人脸
    """
    photos = Photo.objects.filter(face_scanned=False)
    if limit:
        photos = photos[:limit]
        
    count = 0
    for photo in photos:
        detect_faces_in_photo(photo.id)
        count += 1
        
    # 扫描完后尝试聚类
    if count > 0:
        cluster_faces()
        
    return count

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

def detect_faces_in_photo(photo_id):
    """检测照片中的人脸并保存到 Face 模型"""
    
    def process_image_array(photo_id, img_array, detector_obj, timestamp=None):
        if img_array is None:
            return 0
            
        h, w, _ = img_array.shape
        
        # 如果不在事务中，才彻底关闭连接，AI 推理期间不持有任何 DB 资源
        try:
            from django.db import transaction, connections
            if not transaction.get_connection().in_atomic_block:
                for conn in connections.all():
                    conn.close()
                    conn.connection = None # 强力清除
        except:
            pass
            
        # AI 推理过程 (最耗时且可能干扰连接的操作)
        detections = detector_obj.process(img_array)
        
        # 推理结束后，不依赖传入的对象，而是重新开启连接保存数据
        detected_count = 0
        for det in detections:
            x1, y1, width, height = det['bbox']
            
            # 边界检查
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(w, x1 + width)
            y2 = min(h, y1 + height)
            
            # 使用带重试机制的函数保存数据
            def save_face():
                # 重新获取 photo 对象，确保连接是新鲜的
                current_photo = Photo.objects.get(id=photo_id)
                
                # 创建人脸记录
                face = Face(
                    photo=current_photo,
                    bbox=[x1, y1, x2, y2],
                    prob=det['score']
                )
                
                if timestamp is not None:
                    face.timestamp = timestamp
                
                if 'embedding' in det:
                    face.embedding = det['embedding'].tolist()
                
                face.save()
            
            db_execute_with_retry(save_face)
            detected_count += 1
        return detected_count

    try:
        # 获取基础信息后立即释放连接
        photo = db_execute_with_retry(lambda: Photo.objects.get(id=photo_id))
        detector = get_face_detector()
        total_count = 0
        
        file_path = photo.file_path
        is_pure_video = photo.is_pure_video
        is_video = photo.is_video
        
        if is_pure_video:
             # 视频处理：多帧提取
             for timestamp, img_obj in extract_video_frames_generator(file_path, interval=10.0, max_frames=50):
                 image_rgb = np.array(img_obj)
                 count = process_image_array(photo_id, image_rgb, detector, timestamp)
                 total_count += count
                 
        else:
            # 图片处理
            image_rgb = None
            if os.path.exists(file_path):
                try:
                    img_obj = Image.open(file_path)
                    img_obj = ImageOps.exif_transpose(img_obj)
                    img_rgb = img_obj.convert('RGB')
                    image_rgb = np.array(img_rgb)
                except Exception as e:
                     if is_video:
                          img_obj = extract_video_frame(file_path)
                          if img_obj:
                              image_rgb = np.array(img_obj)
                     else:
                          print(f"读取图片失败 {file_path}: {e}")
            
            if image_rgb is None and is_video:
                 img_obj = extract_video_frame(file_path)
                 if img_obj:
                     image_rgb = np.array(img_obj)
                     
            if image_rgb is not None:
                total_count = process_image_array(photo_id, image_rgb, detector, None)
        
        # 标记为已扫描
        db_execute_with_retry(lambda: Photo.objects.filter(id=photo_id).update(face_scanned=True))
        return total_count
    except Exception as e:
        # 打印更详细的错误
        import traceback
        print(f"人脸检测异常 {photo_id}: {str(e)}")
        traceback.print_exc()
        return 0

def extract_face_embedding(face, face_image_rgb):
    """提取人脸特征向量 (优先使用 GPU)"""
    try:
        if face_image_rgb.size == 0:
            return
            
        detector = get_face_detector()
        embedding = detector.extract_embedding(face_image_rgb)
        
        if embedding is not None:
            face.embedding = embedding.tolist()
            face.save()
            
    except Exception as e:
        print(f"特征提取异常: {e}")
