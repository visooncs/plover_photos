import os
import random
from datetime import datetime, timedelta
from django.db.models import Count, Q
from django.utils import timezone
from ..models import Photo, Person, Face, Memory
import numpy as np

class MemoryService:
    @staticmethod
    def generate_all():
        """执行所有回忆生成逻辑并返回统计"""
        stats = {
            "那年今日": 0,
            "旅行足迹": 0,
            "人物重聚": 0,
            "心境氛围": 0,
            "季节精选": 0,
            "人物特辑": 0
        }
        
        m1 = MemoryService.generate_on_this_day()
        if m1: stats["那年今日"] = 1
        
        m2_count = MemoryService.generate_travel_memories()
        stats["旅行足迹"] = m2_count or 0
        
        m3 = MemoryService.generate_people_reunion()
        if m3: stats["人物重聚"] = 1
        
        m4_count = MemoryService.generate_mood_memories()
        stats["心境氛围"] = m4_count or 0

        m5_count = MemoryService.generate_seasonal_memories()
        stats["季节精选"] = m5_count or 0

        m6_count = MemoryService.generate_person_spotlight()
        stats["人物特辑"] = m6_count or 0
        
        return stats

    @staticmethod
    def generate_on_this_day():
        """生成“那年今日”回忆"""
        today = timezone.now().date()
        # 查找过去年份中同一天的照片
        photos = Photo.objects.filter(
            captured_at__month=today.month,
            captured_at__day=today.day
        ).exclude(captured_at__year=today.year)

        if photos.count() >= 3:
            title = f"那年今日：{today.month}月{today.day}日"
            if not Memory.objects.filter(title=title, memory_type=Memory.MemoryType.ON_THIS_DAY).exists():
                memory = Memory.objects.create(
                    title=title,
                    memory_type=Memory.MemoryType.ON_THIS_DAY,
                    cover=photos.first(),
                    description=f"回顾您在往年 {today.month}月{today.day}日 度过的时光。"
                )
                memory.photos.add(*photos)
                return memory
        return None

    @staticmethod
    def generate_seasonal_memories():
        """生成季节精选回忆"""
        now = timezone.now()
        month = now.month
        year = now.year
        
        # 确定当前季节
        if month in [12, 1, 2]:
            season_name = "冬季"
            months = [12, 1, 2]
        elif month in [3, 4, 5]:
            season_name = "春季"
            months = [3, 4, 5]
        elif month in [6, 7, 8]:
            season_name = "夏季"
            months = [6, 7, 8]
        else:
            season_name = "秋季"
            months = [9, 10, 11]

        # 检查上一个季节的照片 (为了生成“回顾”)
        # 简化逻辑：生成去年的同季节回顾
        last_year = year - 1
        photos = Photo.objects.filter(
            captured_at__year=last_year,
            captured_at__month__in=months
        )

        count = 0
        if photos.count() >= 20:
            title = f"{last_year}年{season_name}精选"
            if not Memory.objects.filter(title=title, memory_type=Memory.MemoryType.CUSTOM).exists():
                memory = Memory.objects.create(
                    title=title,
                    memory_type=Memory.MemoryType.CUSTOM,
                    cover=photos.order_by('?').first(),
                    description=f"重温您在 {last_year} 年 {season_name} 留下的美好记忆。"
                )
                memory.photos.add(*photos[:100])
                count += 1
        return count

    @staticmethod
    def generate_travel_memories():
        """生成“旅行足迹”回忆：基于地点聚类"""
        count = 0
        # 统计地点，排除空地点
        travel_locations = Photo.objects.exclude(location_name="").values('location_name').annotate(
            photo_count=Count('id')
        ).filter(photo_count__gte=5) # 降低门槛到 5 张

        for loc in travel_locations:
            loc_name = loc['location_name']
            # 提取城市名 (通常在地点名称中，这里简单处理，取前两个字或按逗号分割)
            city_name = loc_name.split('·')[0].split(',')[0].split(' ')[0]
            if len(city_name) < 2: city_name = loc_name

            photos = Photo.objects.filter(location_name__icontains=city_name).order_by('captured_at')
            
            title = f"重温 {city_name} 之旅"
            if not Memory.objects.filter(title=title, memory_type=Memory.MemoryType.TRAVEL).exists():
                memory = Memory.objects.create(
                    title=title,
                    memory_type=Memory.MemoryType.TRAVEL,
                    cover=photos.first(),
                    description=f"那是您在 {city_name} 留下的精彩瞬间。"
                )
                memory.photos.add(*photos)
                count += 1
        return count

    @staticmethod
    def generate_person_spotlight():
        """生成“人物特辑”：为经常出现的人物生成回忆"""
        count = 0
        # 查找照片数量较多的人物
        top_people = Person.objects.annotate(
            photo_count=Count('photos')
        ).filter(photo_count__gte=10, is_hidden=False).exclude(name="未命名")

        for person in top_people:
            title = f"人物特辑：{person.name}"
            if not Memory.objects.filter(title=title, memory_type=Memory.MemoryType.PEOPLE).exists():
                photos = person.photos.all().order_by('-captured_at')
                if photos.exists():
                    memory = Memory.objects.create(
                        title=title,
                        memory_type=Memory.MemoryType.PEOPLE,
                        cover=person.avatar if person.avatar else photos.first(),
                        description=f"每一张照片，都记录了与 {person.name} 共同度过的点滴。"
                    )
                    memory.photos.add(*photos[:100])
                    count += 1
        return count

    @staticmethod
    def generate_people_reunion():
        """生成“人物重聚”回忆：多个人物出现在同一张照片中"""
        # 查找有至少 2 个已命名人物的照片
        photos_with_multiple_people = Photo.objects.annotate(
            named_person_count=Count('faces__person', filter=~Q(faces__person__name="未命名") & Q(faces__person__isnull=False), distinct=True)
        ).filter(named_person_count__gte=2)

        if photos_with_multiple_people.exists():
            title = "老友重聚时刻"
            if not Memory.objects.filter(title=title, memory_type=Memory.MemoryType.PEOPLE).exists():
                memory = Memory.objects.create(
                    title=title,
                    memory_type=Memory.MemoryType.PEOPLE,
                    cover=photos_with_multiple_people.first(),
                    description="记录下您与亲友们共度的欢乐时光。"
                )
                memory.photos.add(*photos_with_multiple_people[:100])
                return memory
        return None

    @staticmethod
    def generate_mood_memories():
        """生成“心境氛围”回忆：利用 CLIP 语义搜索"""
        count = 0
        moods = [
            {"tag": "开心时刻", "keywords": ["happy people smiling", "laughing together", "party celebration"], "desc": "捕捉那些充满欢笑的瞬间。"},
            {"tag": "宁静时光", "keywords": ["peaceful landscape", "calm nature sunset", "quiet forest"], "desc": "在自然中寻找片刻宁静。"},
            {"tag": "美食主义", "keywords": ["delicious food", "gourmet meal", "restaurant table"], "desc": "唯有美食不可辜负。"},
            {"tag": "萌宠出没", "keywords": ["cute cat dog", "lovely pet", "animal friend"], "desc": "治愈系的小精灵们。"},
            {"tag": "运动活力", "keywords": ["running cycling sport", "workout fitness", "active lifestyle"], "desc": "生命在于运动。"},
            {"tag": "城市光影", "keywords": ["city night lights", "urban street photography", "architecture"], "desc": "穿梭在繁华的都市之间。"},
        ]
        
        from .embeddings import search_photos_by_text
        
        for mood in moods:
            title = mood['tag']
            if not Memory.objects.filter(title=title, memory_type=Memory.MemoryType.MOOD).exists():
                # 尝试多个关键词以增加成功率
                photos = []
                for kw in mood['keywords']:
                    results = search_photos_by_text(kw, limit=20)
                    if results:
                        photos.extend(results)
                        if len(photos) >= 5: break
                
                if len(photos) >= 3:
                    # 去重
                    unique_photos = list({p.id: p for p in photos}.values())
                    memory = Memory.objects.create(
                        title=title,
                        memory_type=Memory.MemoryType.MOOD,
                        cover=unique_photos[0],
                        description=mood['desc']
                    )
                    memory.photos.add(*unique_photos)
                    count += 1
        return count
