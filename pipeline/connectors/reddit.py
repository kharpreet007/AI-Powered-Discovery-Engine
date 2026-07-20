import logging
import asyncio
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from pipeline.connectors.base import RawItem, SourceConnector

# BAScraper might not be installed in all environments during dry-runs, so we handle imports safely
try:
    from BAScraper.BAScraper_async import PullPushAsync, ArcticShiftAsync
except ImportError:
    PullPushAsync, ArcticShiftAsync = None, None

logger = logging.getLogger(__name__)

TARGET_SUBREDDITS = [
    "india", "bangalore", "mumbai", "delhi", "pune", "hyderabad", 
    "gurgaon", "noida", "IndianFoodPhotography"
]

BRANDED_QUERIES = [
    "blinkit", "blinkit review", "blinkit delivery", "blinkit app", "blinkit scam"
]

QUICK_COMMERCE_QUERIES = [
    "quick commerce india", "instant delivery grocery", "10 minute delivery",
    "swiggy instamart", "zepto"
]

class RedditConnector(SourceConnector):
    source_name = "reddit"
    tier = 1

    def __init__(self):
        if not PullPushAsync:
            logger.warning("BAScraper not installed. Reddit connector will fail if run.")
            
    def fetch(self, since: datetime, limit: Optional[int] = None) -> List[RawItem]:
        """Fetch Reddit posts and comments using BAScraper (Arctic Shift + PullPush)."""
        if not PullPushAsync:
            raise ImportError("BAScraper is required for RedditConnector. Install it via pip.")
            
        return asyncio.run(self._fetch_async(since, limit))

    async def _fetch_async(self, since: datetime, limit: Optional[int] = None) -> List[RawItem]:
        # Formats for BAScraper: ISO strings
        after_str = since.isoformat()
        
        fetched_items = {} # Use dict to deduplicate by ID
        
        ppa = PullPushAsync(log_stream_level="WARNING", task_num=5)
        asa = ArcticShiftAsync(log_stream_level="WARNING", task_num=5)

        logger.info(f"Fetching Reddit data since {after_str}")

        # 1. Branded Queries -> Arctic Shift (Fallback to PullPush)
        for query in BRANDED_QUERIES:
            for sub in TARGET_SUBREDDITS:
                # Submissions
                try:
                    res = await asa.fetch(
                        mode='submissions_search', subreddit=sub, title=query, 
                        after=after_str, limit=limit if limit else 100
                    )
                    self._parse_bascraper_results(res, "branded", fetched_items)
                except Exception as e:
                    logger.warning(f"Arctic Shift submission query failed for '{query}' in r/{sub}: {e}. Falling back to PullPush.")
                    try:
                        res = await ppa.fetch(
                            mode='submissions', subreddit=sub, q=query, 
                            after=after_str, limit=limit if limit else 100
                        )
                        self._parse_bascraper_results(res, "branded", fetched_items)
                    except Exception as e2:
                        logger.error(f"Both mirrors failed for submission query '{query}' in r/{sub}.")

                # Comments
                try:
                    res = await asa.fetch(
                        mode='comments_search', subreddit=sub, body=query, 
                        after=after_str, limit=limit if limit else 100
                    )
                    self._parse_bascraper_results(res, "branded", fetched_items)
                except Exception as e:
                    logger.warning(f"Arctic Shift comment query failed for '{query}' in r/{sub}: {e}. Falling back to PullPush.")
                    try:
                        res = await ppa.fetch(
                            mode='comments', subreddit=sub, q=query, 
                            after=after_str, limit=limit if limit else 100
                        )
                        self._parse_bascraper_results(res, "branded", fetched_items)
                    except Exception as e2:
                        logger.error(f"Both mirrors failed for comment query '{query}' in r/{sub}.")
        
        # 2. Quick Commerce Queries -> PullPush (Fallback to Arctic Shift over target subreddits)
        for query in QUICK_COMMERCE_QUERIES:
            # Submissions
            try:
                res = await ppa.fetch(
                    mode='submissions', q=query, 
                    after=after_str, limit=limit if limit else 100
                )
                self._parse_bascraper_results(res, "quick_commerce", fetched_items)
            except Exception as e:
                logger.warning(f"PullPush submission query failed for '{query}': {e}. Falling back to Arctic Shift over target subs.")
                for sub in TARGET_SUBREDDITS:
                    try:
                        res = await asa.fetch(
                            mode='submissions_search', subreddit=sub, title=query, 
                            after=after_str, limit=limit if limit else 100
                        )
                        self._parse_bascraper_results(res, "quick_commerce", fetched_items)
                    except Exception as e2:
                        logger.error(f"Both mirrors failed for submission query '{query}' in fallback r/{sub}.")
            
            # Comments
            try:
                res = await ppa.fetch(
                    mode='comments', q=query, 
                    after=after_str, limit=limit if limit else 100
                )
                self._parse_bascraper_results(res, "quick_commerce", fetched_items)
            except Exception as e:
                logger.warning(f"PullPush comment query failed for '{query}': {e}. Falling back to Arctic Shift over target subs.")
                for sub in TARGET_SUBREDDITS:
                    try:
                        res = await asa.fetch(
                            mode='comments_search', subreddit=sub, body=query, 
                            after=after_str, limit=limit if limit else 100
                        )
                        self._parse_bascraper_results(res, "quick_commerce", fetched_items)
                    except Exception as e2:
                        logger.error(f"Both mirrors failed for comment query '{query}' in fallback r/{sub}.")

        results = list(fetched_items.values())
        if not results:
            logger.error("Reddit connector returned 0 items. Both mirrors may be unreachable.")
            
        logger.info(f"Finished fetching {len(results)} Reddit items (deduplicated).")
        return results

    def _parse_bascraper_results(self, items: List[Dict[str, Any]], query_set: str, store: Dict[str, RawItem]):
        """Parse raw BAScraper dictionaries into RawItem objects and deduplicate."""
        if not items:
            return
            
        for obj in items:
            item_id = obj.get("id", "")
            if not item_id:
                continue
                
            # Filter out deleted/removed content per edge cases
            text = obj.get("body") or obj.get("selftext") or obj.get("title") or ""
            if text in ("[deleted]", "[removed]", ""):
                continue
                
            created_utc = obj.get("created_utc")
            if isinstance(created_utc, (int, float)):
                dt = datetime.fromtimestamp(created_utc, tz=timezone.utc)
            elif isinstance(created_utc, str):
                try:
                    # simplistic fallback parsing
                    dt = datetime.fromisoformat(created_utc.replace("Z", "+00:00"))
                except ValueError:
                    dt = datetime.now(timezone.utc)
            else:
                dt = datetime.now(timezone.utc)
                
            full_id = f"reddit_{item_id}"
            
            if full_id in store:
                # Deduplicate: merge query_sets
                existing_sets = store[full_id].metadata.get("query_sets", [])
                if query_set not in existing_sets:
                    existing_sets.append(query_set)
                    store[full_id].metadata["query_sets"] = existing_sets
            else:
                url = obj.get("url") or obj.get("permalink")
                if url and not url.startswith("http"):
                    url = f"https://reddit.com{url}"
                    
                store[full_id] = RawItem(
                    source=self.source_name,
                    item_id=full_id,
                    text=text,
                    timestamp=dt,
                    rating=None,
                    url=url,
                    metadata={
                        "query_sets": [query_set],
                        "subreddit": obj.get("subreddit"),
                        "author": obj.get("author"),
                        "score": obj.get("score")
                    }
                )
