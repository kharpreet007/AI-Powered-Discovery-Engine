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

    def upsert(self, item: Dict[str, Any]) -> None:
        source = item.get("source")
        if not source:
            raise ValueError("Item must have a 'source' field")
            
        file_path = self._get_file_path(source)
        
        items = {}
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        obj = json.loads(line)
                        items[obj["item_id"]] = obj
                        
        items[item["item_id"]] = item
        
        with open(file_path, "w", encoding="utf-8") as f:
            for obj in items.values():
                f.write(json.dumps(obj, ensure_ascii=False) + "\n")

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
