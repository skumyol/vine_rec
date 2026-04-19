import os
import hashlib
import aiofiles
from typing import Optional
import httpx
from urllib.parse import urlparse

from app.models.candidate import ImageCandidate
from app.core.config import settings


class ImageDownloader:
    def __init__(self):
        self.storage_dir = settings.IMAGE_STORAGE
        self.original_dir = os.path.join(self.storage_dir, "original")
        self.processed_dir = os.path.join(self.storage_dir, "processed")
        self._ensure_dirs()
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
    
    def _ensure_dirs(self):
        os.makedirs(self.original_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
    
    async def download(self, candidate: ImageCandidate) -> ImageCandidate:
        try:
            extension = self._get_extension(candidate.image_url)
            file_hash = hashlib.md5(candidate.image_url.encode()).hexdigest()[:16]
            filename = f"{file_hash}{extension}"
            
            original_path = os.path.join(self.original_dir, filename)
            processed_path = os.path.join(self.processed_dir, filename)
            
            if os.path.exists(original_path):
                file_size = os.path.getsize(original_path)
                candidate.local_path = processed_path
                candidate.original_path = original_path
                candidate.file_size = file_size
                candidate.download_status = "cached"
                return candidate
            
            response = await self.client.get(candidate.image_url)
            response.raise_for_status()
            
            content = response.content
            content_type = response.headers.get('content-type', '')
            
            if not content_type.startswith('image/'):
                candidate.download_status = "failed"
                candidate.download_error = "Not an image"
                return candidate
            
            async with aiofiles.open(original_path, 'wb') as f:
                await f.write(content)
            
            # Check actual image dimensions
            from PIL import Image
            with Image.open(original_path) as img:
                width, height = img.size
                candidate.width = width
                candidate.height = height
                
                # Skip tiny images - require at least 300x300 for OCR
                if width < 300 or height < 300:
                    candidate.download_status = "failed"
                    candidate.download_error = f"Image too small: {width}x{height}"
                    return candidate
            
            candidate.local_path = processed_path
            candidate.original_path = original_path
            candidate.file_size = len(content)
            candidate.download_status = "downloaded"
            
        except httpx.HTTPStatusError as e:
            candidate.download_status = "failed"
            candidate.download_error = f"HTTP {e.response.status_code}"
        except httpx.TimeoutException:
            candidate.download_status = "failed"
            candidate.download_error = "Timeout"
        except Exception as e:
            candidate.download_status = "failed"
            candidate.download_error = str(e)[:100]
        
        return candidate
    
    def _get_extension(self, url: str) -> str:
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        if '.jpg' in path or '.jpeg' in path:
            return '.jpg'
        elif '.png' in path:
            return '.png'
        elif '.gif' in path:
            return '.gif'
        elif '.webp' in path:
            return '.webp'
        else:
            return '.jpg'
    
    async def close(self):
        await self.client.aclose()
