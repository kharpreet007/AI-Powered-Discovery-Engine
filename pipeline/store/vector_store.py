import os
import logging
import chromadb
from typing import Optional
from pipeline.config import settings

logger = logging.getLogger(__name__)

class VectorStore:
    """Singleton wrapper for ChromaDB PersistentClient."""
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorStore, cls).__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        chroma_dir = os.path.join(settings.data_dir, "chroma_snapshot")
        os.makedirs(chroma_dir, exist_ok=True)
        self._client = chromadb.PersistentClient(path=chroma_dir)
        logger.info(f"Initialized singleton ChromaDB client at {chroma_dir}")

    @property
    def client(self) -> chromadb.PersistentClient:
        return self._client

    def get_collection(self, name: str = "blinkit_insights") -> chromadb.Collection:
        """Dynamically fetch the collection to avoid caching stale metadata/counts."""
        return self._client.get_or_create_collection(name=name)
        
    def count(self, name: str = "blinkit_insights") -> int:
        """Helper to safely count a collection."""
        try:
            return self.get_collection(name).count()
        except Exception as e:
            logger.error(f"Error counting collection {name}: {e}")
            return 0

vector_store = VectorStore()
