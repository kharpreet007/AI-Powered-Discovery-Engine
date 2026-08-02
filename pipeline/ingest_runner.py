import logging
import asyncio
from typing import Dict, Any
from collections import deque
from pipeline.__main__ import run_ingestion, run_cleaning, run_extraction, run_embedding

logger = logging.getLogger(__name__)

class MemoryLogHandler(logging.Handler):
    def __init__(self, maxlen=50):
        super().__init__()
        self.logs = deque(maxlen=maxlen)
        self.setFormatter(logging.Formatter('%(asctime)s|%(levelname)s|%(message)s'))
        
    def emit(self, record):
        self.logs.append(self.format(record))

memory_handler = MemoryLogHandler(maxlen=50)
logging.getLogger("pipeline").addHandler(memory_handler)
# Prevent propagation issues if needed, but adding to root pipeline logger should catch most.


ingestion_state = {
    "is_ingesting": False,
    "mode": None,
    "status": "idle", # idle, fetching, cleaning, extracting, embedding, completed, failed
    "progress": 0,
    "total_steps": 4,
    "last_error": None
}

def get_ingestion_status() -> Dict[str, Any]:
    st = ingestion_state.copy()
    st["logs"] = list(memory_handler.logs)
    return st

async def run_ingestion_pipeline(mode: str = "demo"):
    """
    Runs the full ingestion pipeline asynchronously.
    Should be called via FastAPI BackgroundTasks.
    """
    global ingestion_state
    
    if ingestion_state["is_ingesting"]:
        logger.warning("Ingestion is already running. Skipping new trigger.")
        return
        
    logger.info(f"Starting ingestion pipeline in {mode} mode.")
    
    ingestion_state.update({
        "is_ingesting": True,
        "mode": mode,
        "status": "fetching",
        "progress": 0,
        "last_error": None
    })
    
    limit = 10 if mode == "demo" else 200
    
    try:
        # Step 1: Fetch
        ingestion_state["status"] = "fetching"
        logger.info("Ingestion Step 1: Fetching")
        await asyncio.to_thread(run_ingestion, "tier1", limit)
        ingestion_state["progress"] = 1
        
        # Step 2: Clean
        ingestion_state["status"] = "cleaning"
        logger.info("Ingestion Step 2: Cleaning")
        await asyncio.to_thread(run_cleaning)
        ingestion_state["progress"] = 2
        
        # Step 3: Extract
        ingestion_state["status"] = "extracting"
        logger.info("Ingestion Step 3: Extracting")
        await asyncio.to_thread(run_extraction)
        ingestion_state["progress"] = 3
        
        # Step 4: Embed
        ingestion_state["status"] = "embedding"
        logger.info("Ingestion Step 4: Embedding")
        await asyncio.to_thread(run_embedding)
        ingestion_state["progress"] = 4
        
        ingestion_state["status"] = "completed"
        logger.info("Ingestion pipeline completed successfully.")
        
    except Exception as e:
        logger.exception("Ingestion pipeline failed.")
        ingestion_state["status"] = "failed"
        ingestion_state["last_error"] = str(e)
    finally:
        ingestion_state["is_ingesting"] = False
