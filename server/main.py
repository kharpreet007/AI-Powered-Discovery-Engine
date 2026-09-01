import logging
import json
from collections import Counter
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import os

from server.models import ChatRequest, StatsResponse, SummaryRequest, SummaryResponse, IngestRequest, IngestStatusResponse
from server.retriever import retriever
from server.synthesizer import synthesizer
from pipeline.store.tagged_store import tagged_store
from pipeline.ingest_runner import run_ingestion_pipeline, get_ingestion_status
from pipeline.reporting.funnel import generate_volume_funnel
from pipeline.reporting.summary import generate_insight_summary, get_emergent_themes, get_sneak_peek_data
from pipeline.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("server")

app = FastAPI(title="Blinkit Discovery Engine API", version="1.0.0")

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, set to specific Vercel domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

def verify_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    admin_token = os.environ.get("ADMIN_TOKEN", "dev_token_123")
    if credentials.credentials != admin_token:
        raise HTTPException(status_code=401, detail="Invalid admin token")
    return credentials.credentials

@app.get("/api/health")
async def health_check():
    """Basic health check and ChromaDB status."""
    try:
        count = retriever.collection.count()
        db_status = "ok"
    except Exception as e:
        count = 0
        db_status = f"error: {str(e)}"
        
    return {
        "status": "healthy",
        "chromadb_status": db_status,
        "chromadb_documents": count,
        "debug": "YES_CHANGES_ARE_LOADED"
    }

@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Returns volume statistics of ingested and tagged data."""
    all_items = tagged_store.get_all()
    relevant_items = [item for item in all_items if item.get("metadata", {}).get("relevant") is True]
    
    source_counts = Counter()
    for item in relevant_items:
        source_counts[item.get("source", "unknown")] += 1
        
    funnel_data = generate_volume_funnel()
    themes_data = get_emergent_themes()
    sneak_peek_data = get_sneak_peek_data()
    import os
    from datetime import datetime
    
    last_updated_str = "Unknown"
    chroma_dir = os.path.join(settings.data_dir, "chroma_snapshot")
    if os.path.exists(chroma_dir):
        mtime = os.path.getmtime(chroma_dir)
        last_updated_str = datetime.fromtimestamp(mtime).strftime("%b %d, %I:%M %p")
        
    logger.info(f"Returning stats: {len(relevant_items)} items"); return StatsResponse(
        total_items=len(relevant_items),
        source_counts=dict(source_counts),
        volume_funnel=funnel_data,
        emergent_themes=themes_data,
        sneak_peek=sneak_peek_data,
        last_updated=last_updated_str
    )

@app.get("/api/items/theme")
async def get_items_by_theme(barrier: str = None, category: str = None):
    """Returns items for a specific theme based on barrier and category."""
    all_items = tagged_store.get_all()
    
    b_val = (barrier or "").strip().lower()
    c_val = (category or "").strip().lower()

    filtered_items = [
        item for item in all_items 
        if str(item.get("metadata", {}).get("barrier_type") or "").strip().lower() == b_val
        and str(item.get("metadata", {}).get("category_mentioned") or "").strip().lower() == c_val
        and item.get("metadata", {}).get("relevant") is True
    ]
    return {"items": filtered_items[::-1][:50], "debug": {"b_val": b_val, "c_val": c_val, "barrier": barrier, "category": category}}

@app.get("/api/items/{source}")
async def get_items_by_source(source: str):
    """Returns items for a specific source (e.g. youtube, playstore, reddit, appstore)."""
    all_items = tagged_store.get_all()
    # Filter by source, ignoring case
    filtered_items = [
        item for item in all_items 
        if item.get("source", "").lower() == source.lower()
        and item.get("metadata", {}).get("relevant") is True
    ]
    # Return newest first (assuming they were appended, reversing gets latest)
    return {"items": filtered_items[::-1][:50]}  # limit to top 50


@app.post("/api/chat")
async def chat_stream(request: Request, body: ChatRequest):
    """
    RAG Chat endpoint returning Server-Sent Events (SSE).
    """
    # Convert pydantic models to dicts
    messages_dicts = [{"role": msg.role, "content": msg.content} for msg in body.messages]
    
    # Get last query for retriever
    last_query = messages_dicts[-1]["content"] if messages_dicts else ""
    logger.info(f"Received chat request: {last_query}")
    
    # 1. Retrieve evidence and stats
    try:
        evidence = retriever.retrieve(query=last_query, top_k=body.top_k, filters=body.filters)
        stats = retriever.get_aggregated_stats()
    except Exception as e:
        logger.error(f"Retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve evidence")

    # 2. Synthesize using generator
    async def event_generator():
        try:
            # Yield initial metadata about retrieved chunks
            yield {
                "data": json.dumps({
                    "event": "meta",
                    "data": {"retrieved_count": len(evidence)}
                })
            }
            
            # Stream citations
            for i, item in enumerate(evidence[:3]):
                yield {
                    "data": json.dumps({
                        "event": "citation",
                        "data": {
                            "id": i + 1,
                            "source": item.metadata.get("source", "unknown"),
                            "text": item.document[:200] + "..."
                        }
                    })
                }
            
            if not evidence:
                yield {
                    "data": json.dumps({
                        "event": "token",
                        "data": "I don't have enough information in the database to answer that question."
                    })
                }
                return
                
            # Stream the generated chunks
            generator = synthesizer.synthesize_stream(messages_dicts, evidence, stats)
            for chunk in generator:
                # If client disconnected, stop generating
                if await request.is_disconnected():
                    logger.info("Client disconnected, stopping generation.")
                    break
                    
                yield {
                    "data": json.dumps({
                        "event": "token",
                        "data": chunk
                    })
                }
                
            # Signal completion
            yield {
                "data": json.dumps({
                    "event": "done",
                    "data": "[DONE]"
                })
            }
            
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            yield {
                "data": json.dumps({
                    "event": "token",
                    "data": f"\n\n[System Error: {str(e)}]"
                })
            }

    return EventSourceResponse(event_generator())

@app.post("/api/summary", response_model=SummaryResponse)
async def generate_summary(body: SummaryRequest):
    """Generates an 8-question summary report."""
    logger.info("Generating Insight Summary Report...")
    summary_data = generate_insight_summary(body.questions)
    funnel_data = generate_volume_funnel()
    
    return SummaryResponse(
        answers=summary_data["answers"],
        emergent_themes=summary_data["emergent_themes"],
        volume_funnel=funnel_data
    )

from fastapi.responses import Response

@app.get("/api/reports/summary")
async def download_summary_report():
    """Generates and downloads an AI-generated Executive Summary report containing the 8 Q&A."""
    logger.info("Generating downloadable Insight Summary Report...")
    try:
        stats = retriever.get_aggregated_stats()
        themes = get_emergent_themes()
        
        # 1. Generate the executive summary from the LLM
        exec_summary = synthesizer.generate_executive_summary(stats, themes)
        
        # 2. Fetch the 8 predefined questions & answers
        logger.info("Answering the 8 core Workflow Analyzer questions for the report...")
        qa_data = generate_insight_summary("all")
        
        # 3. Append the 8 questions and answers to the markdown
        qa_markdown = "## Workflow Analyzer Deep Dive\n\n"
        for item in qa_data.get("answers", []):
            q = item.get("question", "Question")
            a = item.get("answer", "No answer generated.")
            qa_markdown += f"### {q}\n{a}\n\n"
            
        full_markdown = f"{exec_summary}\n\n---\n\n{qa_markdown}"
        
        return Response(
            content=full_markdown,
            media_type="text/markdown",
            headers={
                "Content-Disposition": "attachment; filename=Blinkit_Discovery_Insights.md"
            }
        )
    except Exception as e:
        logger.error(f"Failed to generate summary report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate report")

@app.post("/api/ingest", response_model=IngestStatusResponse)
async def start_ingestion(
    request: IngestRequest, 
    background_tasks: BackgroundTasks,
    token: str = Depends(verify_admin)
):
    """Triggers a background ingestion job."""
    status = get_ingestion_status()
    if status["is_ingesting"]:
        raise HTTPException(status_code=409, detail="Ingestion already in progress")
        
    background_tasks.add_task(run_ingestion_pipeline, request.mode)
    
    # Return optimistic initial state
    return IngestStatusResponse(
        is_ingesting=True,
        mode=request.mode,
        status="starting",
        progress=0,
        total_steps=status["total_steps"],
        last_error=None
    )

@app.get("/api/ingest/status", response_model=IngestStatusResponse)
async def check_ingestion_status(token: str = Depends(verify_admin)):
    """Checks the progress of a running ingestion job."""
    status = get_ingestion_status()
    return IngestStatusResponse(**status)
