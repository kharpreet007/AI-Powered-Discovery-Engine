import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from google_play_scraper import Sort, reviews

from pipeline.connectors.base import RawItem, SourceConnector

logger = logging.getLogger(__name__)

class PlayStoreConnector(SourceConnector):
    source_name = "playstore"
    tier = 1
    
    def __init__(self, app_id: str = "com.grofers.customerapp"):
        self.app_id = app_id

    def fetch(self, since: datetime, limit: Optional[int] = None) -> List[RawItem]:
        """Fetch reviews for the Blinkit (formerly Grofers) Android app."""
        fetched_items = []
        continuation_token = None
        count_per_request = 200
        
        logger.info(f"Fetching Play Store reviews for {self.app_id} since {since}")

        while True:
            batch, continuation_token = reviews(
                self.app_id,
                lang='en',
                country='in',
                sort=Sort.NEWEST,
                count=count_per_request,
                continuation_token=continuation_token
            )

            if not batch:
                break

            for review in batch:
                # review['at'] is a datetime object
                review_time = review.get('at')
                if review_time:
                    # ensure timezone awareness
                    if review_time.tzinfo is None:
                        review_time = review_time.replace(tzinfo=timezone.utc)
                else:
                    continue

                if review_time < since:
                    logger.info("Reached reviews older than the 'since' threshold.")
                    continuation_token = None  # Force exit outer loop
                    break

                item = RawItem(
                    source=self.source_name,
                    item_id=f"playstore_{review['reviewId']}",
                    text=review.get('content', ''),
                    timestamp=review_time,
                    rating=float(review.get('score', 0)),
                    url=None,  # Play store scraper doesn't give a direct link to the review easily
                    metadata={
                        "app_version": review.get("reviewCreatedVersion"),
                        "reviewer_name": review.get("userName"),
                        "thumbs_up_count": review.get("thumbsUpCount", 0),
                        "reply_content": review.get("replyContent"),
                        "reply_at": review.get("repliedAt")
                    }
                )
                fetched_items.append(item)

                if limit and len(fetched_items) >= limit:
                    logger.info(f"Reached specified limit of {limit} items.")
                    return fetched_items

            if not continuation_token:
                break

        logger.info(f"Finished fetching {len(fetched_items)} Play Store reviews.")
        return fetched_items
