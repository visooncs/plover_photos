from rest_framework import serializers
from apps.photos.models import Photo
from .face import FaceSerializer

class SimplePhotoSerializer(serializers.ModelSerializer):
    """用于嵌套在 Album/Person 中的简化版照片信息"""
    thumbnail = serializers.SerializerMethodField()
    
    class Meta:
        model = Photo
        fields = ['id', 'thumbnail']

    def get_thumbnail(self, obj):
        return f"/photo/{obj.id}/serve/?size=300&crop=1"

class PhotoSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()
    faces = FaceSerializer(many=True, read_only=True)

    class Meta:
        model = Photo
        fields = [
            'id', 
            'file_path', 
            'captured_at', 
            'width', 
            'height', 
            'size',
            'latitude',
            'longitude',
            'location_name', 
            'is_live_photo',
            'is_video',
            'duration',
            'url',
            'thumbnail',
            'video_url',
            'faces',
            # EXIF
            'exif_camera_make', 'exif_camera_model', 'exif_lens_model',
            'exif_iso', 'exif_f_number', 'exif_exposure_time', 'exif_focal_length'
        ]

    def get_url(self, obj):
        return f"/photo/{obj.id}/serve/"

    def get_thumbnail(self, obj):
        return f"/photo/{obj.id}/serve/?size=300&crop=1"
        
    def get_video_url(self, obj):
        if obj.is_video or obj.is_live_photo:
            return f"/photo/{obj.id}/video/"
        return None
