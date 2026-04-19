import json
from typing import Optional, Dict, Any
import base64

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from app.models.sku import ParsedSKU
from app.models.candidate import VLMVerification
from app.core.config import settings


class GeminiVerifier:
    def __init__(self):
        # Check if GEMINI_API_KEY is a real key or placeholder
        gemini_key = settings.GEMINI_API_KEY
        is_gemini_placeholder = not gemini_key or gemini_key.startswith("your_") or len(gemini_key) < 20
        
        # Prioritize OpenRouter when Gemini key is not valid
        if not is_gemini_placeholder:
            # Use native Gemini API
            self.api_key = gemini_key
            self.use_openrouter = False
            self.model_name = settings.GEMINI_MODEL
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
        elif settings.OPENROUTER_API_KEY:
            # Use OpenRouter
            self.api_key = settings.OPENROUTER_API_KEY
            self.use_openrouter = True
            self.model_name = settings.OPENROUTER_MODEL or "google/gemini-2.0-flash-001"
            self.base_url = settings.OPENROUTER_BASE_URL or "https://openrouter.ai/api/v1"
            self.model = None  # Will use httpx for OpenRouter
        else:
            # No API available
            self.api_key = None
            self.use_openrouter = False
            self.model = None
    
    def is_available(self) -> bool:
        return self.api_key is not None
    
    async def verify(
        self,
        candidate_path: str,
        parsed_sku: ParsedSKU,
        ocr_text: str
    ) -> VLMVerification:
        if not self.api_key:
            return VLMVerification(
                is_real_photo=False,
                reasoning_summary="Gemini API not configured"
            )
        
        prompt = self._build_prompt(parsed_sku, ocr_text)
        
        try:
            with open(candidate_path, 'rb') as f:
                image_data = f.read()
            
            # Use OpenRouter if configured
            if self.use_openrouter:
                return await self._verify_openrouter(prompt, image_data)
            
            # Use native Gemini API
            image_parts = [
                {
                    "mime_type": "image/jpeg",
                    "data": image_data
                }
            ]
            
            response = self.model.generate_content(
                [prompt, image_parts[0]],
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            result = self._parse_response(response.text)
            return VLMVerification(
                is_real_photo=result.get("is_real_photo", False),
                single_bottle=result.get("single_bottle", False),
                background_ok=result.get("background_ok", False),
                producer_match=result.get("producer_match", False),
                appellation_match=result.get("appellation_match", False),
                vineyard_match=result.get("vineyard_match", False),
                vintage_match=result.get("vintage_match", False),
                classification_match=result.get("classification_match", False),
                reasoning_summary=result.get("reasoning", ""),
                confidence=result.get("confidence", 0.0),
                raw_response=response.text
            )
            
        except Exception as e:
            return VLMVerification(
                is_real_photo=False,
                reasoning_summary=f"Gemini error: {str(e)[:100]}"
            )
    
    def _build_prompt(self, parsed_sku: ParsedSKU, ocr_text: str) -> str:
        fields = []
        if parsed_sku.producer:
            fields.append(f"Producer: {parsed_sku.producer}")
        if parsed_sku.appellation:
            fields.append(f"Appellation: {parsed_sku.appellation}")
        if parsed_sku.vineyard:
            fields.append(f"Vineyard/Climat: {parsed_sku.vineyard}")
        if parsed_sku.classification:
            fields.append(f"Classification: {parsed_sku.classification}")
        if parsed_sku.vintage:
            fields.append(f"Vintage: {parsed_sku.vintage}")
        
        target_info = "\n".join(fields)
        
        prompt = f"""Analyze this wine bottle image and determine if it matches the target wine.

TARGET WINE:
{target_info}

OCR TEXT EXTRACTED FROM IMAGE:
{ocr_text}

Evaluate the following and respond in JSON format:

{{
  "is_real_photo": true/false,
  "single_bottle": true/false,
  "background_ok": true/false,
  "producer_match": true/false,
  "producer_found": "producer name on label or null",
  "appellation_match": true/false,
  "appellation_found": "appellation on label or null",
  "vineyard_match": true/false,
  "vineyard_found": "vineyard/climat on label or null",
  "vintage_match": true/false,
  "vintage_found": "vintage on label or null",
  "classification_match": true/false,
  "classification_found": "classification on label or null",
  "reasoning": "brief explanation of your judgment",
  "confidence": 0.0-1.0
}}

Rules:
- is_real_photo: Image must be a photograph of a real wine bottle, not AI-generated or a drawing
- single_bottle: Only one bottle should be clearly visible
- background_ok: Background should be clean (white, neutral, or simple), not restaurant/shelf scenes
- For each match field: Compare label text carefully to target. Partial matches are acceptable if the core identity matches.
- Be conservative: when in doubt, return false for match fields
- Confidence should reflect your certainty in the overall match"""
        
        return prompt
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        try:
            text = response_text.strip()
            
            if "```json" in text:
                json_start = text.find("```json") + 7
                json_end = text.find("```", json_start)
                text = text[json_start:json_end].strip()
            elif "```" in text:
                json_start = text.find("```") + 3
                json_end = text.find("```", json_start)
                text = text[json_start:json_end].strip()
            
            return json.loads(text)
        except Exception as e:
            print(f"Failed to parse Gemini response: {e}")
            print(f"Response was: {response_text[:500]}")
            
            result = {
                "is_real_photo": "real photo" in response_text.lower() or "photograph" in response_text.lower(),
                "single_bottle": "single" in response_text.lower() or "one bottle" in response_text.lower(),
                "background_ok": "clean" in response_text.lower() or "neutral" in response_text.lower(),
                "producer_match": "producer" in response_text.lower() and "match" in response_text.lower(),
                "appellation_match": "appellation" in response_text.lower() and "match" in response_text.lower(),
                "vineyard_match": True,
                "vintage_match": "vintage" in response_text.lower() and "match" in response_text.lower(),
                "classification_match": True,
                "reasoning": response_text[:200],
                "confidence": 0.5
            }
            return result
    
    async def _verify_openrouter(self, prompt: str, image_data: bytes) -> VLMVerification:
        """Use OpenRouter API for vision models."""
        import httpx
        
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://wine-photo-pipeline.local",
            "X-Title": "Wine Photo Verification"
        }
        
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
                        }
                    ]
                }
            ],
            "max_tokens": 1024
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            response_text = data["choices"][0]["message"]["content"]
            result = self._parse_response(response_text)
            
            return VLMVerification(
                is_real_photo=result.get("is_real_photo", False),
                single_bottle=result.get("single_bottle", False),
                background_ok=result.get("background_ok", False),
                producer_match=result.get("producer_match", False),
                appellation_match=result.get("appellation_match", False),
                vineyard_match=result.get("vineyard_match", False),
                vintage_match=result.get("vintage_match", False),
                classification_match=result.get("classification_match", False),
                reasoning_summary=result.get("reasoning", ""),
                confidence=result.get("confidence", 0.0),
                raw_response=response_text
            )
