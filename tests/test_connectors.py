import pytest
import sys
from unittest.mock import MagicMock

# Mock heavy dependencies that might not be installed in the current environment
sys.modules['google_play_scraper'] = MagicMock()
sys.modules['app_store_scraper'] = MagicMock()
sys.modules['googleapiclient'] = MagicMock()
sys.modules['googleapiclient.discovery'] = MagicMock()
sys.modules['googleapiclient.errors'] = MagicMock()

class MockBaseSettings:
    def __init__(self, **kwargs):
        pass
        
mock_pydantic_settings = MagicMock()
mock_pydantic_settings.BaseSettings = MockBaseSettings
mock_pydantic_settings.SettingsConfigDict = MagicMock()
sys.modules['pydantic_settings'] = mock_pydantic_settings

from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock, AsyncMock

from pipeline.connectors.base import RawItem
from pipeline.connectors.play_store import PlayStoreConnector
from pipeline.connectors.app_store import AppStoreConnector
from pipeline.connectors.youtube import YouTubeConnector
from pipeline.connectors.reddit import RedditConnector

@pytest.fixture
def recent_date():
    return datetime.now(timezone.utc) - timedelta(days=30)

@pytest.fixture
def old_date():
    return datetime.now(timezone.utc) - timedelta(days=600)  # ~20 months

def test_play_store_connector_filters_old_reviews(recent_date, old_date):
    """Ensure recency window filters out content older than 18 months."""
    connector = PlayStoreConnector()
    
    mock_reviews = [
        {"reviewId": "1", "content": "Recent", "at": recent_date, "score": 5},
        {"reviewId": "2", "content": "Old", "at": old_date, "score": 1}
    ]
    
    with patch("pipeline.connectors.play_store.reviews", return_value=(mock_reviews, None)):
        items = connector.fetch(since=recent_date - timedelta(days=100))
        assert len(items) == 1
        assert items[0].item_id == "playstore_1"

def test_youtube_returns_comments(recent_date):
    """Ensure YouTube connector returns comments (not just video metadata)."""
    connector = YouTubeConnector(developer_key="dummy")
    
    # Mocking the discovery client
    mock_youtube = MagicMock()
    connector.youtube = mock_youtube
    
    # Mock search response (videos)
    mock_search_request = MagicMock()
    mock_search_request.execute.return_value = {
        "items": [
            {"id": {"videoId": "v1"}, "snippet": {"title": "Test Video"}}
        ]
    }
    mock_youtube.search().list.return_value = mock_search_request
    
    # Mock comment threads response
    mock_comment_request = MagicMock()
    mock_comment_request.execute.return_value = {
        "items": [
            {
                "snippet": {
                    "topLevelComment": {
                        "id": "c1",
                        "snippet": {
                            "textDisplay": "Great video!",
                            "publishedAt": recent_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "authorDisplayName": "User1",
                            "likeCount": 10
                        }
                    }
                }
            }
        ]
    }
    mock_youtube.commentThreads().list.return_value = mock_comment_request

    items = connector.fetch(since=recent_date - timedelta(days=10))
    assert len(items) == 1
    assert items[0].text == "Great video!"
    assert items[0].metadata["video_id"] == "v1"

@pytest.mark.asyncio
async def test_reddit_deduplicates_query_sets(recent_date):
    """Ensure Reddit connector deduplicates across both query sets."""
    connector = RedditConnector()
    
    # Create identical item from two different queries
    item_dict = {
        "id": "post123",
        "title": "Blinkit is fast",
        "created_utc": recent_date.timestamp(),
        "subreddit": "india",
        "url": "http://reddit.com/post123"
    }

    # Mock parse method since we only want to test the parsing/dedup logic directly
    store = {}
    connector._parse_bascraper_results([item_dict], "branded", store)
    connector._parse_bascraper_results([item_dict], "quick_commerce", store)
    
    assert len(store) == 1
    full_id = "reddit_post123"
    assert full_id in store
    assert "branded" in store[full_id].metadata["query_sets"]
    assert "quick_commerce" in store[full_id].metadata["query_sets"]

@patch("pipeline.connectors.reddit.PullPushAsync")
@patch("pipeline.connectors.reddit.ArcticShiftAsync")
def test_reddit_fallback_logic(mock_asa_cls, mock_ppa_cls, recent_date):
    """Ensure Reddit connector falls back to PullPush when Arctic Shift errors."""
    connector = RedditConnector()
    
    mock_asa = AsyncMock()
    mock_ppa = AsyncMock()
    mock_asa_cls.return_value = mock_asa
    mock_ppa_cls.return_value = mock_ppa
    
    # Force Arctic Shift to raise an exception
    mock_asa.fetch.side_effect = Exception("Arctic Shift is down")
    
    # PullPush returns a valid item
    mock_ppa.fetch.return_value = [{
        "id": "fallback1",
        "title": "Worked via fallback",
        "created_utc": recent_date.timestamp(),
        "subreddit": "india"
    }]
    
    # We use a very limited target set to avoid huge mock loops
    with patch("pipeline.connectors.reddit.BRANDED_QUERIES", ["blinkit"]):
        with patch("pipeline.connectors.reddit.TARGET_SUBREDDITS", ["india"]):
            with patch("pipeline.connectors.reddit.QUICK_COMMERCE_QUERIES", []):
                import asyncio
                items = asyncio.run(connector._fetch_async(since=recent_date - timedelta(days=10)))
    
    # The item should still be fetched despite AS failing
    assert len(items) > 0
    assert items[0].item_id == "reddit_fallback1"
    # Ensure PullPush was actually called
    mock_ppa.fetch.assert_called()
