import logging
from typing import Dict, Any

from pipeline.store.raw_store import raw_store
from pipeline.store.tagged_store import tagged_store
from server.retriever import retriever

logger = logging.getLogger(__name__)

def generate_volume_funnel() -> Dict[str, Any]:
    """
    Computes the end-to-end ingestion pipeline funnel grouped by source.
    """
    try:
        # Get all raw items (this represents raw_ingested)
        raw_items = raw_store.get_all()
        
        # Get all tagged items
        tagged_items = tagged_store.get_all()
        
        # Get actual embedded count from ChromaDB dynamically
        try:
            embedded_count = retriever.get_count()
        except:
            embedded_count = 0
            
        sources = ["playstore", "appstore", "youtube", "reddit"]
        funnel = {
            "total": {"raw": len(raw_items), "clean": len(tagged_items), "relevant": 0, "embedded": embedded_count},
            "sources": {s: {"raw": 0, "clean": 0, "relevant": 0, "embedded": 0} for s in sources}
        }
        
        for item in raw_items:
            s = item.get("source", "unknown").lower()
            if s in funnel["sources"]:
                funnel["sources"][s]["raw"] += 1
                
        for item in tagged_items:
            s = item.get("source", "unknown").lower()
            if s in funnel["sources"]:
                funnel["sources"][s]["clean"] += 1
                if item.get("metadata", {}).get("relevant") is True:
                    funnel["sources"][s]["relevant"] += 1
                    funnel["total"]["relevant"] += 1
                    
        # Apportion embedded count by source based on relevance ratio (approximate if actuals don't match exactly)
        if funnel["total"]["relevant"] > 0:
            ratio = embedded_count / funnel["total"]["relevant"]
            for s in sources:
                funnel["sources"][s]["embedded"] = int(funnel["sources"][s]["relevant"] * ratio)
                
        return funnel
        
    except Exception as e:
        logger.error(f"Error generating funnel: {e}")
        return {
            "total": {"raw": 0, "clean": 0, "relevant": 0, "embedded": 0},
            "sources": {}
        }
