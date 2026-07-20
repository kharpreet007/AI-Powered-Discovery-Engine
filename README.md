# Blinkit Discovery Engine

An AI-powered discovery engine that transforms unstructured user feedback from multiple public sources into a queryable knowledge base for Blinkit user behavior insights.

## What It Does

- Ingests user-generated content from 4+ public sources (App Store, Play Store, Reddit, YouTube)
- Cleans, deduplicates, and filters for relevance
- Tags each item against a fixed research taxonomy via LLM extraction (Groq / Llama-3)
- Embeds relevant items into a ChromaDB vector store for semantic retrieval
- Serves a RAG-powered chat interface (Gemini synthesis) with cited evidence
- Generates on-demand insight summaries against 8 seed research questions

## Architecture

- **Backend:** Python + FastAPI (deployed to Railway)
- **Frontend:** Next.js / React (deployed to Vercel)
- **LLM Extraction:** Groq API (Llama-3) for high-speed taxonomy tagging
- **LLM Synthesis:** Google Gemini for RAG chat answers
- **Vector Store:** ChromaDB (local persistence + Railway persistent volume)
- **Reddit Access:** Arctic Shift + PullPush.io (keyless community mirrors via BAScraper)

## Setup

1. Copy `.env.example` to `.env` and fill in your API keys
2. Install dependencies: `pip install -r requirements.txt`
3. Run the ingestion pipeline locally: `python -m pipeline run --sources tier1 --limit 100`
4. Start the backend server: `uvicorn server.main:app --reload`

## Documentation

- [PRD](docs/blinkit-discovery-engine-prd.md)
- [Architecture](docs/architecture.md)
- [Implementation Plan](docs/implementation-plan.md)
- [Edge Cases](docs/edge-cases.md)

## Disclaimer

This system is for personal research/case-study purposes only. Scraping app reviews and forum pages sits in a ToS gray area — do not commercially redistribute the collected data.
