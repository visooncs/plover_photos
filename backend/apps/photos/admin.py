from django.contrib import admin
from .models import Photo

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'captured_at', 'is_live_photo', 'width', 'height', 'size')
    list_filter = ('is_live_photo',)
    search_fields = ('file_path', 'hash_md5')
