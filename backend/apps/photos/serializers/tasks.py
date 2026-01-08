from rest_framework import serializers
from apps.photos.models import ScheduledTask, MaintenanceTask

class ScheduledTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduledTask
        fields = '__all__'
        read_only_fields = ['last_run_at', 'next_run_at', 'created_at']

class MaintenanceTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceTask
        fields = '__all__'
        read_only_fields = ['status', 'progress', 'logs', 'error_message', 'created_at', 'started_at', 'finished_at', 'created_by']
