from rest_framework import serializers
from apps.photos.models import Album
from .photo import SimplePhotoSerializer

class AlbumSerializer(serializers.ModelSerializer):
    cover = SimplePhotoSerializer(read_only=True)
    photo_count = serializers.IntegerField(source='photos.count', read_only=True)

    class Meta:
        model = Album
        fields = ['id', 'name', 'description', 'cover', 'photo_count', 'created_at', 'updated_at']
