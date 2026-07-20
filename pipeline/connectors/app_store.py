import logging
from datetime import datetime, timezone
from typing import List, Optional
from app_store_scraper import AppStore

from pipeline.connectors.base import RawItem, SourceConnector

logger = logging.getLogger(__name__)

class AppStoreConnector(SourceConnector):
    source_name = "appstore"
    tier = 1
    
    def __init__(self, app_name: str = "blinkit", app_id: str = "1044431520", country: str = "in"):
        self.app_name = app_name
        self.app_id = app_id
        self.country = country

    def fetch(self, since: datetime, limit: Optional[int] = None) -> List[RawItem]:
        """Fetch reviews for the Blinkit iOS app."""
        logger.info(f"Fetching App Store reviews for {self.app_name} ({self.country}) since {since}")
        
        # We specify how_many to prevent fetching all history if not needed
        # We fetch in batches or use after filter.
        # app_store_scraper doesn't natively support a datetime cutoff in the fetch call, 
        # so we fetch a chunk and filter. If we need more, we'd have to manage pagination, 
        # but the scraper handles fetching internally when we pass `how_many`.
        
        fetch_limit = limit if limit else 2000
        
        app = AppStore(country=self.country, app_name=self.app_name, app_id=self.app_id)
        
        # after argument takes a datetime object
        app.review(how_many=fetch_limit, after=since)
        
        fetched_items = []
        
        for review in app.reviews:
            review_time = review.get('date')
            if review_time:
                if review_time.tzinfo is None:
                    review_time = review_time.replace(tzinfo=timezone.utc)
            
            # Additional safety check
            if review_time and review_time < since:
                continue
                
            item = RawItem(
                source=self.source_name,
                item_id=f"appstore_{review.get('id')}",
                text=review.get('review', ''),
                timestamp=review_time,
                rating=float(review.get('rating', 0)),
                url=None,
                metadata={
                    "reviewer_name": review.get("userName"),
                    "title": review.get("title"),
                    "developer_response": review.get("developerResponse")
                }
            )
            fetched_items.append(item)
            
        logger.info(f"Finished fetching {len(fetched_items)} App Store reviews.")
        return fetched_items
