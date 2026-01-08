from django.shortcuts import get_object_or_404
from django.http import FileResponse, Http404, HttpResponse
from django.core.cache import cache
from PIL import Image, ImageOps
import io
import os
import cv2
import mimetypes

from ..models import Photo, Face
from ..services.motion_photo import MotionPhotoService
from ..utils import resolve_docker_path

def face_crop_serve(request, pk):
    """提供人脸裁剪图"""
    size = request.GET.get('size', '200')
    try:
        size_int = int(size)
    except ValueError:
        size_int = 200

    face = get_object_or_404(Face, pk=pk)
    photo = face.photo
    
    # 尝试从缓存读取
    cache_key = f"face_crop_v2_{pk}_{size_int}"
    cached_face = cache.get(cache_key)
    if cached_face:
        return HttpResponse(cached_face, content_type="image/jpeg")
        
    real_path = resolve_docker_path(photo.file_path)
    if not os.path.exists(real_path):
        raise Http404("Original photo not found")
        
    try:
        with Image.open(real_path) as img:
            img = ImageOps.exif_transpose(img)
            # bbox: [x1, y1, x2, y2]
            x1, y1, x2, y2 = face.bbox
            
            # 计算原始人脸的中心和尺寸
            bw, bh = x2 - x1, y2 - y1
            cx, cy = x1 + bw / 2, y1 + bh / 2
            
            # 增加边距，使头像包含更多头部信息 (扩充到人脸尺寸的 2.0 倍左右)
            # 这样看起来更像是一个标准的头像，而不是紧贴着五官的特写
            side_length = max(bw, bh) * 1.8
            
            # 计算正方形裁剪区域
            half_side = side_length / 2
            x1 = cx - half_side
            y1 = cy - half_side
            x2 = cx + half_side
            y2 = cy + half_side
            
            # 边界检查与平移处理：如果超出边界，尝试平移正方形而不是直接缩小
            w, h = img.size
            
            if x1 < 0:
                x2 -= x1
                x1 = 0
            if y1 < 0:
                y2 -= y1
                y1 = 0
            if x2 > w:
                x1 -= (x2 - w)
                x2 = w
            if y2 > h:
                y1 -= (y2 - h)
                y2 = h
            
            # 再次确保不越界 (防止图片本身小于目标 side_length)
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(w, x2)
            y2 = min(h, y2)
            
            crop = img.crop((int(x1), int(y1), int(x2), int(y2)))
            
            # 转换为 RGB
            if crop.mode in ("RGBA", "P"):
                crop = crop.convert("RGB")
                
            # 缩放到统一大小
            crop.thumbnail((size_int, size_int), Image.Resampling.LANCZOS)
            
            buf = io.BytesIO()
            crop.save(buf, format="JPEG", quality=90)
            img_data = buf.getvalue()
            
            # 缓存 1 天
            cache.set(cache_key, img_data, 86400)
            
            return HttpResponse(img_data, content_type="image/jpeg")
    except Exception as e:
        print(f"Face crop error: {e}")
        raise Http404("Error generating face crop")

def photo_serve(request, pk):
    """
    提供照片文件，支持实时生成缩略图
    参数: 
    - size: 缩略图尺寸 (如: 300, 600, 1200)
    - crop: 是否裁剪为正方形 (1 或 0)
    """
    size = request.GET.get('size')
    crop = request.GET.get('crop') == '1'
    
    # 1. 如果有尺寸要求，先尝试从缓存读取缩略图内容，完全跳过数据库查询
    if size:
        try:
            size_int = int(size)
            cache_key = f"thumb_{pk}_{size_int}_{'crop' if crop else 'fit'}"
            cached_thumb = cache.get(cache_key)
            if cached_thumb:
                return HttpResponse(cached_thumb, content_type="image/jpeg")
        except ValueError:
            pass

    # 2. 如果缓存没有，再查询数据库。先尝试从缓存获取照片元数据，减少 DB 压力
    photo_meta_cache_key = f"photo_meta_{pk}"
    photo_meta = cache.get(photo_meta_cache_key)
    
    if not photo_meta:
        photo = get_object_or_404(Photo, pk=pk)
        photo_meta = {
            'file_path': photo.file_path,
            'is_pure_video': photo.is_pure_video,
        }
        # 元数据缓存 1 小时
        cache.set(photo_meta_cache_key, photo_meta, 3600)
    
    file_path = resolve_docker_path(photo_meta['file_path'])
    is_pure_video = photo_meta['is_pure_video']

    # 如果没有指定尺寸，或者尺寸解析失败，返回原图
    if not size:
        if os.path.exists(file_path):
            content_type, _ = mimetypes.guess_type(file_path)
            f = open(file_path, 'rb')
            return FileResponse(f, content_type=content_type or 'application/octet-stream')
        raise Http404("File not found")
    
    try:
        size = int(size)
    except ValueError:
        if os.path.exists(file_path):
            content_type, _ = mimetypes.guess_type(file_path)
            f = open(file_path, 'rb')
            return FileResponse(f, content_type=content_type or 'application/octet-stream')
        raise Http404("File not found")

    # 再次确认缓存键（统一逻辑）
    cache_key = f"thumb_{pk}_{size}_{'crop' if crop else 'fit'}"

    # 实时生成缩略图
    try:
        if is_pure_video:
            # 视频截帧逻辑
            # 使用绝对路径并确保路径格式正确
            video_path = os.path.abspath(file_path)
            if not os.path.exists(video_path):
                raise Exception(f"Video file not found: {video_path}")
            
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise Exception("Could not open video file")
            
            # 尝试读取一帧（循环几次跳过可能损坏的开头）
            success = False
            frame = None
            for _ in range(5):
                success, frame = cap.read()
                if success and frame is not None:
                    break
                
            cap.release()
            
            if success and frame is not None:
                # BGR 转 RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
            else:
                raise Exception("Could not read video frame")
        else:
            # 照片逻辑
            if not os.path.exists(file_path):
                raise Http404("File not found")
            img = Image.open(file_path)
            img = ImageOps.exif_transpose(img)
            
        with img:
            # 转换为 RGB (处理 RGBA 或 P 模式)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # 裁剪为正方形
            if crop:
                w, h = img.size
                min_dim = min(w, h)
                left = (w - min_dim) / 2
                top = (h - min_dim) / 2
                right = (w + min_dim) / 2
                bottom = (h + min_dim) / 2
                img = img.crop((left, top, right, bottom))
            
            # 调整尺寸
            img.thumbnail((size, size), Image.Resampling.LANCZOS)
            
            # 写入内存
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=80, optimize=True)
            img_data = buf.getvalue()
            
            # 写入缓存 (1天)
            cache.set(cache_key, img_data, 86400)
            
            return HttpResponse(img_data, content_type="image/jpeg")
            
    except Exception as e:
        # 如果生成缩略图失败且是视频，返回一个生成的占位图而不是视频文件本身
        if is_pure_video and size:
            try:
                # 创建一个深灰色占位图
                placeholder = Image.new('RGB', (int(size), int(size)), color=(31, 41, 55))
                buf = io.BytesIO()
                placeholder.save(buf, format="JPEG")
                return HttpResponse(buf.getvalue(), content_type="image/jpeg")
            except:
                pass

        # 如果生成失败，降级返回原图
        if os.path.exists(file_path):
            content_type, _ = mimetypes.guess_type(file_path)
            f = open(file_path, 'rb')
            return FileResponse(f, content_type=content_type or 'application/octet-stream')
        raise Http404("File not found")

def photo_video_serve(request, pk):
    photo = get_object_or_404(Photo, pk=pk)
    
    # 1. 优先使用 video_path (如果存在且文件存在)
    # 这适用于纯视频文件，或者已经提取出视频文件的旧 Live Photo
    real_video_path = resolve_docker_path(photo.video_path) if photo.video_path else None
    if real_video_path and os.path.exists(real_video_path):
        content_type, _ = mimetypes.guess_type(real_video_path)
        f = open(real_video_path, 'rb')
        return FileResponse(f, content_type=content_type or 'application/octet-stream')

    # 2. 如果是 Live Photo 且 video_path 为空 (或文件不存在)，尝试从原图实时提取
    # 这适用于新的 Motion Photo 逻辑
    real_file_path = resolve_docker_path(photo.file_path)
    if photo.is_live_photo and os.path.exists(real_file_path):
        video_data = MotionPhotoService.extract_video_data(real_file_path)
        if video_data:
            f = io.BytesIO(video_data)
            # FileResponse 可以处理 BytesIO，但不支持 range request 的所有特性，
            # 不过对于小视频通常足够。如果需要更好的流式支持，可能需要更复杂的实现。
            return FileResponse(f, content_type='video/mp4')

    raise Http404("Video not found")
