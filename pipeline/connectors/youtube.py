import logging
from datetime import datetime, timezone
from typing import List, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from pipeline.connectors.base import RawItem, SourceConnector
from pipeline.config import settings

logger = logging.getLogger(__name__)

class YouTubeConnector(SourceConnector):
    source_name = "youtube"
    tier = 1

    def __init__(self, developer_key: str = settings.youtube_api_key):
        self.developer_key = developer_key
        if not self.developer_key:
            logger.warning("YouTube API key is missing. Connector will fail if run.")
            self.youtube = None
        else:
            self.youtube = build("youtube", "v3", developerKey=self.developer_key)

    def fetch(self, since: datetime, limit: Optional[int] = None) -> List[RawItem]:
        """Fetch YouTube comments for Blinkit-related videos."""
        if not self.youtube:
            raise ValueError("YouTube API key not configured.")

        # Search for Blinkit videos
        try:
            search_response = self.youtube.search().list(
                q="blinkit review OR blinkit delivery OR blinkit 10 min",
                part="id,snippet",
                maxResults=10, # fetch top 10 videos
                type="video",
                publishedAfter=since.isoformat("T") + "Z" if since.tzinfo else since.isoformat() + "Z"
            ).execute()
        except HttpError as e:
            logger.error(f"YouTube search API error: {e}")
            return []

        videos = []
        for search_result in search_response.get("items", []):
            videos.append({
                "video_id": search_result["id"]["videoId"],
                "title": search_result["snippet"]["title"]
            })

        fetched_items = []
        fetch_limit = limit if limit else 1000

        # Fetch comments for each video
        for video in videos:
            if len(fetched_items) >= fetch_limit:
                break
                
            video_id = video["video_id"]
            video_title = video["title"]
            
            next_page_token = None
            while True:
                if len(fetched_items) >= fetch_limit:
                    break
                    
                try:
                    results = self.youtube.commentThreads().list(
                        part="snippet",
                        videoId=video_id,
                        textFormat="plainText",
                        maxResults=100,
                        pageToken=next_page_token
                    ).execute()
                except HttpError as e:
                    # e.g., comments disabled on this video
                    logger.warning(f"Failed to fetch comments for video {video_id}: {e}")
                    break

                for item in results.get("items", []):
                    if len(fetched_items) >= fetch_limit:
                        break
                        
                    comment = item["snippet"]["topLevelComment"]["snippet"]
                    comment_id = item["snippet"]["topLevelComment"]["id"]
                    text = comment["textDisplay"]
                    published_at_str = comment["publishedAt"]
                    
                    try:
                        # e.g. "2021-08-30T09:23:02Z"
                        dt = datetime.strptime(published_at_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                    except ValueError:
                        dt = datetime.now(timezone.utc)

                    if dt < since:
                        continue

                    raw_item = RawItem(
                        source=self.source_name,
                        item_id=f"youtube_{comment_id}",
                        text=text,
                        timestamp=dt,
                        rating=None,
                        url=f"https://www.youtube.com/watch?v={video_id}&lc={comment_id}",
                        metadata={
                            "video_id": video_id,
                            "video_title": video_title,
                            "author": comment.get("authorDisplayName"),
                            "like_count": comment.get("likeCount", 0)
                        }
                    )
                    fetched_items.append(raw_item)
                    
                next_page_token = results.get("nextPageToken")
                if not next_page_token:
                    break

        logger.info(f"Finished fetching {len(fetched_items)} YouTube comments.")
        return fetched_items
