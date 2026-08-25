import argparse
import sys
import logging
from datetime import datetime, timezone, timedelta

from pipeline.connectors.play_store import PlayStoreConnector
from pipeline.connectors.app_store import AppStoreConnector
from pipeline.connectors.reddit import RedditConnector
from pipeline.connectors.youtube import YouTubeConnector
from pipeline.store.raw_store import raw_store
from pipeline.cleaning.dedup import Deduplicator
from pipeline.cleaning.language import LanguageProcessor
from pipeline.cleaning.spam import SpamFilter
from pipeline.filtering.rules import RuleBasedFilter
from pipeline.extraction.extractor import Extractor
from pipeline.embedding.embedder import Embedder
from pipeline.store.tagged_store import tagged_store
from pipeline.connectors.base import RawItem
import shutil
import os
from pipeline.config import settings

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
            
            items_to_upsert = []
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
                items_to_upsert.append(item_dict)
                total_ingested += 1
                
            if items_to_upsert:
                raw_store.upsert_batch(items_to_upsert)
                
        except Exception as e:
            logger.exception(f"Failed to ingest from {connector.source_name}: {e}")
            
    logger.info(f"Ingestion complete. Total items upserted: {total_ingested}")

def run_cleaning():
    logger.info("Starting Phase 3: Cleaning & Relevance Filter")
    raw_dicts = raw_store.get_all()
    logger.info(f"Loaded {len(raw_dicts)} raw items from store.")
    
    if not raw_dicts:
        logger.warning("No items to clean.")
        return
        
    # Convert dicts back to RawItem dataclasses
    items = []
    for d in raw_dicts:
        # Convert ISO string back to datetime
        try:
            dt = datetime.fromisoformat(d["timestamp"])
        except ValueError:
            dt = datetime.now(timezone.utc)
            
        items.append(RawItem(
            source=d["source"],
            item_id=d["item_id"],
            text=d["text"],
            timestamp=dt,
            rating=d.get("rating"),
            url=d.get("url"),
            metadata=d.get("metadata", {})
        ))
        
    # Phase 3.1: Deduplication
    deduper = Deduplicator()
    items = deduper.process(items)
    
    # Phase 3.2: Language Detection & Translation
    lang_proc = LanguageProcessor()
    items = lang_proc.process(items)
    
    # Phase 3.3: Spam Filter
    spam_filter = SpamFilter()
    items = spam_filter.process(items)
    
    # Phase 3.4: Relevance Filter (Stage 1)
    rule_filter = RuleBasedFilter()
    items = rule_filter.process(items)
    
    # Save cleaned items back to raw_store (metadata flag updates + translation updates)
    items_to_upsert = []
    for item in items:
        item_dict = {
            "source": item.source,
            "item_id": item.item_id,
            "text": item.text,
            "timestamp": item.timestamp.isoformat(),
            "rating": item.rating,
            "url": item.url,
            "metadata": item.metadata,
            # preserve original ingested_at if we want, or just let it be
        }
        items_to_upsert.append(item_dict)
        
    if items_to_upsert:
        raw_store.upsert_batch(items_to_upsert)
        
    logger.info("Cleaning pipeline complete. Items updated in store.")

def run_extraction():
    logger.info("Starting Phase 4: LLM Extraction")
    raw_dicts = raw_store.get_all()
    logger.info(f"Loaded {len(raw_dicts)} raw items from store for extraction.")
    
    if not raw_dicts:
        logger.warning("No items to extract.")
        return
        
    items = []
    for d in raw_dicts:
        try:
            dt = datetime.fromisoformat(d["timestamp"])
        except ValueError:
            dt = datetime.now(timezone.utc)
            
        items.append(RawItem(
            source=d["source"],
            item_id=d["item_id"],
            text=d["text"],
            timestamp=dt,
            rating=d.get("rating"),
            url=d.get("url"),
            metadata=d.get("metadata", {})
        ))
        
    extractor = Extractor()
    processed_items = extractor.process(items)
    
    saved_count = 0
    items_to_upsert = []
    for item in processed_items:
        if item.metadata.get("extracted", False):
            item_dict = {
                "source": item.source,
                "item_id": item.item_id,
                "text": item.text, # may have been truncated by rules.py
                "timestamp": item.timestamp.isoformat(),
                "rating": item.rating,
                "url": item.url,
                "metadata": item.metadata,
            }
            items_to_upsert.append(item_dict)
            saved_count += 1
            
    if items_to_upsert:
        tagged_store.upsert_batch(items_to_upsert)
            
    logger.info(f"Extraction pipeline complete. {saved_count} items tagged and saved.")

def run_embedding():
    logger.info("Starting Phase 5: Embedding & Vector Store")
    embedder = Embedder()
    embedder.embed_all()

def run_export_snapshot():
    logger.info("Exporting ChromaDB snapshot...")
    chroma_dir = os.path.join(settings.data_dir, "chroma_snapshot")
    if not os.path.exists(chroma_dir):
        logger.error(f"Snapshot directory not found: {chroma_dir}")
        sys.exit(1)
        
    export_path = os.path.join(settings.data_dir, "chroma_snapshot_export")
    shutil.make_archive(export_path, 'zip', chroma_dir)
    logger.info(f"Successfully exported ChromaDB snapshot to {export_path}.zip")

def main():
    parser = argparse.ArgumentParser(description="Blinkit Discovery Engine Pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # run command
    run_parser = subparsers.add_parser("run", help="Run the ingestion pipeline")
    run_parser.add_argument("--sources", type=str, default="tier1", help="Sources to ingest (e.g., tier1, all, playstore, reddit)")
    run_parser.add_argument("--limit", type=int, default=100, help="Limit items per source")
    
    # clean command
    clean_parser = subparsers.add_parser("clean", help="Run the cleaning & relevance filter (Phase 3)")

    # extract command
    extract_parser = subparsers.add_parser("extract", help="Run the LLM extraction (Phase 4)")

    # audit-filter command
    audit_parser = subparsers.add_parser("audit-filter", help="Spot-check relevance filter output")
    # embed command
    embed_parser = subparsers.add_parser("embed", help="Run the embedding pipeline (Phase 5)")

    # export-snapshot command
    export_parser = subparsers.add_parser("export-snapshot", help="Export ChromaDB snapshot to zip (Phase 5)")
    
    args = parser.parse_args()

    if args.command == "run":
        run_ingestion(args.sources, args.limit)
    elif args.command == "clean":
        run_cleaning()
    elif args.command == "extract":
        run_extraction()
    elif args.command == "embed":
        run_embedding()
    elif args.command == "export-snapshot":
        run_export_snapshot()
    elif args.command == "audit-filter":
        print("Running filter audit... (To be implemented in Phase 3)")
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
