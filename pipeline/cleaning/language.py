import logging
import time
from typing import List
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
from pipeline.connectors.base import RawItem

try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None

# For reproducible language detection
DetectorFactory.seed = 0

logger = logging.getLogger(__name__)

class LanguageProcessor:
    """Detects non-English text and translates it to English using deep-translator."""
    
    def __init__(self, batch_size=20):
        # We don't necessarily need batch_size for deep-translator in the same way,
        # but we can translate sequentially for simplicity and safety.
        self.translator = GoogleTranslator(source='auto', target='en') if GoogleTranslator else None
        
        if not self.translator:
            logger.warning("deep-translator library not installed. Translation will be skipped.")

    def _is_english(self, text: str) -> bool:
        if not text or len(text.strip()) < 5:
            return True # Too short to confidently say it's non-English, skip translating
            
        try:
            lang = detect(text)
            # We consider anything detected as english (en) as english.
            return lang == 'en'
        except LangDetectException:
            return True

    def process(self, items: List[RawItem]) -> List[RawItem]:
        """Detects language and translates non-English items using deep-translator."""
        if not self.translator:
            return items

        translated_count = 0
        
        for i, item in enumerate(items):
            if i > 0 and i % 500 == 0:
                logger.info(f"LanguageProcessor: processed {i}/{len(items)} items...")
                
            if "original_text" in item.metadata:
                continue
                
            if not self._is_english(item.text):
                original = item.text
                try:
                    # Translate item using Google Translator
                    translated_text = self.translator.translate(original)
                    
                    if translated_text and translated_text != original:
                        # Keep original in metadata and update the main text
                        item.metadata["original_text"] = original
                        item.text = translated_text
                        translated_count += 1
                        
                except Exception as e:
                    logger.error(f"Translation failed for item {item.item_id}: {e}")
                
                # Small sleep to prevent aggressive rate limiting from Google endpoints
                time.sleep(0.1)
                
        logger.info(f"LanguageProcessor: Detected and translated {translated_count} non-English items using deep-translator.")
        return items
