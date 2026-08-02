import json
import logging
import time
from typing import List, Dict, Any
import google.generativeai as genai
from groq import Groq

from pipeline.config import settings
from pipeline.connectors.base import RawItem
from pipeline.extraction.prompts import EXTRACTION_PROMPT

logger = logging.getLogger(__name__)

class Extractor:
    """Extracts structured taxonomy tags using Gemini as primary, Groq as fallback."""
    
    def __init__(self):
        # Primary: Gemini
        genai.configure(api_key=settings.gemini_api_key)
        self.gemini_model = genai.GenerativeModel("gemini-flash-latest", system_instruction=EXTRACTION_PROMPT)
        
        # Fallback: Groq
        self.groq_client = Groq(api_key=settings.groq_api_key)
        self.groq_model = "llama-3.3-70b-versatile"

    def _call_gemini(self, items: List[Dict]) -> List[Dict]:
        logger.info(f"Calling Gemini (primary) for {len(items)} items")
        prompt = json.dumps(items)
        response = self.gemini_model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.0
            )
        )
        data = json.loads(response.text)
        return data.get("results", [])
        
    def _call_groq(self, items: List[Dict]) -> List[Dict]:
        logger.info(f"Calling Groq (fallback) for {len(items)} items")
        prompt = json.dumps(items)
        response = self.groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": EXTRACTION_PROMPT},
                {"role": "user", "content": prompt}
            ],
            model=self.groq_model,
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        text = response.choices[0].message.content
        data = json.loads(text)
        return data.get("results", [])

    def process(self, items: List[RawItem]) -> List[RawItem]:
        """Process items and add metadata."""
        items_to_process = [
            item for item in items 
            if item.metadata.get("stage1_passed", False) 
            and not item.metadata.get("is_spam", False)
            and not item.metadata.get("extracted", False)
        ]
        
        if not items_to_process:
            logger.info("No items passed stage 1 for extraction (or all were already extracted).")
            return items

        BATCH_SIZE = 10
        total = len(items_to_process)
        processed_count = 0
        
        logger.info(f"Extractor: Starting extraction for {total} items")

        for i in range(0, total, BATCH_SIZE):
            batch = items_to_process[i:i+BATCH_SIZE]
            
            # Prepare payload
            payload = [{"id": item.item_id, "text": item.text} for item in batch]
            results = []
            
            try:
                # Primary: Gemini
                results = self._call_gemini(payload)
            except Exception as e:
                logger.warning(f"Gemini failed: {e}. Falling back to Groq.")
                try:
                    # Fallback: Groq
                    results = self._call_groq(payload)
                except Exception as e2:
                    logger.error(f"Groq fallback failed: {e2}")
                    # Skip this batch if both fail
                    continue
                    
            # Map results back to items
            result_map = {res.get("id"): res for res in results if isinstance(res, dict) and "id" in res}
            
            for item in batch:
                res = result_map.get(item.item_id)
                if res:
                    item.metadata.update(res)
                    item.metadata.pop('id', None)
                    item.metadata.pop('text', None)
                    item.metadata["extracted"] = True
                else:
                    item.metadata["extracted"] = False
            
            processed_count += len(batch)
            logger.info(f"Extractor progress: {processed_count}/{total} items processed.")
            time.sleep(1) # rate limiting
            
        return items
