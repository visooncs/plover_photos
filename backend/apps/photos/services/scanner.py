import os
import hashlib
import re
from datetime import datetime
from PIL import Image, ImageOps
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass
from django.utils.timezone import make_aware
from django import db
from django.db import transaction
from django.conf import settings
from apps.photos.models import Photo, Library, MaintenanceTask
from .faces import detect_faces_in_photo, cluster_faces
from .embeddings import generate_photo_embedding
from .motion_photo import MotionPhotoService
from .video import extract_video_metadata

def get_gps_data(exif):
    """从 EXIF 中提取 GPS 经纬度"""
    if not exif:
        return None, None
    
    gps_info = exif.get_ifd(0x8825) # GPSInfo
    if not gps_info:
        return None, None

    def _to_float(v):
        if isinstance(v, tuple) and len(v) == 2:
            return float(v[0]) / float(v[1]) if v[1] != 0 else 0.0
        if hasattr(v, 'numerator') and hasattr(v, 'denominator'):
             return float(v.numerator) / float(v.denominator) if v.denominator != 0 else 0.0
        return float(v)

    def _convert_to_degrees(value):
        try:
            d = _to_float(value[0])
            m = _to_float(value[1])
            s = _to_float(value[2])
            return d + (m / 60.0) + (s / 3600.0)
        except (ValueError, IndexError, TypeError):
            return 0.0

    try:
        lat_raw = gps_info.get(2)
        if not lat_raw: return None, None
        lat = _convert_to_degrees(lat_raw)
        if gps_info.get(1) == 'S': lat = -lat
        
        lon_raw = gps_info.get(4)
        if not lon_raw: return None, None
        lon = _convert_to_degrees(lon_raw)
        if gps_info.get(3) == 'W': lon = -lon
        
        return lat, lon
    except Exception as e:
        print(f"GPS parsing error: {e}")
        return None, None

def get_exif_details(exif):
    """从 EXIF 中提取详细摄影参数"""
    if not exif:
        return {}
    
    data = {}
    
    def _to_float(v):
        if not v: return None
        try:
            if hasattr(v, 'numerator') and hasattr(v, 'denominator'):
                 return float(v.numerator) / float(v.denominator) if v.denominator != 0 else 0.0
            if isinstance(v, tuple) and len(v) == 2:
                return float(v[0]) / float(v[1]) if v[1] != 0 else 0.0
            return float(v)
        except:
            return None

    # Basic tags
    # Make: 271, Model: 272
    data['make'] = exif.get(271)
    data['model'] = exif.get(272)
    
    # Exif SubIFD
    exif_ifd = exif.get_ifd(0x8769)
    if exif_ifd:
        # ISO: 34855
        iso = exif_ifd.get(34855)
        # Some cameras return tuple for ISO? Usually integer.
        if isinstance(iso, tuple): iso = iso[0]
        try:
            data['iso'] = int(iso) if iso else None
        except:
            data['iso'] = None
        
        # FNumber: 33437
        data['f_number'] = _to_float(exif_ifd.get(33437))
        
        # ExposureTime: 33434
        exp_time = exif_ifd.get(33434)
        if exp_time:
            if hasattr(exp_time, 'numerator') and hasattr(exp_time, 'denominator'):
                if exp_time.numerator == 1 and exp_time.denominator > 1:
                    data['exposure_time'] = f"1/{exp_time.denominator}"
                else:
                    val = float(exp_time.numerator) / float(exp_time.denominator) if exp_time.denominator != 0 else 0
                    if val < 1 and val > 0:
                        data['exposure_time'] = f"1/{int(1/val)}"
                    else:
                        data['exposure_time'] = str(val)
            else:
                data['exposure_time'] = str(exp_time)

        # FocalLength: 37386
        data['focal_length'] = _to_float(exif_ifd.get(37386))
        
        # LensModel: 42036 or 42035
        # decode bytes if necessary
        lens = exif_ifd.get(42036) or exif_ifd.get(42035)
        if isinstance(lens, bytes):
            try: lens = lens.decode('utf-8').strip('\x00')
            except: pass
        data['lens_model'] = lens
        
    return data

def extract_date_from_filename(filename):
    """从文件名中提取日期时间 (优先匹配)"""
    match = re.search(r'(20\d{2})[-_.\s]?(\d{2})[-_.\s]?(\d{2})[-_.\sT]*(\d{2})[-_.\s]?(\d{2})[-_.\s]?(\d{2})', filename)
    if match:
        try:
            year, month, day, hour, minute, second = map(int, match.groups())
            if 1 <= month <= 12 and 1 <= day <= 31:
                return datetime(year, month, day, hour, minute, second)
        except ValueError:
            pass

    match = re.search(r'(20\d{2})[-_.]?(\d{2})[-_.]?(\d{2})', filename)
    if match:
        try:
            year, month, day = map(int, match.groups())
            if 1 <= month <= 12 and 1 <= day <= 31:
                return datetime(year, month, day)
        except ValueError:
            pass
            
    return None

from ..utils import resolve_docker_path

def process_single_file(file_path, log_func=None):
    """处理单个文件导入 (照片或视频)"""
    try:
        existing_photo = Photo.objects.filter(file_path=file_path).first()
        if existing_photo:
            # 检查是否有更新日期
            filename_date = extract_date_from_filename(os.path.basename(file_path))
            if filename_date:
                try:
                    filename_date = make_aware(filename_date)
                    if existing_photo.captured_at != filename_date:
                        existing_photo.captured_at = filename_date
                        existing_photo.save(update_fields=['captured_at'])
                except ValueError:
                    pass
            
            # 检查是否遗漏了 Motion Photo (针对已导入但未识别的)
            if not existing_photo.is_video and not existing_photo.is_live_photo:
                 if MotionPhotoService.is_motion_photo(file_path):
                    existing_photo.is_live_photo = True
                    # video_path 为空表示视频内容嵌入在原文件中
                    existing_photo.video_path = None 
                    existing_photo.save(update_fields=['is_live_photo', 'video_path'])
                    if log_func:
                        log_func(f"修正已存在的 Motion Photo: {os.path.basename(file_path)}", 'success')

            return False

        md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b''):
                md5.update(chunk)
        file_hash = md5.hexdigest()
        
        photo = Photo.objects.filter(hash_md5=file_hash).first()
        if photo:
            # 检查是否是同一个文件（路径大小写不同或已移动）
            # 1. 如果路径 normcase 后相同，说明是同一个文件（Windows 大小写差异）
            # 2. 如果原路径文件不存在，说明是文件移动
            if os.path.normcase(photo.file_path) == os.path.normcase(file_path):
                if photo.file_path != file_path:
                    photo.file_path = file_path
                    photo.save(update_fields=['file_path'])
            elif not os.path.exists(photo.file_path):
                # 原文件不存在，视为移动
                if log_func:
                    log_func(f"文件路径更新: {os.path.basename(file_path)}", 'info')
                photo.file_path = file_path
                photo.save(update_fields=['file_path'])
            else:
                # 原文件存在且路径不同，这是重复文件
                # 这种情况下不应该根据副本的文件名修改原库中照片的时间
                # if log_func:
                #     log_func(f"忽略重复文件: {os.path.basename(file_path)}", 'info')
                return False

            filename_date = extract_date_from_filename(os.path.basename(file_path))
            if filename_date:
                try:
                    filename_date = make_aware(filename_date)
                except ValueError:
                    pass
                
                if photo.captured_at != filename_date:
                    photo.captured_at = filename_date
                    photo.save(update_fields=['captured_at'])
                    if log_func:
                        log_func(f"根据文件名修正时间: {os.path.basename(file_path)}", 'info')
            
            return False
            
        ext = os.path.splitext(file_path)[1].lower()
        # photo_extensions = ('.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif', '.tiff', '.bmp', '.gif')
        video_extensions = ('.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm')

        captured_at = extract_date_from_filename(os.path.basename(file_path))
        if captured_at:
             try:
                 captured_at = make_aware(captured_at)
             except ValueError:
                 pass
        
        width, height = 0, 0
        duration = 0.0
        lat, lon = None, None
        is_video = ext in video_extensions
        video_path = file_path if is_video else None
        is_live_photo = False

        # 如果是视频文件，检查是否是 Live Photo 的伴生视频
        # 如果存在同名的图片文件，则认为该视频是 Live Photo 的一部分，跳过单独导入
        if is_video:
            base_name = os.path.splitext(file_path)[0]
            # 检查常见的图片扩展名
            for img_ext in ['.jpg', '.jpeg', '.heic', '.heif', '.png', '.JPG', '.JPEG', '.HEIC', '.HEIF', '.PNG']:
                if os.path.exists(base_name + img_ext):
                    # if log_func:
                    #     log_func(f"跳过 Live Photo 伴生视频: {os.path.basename(file_path)} (属于 {os.path.basename(base_name + img_ext)})", 'info')
                    return False

        if not is_video:
            try:
                # 尝试检测 Motion Photo (嵌入式视频)
                if not is_live_photo and not video_path:
                    # 先快速检查是否有标记，避免不必要的 I/O
                    if MotionPhotoService.is_motion_photo(file_path):
                        is_live_photo = True
                        video_path = None # 嵌入式视频，无独立路径
                        if log_func:
                            log_func(f"发现 Motion Photo: {os.path.basename(file_path)}", 'success')

                with Image.open(file_path) as img:
                    exif = img.getexif()
                    img = ImageOps.exif_transpose(img)
                    width, height = img.size
                    if exif:
                        if not captured_at:
                            dt_orig = exif.get(36867)
                            if dt_orig:
                                try:
                                    captured_at = datetime.strptime(dt_orig, '%Y:%m:%d %H:%M:%S')
                                except: pass
                        
                        lat, lon = get_gps_data(exif)

                base_name = os.path.splitext(file_path)[0]
                for v_ext in ['.mov', '.mp4', '.MOV', '.MP4']:
                    v_path = base_name + v_ext
                    if os.path.exists(v_path):
                        try:
                            v_size = os.path.getsize(v_path)
                            if v_size > 100 * 1024 * 1024:
                                if log_func:
                                    log_func(f"忽略同名视频 {v_path}: 文件过大 ({v_size // 1024 // 1024}MB)", 'info')
                                continue
                        except OSError:
                            continue

                        video_path = v_path
                        is_live_photo = True
                        break
            except Exception as e:
                if log_func:
                    log_func(f"照片解析异常 {file_path}: {e}", 'warn')

        if not captured_at:
            mtime = os.path.getmtime(file_path)
            captured_at = datetime.fromtimestamp(mtime)
        
        if captured_at:
            try:
                captured_at = make_aware(captured_at)
            except ValueError:
                pass

        photo = Photo.objects.create(
            file_path=file_path,
            hash_md5=file_hash,
            captured_at=captured_at,
            width=width,
            height=height,
            latitude=lat,
            longitude=lon,
            size=os.path.getsize(file_path),
            is_live_photo=is_live_photo,
            video_path=video_path,
            duration=duration
        )
        
        # 无论是图片还是视频，都尝试进行人脸检测和向量生成
        # [MODIFIED] 用户要求解耦，扫描时不再自动执行这些耗时操作
        # try:
        #      detect_faces_in_photo(photo.id)
        # except Exception as e:
        #      if log_func: log_func(f"人脸检测失败: {e}", 'error')
        
        # try:
        #      generate_photo_embedding(photo.id)
        # except Exception as e:
        #      if log_func: log_func(f"向量化失败: {e}", 'error')

        return True
            
    except Exception as e:
        if log_func:
            log_func(f"处理失败 {file_path}: {e}", 'error')
        return False


def scan_directory(path, logger=None, library_id=None, task_id=None):
    """
    扫描目录并导入照片
    """
    # 尝试解析 Docker 路径映射
    real_path = resolve_docker_path(path)
    
    library = None
    if library_id:
        library = Library.objects.get(id=library_id)
        library.scan_status = Library.ScanStatus.SCANNING
        library.processed_files = 0
        library.total_files = 0
        library.scan_error = None
        library.save()
        
    task = None
    if task_id:
        try:
            task = MaintenanceTask.objects.get(id=task_id)
        except MaintenanceTask.DoesNotExist:
            pass

    def log(msg, style='info'):
        if logger:
            logger(msg)
        else:
            print(f"[{style.upper()}] {msg}")

    if not os.path.exists(real_path):
        msg = f"路径不存在: {real_path} (原路径: {path})"
        log(msg, 'error')
        if library:
            library.scan_status = Library.ScanStatus.FAILED
            library.scan_error = msg
            library.save()
        return 0

    log(f"开始扫描目录: {real_path}")
    
    all_files = []
    photo_extensions = ('.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif', '.tiff', '.bmp', '.gif')
    video_extensions = ('.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm')
    valid_extensions = photo_extensions + video_extensions
    
    for root, dirs, files in os.walk(real_path):
        for file in files:
            if file.lower().endswith(valid_extensions):
                all_files.append(os.path.join(root, file))
    
    total_count = len(all_files)
    if library:
        library.total_files = total_count
        start_index = library.processed_files if library.scan_status == Library.ScanStatus.SCANNING else 0
        library.save()
    else:
        start_index = 0

    count = 0
    last_update_index = start_index
    # 提高进度更新频率，以便前端能更快看到进度变化
    update_interval = max(5, total_count // 50)
    
    batch_size = 100
    
    for i in range(start_index, total_count, batch_size):
        db.close_old_connections()
        batch_files = all_files[i : i + batch_size]
        
        for j, full_path in enumerate(batch_files):
            current_index = i + j
            
            if library:
                try:
                    current_lib = Library.objects.only('scan_status').get(id=library.id)
                    if current_lib.scan_status != Library.ScanStatus.SCANNING:
                        log(f"扫描任务被用户手动{current_lib.get_scan_status_display()}", 'warning')
                        return count
                except Exception:
                    # 如果查询失败，可能是连接问题，尝试继续
                    pass

            try:
                # 再次确保连接新鲜
                db.close_old_connections()
                with transaction.atomic():
                    if process_single_file(full_path, log):
                        count += 1
            except Exception as e:
                log(f"处理异常 {full_path}: {e}", 'error')
            
            if (current_index - last_update_index >= update_interval or current_index == total_count - 1):
                    if library:
                        Library.objects.filter(id=library.id).update(processed_files=current_index + 1)
                    if task:
                        progress = int(((current_index + 1) / total_count) * 100)
                        MaintenanceTask.objects.filter(id=task.id).update(progress=progress)
                    
                    last_update_index = current_index
    
    if library:
        norm_lib_path = os.path.normpath(path)
        db_photos = Photo.objects.filter(file_path__startswith=path).values_list('id', 'file_path')
        disk_files_set = set(os.path.normpath(p) for p in all_files)
        
        ids_to_delete = []
        for photo_id, photo_path in db_photos:
            norm_photo_path = os.path.normpath(photo_path)
            if not norm_photo_path.startswith(norm_lib_path):
                continue
            if norm_photo_path not in disk_files_set:
                ids_to_delete.append(photo_id)
        
        if ids_to_delete:
            count_deleted = len(ids_to_delete)
            batch_size = 900
            for i in range(0, count_deleted, batch_size):
                batch_ids = ids_to_delete[i:i+batch_size]
                Photo.objects.filter(id__in=batch_ids).delete()
            
            log(f"清理已删除文件: {count_deleted} 个", 'warning')

        library.processed_files = total_count
        library.total_files = total_count
        library.scan_status = Library.ScanStatus.COMPLETED
        library.last_scanned_at = make_aware(datetime.now())
        library.save()

    if count > 0:
        from django.core.cache import cache
        cache.delete('years_timeline_data')
        log("开始人脸聚类...", 'info')
        cluster_faces()

    log(f"导入完成，新增 {count} 张照片", 'success')
    return count
