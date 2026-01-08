import os
import re

class MotionPhotoService:
    """
    Handle Android Motion Photos (embedded video in JPEG/HEIC)
    Supports:
    - Google Pixel (MicroVideoOffset)
    - Samsung (MotionPhoto_Data / SEF)
    - Generic Embedded MP4 (File appending)
    """
    
    @staticmethod
    def extract_video_data(image_path):
        """
        Extract embedded video data from a JPEG/HEIC file into memory.
        Returns bytes if successful, None otherwise.
        """
        try:
            file_size = os.path.getsize(image_path)
            
            with open(image_path, 'rb') as f:
                content = f.read()

                # 1. Google Pixel / GCamera approach (MicroVideoOffset)
                match = re.search(b'MicroVideoOffset="(\d+)"', content[:100*1024]) # Check header
                if match:
                    offset = int(match.group(1))
                    if offset > 0 and offset < file_size:
                        return content[-offset:]

                # 2. Samsung Motion Photo (SEF / MotionPhoto_Data)
                # Look for "MotionPhoto_Data" marker
                motion_photo_marker = b"MotionPhoto_Data"
                if b"MotionPhoto_Data" in content:
                    # Samsung Motion Photos usually have the video appended at the end.
                    # We will rely on the generic 'ftyp' scan below to find it.
                    # This marker just confirms it's likely a motion photo.
                    pass 

                # 3. Generic Appended MP4 (looking for ftyp)
                # Scan for 'ftyp' marker from the end backwards or in the tail
                # We'll use the tail approach as before but on the memory content
                
                # We limit scan to last 20MB
                scan_start_index = max(0, len(content) - 20 * 1024 * 1024)
                tail_data = content[scan_start_index:]
                
                # Find all occurrences of b'ftyp'
                ftyp_indices = [m.start() for m in re.finditer(b'ftyp', tail_data)]
                
                for idx in ftyp_indices:
                    if idx < 4: continue
                    
                    # idx is relative to tail_data start
                    # box_size is at idx-4
                    
                    # offset relative to whole file
                    real_offset = scan_start_index + idx - 4
                    
                    if real_offset == 0:
                        continue # File header
                        
                    # Check brand
                    brand = tail_data[idx+4:idx+8]
                    if brand in [b'mp41', b'mp42', b'isom', b'qt  ', b'3gp5', b'MSNV']:
                         # Likely a video
                         return content[real_offset:]

            return None
            
        except Exception as e:
            print(f"Error extracting motion photo data: {e}")
            return None

    @staticmethod
    def extract_video(image_path, output_path):
        """
        Try to detect and extract embedded video from a JPEG/HEIC file.
        Returns True if successful, False otherwise.
        """
        video_data = MotionPhotoService.extract_video_data(image_path)
        if video_data:
            try:
                with open(output_path, 'wb') as out:
                    out.write(video_data)
                return True
            except Exception as e:
                print(f"Error writing extracted video: {e}")
                return False
        return False

    @staticmethod
    def is_motion_photo(image_path):
        """
        Fast check if file might be a motion photo
        """
        try:
            # Check file extension first
            ext = os.path.splitext(image_path)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.heic', '.heif']:
                return False

            with open(image_path, 'rb') as f:
                # 1. Check XMP for MicroVideo
                head = f.read(50 * 1024) 
                if b'MicroVideo' in head or b'MotionPhoto' in head:
                    return True
                
                # 2. Check for appended MP4 (Magic check)
                # Read tail to see if there is an MP4 signature
                f.seek(0, 2)
                size = f.tell()
                if size < 1024: return False
                
                # Check last 5MB for 'ftyp'
                scan_size = min(size, 5 * 1024 * 1024)
                f.seek(-scan_size, 2)
                tail = f.read()
                
                # Ignore file start
                if b'ftyp' in tail:
                    # Need to ensure it's not the file header (if file < 5MB)
                    # Simple heuristic: if we find ftyp not at the very beginning of our read buffer
                    # (unless buffer started > 0)
                    
                    # Actually, if we find 'ftyp' anywhere that is NOT the absolute beginning of the file,
                    # it's a strong indicator of embedded video.
                    # If file is small (read whole file), ftyp at 4 is the image itself (HEIC).
                    # We need another ftyp later.
                    
                    first_ftyp = tail.find(b'ftyp')
                    if first_ftyp != -1:
                        real_offset = size - scan_size + first_ftyp
                        if real_offset > 100: # Margin to skip file header
                            return True
                            
            return False
        except:
            return False
