from django.db.models import Count, Min, Max
from django.db.models.functions import TruncDate
from ..models import Photo, Person
from datetime import timedelta

def get_person_recommendations(limit=3):
    """
    Recommend albums based on people with many photos.
    """
    recommendations = []
    
    # Get top people by photo count who are not hidden
    top_people = Person.objects.filter(is_hidden=False).annotate(
        count=Count('photos')
    ).order_by('-count')[:limit]
    
    for person in top_people:
        if person.count < 5: # Skip if too few photos
            continue
            
        # Get a nice cover photo (e.g., the avatar or the first photo)
        cover = person.avatar or person.photos.first()
        
        recommendations.append({
            'id': f"person_{person.id}",
            'title': f"{person.name} 的精选集",
            'type': 'person',
            'cover_id': cover.id if cover else None,
            'photo_count': person.count,
            'description': f"包含 {person.name} 的 {person.count} 张照片",
            'query_params': {'people': person.id} # Used to fetch photos for this album
        })
        
    return recommendations

def get_location_recommendations(limit=3):
    """
    Recommend albums based on locations with many photos.
    """
    recommendations = []
    
    # Group by location_name
    locations = Photo.objects.exclude(location_name='').values('location_name').annotate(
        count=Count('id')
    ).order_by('-count')[:limit]
    
    for loc in locations:
        if loc['count'] < 5:
            continue
            
        # Get a representative photo (most recent one due to default ordering)
        cover = Photo.objects.filter(location_name=loc['location_name']).first()
        
        recommendations.append({
            'id': f"loc_{loc['location_name']}",
            'title': f"{loc['location_name']} 之旅",
            'type': 'location',
            'cover_id': cover.id if cover else None,
            'photo_count': loc['count'],
            'description': f"在 {loc['location_name']} 拍摄的精彩瞬间",
            'query_params': {'location': loc['location_name']}
        })
        
    return recommendations

def get_date_recommendations(limit=3):
    """
    Recommend albums based on date clusters (simple implementation).
    Looking for days with many photos.
    """
    recommendations = []
    
    # Group by date
    dates = Photo.objects.annotate(
        date=TruncDate('captured_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('-count')[:limit]
    
    for d in dates:
        if not d['date'] or d['count'] < 10:
            continue
            
        # Get a representative photo for this date
        cover = Photo.objects.filter(captured_at__date=d['date']).first()
        
        date_str = d['date'].strftime('%Y年%m月%d日')
        
        recommendations.append({
            'id': f"date_{d['date']}",
            'title': f"{date_str} 的记忆",
            'type': 'event',
            'cover_id': cover.id if cover else None,
            'photo_count': d['count'],
            'description': f"这一天拍摄了 {d['count']} 张照片",
            'query_params': {
                'date_after': d['date'], 
                'date_before': d['date'] + timedelta(days=1)
            }
        })
        
    return recommendations

def get_all_recommendations():
    """
    Combine all recommendations.
    """
    recs = []
    recs.extend(get_person_recommendations(2))
    recs.extend(get_location_recommendations(2))
    recs.extend(get_date_recommendations(2))
    
    # Deduplicate or sort if needed
    return recs
