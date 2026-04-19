import os
import cv2
import numpy as np
from PIL import Image, ImageEnhance
import imagehash
from typing import Optional, Tuple, Dict, Any

from app.models.candidate import ImageCandidate
from app.core.config import settings


class ImagePreprocessor:
    def __init__(self):
        self.processed_dir = os.path.join(settings.IMAGE_STORAGE, "processed")
        os.makedirs(self.processed_dir, exist_ok=True)
    
    def preprocess(self, candidate: ImageCandidate) -> ImageCandidate:
        if candidate.download_status != "downloaded" and candidate.download_status != "cached":
            return candidate
        
        try:
            original_path = candidate.original_path
            if not original_path or not os.path.exists(original_path):
                return candidate
            
            img = cv2.imread(original_path)
            if img is None:
                candidate.download_status = "failed"
                candidate.download_error = "Could not load image"
                return candidate
            
            height, width = img.shape[:2]
            
            if width < settings.OPENCV_MIN_DIMENSION or height < settings.OPENCV_MIN_DIMENSION:
                candidate.download_status = "failed"
                candidate.download_error = f"Image too small: {width}x{height}"
                return candidate
            
            if width > settings.OPENCV_MAX_DIMENSION or height > settings.OPENCV_MAX_DIMENSION:
                scale = settings.OPENCV_MAX_DIMENSION / max(width, height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
                height, width = new_height, new_width
            
            processed_path = candidate.local_path
            cv2.imwrite(processed_path, img, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            candidate.width = width
            candidate.height = height
            
            perceptual_hash = self._compute_phash(processed_path)
            candidate.perceptual_hash = str(perceptual_hash)
            
            file_hash = self._compute_file_hash(processed_path)
            candidate.file_hash = file_hash
            
        except Exception as e:
            candidate.download_status = "failed"
            candidate.download_error = f"Preprocessing error: {str(e)[:100]}"
        
        return candidate
    
    def _compute_phash(self, image_path: str) -> imagehash.ImageHash:
        img = Image.open(image_path)
        return imagehash.phash(img)
    
    def _compute_file_hash(self, image_path: str) -> str:
        import hashlib
        with open(image_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()[:16]
    
    def enhance_for_ocr(self, image_path: str) -> np.ndarray:
        img = cv2.imread(image_path)
        if img is None:
            return np.array([])
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        
        return sharpened
    
    def save_enhanced(self, original_path: str, suffix: str = "enhanced") -> str:
        enhanced = self.enhance_for_ocr(original_path)
        if enhanced.size == 0:
            return original_path
        
        base_name = os.path.splitext(os.path.basename(original_path))[0]
        enhanced_path = os.path.join(self.processed_dir, f"{base_name}_{suffix}.jpg")
        cv2.imwrite(enhanced_path, enhanced, [cv2.IMWRITE_JPEG_QUALITY, 95])
        
        return enhanced_path
    
    def get_image_dimensions(self, image_path: str) -> Tuple[int, int]:
        img = cv2.imread(image_path)
        if img is None:
            return (0, 0)
        height, width = img.shape[:2]
        return (width, height)
