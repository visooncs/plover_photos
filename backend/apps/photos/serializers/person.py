from rest_framework import serializers
from apps.photos.models import Person
from .photo import SimplePhotoSerializer

class PersonSerializer(serializers.ModelSerializer):
    avatar = SimplePhotoSerializer(read_only=True)
    photo_count = serializers.IntegerField(source='photos.count', read_only=True)
    face_url = serializers.SerializerMethodField()

    class Meta:
        model = Person
        fields = ['id', 'name', 'avatar', 'photo_count', 'created_at', 'face_url', 'is_starred']

    def get_face_url(self, obj):
        face = obj.representative_face
        if face:
            return f"/face/{face.id}/crop/"
        return None
