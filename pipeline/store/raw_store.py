import json
import os
from typing import List, Dict, Any, Optional

from pipeline.config import settings

class RawStore:
    def __init__(self, data_dir: str = settings.data_dir):
        self.raw_dir = os.path.join(data_dir, "raw")
        os.makedirs(self.raw_dir, exist_ok=True)
        
    def _get_file_path(self, source: str) -> str:
        return os.path.join(self.raw_dir, f"{source}.jsonl")

    def upsert(self, item: Dict[str, Any]) -> None:
        """
        Idempotent write based on item_id. 
        Note: In-memory deduplication for small scale. 
        For larger scale, this would use a database.
        """
        source = item.get("source")
        if not source:
            raise ValueError("Item must have a 'source' field")
            
        file_path = self._get_file_path(source)
        
        # Read existing items
        items = {}
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        obj = json.loads(line)
                        items[obj["item_id"]] = obj
                        
        # Upsert
        items[item["item_id"]] = item
        
        # Write back
        with open(file_path, "w", encoding="utf-8") as f:
            for obj in items.values():
                f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    def get_all(self, source: Optional[str] = None) -> List[Dict[str, Any]]:
        """Read items, optionally filtered by source."""
        results = []
        
        sources_to_check = [source] if source else [
            f.replace(".jsonl", "") for f in os.listdir(self.raw_dir) if f.endswith(".jsonl")
        ]
        
        for src in sources_to_check:
            file_path = self._get_file_path(src)
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            results.append(json.loads(line))
        return results

    def count(self, source: Optional[str] = None) -> int:
        """Volume counts for funnel reporting."""
        return len(self.get_all(source))

raw_store = RawStore()
