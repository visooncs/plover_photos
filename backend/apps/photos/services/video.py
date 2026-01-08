import cv2
import os
from PIL import Image
import numpy as np

def extract_video_metadata(video_path):
    """
    提取视频元数据
    返回: {'width': int, 'height': int, 'duration': float, 'fps': float}
    """
    if not os.path.exists(video_path):
        return None

    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0

        cap.release()

        return {
            'width': width,
            'height': height,
            'duration': duration,
            'fps': fps
        }
    except Exception as e:
        print(f"Error extracting video metadata for {video_path}: {e}")
        return None

def extract_video_frame(video_path, timestamp=None):
    """
    从视频中提取一帧
    timestamp: 提取的时间点（秒），如果为 None，则提取视频 10% 处的一帧（避开片头黑屏）
    返回: PIL Image 对象
    """
    if not os.path.exists(video_path):
        return None

    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0

        if timestamp is None:
            # 默认取 10% 处，或者如果视频很短，取中间
            target_frame = int(frame_count * 0.1)
            if duration < 5:
                target_frame = int(frame_count * 0.5)
        else:
            target_frame = int(timestamp * fps)

        # 确保不超过总帧数
        target_frame = min(target_frame, frame_count - 1)
        target_frame = max(0, target_frame)

        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        ret, frame = cap.read()
        cap.release()

        if ret:
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return Image.fromarray(frame_rgb)
        else:
            return None

    except Exception as e:
        print(f"Error extracting video frame for {video_path}: {e}")
        return None

def extract_video_frames_generator(video_path, interval=5.0, max_frames=20):
    """
    生成器：从视频中按间隔提取帧
    video_path: 视频路径
    interval: 提取间隔（秒）
    max_frames: 最大提取帧数限制，防止长视频处理时间过长
    
    Yields: (timestamp, PIL.Image)
    """
    if not os.path.exists(video_path):
        return

    cap = None
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        if fps <= 0:
            return

        # 始终提取第一帧 (或者 1秒处，避开纯黑开头)
        # 很多视频开头是黑屏，我们从 1秒 或者 5% 处开始
        start_time = min(1.0, duration * 0.05)
        
        current_time = start_time
        frames_extracted = 0
        
        while current_time < duration and frames_extracted < max_frames:
            target_frame = int(current_time * fps)
            
            # 边界检查
            if target_frame >= frame_count:
                break
                
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            ret, frame = cap.read()
            
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                yield current_time, Image.fromarray(frame_rgb)
                frames_extracted += 1
            else:
                # 读取失败可能是文件损坏或结束
                break
                
            current_time += interval

    except Exception as e:
        print(f"Error iterating video frames for {video_path}: {e}")
    finally:
        if cap:
            cap.release()
