import os
import logging
from typing import List, Dict, Any, Optional

import chromadb
from sentence_transformers import SentenceTransformer

from pipeline.store.vector_store import vector_store

logger = logging.getLogger(__name__)

class RetrievedItem:
    def __init__(self, item_id: str, document: str, metadata: Dict[str, Any], distance: float):
        self.item_id = item_id
        self.document = document
        self.metadata = metadata
        self.distance = distance
        
    def to_dict(self):
        return {
            "item_id": self.item_id,
            "document": self.document,
            "metadata": self.metadata,
            "distance": self.distance
        }

class Retriever:
    def __init__(self):
        self.client = vector_store.client
        self.model = SentenceTransformer("BAAI/bge-small-en-v1.5")
        
    @property
    def collection(self):
        return vector_store.get_collection("blinkit_insights")
        
    def get_count(self) -> int:
        return vector_store.count("blinkit_insights")
        
    def get_aggregated_stats(self) -> str:
        """Returns structured aggregation (the 'graded forms' math) for the LLM."""
        from pipeline.store.tagged_store import tagged_store
        from collections import Counter
        
        all_items = tagged_store.get_all()
        relevant = [item for item in all_items if item.get("metadata", {}).get("relevant") is True]
        
        if not relevant:
            return "No relevant data in database."
            
        barriers = Counter(item.get("metadata", {}).get("barrier_type", "unknown") for item in relevant)
        categories = Counter(item.get("metadata", {}).get("category_mentioned", "unknown") for item in relevant)
        unmet_needs = Counter(item.get("metadata", {}).get("unmet_need", "unknown") for item in relevant)
        
        stats = f"Total Highly Relevant Items: {len(relevant)}\n\n"
        stats += "Top Categories:\n" + "\n".join(f"- {k}: {v}" for k, v in categories.most_common(5)) + "\n\n"
        stats += "Top Barriers (Root Causes):\n" + "\n".join(f"- {k}: {v}" for k, v in barriers.most_common(5)) + "\n\n"
        stats += "Top Unmet Needs:\n" + "\n".join(f"- {k}: {v}" for k, v in unmet_needs.most_common(5))
        
        return stats
        
    def retrieve(self, query: str, top_k: int = 20, filters: Optional[Dict[str, Any]] = None) -> List[RetrievedItem]:
        logger.info(f"Retrieving top {top_k} results for query: '{query}'")
        
        query_embedding = self.model.encode([query], show_progress_bar=False).tolist()
        
        # Format filters for chroma if provided
        where = None
        if filters:
            if len(filters) == 1:
                k, v = list(filters.items())[0]
                where = {k: v}
            elif len(filters) > 1:
                where = {"$and": [{k: v} for k, v in filters.items()]}
                
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"]
        )
        
        retrieved_items = []
        if not results["ids"] or not results["ids"][0]:
            return retrieved_items
            
        for i in range(len(results["ids"][0])):
            distance = results["distances"][0][i] if "distances" in results and results["distances"] else 0.0
            
            # Apply strict distance threshold to remove irrelevant noise
            if distance > 1.2:
                continue
                
            item = RetrievedItem(
                item_id=results["ids"][0][i],
                document=results["documents"][0][i],
                metadata=results["metadatas"][0][i],
                distance=distance
            )
            retrieved_items.append(item)
            
        return retrieved_items

# Global instance
retriever = Retriever()
