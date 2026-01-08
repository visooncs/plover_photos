from rest_framework import serializers
from apps.photos.models import Library

class LibrarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Library
        fields = ['id', 'name', 'path', 'scan_status', 'processed_files', 'total_files', 'scan_error', 'last_scanned_at', 'created_at']
        read_only_fields = ['scan_status', 'processed_files', 'total_files', 'scan_error', 'last_scanned_at', 'created_at']
