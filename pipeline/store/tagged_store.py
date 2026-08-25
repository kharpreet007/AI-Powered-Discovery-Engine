import json
import os
from typing import List, Dict, Any, Optional

from pipeline.config import settings

class TaggedStore:
    def __init__(self, data_dir: str = settings.data_dir):
        self.tagged_dir = os.path.join(data_dir, "tagged")
        os.makedirs(self.tagged_dir, exist_ok=True)
        
    def _get_file_path(self, source: str) -> str:
        return os.path.join(self.tagged_dir, f"{source}.jsonl")

    def upsert_batch(self, new_items: List[Dict[str, Any]]) -> None:
        """Idempotent batch write based on item_id with atomic file replacement."""
        if not new_items:
            return
            
        # Group by source
        source_groups = {}
        for item in new_items:
            source = item.get("source")
            if not source:
                continue
            if source not in source_groups:
                source_groups[source] = []
            source_groups[source].append(item)
            
        for source, items_for_source in source_groups.items():
            file_path = self._get_file_path(source)
            items_dict = {}
            
            # Read existing items safely
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            try:
                                obj = json.loads(line)
                                items_dict[obj["item_id"]] = obj
                            except json.JSONDecodeError:
                                pass # Skip corrupt lines from previous bad writes
                                
            # Upsert new items
            for item in items_for_source:
                items_dict[item["item_id"]] = item
                
            # Write atomically to prevent data loss on kill/timeout
            tmp_path = file_path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                for obj in items_dict.values():
                    f.write(json.dumps(obj, ensure_ascii=False) + "\n")
            os.replace(tmp_path, file_path)

    def upsert(self, item: Dict[str, Any]) -> None:
        """Single item upsert wrapper for backwards compatibility."""
        self.upsert_batch([item])

    def get_all(self, source: Optional[str] = None) -> List[Dict[str, Any]]:
        results = []
        if not os.path.exists(self.tagged_dir):
            return results
            
        sources_to_check = [source] if source else [
            f.replace(".jsonl", "") for f in os.listdir(self.tagged_dir) if f.endswith(".jsonl")
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
        return len(self.get_all(source))

tagged_store = TaggedStore()
