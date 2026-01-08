from django.http import JsonResponse
from django.urls import reverse
from django.db.models import Count, Avg, Subquery, OuterRef

from ..models import Photo

def places_list(request):
    """
    获取地点列表 (按 location_name 分组)
    """
    # 子查询：获取每个地点最新的一张照片 ID
    latest_photo = Photo.objects.filter(
        location_name=OuterRef('location_name')
    ).order_by('-captured_at').values('id')[:1]

    # 过滤掉 location_name 为空的
    places = Photo.objects.exclude(location_name__exact='').exclude(location_name__isnull=True).values('location_name').annotate(
        count=Count('id'),
        cover_id=Subquery(latest_photo), 
        lat=Avg('latitude'),
        lng=Avg('longitude')
    ).order_by('-count')
    
    data = []
    for p in places:
        # 获取封面图 ID
        cover_id = p['cover_id']
        
        data.append({
            'name': p['location_name'],
            'count': p['count'],
            'lat': p['lat'],
            'lng': p['lng'],
            'cover': reverse('photo_serve', args=[cover_id]) + '?size=400&crop=1'
        })
        
    return JsonResponse(data, safe=False)

def map_markers(request):
    """
    获取地图标记点
    支持网格聚合: 根据 zoom 级别将相近的点合并
    """
    try:
        min_lat = float(request.GET.get('min_lat'))
        max_lat = float(request.GET.get('max_lat'))
        min_lng = float(request.GET.get('min_lng'))
        max_lng = float(request.GET.get('max_lng'))
        zoom = float(request.GET.get('zoom', 10))
        
        # 1. 基础查询
        photos = Photo.objects.filter(
            latitude__range=(min_lat, max_lat),
            longitude__range=(min_lng, max_lng)
        ).only('id', 'latitude', 'longitude', 'captured_at').order_by('-captured_at')
        
        # 限制最大数量以防止 Python 处理过慢 (例如最多取前 3000 张进行聚合)
        # 如果需要显示所有，可以考虑在数据库层做聚合 (需要 PostGIS) 或优化算法
        photos = photos[:3000]
        
        # 2. 网格聚合逻辑
        # 计算网格大小: zoom 越大，网格越小
        # 粗略估算: 360 度 / 2^zoom
        # 系数可调，决定聚合的松紧程度
        grid_size = 100.0 / (2 ** zoom) 
        
        clusters = {}
        
        for p in photos:
            # 计算网格坐标
            grid_x = int(p.latitude / grid_size)
            grid_y = int(p.longitude / grid_size)
            key = (grid_x, grid_y)
            
            if key not in clusters:
                clusters[key] = {
                    'count': 0,
                    'lat_sum': 0,
                    'lng_sum': 0,
                    'cover_photo': p, # 默认取第一张（也就是最新的，因为按时间倒序）
                    'ids': []
                }
            
            c = clusters[key]
            c['count'] += 1
            c['lat_sum'] += p.latitude
            c['lng_sum'] += p.longitude
            # c['ids'].append(str(p.id)) # 暂时不需要返回所有 ID
            
        # 3. 生成结果
        data = []
        for c in clusters.values():
            # 计算中心点 (可以是网格中心，也可以是所有点的平均中心)
            # 这里使用平均中心，显示更准确
            avg_lat = c['lat_sum'] / c['count']
            avg_lng = c['lng_sum'] / c['count']
            
            p = c['cover_photo']
            data.append({
                'id': str(p.id), # 代表照片 ID
                'lat': avg_lat,
                'lng': avg_lng,
                'count': c['count'],
                'thumb': reverse('photo_serve', args=[p.id]) + '?size=100&crop=1',
                'preview': reverse('photo_serve', args=[p.id]) + '?size=400',
                'date': p.captured_at.strftime('%Y年%m月%d日') if p.captured_at else ''
            })
            
        return JsonResponse(data, safe=False)

    except (TypeError, ValueError):
        # 如果没有传边界，返回空的
        return JsonResponse([], safe=False)
