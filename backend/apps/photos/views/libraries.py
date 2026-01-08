from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
import threading
from django.db import connection

from ..models import Library
from ..serializers import LibrarySerializer
from ..services import scan_directory

class LibraryViewSet(viewsets.ModelViewSet):
    queryset = Library.objects.all().order_by('-created_at')
    serializer_class = LibrarySerializer
    
    @action(detail=True, methods=['post'])
    def scan(self, request, pk=None):
        library = self.get_object()
        force = request.data.get('force', False)
        
        if library.scan_status != Library.ScanStatus.PAUSED or force:
            library.processed_files = 0
            
        library.scan_status = Library.ScanStatus.SCANNING
        library.save()
        
        def run_scan():
            try:
                # 传入 library_id，内部会继续更新进度
                scan_directory(library.path, library_id=library.id)
            except Exception as e:
                try:
                    Library.objects.filter(id=library.id).update(
                        scan_status=Library.ScanStatus.FAILED,
                        scan_error=str(e)
                    )
                except:
                    pass
            finally:
                connection.close()

        thread = threading.Thread(target=run_scan)
        thread.daemon = True
        thread.start()
        
        return Response({'status': 'scanning_started'})

    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        library = self.get_object()
        if library.scan_status == Library.ScanStatus.SCANNING:
            library.scan_status = Library.ScanStatus.PAUSED
            library.save()
            return Response({'status': 'paused'})
        return Response({'status': 'not_scanning'}, status=status.HTTP_400_BAD_REQUEST)
