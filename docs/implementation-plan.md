# Implementation Plan — Blinkit Discovery Engine

> Derived from [architecture.md](file:///Users/harpreetkaur/Desktop/Harpreet%20Projects/Blinkit/docs/architecture.md) · [blinkit-discovery-engine-prd.md](file:///Users/harpreetkaur/Desktop/Harpreet%20Projects/Blinkit/docs/blinkit-discovery-engine-prd.md)

---

## Prerequisites (Day 0 — Before Any Code)

These have unpredictable approval delays and must not sit on the critical path.

| Account / Key | Purpose | How to Get |
|---|---|---|
| **Groq API Key** | LLM extraction (Llama-3, high-speed batch tagging) | [console.groq.com](https://console.groq.com) — free tier |
| **Google Gemini API Key** | RAG synthesis (high-quality reasoning) | [aistudio.google.com](https://aistudio.google.com) — free tier |
| **YouTube Data API v3 Key** | YouTube comment fetching (Tier 1) | Google Cloud Console → Enable YouTube Data API v3 → Create API Key |

> **Reddit no longer requires API registration.** The connector uses keyless community mirrors (Arctic Shift + PullPush) via the BAScraper library. No credentials needed.

> [!IMPORTANT]
> **Do not start coding until all three keys are provisioned and tested.** Store them in a `.env` file (never committed). Create `.env.example` as a template.

```
# .env.example
GROQ_API_KEY=
GEMINI_API_KEY=
YOUTUBE_API_KEY=
ADMIN_INGEST_TOKEN=          # Secures POST /api/ingest on Railway
```

---

## Phase 1 — Project Scaffolding & Data Models

**Goal:** Repository structure, Python environment, shared data models, and configuration.
**Maps to:** Architecture §7 (Directory Structure), §5 (Data Models)
**Estimated time:** ~2 hours

### 1.1 Initialize Repository Structure

Create the directory layout specified in Architecture §7:

```
blinkit-discovery-engine/
├── docs/                           # PRD, Architecture, this plan
├── pipeline/                       # Shared pipeline module (local + server)
│   ├── __init__.py
│   ├── __main__.py                 # CLI entry point
│   ├── config.py                   # Settings, constants, enums
│   ├── connectors/
│   │   ├── __init__.py
│   │   ├── base.py                 # SourceConnector protocol
│   │   ├── play_store.py
│   │   ├── app_store.py
│   │   ├── reddit.py
│   │   ├── youtube.py
│   │   └── forums.py              # Tier 2
│   ├── cleaning/
│   │   ├── __init__.py
│   │   ├── dedup.py
│   │   ├── language.py
│   │   └── spam.py
│   ├── filtering/
│   │   ├── __init__.py
│   │   └── rules.py               # Stage 1 rule-based filter
│   ├── extraction/
│   │   ├── __init__.py
│   │   ├── extractor.py            # Groq API taxonomy tagging
│   │   └── prompts.py              # Prompt templates
│   ├── embedding/
│   │   ├── __init__.py
│   │   └── embedder.py             # sentence-transformers + ChromaDB
│   ├── reporting/
│   │   ├── __init__.py
│   │   ├── funnel.py               # Volume funnel report
│   │   └── summary.py              # 8-question insight summary
│   └── store/
│       ├── __init__.py
│       ├── raw_store.py            # JSON-lines for raw items
│       └── tagged_store.py         # JSON-lines for tagged items
│
├── server/                         # FastAPI backend (deployed to Railway)
│   ├── __init__.py
│   ├── main.py                     # FastAPI app
│   ├── retriever.py                # ChromaDB semantic search
│   ├── synthesizer.py              # Gemini synthesis
│   └── models.py                   # Pydantic request/response models
│
├── frontend/                       # Next.js app (deployed to Vercel)
│
├── data/                           # Local data (gitignored except snapshot)
│   ├── raw/
│   ├── tagged/
│   └── chroma_snapshot/
│
├── tests/
├── requirements.txt
├── Dockerfile
├── railway.toml
├── .env.example
├── .gitignore
└── README.md
```

### 1.2 Python Environment & Dependencies

#### [NEW] `requirements.txt`

```
# Core
fastapi>=0.100.0
uvicorn>=0.23.0
groq>=0.9.0
google-generativeai>=0.5.0
chromadb>=0.4.0
sentence-transformers>=2.2.0
pydantic>=2.0

# Scraping (Tier 1)
google-play-scraper>=1.0.0
app-store-scraper>=0.3.5
BAScraper>=0.2.0               # Arctic Shift + PullPush async wrapper (Reddit)
beautifulsoup4>=4.12.0
requests>=2.31.0

# NLP
langdetect>=1.0.9

# YouTube (Tier 1)
google-api-python-client>=2.0

# Dev
pytest>=7.0
python-dotenv>=1.0
```

### 1.3 Shared Data Models & Configuration

#### [NEW] `pipeline/config.py`

Define all constants, enums, and settings:

- `CategoryMentioned` enum (13 categories + `other` + `not stated`) — Architecture §5.4
- `CategoryTier` enum (`core`, `exploratory`, `not stated`)
- `BehaviorType`, `DiscoveryChannel`, `BarrierType`, `SegmentSignal`, `Sentiment` enums
- `EvidenceType` enum (`direct`, `proxy`)
- `CATEGORY_KEYWORDS`, `BEHAVIOR_SIGNAL_WORDS`, `TECH_ONLY_VOCAB` word lists — Architecture §4.3
- `SEED_QUESTIONS` list (the 8 research questions) — Architecture §4.7
- Settings class loading from `.env` (API keys, paths, batch sizes)

#### [NEW] `pipeline/connectors/base.py`

Define the `RawItem` dataclass and `SourceConnector` protocol — Architecture §4.1.

#### [NEW] `pipeline/store/raw_store.py` & `pipeline/store/tagged_store.py`

JSON-lines backed stores keyed by `source + item_id`. Support:
- `upsert(item)` — idempotent write
- `get_all(source=None)` — read with optional source filter
- `count(source=None)` — volume counts for funnel reporting

### 1.4 Acceptance Criteria — Phase 1

- [ ] `python -c "from pipeline.config import CategoryMentioned; print(list(CategoryMentioned))"` prints all 15 values
- [ ] `RawItem` and `SourceConnector` are importable and type-checkable
- [ ] `.env.example` contains all 5 key placeholders (Groq, Gemini, YouTube, Admin Token, no Reddit keys needed)
- [ ] `.gitignore` excludes `data/`, `.env`, `__pycache__/`

---

## Phase 2 — Ingestion Layer (Tier 1 Connectors)

**Goal:** Fetch raw user-generated content from all 4 Tier 1 sources.
**Maps to:** Architecture §4.1, PRD §6, Spec A1, FR1/FR2/FR5
**Estimated time:** ~4–5 hours

### 2.1 Play Store Connector

#### [NEW] `pipeline/connectors/play_store.py`

- Uses `google-play-scraper` library
- Fetches Blinkit reviews sorted by most recent
- Applies 12–18 month recency window
- Maps to `RawItem` (source=`"playstore"`, rating from stars, url to Play Store page)
- Target: 500–1000+ reviews

### 2.2 App Store Connector

#### [NEW] `pipeline/connectors/app_store.py`

- Uses `app-store-scraper` or RSS feed parsing
- Fetches Blinkit reviews for the India region
- Applies 12–18 month recency window
- Maps to `RawItem` (source=`"appstore"`)
- Target: 500–1000+ reviews

### 2.3 Reddit Connector

#### [NEW] `pipeline/connectors/reddit.py`

> **Access method change (July 2026):** Reddit's official API (PRAW) is no longer available for new developer registrations. The `.json` URL fallback also returns 403 as of May 2026. This connector uses two free, keyless, community-maintained Reddit data mirrors.

- Uses [BAScraper](https://github.com/maxjo020418/BAScraper) (`pip install BAScraper`), an async Python wrapper for both Arctic Shift and PullPush with built-in rate-limit management. Requires Python 3.12+.
- **Query routing:**
  - **Arctic Shift** (`ArcticShiftAsync`) for subreddit-scoped branded queries — iterates through target subreddits (`r/india`, `r/bangalore`, `r/mumbai`, etc.) one at a time, searching for Blinkit-related keywords in post titles/selftext/comments.
    - Uses `/api/posts/search?subreddit={sub}&title={query}&after={date}&before={date}&limit=100`
    - Uses `/api/comments/search?subreddit={sub}&body={query}&after={date}&before={date}&limit=100`
  - **PullPush** (`PullPushAsync`) for Reddit-wide broadened queries — searches across all subreddits for quick-commerce terms (e.g., "quick commerce india", "instant delivery grocery") since Arctic Shift cannot do Reddit-wide text search.
- **Mandatory cross-fallback:** If Arctic Shift returns an error or times out, retry the same query via PullPush, and vice versa. The connector must never implement a single-service path.
- **Single connector, two query sets** (unchanged from original design, per PRD §6):
  - `branded`: `["blinkit", "blinkit review", "blinkit delivery", ...]`
  - `quick_commerce`: `["quick commerce india", "instant delivery grocery", "10 minute delivery", ...]`
- Both query sets write to the same raw store, keyed by Reddit post/comment ID — a post matching both sets is stored **once**
- Applies 12–18 month recency window via `after`/`before` date params on both services
- Target: 500–1000+ items

### 2.4 YouTube Connector

#### [NEW] `pipeline/connectors/youtube.py`

- Uses `google-api-python-client` (YouTube Data API v3, free quota)
- Searches for Blinkit-related videos (reviews, comparisons, complaints)
- Fetches top-level comments from discovered videos
- Maps to `RawItem` (source=`"youtube"`, url to video, metadata includes video title)
- Target: 500–1000+ comments

### 2.5 CLI — Ingestion Command

#### [NEW] `pipeline/__main__.py` (partial — ingestion commands)

```bash
python -m pipeline run --sources playstore --limit 30    # dry-run single source
python -m pipeline run --sources tier1 --limit 1000      # all Tier 1
python -m pipeline run --sources all --limit 500          # include Tier 2
```

### 2.6 Acceptance Criteria — Phase 2

- [ ] Each connector independently fetches ≥20 items in a dry run
- [ ] All items written to `data/raw/{source}.jsonl` with valid `RawItem` schema
- [ ] Reddit connector deduplicates across both query sets (no duplicate `item_id`s)
- [ ] Reddit connector falls back to PullPush when Arctic Shift errors, and vice versa
- [ ] Reddit connector gracefully returns 0 items with a clear error when both mirrors are unreachable
- [ ] YouTube connector returns comments (not just video metadata)
- [ ] Recency window filters out content older than 18 months

---

## Phase 3 — Cleaning & Relevance Filter

**Goal:** Deduplicate, detect/translate non-English text, filter spam, and apply rule-based relevance filter.
**Maps to:** Architecture §4.2, §4.3, PRD §7a, Spec B, FR6/FR7a
**Estimated time:** ~3–4 hours

### 3.1 Deduplication

#### [NEW] `pipeline/cleaning/dedup.py`

- Hash on normalized text (lowercased, whitespace-collapsed)
- Exact and near-exact duplicates merged; keep earliest instance
- Cross-source dedup (same review posted on multiple platforms)

### 3.2 Language Detection & Translation

#### [NEW] `pipeline/cleaning/language.py`

- Uses `langdetect` for language classification → `en`, `hi`, `hinglish`, `other`
- Hinglish detection via character-set analysis (Devanagari + Latin mix) and confidence thresholds
- Non-English text sent to **Groq API** for normalization/translation
- Stores both `original_text` and `normalized_text` — downstream uses `normalized_text`

### 3.3 Spam Filter

#### [NEW] `pipeline/cleaning/spam.py`

- Rule-based heuristics: promotional content, bot-generated reviews, repeated identical patterns
- Flags items but does not delete them

### 3.4 Relevance Filter (Stage 1)

#### [NEW] `pipeline/filtering/rules.py`

Implements the zero-cost, rule-based filter from Architecture §4.3:

1. **Too short AND no category mention** → discard
2. **Only tech vocabulary AND no behavior signal** → discard (with delivery-complaint exception)
3. **Ambiguous** → pass through to Stage 2 (LLM extraction)

> [!WARNING]
> **Delivery-complaint exception is critical.** "Won't order meat, delivery's too slow" is category-avoidance signal (`barrier_type`), not generic noise. The filter must not blanket-discard delivery complaints.

### 3.5 Acceptance Criteria — Phase 3

- [ ] Duplicate items across sources are detected and merged
- [ ] Hinglish sample text is correctly detected and translated (spot-check 5 examples)
- [ ] Stage 1 filter discards pure tech-complaint items (e.g., "app crashes on login")
- [ ] Stage 1 filter passes delivery complaints tied to categories (e.g., "delivery too slow for electronics")
- [ ] All items retain `original_text` even after normalization
- [ ] `stage1_passed` field set on every cleaned item

---

## Phase 4 — Extraction Layer (Groq LLM Tagging)

**Goal:** Tag every Stage-1-passed item against the full Section 5 taxonomy using Groq API.
**Maps to:** Architecture §4.4, PRD §5, Spec B, FR7/FR7a
**Estimated time:** ~4–5 hours

### 4.1 Extraction Prompt

#### [NEW] `pipeline/extraction/prompts.py`

- System prompt with full taxonomy instructions (Architecture §4.4)
- Canonical category list embedded in prompt to prevent free-text fragmentation
- Strict JSON output format with all 11 fields including `relevant: true/false`
- Batched input format (10–20 items per call as JSON array)

### 4.2 Groq Extractor

#### [NEW] `pipeline/extraction/extractor.py`

- Groq API client with batch processing (10–20 items per call)
- Exponential backoff retry on rate limits (max 3 retries per batch)
- JSON parsing with validation against Pydantic models
- Failed items logged with `item_id` and error for manual retry
- All tagged items (both `relevant: true` and `relevant: false`) written to tagged store

### 4.3 Dry-Run Gate

> [!IMPORTANT]
> **Before scaling to full volume,** run extraction on a small sample (~20–30 items per Tier 1 source, ~100 total). Spot-check the output:
> - Are categories firing correctly against the canonical list?
> - Is `evidence_type` distinguishing `direct` vs. `proxy` correctly?
> - Is the `relevant` flag discarding the right things?
> - Are `segment_signal` values reasonable (not over-guessing demographics)?
>
> Fix taxonomy/prompt issues on ~100 items, not after ingesting thousands.

### 4.4 Acceptance Criteria — Phase 4

- [ ] Dry run on 100 items produces valid JSON for every item (no parse failures)
- [ ] `category_mentioned` values only come from the canonical enum (no free-text variants)
- [ ] `relevant: false` items are retained in tagged store but flagged
- [ ] Spot-check 10 random tagged items — tags match human judgment on ≥8/10
- [ ] Batch processing handles Groq rate limits gracefully (retries, no crashes)
- [ ] Pipeline can be re-run without re-extracting already-tagged items (idempotency)

---

## Phase 5 — Embedding & Vector Store

**Goal:** Embed `relevant: true` items and populate ChromaDB.
**Maps to:** Architecture §4.5, Spec C (partial), FR8
**Estimated time:** ~2–3 hours

### 5.1 Embedder

#### [NEW] `pipeline/embedding/embedder.py`

- Uses `sentence-transformers` with `all-MiniLM-L6-v2` (free, local, no API cost)
- Embeds `normalized_text` (not raw text)
- Only processes items tagged `relevant: true`
- Writes to ChromaDB with full metadata (all taxonomy tags, source, evidence_type, item_id, source_snippet, timestamp)
- Single ChromaDB collection with metadata-based filtering at query time

### 5.2 ChromaDB Setup

- Local persistent mode writing to `data/chroma_snapshot/`
- On Railway: maps to a **Persistent Volume** (critical for live ingestion)
- Collection name: `blinkit_insights`

### 5.3 CLI — Export Snapshot Command

```bash
python -m pipeline export-snapshot    # Packages chroma_snapshot/ for deployment
```

### 5.4 Acceptance Criteria — Phase 5

- [ ] Only `relevant: true` items are embedded (verify count matches tagged store)
- [ ] ChromaDB collection contains all expected metadata fields
- [ ] A simple similarity search returns topically relevant results
- [ ] Snapshot directory can be copied to another location and loaded successfully
- [ ] Re-running embedder on already-embedded items doesn't create duplicates (upsert behavior)

---

## Phase 6 — FastAPI Backend (RAG Chat + Ingestion API)

**Goal:** Build the deployed backend with retrieval, Gemini synthesis, and server-side ingestion.
**Maps to:** Architecture §4.6, §9, Spec C, FR8-10/FR13
**Estimated time:** ~5–6 hours

### 6.1 Retriever

#### [NEW] `server/retriever.py`

- ChromaDB similarity search with `top_k=20` default
- Supports metadata filtering (source, evidence_type, category_tier, barrier_type)
- Returns `RetrievedItem` objects with similarity scores and full metadata
- Results sorted by relevance score

### 6.2 Synthesizer

#### [NEW] `server/synthesizer.py`

- Gemini API integration with the synthesis prompt template (Architecture §4.6)
- **Streaming response** via Server-Sent Events (SSE)
- Handles 5 output requirements:
  1. Synthesized answer grounded in evidence
  2. Citations linked to `source_snippet` + `source` + `item_id`
  3. Evidence-type flagging for proxy sources
  4. Split handling for contradictory evidence (with counts)
  5. Sample size disclosure for quantified claims

### 6.3 FastAPI Application

#### [NEW] `server/main.py`

| Endpoint | Method | Auth | Purpose |
|---|---|---|---|
| `/api/chat` | POST | Public | SSE-streamed chat with citations (Architecture §9.1) |
| `/api/summary` | POST | Public | Generate 8-question insight summary (Architecture §9.2) |
| `/api/stats` | GET | Public | Per-source volume statistics (Architecture §9.3) |
| `/api/health` | GET | Public | Health check + ChromaDB status (Architecture §9.4) |
| `/api/ingest` | POST | Admin token | Trigger background ingestion job (Architecture §9.5) |
| `/api/ingest/status` | GET | Admin token | Check background job status (Architecture §9.5) |

- CORS middleware configured for Vercel frontend origin
- ChromaDB loaded from Persistent Volume path (configured via env var)
- Background task runner for `/api/ingest` (FastAPI `BackgroundTasks`)

### 6.4 Pydantic Models

#### [NEW] `server/models.py`

- `ChatRequest`: question, filters (sources, evidence_type, category_tier), top_k
- `ChatEvent`: SSE event types (token, citation, done)
- `SummaryRequest`: question indices or "all"
- `SummaryResponse`: answers with citations, emergent themes, volume funnel
- `StatsResponse`: per-source counts with tier labels
- `IngestRequest`: sources list, limit
- `IngestStatusResponse`: job status, progress, errors

### 6.5 Acceptance Criteria — Phase 6

- [ ] `/api/chat` streams SSE tokens with valid citation events
- [ ] Citations reference real items from ChromaDB (verifiable by item_id)
- [ ] Gemini synthesis flags proxy evidence when present
- [ ] Contradictory evidence produces a split answer with counts (FR13)
- [ ] `/api/ingest` requires admin token — returns 401 without it
- [ ] `/api/ingest` runs pipeline in background; `/api/ingest/status` reports progress

#### [NEW] `frontend/src/components/CitationCard.tsx`

- Collapsible card showing: source icon (Play Store / Reddit / YouTube / App Store), source snippet text, evidence type badge (`direct` / `proxy`), item ID
- Visual differentiation between direct and proxy evidence
- Animated expand/collapse

#### [NEW] `frontend/src/components/SourceBreakdown.tsx`

- Horizontal bar or pill badges showing how many items from each source contributed to the answer
- Displayed at the bottom of each AI response

#### [NEW] `frontend/src/components/InsightDashboard.tsx`

- Calls `/api/stats` to show ingestion volume by source
- Visual funnel chart or table for raw → filtered → embedded counts
- Calls `/api/summary` to display the 8-question insight report

#### [NEW] `frontend/src/lib/api.ts`

- SSE client for `/api/chat` (EventSource or fetch with ReadableStream)
- REST client for `/api/stats`, `/api/summary`, `/api/ingest`
- Base URL configured via `NEXT_PUBLIC_API_URL` environment variable

### 7.3 Design System

- **Color palette:** Dark background (#0a0a0f) with accent gradients (violet → indigo → teal)
- **Typography:** Google Fonts — Inter for body, JetBrains Mono for code/citations
- **Glassmorphism:** Frosted-glass effect on citation cards and sidebar
- **Micro-animations:** Typing indicator, smooth message transitions, citation card reveal
- **Responsive:** Works on desktop and tablet; mobile is secondary

### 7.4 Acceptance Criteria — Phase 7

- [ ] Chat input sends question and displays streaming response token-by-token
- [ ] Citation cards render with correct source icons and evidence type badges
- [ ] Quick-access buttons for all 8 seed questions work end-to-end
- [ ] Source breakdown shows per-source item counts after each answer
- [ ] UI handles error states (API down, empty results) gracefully
- [ ] Design feels premium — dark mode, glassmorphism, smooth animations

---

## Phase 8 — Deployment

**Goal:** Deploy backend to Railway and frontend to Vercel.
**Maps to:** Architecture §3, §11
**Estimated time:** ~2–3 hours

### 8.1 Railway (Backend)

#### [NEW] `Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY pipeline/ pipeline/
COPY server/ server/
COPY data/chroma_snapshot/ data/chroma_snapshot/
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### [NEW] `railway.toml`

- Configure Persistent Volume mount at `/app/data/chroma_snapshot`
- Set environment variables (API keys, `ADMIN_INGEST_TOKEN`)

### 8.2 Vercel (Frontend)

- Connect `frontend/` directory to Vercel
- Set `NEXT_PUBLIC_API_URL` to the Railway backend URL
- Enable automatic deployments on push

### 8.3 Acceptance Criteria — Phase 8

- [ ] Railway health endpoint returns `{"status": "ok"}` with ChromaDB loaded
- [ ] Vercel frontend loads and connects to Railway backend (no CORS errors)
- [ ] End-to-end: ask a question on Vercel → get streamed answer from Railway
- [ ] `/api/ingest` on Railway successfully scrapes and embeds new data to Persistent Volume
- [ ] Data persists across Railway redeployments (Persistent Volume verified)

---

## Phase 9 — Insight Summary & Reporting

**Goal:** Generate the 8-question insight report and volume funnel.
**Maps to:** Architecture §4.7, §12, Spec D, FR11/FR12
**Estimated time:** ~2–3 hours

### 9.1 Insight Summary Generator

#### [NEW] `pipeline/reporting/summary.py`

- Runs all 8 seed questions through the RAG pipeline
- Compiles structured output: answer + citations + confidence + per-source breakdown
- Detects emergent themes (tag clusters not mapped to any seed question)

### 9.2 Volume Funnel Report

#### [NEW] `pipeline/reporting/funnel.py`

- Per-source funnel: raw ingested → deduped → cleaned → Stage 1 passed → relevant true → embedded
- Flags low-volume sources with ⚠️ warnings
- CLI command: `python -m pipeline report`

### 9.3 Acceptance Criteria — Phase 9

- [ ] All 8 seed questions produce answers with ≥3 cited examples each (PRD §10)
- [ ] At least one emergent theme surfaces that isn't covered by the 8 questions
- [ ] Volume funnel accurately reflects counts at each pipeline stage
- [ ] Low-volume sources are flagged as "directional only"

---

## Phase 10 — Tier 2 Sources (Best-Effort)

**Goal:** Add community forums and other social connectors if time allows.
**Maps to:** Architecture §4.1, Spec A2, FR3/FR4
**Estimated time:** ~3–4 hours (only if Phases 1–9 complete with time to spare)

> [!CAUTION]
> **This phase is explicitly non-blocking.** If time runs out, ship the Tier-1-only system and document Tier 2 as a gap. A working 4-source system beats a broken 6-source one.

### 10.1 Forum Connectors

#### [NEW] `pipeline/connectors/forums.py`

- Per-forum BeautifulSoup scrapers (Quora, MouthShut, consumer-complaint boards)
- Expect lower volume and higher fragility
- Feed into the same cleaning → extraction → embedding pipeline

### 10.2 Acceptance Criteria — Phase 10

- [ ] Forum connector fetches ≥20 items from at least one forum
- [ ] Items pass through the full pipeline and appear in ChromaDB
- [ ] Insight summary reflects the new source in its volume funnel

---

## Validation Checklist (PRD §10 — Success Criteria)

Run these checks after Phase 9 to confirm the system meets the PRD's success criteria:

| # | Criterion | How to Verify |
|---|---|---|
| SC1 | Chat answers all 8 seed questions with ≥3 cited examples each | Run each question through `/api/chat`, count citation events |
| SC2 | Retrieval is topically relevant | Manually spot-check 10 random Q&A pairs against source data |
| SC3 | Insight summary surfaces ≥1 emergent theme | Check `emergent_themes` in `/api/summary` response |
| SC4 | Quantified claims state sample size | Verify synthesis prompt forces n-counts in output |
| SC5 | Mixed evidence produces split answer | Test with a question known to have contradictory evidence |
| SC6 | Per-source volume funnel is visible | Check `/api/stats` and funnel report output |

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Groq rate limit exhausted during extraction | Medium | Blocks pipeline | Exponential backoff; fall back to Together AI or local Ollama |
| Gemini rate limit during chat synthesis | Low | Degrades UX | Retry with backoff; consider GPT-4o-mini or Claude as fallback |
| Reddit mirrors (Arctic Shift + PullPush) both unreachable | Medium | Zero Reddit data ingested | Mandatory cross-fallback between mirrors; if both fail, connector returns 0 items with clear error in funnel report |
| Reddit data staleness (archive mirrors lag on recent posts) | Medium | Most recent 1–7 days of posts may be absent | 12–18 month recency window makes this rarely impactful; document as known limitation |
| Play Store / App Store scrapers blocked | Low | Blocks Tier 1 ingestion | Run locally from home IP; libraries are well-maintained |
| Railway datacenter IPs blocked during server-side ingest | High | Server ingest fails | Local ingestion as primary; proxy service (BrightData) as future option |
| YouTube API quota exhaustion | Medium | Blocks YouTube connector | Free quota is 10,000 units/day; monitor usage; batch requests |
| Hinglish/code-mixed text mis-tagged by Groq | Medium | Reduces tagging quality | Language detection before extraction; retain original text; spot-check |
| Relevance filter too aggressive | Medium | Drops real signal | `relevant: false` items retained; `audit-filter` CLI for spot-checking |

---

## Build Sequence Summary

| Day | Phases | Spec | Key Deliverable |
|---|---|---|---|
| **Day 0** | Prerequisites | — | All API keys provisioned and tested |
| **Day 1** | Phase 1 + 2 + 3 + 4 | A1, B | Working local pipeline: scrape → clean → filter → extract (dry-run gate) |
| **Day 2** | Phase 5 + 6 + 7 | C | ChromaDB populated, FastAPI backend live, Next.js chat UI functional |
| **Day 3** | Phase 8 + 9 | C, D | Deployed to Railway + Vercel; insight summary + volume funnel |
| **Day 3+** | Phase 10 | A2 | Tier 2 connectors (best-effort, non-blocking) |
