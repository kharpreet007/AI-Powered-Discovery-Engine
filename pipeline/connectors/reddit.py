"""
Reddit connector — direct HTTP calls to Arctic Shift and PullPush APIs.

Bypasses BAScraper library entirely because its v0.3 dict-based API
does not match the actual REST endpoints. We call httpx directly.

Strategy:
  - Intent-based searches driven by config for high-signal retrieval.
  - PullPush: /reddit/search/submission/ and /reddit/search/comment/ with "q" param
  - Arctic Shift: /api/posts/search with "title" param (fallback)
"""

import logging
import httpx
import asyncio
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple

from pipeline.connectors.base import RawItem, SourceConnector
from pipeline.config import REDDIT_DEFAULT_SUBREDDITS, REDDIT_INTENT_QUERIES

logger = logging.getLogger(__name__)

ARCTIC_SHIFT_BASE = "https://arctic-shift.photon-reddit.com/api"
PULLPUSH_BASE = "https://api.pullpush.io/reddit/search"
TIMEOUT = 30


class RedditConnector(SourceConnector):
    source_name = "reddit"
    tier = 1

    def __init__(self):
        # Keep sync client in case someone uses older helpers directly
        self.client = httpx.Client(timeout=TIMEOUT)

    def get_intent_queries(self) -> Dict[str, List[str]]:
        return REDDIT_INTENT_QUERIES

    def get_default_subreddits(self) -> List[str]:
        return REDDIT_DEFAULT_SUBREDDITS
        
    def build_search_plan(self) -> List[Tuple[str, str, str]]:
        """Returns a list of (intent_group, search_phrase, subreddit)."""
        plan = []
        queries = self.get_intent_queries()
        subreddits = self.get_default_subreddits()
        
        for intent_group, phrases in queries.items():
            for phrase in phrases:
                for sub in subreddits:
                    plan.append((intent_group, phrase, sub))
        return plan

    def fetch(self, since: datetime, limit: Optional[int] = None) -> List[RawItem]:
        """Fetch items synchronously but internally execute an async search plan."""
        return asyncio.run(self._async_fetch(since, limit))

    async def _async_fetch(self, since: datetime, limit: Optional[int] = None) -> List[RawItem]:
        after_epoch = int(since.timestamp())
        after_iso = since.strftime("%Y-%m-%d")
        per_query_limit = min(limit, 50) if limit else 50
        
        fetched_items: Dict[str, RawItem] = {}
        search_plan = self.build_search_plan()
        
        # If limit is set, shuffle the plan so we get a good variety of intents and subreddits,
        # but do NOT slice it, because many combinations return 0 items. We'll use early exit instead.
        if limit:
            import random
            random.shuffle(search_plan)
            
        logger.info(f"Starting Reddit fetch since {after_iso} with {len(search_plan)*2} async tasks.")
        
        # Use a semaphore to avoid hitting rate limits (PullPush and ArcticShift are very strict)
        semaphore = asyncio.Semaphore(2)
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as async_client:
            tasks = []
            for intent_group, query, subreddit in search_plan:
                tasks.append(self._fetch_posts_for_query(
                    async_client, semaphore, intent_group, query, subreddit, 
                    after_epoch, after_iso, per_query_limit, fetched_items, limit
                ))
                tasks.append(self._fetch_comments_for_query(
                    async_client, semaphore, intent_group, query, subreddit, 
                    after_epoch, per_query_limit, fetched_items, limit
                ))
                
            await asyncio.gather(*tasks, return_exceptions=True)

        results = list(fetched_items.values())
        if limit:
            results = results[:limit]
            
        if not results:
            logger.error("Reddit connector returned 0 items. APIs may be down.")
        logger.info(f"Finished fetching {len(results)} Reddit items (deduplicated).")
        return results

    async def _fetch_posts_for_query(self, client: httpx.AsyncClient, sem: asyncio.Semaphore, 
                                     intent_group: str, query: str, subreddit: str, 
                                     after_epoch: int, after_iso: str, limit: int, 
                                     store: Dict[str, RawItem], global_limit: Optional[int] = None):
        if global_limit and len(store) >= global_limit:
            return
            
        async with sem:
            if global_limit and len(store) >= global_limit:
                return
                
            try:
                data = await self._async_pullpush(client, "submission", query, subreddit, after_epoch, limit)
                self._parse_results(data, intent_group, query, store)
            except Exception as e:
                logger.debug(f"PullPush submission '{query}' r/{subreddit} failed: {e}. Trying Arctic Shift.")
                try:
                    data = await self._async_arctic_shift(client, "posts", query, subreddit, after_iso, limit)
                    self._parse_results(data, intent_group, query, store)
                except Exception as e2:
                    logger.debug(f"Both failed for post '{query}' r/{subreddit}: {e2}")

    async def _fetch_comments_for_query(self, client: httpx.AsyncClient, sem: asyncio.Semaphore, 
                                        intent_group: str, query: str, subreddit: str, 
                                        after_epoch: int, limit: int, 
                                        store: Dict[str, RawItem], global_limit: Optional[int] = None):
        if global_limit and len(store) >= global_limit:
            return
            
        async with sem:
            if global_limit and len(store) >= global_limit:
                return
                
            try:
                data = await self._async_pullpush(client, "comment", query, subreddit, after_epoch, limit)
                self._parse_results(data, intent_group, query, store)
            except Exception as e:
                logger.debug(f"PullPush comment '{query}' r/{subreddit} failed: {e}")

    # ── Async HTTP helpers ──────────────────────────────────────────────
    
    async def _async_pullpush(self, client: httpx.AsyncClient, endpoint: str, q: str, 
                              subreddit: Optional[str], after: int, limit: int) -> List[dict]:
        url = f"{PULLPUSH_BASE}/{endpoint}/"
        params: Dict[str, Any] = {"q": q, "after": after, "size": limit}
        if subreddit:
            params["subreddit"] = subreddit
        await asyncio.sleep(1.0)
        r = await client.get(url, params=params)
        r.raise_for_status()
        return r.json().get("data") or []

    async def _async_arctic_shift(self, client: httpx.AsyncClient, endpoint: str, title: str, 
                                  subreddit: str, after: str, limit: int) -> List[dict]:
        url = f"{ARCTIC_SHIFT_BASE}/{endpoint}/search"
        params = {"subreddit": subreddit, "title": title, "after": after, "limit": limit, "sort": "desc"}
        await asyncio.sleep(1.0)
        r = await client.get(url, params=params)
        r.raise_for_status()
        return r.json().get("data") or []

    # ── Parsing ──────────────────────────────────────────────────

    def _parse_results(self, items: List[Dict[str, Any]], intent_group: str, original_query: str, store: Dict[str, RawItem]):
        """Parse raw API dicts into RawItem objects and deduplicate metadata."""
        if not items:
            return
            
        for obj in items:
            item_id = obj.get("id", "")
            if not item_id:
                continue

            # Filter deleted/removed
            text = obj.get("body") or obj.get("selftext") or obj.get("title") or ""
            if text in ("[deleted]", "[removed]", ""):
                continue

            created_utc = obj.get("created_utc")
            if isinstance(created_utc, (int, float)):
                dt = datetime.fromtimestamp(created_utc, tz=timezone.utc)
            elif isinstance(created_utc, str):
                try:
                    dt = datetime.fromisoformat(created_utc.replace("Z", "+00:00"))
                except ValueError:
                    dt = datetime.now(timezone.utc)
            else:
                dt = datetime.now(timezone.utc)

            full_id = f"reddit_{item_id}"

            # If item exists, append query metadata and avoid duplication
            if full_id in store:
                existing_tags = store[full_id].metadata.get("query_tags", [])
                if intent_group not in existing_tags:
                    existing_tags.append(intent_group)
                if original_query not in existing_tags:
                    existing_tags.append(original_query)
                store[full_id].metadata["query_tags"] = existing_tags
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
                        "query_tags": [intent_group, original_query],
                        "subreddit": obj.get("subreddit"),
                        "author": obj.get("author"),
                        "score": obj.get("score")
                    }
                )
