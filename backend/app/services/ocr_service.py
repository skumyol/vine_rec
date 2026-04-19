import re
from typing import List, Dict, Any, Optional
import numpy as np

from app.models.candidate import ImageCandidate, OCRResult
from app.services.image_preprocess import ImagePreprocessor
from app.core.config import settings


_EASYOCR_READER = None


def _get_shared_reader():
    """Module-level EasyOCR reader. Loading the model takes ~3-5s and
    allocates torch tensors; we only want to do this once per process."""
    global _EASYOCR_READER
    if _EASYOCR_READER is None:
        import easyocr
        _EASYOCR_READER = easyocr.Reader(['en', 'fr', 'de', 'it'], gpu=False)
    return _EASYOCR_READER


class OCRService:
    def __init__(self):
        self.engine = settings.OCR_ENGINE
        self.preprocessor = ImagePreprocessor()

    def _get_reader(self):
        return _get_shared_reader()
    
    def extract_text(
        self,
        candidate: ImageCandidate,
        crops: Dict[str, Optional[str]]
    ) -> OCRResult:
        all_texts = []
        all_confidences = []
        
        for crop_type, crop_path in crops.items():
            if not crop_path:
                continue
            
            try:
                enhanced_path = self.preprocessor.save_enhanced(crop_path, f"ocr_{crop_type}")
                text, confidence = self._run_ocr(enhanced_path)
                all_texts.append(text)
                all_confidences.append(confidence)
            except Exception as e:
                print(f"OCR error on {crop_type}: {e}")
                continue
        
        combined_text = " ".join(all_texts)
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0
        
        normalized_text = self._normalize_text(combined_text)
        tokens = self._extract_tokens(normalized_text)
        
        vintage = self._extract_vintage(combined_text)
        
        return OCRResult(
            raw_text=combined_text,
            normalized_text=normalized_text,
            tokens=tokens,
            vintage_found=vintage,
            confidence=avg_confidence
        )
    
    def _run_ocr(self, image_path: str) -> tuple[str, float]:
        if self.engine == "easyocr":
            return self._run_easyocr(image_path)
        else:
            return self._run_tesseract(image_path)
    
    def _run_easyocr(self, image_path: str) -> tuple[str, float]:
        reader = self._get_reader()
        results = reader.readtext(image_path)
        
        texts = []
        confidences = []
        
        for (bbox, text, conf) in results:
            if conf > 0.3:
                texts.append(text)
                confidences.append(conf)
        
        full_text = " ".join(texts)
        avg_conf = sum(confidences) / len(confidences) if confidences else 0
        
        return full_text, avg_conf
    
    def _run_tesseract(self, image_path: str) -> tuple[str, float]:
        import pytesseract
        from PIL import Image
        
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang='eng+fra+deu+ita')
        
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
        avg_conf = sum(confidences) / len(confidences) if confidences else 0
        
        return text, avg_conf / 100.0
    
    def _normalize_text(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r'[^\w\s\-\']', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _extract_tokens(self, text: str) -> List[str]:
        tokens = text.split()
        return [t for t in tokens if len(t) > 2]
    
    def _extract_vintage(self, text: str) -> Optional[str]:
        pattern = r'\b(19\d{2}|20\d{2})\b'
        matches = re.findall(pattern, text)
        if matches:
            return matches[0]
        return None
