from rest_framework import serializers
from apps.photos.models import Memory
from .photo import SimplePhotoSerializer

class MemorySerializer(serializers.ModelSerializer):
    cover = SimplePhotoSerializer(read_only=True)
    photo_count = serializers.IntegerField(source='photos.count', read_only=True)
    
    class Meta:
        model = Memory
        fields = ['id', 'title', 'description', 'memory_type', 'cover', 'photo_count', 'is_favorite', 'created_at']
