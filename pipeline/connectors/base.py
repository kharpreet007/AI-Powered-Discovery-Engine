from typing import Protocol, List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class RawItem:
    source: str              # e.g. "playstore", "reddit", "youtube"
    item_id: str             # unique within source
    text: str                # raw user-generated text
    timestamp: datetime      # when the review/comment was posted
    rating: Optional[float]  # star rating if applicable
    url: Optional[str]       # link back to original
    metadata: Dict[str, Any] # source-specific fields (subreddit, product_category, etc.)

class SourceConnector(Protocol):
    source_name: str
    tier: int  # 1 or 2

    def fetch(self, since: datetime, limit: Optional[int] = None) -> List[RawItem]:
        """Fetch items from this source. Idempotent — re-fetching same items is safe."""
        ...
