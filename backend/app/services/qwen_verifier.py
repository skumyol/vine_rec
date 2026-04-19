import json
from typing import Optional, Dict, Any
import base64

import httpx

from app.models.sku import ParsedSKU
from app.models.candidate import VLMVerification
from app.core.config import settings


class QwenVerifier:
    def __init__(self):
        # Check if QWEN_API_KEY is a real key or placeholder
        qwen_key = settings.QWEN_API_KEY
        is_qwen_placeholder = not qwen_key or qwen_key.startswith("your_") or len(qwen_key) < 20
        
        # Prioritize OpenRouter when available and Qwen is not configured
        if not is_qwen_placeholder:
            # Use native Qwen API
            self.api_key = qwen_key
            self.use_openrouter = False
            self.base_url = settings.QWEN_BASE_URL or "https://dashscope.aliyuncs.com/api/v1"
            self.model_name = settings.QWEN_MODEL
        elif settings.OPENROUTER_API_KEY:
            # Use OpenRouter
            self.api_key = settings.OPENROUTER_API_KEY
            self.use_openrouter = True
            self.base_url = settings.OPENROUTER_BASE_URL
            self.model_name = settings.OPENROUTER_MODEL
        else:
            # No API available
            self.api_key = None
            self.use_openrouter = False
            self.base_url = settings.QWEN_BASE_URL or "https://dashscope.aliyuncs.com/api/v1"
            self.model_name = settings.QWEN_MODEL
    
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
                reasoning_summary="Qwen API not configured"
            )
        
        prompt = self._build_prompt(parsed_sku, ocr_text)
        
        try:
            with open(candidate_path, 'rb') as f:
                image_data = f.read()
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            if self.use_openrouter:
                # OpenRouter uses standard OpenAI-compatible format
                headers["HTTP-Referer"] = "https://wine-verify.local"
                headers["X-Title"] = "Wine Photo Verification"
                
                payload = {
                    "model": self.model_name,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_b64}"
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": prompt
                                }
                            ]
                        }
                    ]
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=60.0
                    )
                    response.raise_for_status()
                    data = response.json()
                
                response_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            else:
                # Native Qwen API format
                payload = {
                    "model": self.model_name,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_b64}"
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": prompt
                                }
                            ]
                        }
                    ]
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}/services/aigc/multimodal-generation/generation",
                        headers=headers,
                        json=payload,
                        timeout=60.0
                    )
                    response.raise_for_status()
                    data = response.json()
                
                response_text = data.get("output", {}).get("choices", [{}])[0].get("message", {}).get("content", "")
            
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
            
        except Exception as e:
            return VLMVerification(
                is_real_photo=False,
                reasoning_summary=f"Qwen error: {str(e)[:100]}"
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

Evaluate the following and respond ONLY in JSON format:

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
- Confidence should reflect your certainty in the overall match
- Output ONLY valid JSON, no markdown formatting"""
        
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
            print(f"Failed to parse Qwen response: {e}")
            print(f"Response was: {response_text[:500]}")
            
            return {
                "is_real_photo": "real" in response_text.lower() and "photo" in response_text.lower(),
                "single_bottle": "single" in response_text.lower(),
                "background_ok": "clean" in response_text.lower() or "good" in response_text.lower(),
                "producer_match": "match" in response_text.lower(),
                "appellation_match": "match" in response_text.lower(),
                "vineyard_match": True,
                "vintage_match": "match" in response_text.lower(),
                "classification_match": True,
                "reasoning": response_text[:200],
                "confidence": 0.5
            }
