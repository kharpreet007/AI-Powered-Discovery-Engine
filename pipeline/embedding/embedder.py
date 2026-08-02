import os
import logging
from typing import List, Dict, Any

from sentence_transformers import SentenceTransformer
import chromadb

from pipeline.config import settings
from pipeline.store.tagged_store import tagged_store
from pipeline.store.vector_store import vector_store

logger = logging.getLogger(__name__)

class Embedder:
    def __init__(self):
        # Disable progress bars to prevent BrokenPipeError in background threads
        os.environ["TQDM_DISABLE"] = "1"
        os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
        
        # 1. Initialize local embedding model
        model_name = "BAAI/bge-small-en-v1.5"
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        
        # 2. Initialize ChromaDB client via singleton
        self.chroma_client = vector_store.client
        
        # 3. Create or get collection dynamically
        self.collection = vector_store.get_collection("blinkit_insights")
        logger.info(f"Initialized singleton ChromaDB collection 'blinkit_insights'")

    def _prepare_metadata(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten item into Chroma-compatible metadata (strings, ints, floats or bools)."""
        meta = item.get("metadata", {})
        metadata = {
            "source": item.get("source", "unknown"),
            "item_id": item.get("item_id", "unknown"),
            "timestamp": item.get("timestamp", ""),
            "evidence_type": meta.get("evidence_type", "direct"),
            "category_mentioned": meta.get("category_mentioned", "not stated"),
            "category_tier": meta.get("category_tier", "not stated"),
            "behavior_type": meta.get("behavior_type", "not stated"),
            "discovery_channel": meta.get("discovery_channel", "not stated"),
            "barrier_type": meta.get("barrier_type", "not stated"),
            "frustration": meta.get("frustration", "none"),
            "unmet_need": meta.get("unmet_need", "none"),
            "segment_signal": meta.get("segment_signal", "not stated"),
            "sentiment": meta.get("sentiment", "neutral")
        }
        # Ensure all values are safe for chroma (no None)
        for k, v in metadata.items():
            if v is None:
                metadata[k] = "none"
            elif isinstance(v, (dict, list)):
                metadata[k] = str(v)
        return metadata

    def embed_all(self):
        logger.info("Starting embedding process for relevant items...")
        
        all_items = tagged_store.get_all()
        relevant_items = [item for item in all_items if item.get("metadata", {}).get("relevant") is True]
        
        logger.info(f"Found {len(relevant_items)} relevant items to embed out of {len(all_items)} total tagged items.")
        
        if not relevant_items:
            logger.info("No relevant items to embed.")
            return

        batch_size = 64
        total_batches = (len(relevant_items) + batch_size - 1) // batch_size
        
        for i in range(0, len(relevant_items), batch_size):
            batch = relevant_items[i:i + batch_size]
            
            ids = []
            documents = []
            metadatas = []
            
            for item in batch:
                ids.append(item["item_id"])
                # text contains the normalized english text
                documents.append(item["text"])
                metadatas.append(self._prepare_metadata(item))
                
            logger.info(f"Encoding batch {i//batch_size + 1}/{total_batches} ({len(batch)} items)...")
            embeddings = self.model.encode(documents, show_progress_bar=False).tolist()
            
            logger.info(f"Upserting batch {i//batch_size + 1}/{total_batches} into ChromaDB...")
            self.collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
            
        logger.info(f"Successfully embedded and stored {len(relevant_items)} items in ChromaDB.")
