import argparse
import sys
import logging
from datetime import datetime, timezone, timedelta

from pipeline.connectors.play_store import PlayStoreConnector
from pipeline.connectors.app_store import AppStoreConnector
from pipeline.connectors.reddit import RedditConnector
from pipeline.connectors.youtube import YouTubeConnector
from pipeline.store.raw_store import raw_store

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("pipeline")

def get_connectors(sources_arg: str):
    connectors = []
    
    tier1 = [PlayStoreConnector(), AppStoreConnector(), RedditConnector(), YouTubeConnector()]
    
    if sources_arg == "all" or sources_arg == "tier1":
        connectors.extend(tier1)
    elif sources_arg == "playstore":
        connectors.append(PlayStoreConnector())
    elif sources_arg == "appstore":
        connectors.append(AppStoreConnector())
    elif sources_arg == "reddit":
        connectors.append(RedditConnector())
    elif sources_arg == "youtube":
        connectors.append(YouTubeConnector())
    else:
        logger.error(f"Unknown source argument: {sources_arg}")
        
    return connectors

def run_ingestion(sources_arg: str, limit: int):
    connectors = get_connectors(sources_arg)
    if not connectors:
        sys.exit(1)
        
    # 18-month recency window
    since_date = datetime.now(timezone.utc) - timedelta(days=18 * 30)
    
    logger.info(f"Starting ingestion for {len(connectors)} connectors with limit {limit} per source.")
    
    total_ingested = 0
    for connector in connectors:
        logger.info(f"--- Running {connector.source_name} ---")
        try:
            items = connector.fetch(since=since_date, limit=limit)
            logger.info(f"{connector.source_name}: Fetched {len(items)} items.")
            
            for item in items:
                # Convert dataclass to dict for storage
                item_dict = {
                    "source": item.source,
                    "item_id": item.item_id,
                    "text": item.text,
                    "timestamp": item.timestamp.isoformat(),
                    "rating": item.rating,
                    "url": item.url,
                    "metadata": item.metadata,
                    "ingested_at": datetime.now(timezone.utc).isoformat()
                }
                raw_store.upsert(item_dict)
                total_ingested += 1
                
        except Exception as e:
            logger.exception(f"Failed to ingest from {connector.source_name}: {e}")
            
    logger.info(f"Ingestion complete. Total items upserted: {total_ingested}")

def main():
    parser = argparse.ArgumentParser(description="Blinkit Discovery Engine Pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # run command
    run_parser = subparsers.add_parser("run", help="Run the ingestion pipeline")
    run_parser.add_argument("--sources", type=str, default="tier1", help="Sources to ingest (e.g., tier1, all, playstore, reddit)")
    run_parser.add_argument("--limit", type=int, default=100, help="Limit items per source")
    
    # audit-filter command
    audit_parser = subparsers.add_parser("audit-filter", help="Spot-check relevance filter output")
    
    args = parser.parse_args()

    if args.command == "run":
        run_ingestion(args.sources, args.limit)
    elif args.command == "audit-filter":
        print("Running filter audit... (To be implemented in Phase 3)")
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
