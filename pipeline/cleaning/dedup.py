import hashlib
import re
from typing import List, Set
import logging
from pipeline.connectors.base import RawItem

logger = logging.getLogger(__name__)

class Deduplicator:
    """Removes exact and near-exact duplicate items across sources."""
    
    def __init__(self):
        self.seen_hashes: Set[str] = set()
        
    def _normalize_text(self, text: str) -> str:
        """Lowercase, strip non-alphanumeric, and collapse whitespace."""
        if not text:
            return ""
        text = text.lower()
        # Keep only alphanumeric and space
        text = re.sub(r'[^a-z0-9\s]', '', text)
        # Collapse multiple spaces
        text = re.sub(r'\s+', ' ', text).strip()
        return text
        
    def _hash_text(self, text: str) -> str:
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def process(self, items: List[RawItem]) -> List[RawItem]:
        """Filters out duplicates, keeping the first occurrence."""
        unique_items = []
        duplicates_removed = 0
        
        for item in items:
            normalized = self._normalize_text(item.text)
            
            # Extremely short texts (e.g. "ok") might overlap coincidentally, 
            # but deduplicating them is fine as they offer low value anyway.
            text_hash = self._hash_text(normalized)
            
            if text_hash in self.seen_hashes:
                duplicates_removed += 1
                continue
                
            self.seen_hashes.add(text_hash)
            unique_items.append(item)
            
        logger.info(f"Deduplicator: Removed {duplicates_removed} duplicates.")
        return unique_items
