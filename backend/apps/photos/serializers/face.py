from rest_framework import serializers
from apps.photos.models import Face

class FaceSerializer(serializers.ModelSerializer):
    person_name = serializers.CharField(source='person.name', read_only=True)
    
    class Meta:
        model = Face
        fields = ['id', 'bbox', 'person', 'person_name', 'prob', 'timestamp']
