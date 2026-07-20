# Edge Cases — Blinkit Discovery Engine

> Derived from [architecture.md](file:///Users/harpreetkaur/Desktop/Harpreet%20Projects/Blinkit/docs/architecture.md) · [implementation-plan.md](file:///Users/harpreetkaur/Desktop/Harpreet%20Projects/Blinkit/docs/implementation-plan.md)

This document catalogs edge cases across every layer of the system. Each entry describes the scenario, why it matters, and the expected behavior.

---

## 1. Ingestion Layer (Connectors)

### 1.1 Play Store / App Store

| # | Edge Case | Why It Matters | Expected Behavior |
|---|---|---|---|
| I-1 | **Scraper library returns 0 reviews** (API change, app delisted, region mismatch) | Silent empty ingest produces a misleading "0 items" funnel without error | Log a warning; pipeline continues with other sources; funnel report shows 0 with ⚠️ flag |
| I-2 | **Review text is entirely emoji** (e.g., "👍👍👍👍👍") | No extractable semantic content; embedding is meaningless | Stage 1 filter discards (below length threshold after emoji stripping); retained in raw store |
| I-3 | **Review contains only a star rating and no text** (common on Play Store) | `text` field is empty string or `None` | Connector skips items with empty/null text; logs count of skipped items |
| I-4 | **Duplicate reviews across App Store and Play Store** (user posts same text on both) | Cross-source duplicate inflates volume counts | Dedup layer catches via normalized text hash; keeps earliest instance; records `duplicate_of` |
| I-5 | **Review timestamp is in the future or year 1970** (malformed date) | Breaks recency window filter | Connector validates timestamp; items with unparseable dates are ingested with `timestamp: null` and flagged |
| I-6 | **Extremely long review (10,000+ characters)** | May exceed Groq prompt token limits during extraction | Connector truncates text to 2,000 characters (configurable); stores full text in `original_text` |
| I-7 | **Non-Blinkit app review returned** (scraper pulls wrong app ID) | Pollutes dataset with irrelevant reviews | Validate app ID in connector config; log and skip mismatched items |
| I-8 | **Rate limiting / HTTP 429 from Play Store** | Connector hangs or crashes mid-fetch | Exponential backoff with max 5 retries; after exhaustion, return partial results and log |

### 1.2 Reddit (Arctic Shift + PullPush via BAScraper)

| # | Edge Case | Why It Matters | Expected Behavior |
|---|---|---|---|
| I-9 | **Reddit post matches both branded AND quick-commerce query sets** | Could be double-counted if stored twice | Single store keyed by post/comment ID; carries both query-match tags; stored once |
| I-10 | **Deleted or [removed] comments returned by mirrors** | Archive mirrors preserve deleted content text | Filter out items where text is exactly `[deleted]`, `[removed]`, or empty |
| I-11 | **Comment is a bot response** (AutoModerator, RemindMeBot) | Adds noise with zero user signal | Spam filter flags known bot usernames; heuristic check for bot signatures |
| I-12 | **Arctic Shift returns error or times out** | Subreddit-scoped queries fail | Mandatory fallback: retry the same query via PullPush. Log the failover. Never silently skip |
| I-13 | **PullPush returns error or times out** | Reddit-wide queries fail | Mandatory fallback: retry the same query via Arctic Shift (will need to iterate per-subreddit). Log the failover |
| I-14 | **Both Arctic Shift AND PullPush are simultaneously unreachable** | Zero Reddit data for this ingest run | Connector fails gracefully; returns 0 items with clear error message; funnel report shows 0 Reddit items with ⚠️ flag. Pipeline continues with other sources |
| I-15 | **Arctic Shift query for a very active subreddit hits the 100-item limit per request** | Misses older matching posts within the recency window | Paginate using `before` parameter to fetch successive pages until the recency window is exhausted or no more results |
| I-16 | **Very recent Reddit posts (last 1–7 days) are missing from mirror results** | Archive mirrors lag behind live Reddit | Accept as documented limitation — recency window is 12–18 months, so missing the last few days rarely impacts research quality. Log a note in the funnel report |
| I-17 | **PullPush returns results from unexpected subreddits** (Reddit-wide search) | May include irrelevant quick-commerce discussions not about Blinkit | Downstream Stage 2 LLM extraction sets `relevant: false`; not embedded. Acceptable noise at ingestion |
| I-18 | **BAScraper rate limiter triggers a long backoff** | Connector appears to hang | BAScraper's built-in rate-limit management handles this; set reasonable `sleep_sec` and `max_retries`. Log backoff events |
| I-19 | **Arctic Shift returns different JSON field names than expected** | Community API — field names may change without notice | Validate required fields (`body`/`selftext`, `id`, `created_utc`) exist in response; log and skip items with missing fields |

### 1.3 YouTube

| # | Edge Case | Why It Matters | Expected Behavior |
|---|---|---|---|
| I-16 | **YouTube API quota exhausted** (10,000 units/day free) | No more comments can be fetched | Detect quota error (HTTP 403); log remaining items; connector returns partial results |
| I-17 | **Video has comments disabled** | API returns empty `commentThreads` | Skip video; log; move to next video in search results |
| I-18 | **Comment is a reply to another comment (nested)** | Nested replies may lack context without parent | Fetch only top-level comments by default; optionally include parent context as metadata |
| I-19 | **Comment is in a non-Latin script** (Tamil, Telugu, Bengali) | `langdetect` may misclassify; translation needed | Language detection flags as `other`; Groq normalizes to English; original retained |
| I-20 | **Search returns unrelated videos** (e.g., "blinkit" matches a gaming channel) | Pollutes dataset | Pre-filter videos by channel relevance or minimum view count; validate video title contains relevant keywords |
| I-21 | **Comment contains only a timestamp** (e.g., "2:34") | No semantic content | Stage 1 filter discards (below length threshold, no category/behavior signal) |

---

## 2. Cleaning Layer

| # | Edge Case | Why It Matters | Expected Behavior |
|---|---|---|---|
| C-1 | **Pure Devanagari text (Hindi, no English)** | `langdetect` may classify as `hi` but it's not Hinglish | Classify as `hi`; send to Groq for English translation; retain original |
| C-2 | **Hinglish with Romanized Hindi** (e.g., "bahut accha product hai") | No Devanagari characters → character-set analysis alone won't detect it | `langdetect` confidence threshold + Roman Hindi keyword list as secondary signal |
| C-3 | **Groq translation API fails on a batch** | Non-English items remain untranslated | Retry with backoff; if persistent, set `normalized_text = original_text` and add `translation_failed: true` flag |
| C-4 | **Text is a mix of 3+ languages** (English + Hindi + Marathi in one sentence) | Language detection returns low confidence for all | Classify as `hinglish`; send entire text to Groq for normalization |
| C-5 | **Near-duplicate reviews with minor variations** ("Great app!" vs. "Great app!!") | Exact hash won't match; both get embedded | Normalize whitespace, punctuation, and case before hashing; consider Jaccard similarity ≥0.95 threshold |
| C-6 | **Spam review with category keywords** (e.g., "Buy cheap electronics at example.com") | Contains `electronics` keyword → passes Stage 1 | Spam filter runs before Stage 1; URL-heavy promotional text is flagged |
| C-7 | **Empty text after cleaning** (original was all emojis/special characters) | Downstream stages receive empty string | If `normalized_text` is empty after cleaning, mark `stage1_passed: false` |
| C-8 | **Review is a single word** (e.g., "Good", "Worst") | Too short for meaningful extraction | Stage 1 filter discards (< 25 characters, no category mention) |

---

## 3. Relevance Filter (Stage 1)

| # | Edge Case | Why It Matters | Expected Behavior |
|---|---|---|---|
| F-1 | **Delivery complaint tied to a category** ("won't order meat, delivery's too slow") | Contains `TECH_ONLY_VOCAB` ("slow") but is actually a `barrier_type` signal | Delivery-complaint exception fires; item passes to Stage 2 because `has_category = true` |
| F-2 | **Pure tech complaint** ("app crashes every time I open it, fix the bug") | No behavior/category signal | Stage 1 discards; retained in raw store with `stage1_passed: false` |
| F-3 | **Tech complaint with behavior signal** ("app crashes when I try to order electronics") | Contains both tech vocab AND category mention | Passes Stage 1 — `has_category = true` triggers the exception |
| F-4 | **Item is exactly 25 characters with no category** | Boundary condition on length threshold | Discarded (rule is `< 25` — items at exactly 25 chars pass if other rules don't discard) |
| F-5 | **Item contains a category keyword in a different context** (e.g., "I'm a pet peeve person") | "pet" matches `CATEGORY_KEYWORDS` but isn't about Pet Care | Passes Stage 1 (false positive is acceptable); Stage 2 LLM sets `relevant: false` |
| F-6 | **All items from a source fail Stage 1** | Entire source produces 0 embedded items | Funnel report shows 0 at Stage 1; logged as warning; investigate keyword lists |

---

## 4. Extraction Layer (Groq LLM)

| # | Edge Case | Why It Matters | Expected Behavior |
|---|---|---|---|
| E-1 | **Groq returns malformed JSON** (truncated response, extra text around JSON) | JSON parse fails | Retry once; if still malformed, log error with `item_id`; mark item as `extraction_failed: true` |
| E-2 | **Groq returns a `category_mentioned` value not in the canonical enum** (e.g., "Cosmetics" instead of "Beauty & Skincare") | Breaks structured querying | Validate against `CategoryMentioned` enum; if invalid, map to closest match or `"other"` |
| E-3 | **Batch of 20 items but Groq returns tags for only 18** | 2 items lose their tags silently | Validate response array length matches input; re-extract missing items individually |
| E-4 | **Item text mentions multiple categories** ("I buy groceries and electronics on Blinkit") | Single `category_mentioned` field can't capture both | Extract the primary/dominant category; note limitation in architecture; consider `categories_mentioned: list` in future |
| E-5 | **Groq rate limit hit mid-extraction** (HTTP 429) | Pipeline stalls | Exponential backoff (1s, 2s, 4s, 8s, max 60s); max 3 retries per batch; log and continue |
| E-6 | **`source_snippet` is longer than the original text** | Groq hallucinated text not present in input | Validate `source_snippet` is a substring of `normalized_text`; if not, fall back to first 200 chars |
| E-7 | **Groq tags everything as `relevant: true`** (prompt not selective enough) | Defeats the purpose of the relevance filter | Spot-check in dry-run gate; tune prompt if >90% pass rate; expect ~60-80% pass rate |
| E-8 | **Groq tags everything as `relevant: false`** (prompt too aggressive) | Almost nothing gets embedded | Spot-check in dry-run gate; loosen prompt criteria; check sample of discarded items |
| E-9 | **Item is ambiguous — genuinely could be relevant or not** | LLM makes a judgment call | Accept LLM decision; retained in tagged store for audit; `audit-filter` CLI enables review |
| E-10 | **`segment_signal` over-inferred** (text says "ordered for my kids" → tagged `homemaker`) | Demographic guesswork from thin evidence | Prompt instructs "use only what's reliably inferable"; default to `not stated` when uncertain |
| E-11 | **Groq API is completely down** (outage) | Entire extraction layer blocks | Detect persistent failures (>5 consecutive); fall back to Together AI / Fireworks AI if configured; otherwise halt and log |
| E-12 | **Same item is extracted twice** (pipeline re-run) | Duplicate tagged entries | Upsert by `source + item_id`; re-extraction overwrites previous tags |

---

## 5. Embedding & Vector Store (ChromaDB)

| # | Edge Case | Why It Matters | Expected Behavior |
|---|---|---|---|
| V-1 | **ChromaDB persist directory is corrupted** (disk failure, partial write) | Service fails to start | Health endpoint reports `chroma_loaded: false`; log error; require re-deployment of snapshot |
| V-2 | **Embedding model produces NaN or zero vectors** | Similarity search returns garbage | Validate embedding vectors before inserting; skip items with invalid vectors |
| V-3 | **Two items have identical `normalized_text`** (different sources) | Produce identical embeddings; duplicate results in retrieval | Acceptable — they have different metadata (source, item_id); retriever deduplicates by content if needed |
| V-4 | **ChromaDB collection exceeds memory on Railway free tier** | OOM crash on service startup | Monitor collection size; target 5,000–10,000 items max; document Railway memory limits |
| V-5 | **Concurrent read (chat query) and write (live ingest) on Railway** | Potential data inconsistency or lock contention | ChromaDB handles concurrent access; wrap writes in a mutex if needed; test under load |
| V-6 | **Persistent Volume detaches on Railway** | All ingested data lost | Railway PV is durable; but document backup strategy (periodic snapshot export) |
| V-7 | **Item upserted with changed tags but same embedding** | Metadata updates but vector stays the same | ChromaDB `upsert` updates metadata; old metadata is overwritten |
| V-8 | **`sentence-transformers` model download fails on Railway** (network issue at startup) | Embedder can't initialize | Pre-download model in Dockerfile; or cache in persistent volume |

---

## 6. RAG Chat Layer (Retriever + Synthesizer)

### 6.1 Retriever

| # | Edge Case | Why It Matters | Expected Behavior |
|---|---|---|---|
| R-1 | **Query returns 0 results** (topic not in dataset) | Synthesizer has no evidence to work with | Return explicit message: "No relevant evidence found in the dataset for this question" |
| R-2 | **Query returns results from only 1 source** | Answer lacks source diversity | Synthesizer discloses: "Based solely on {source} data — other sources had no relevant matches" |
| R-3 | **All top-k results are `evidence_type: proxy`** | No direct Blinkit evidence | Synthesizer explicitly flags entire answer as based on general e-commerce patterns |
| R-4 | **Query is not related to Blinkit at all** (e.g., "What's the weather today?") | Retriever returns low-relevance noise | Synthesizer detects low similarity scores; responds: "This question is outside the scope of the Blinkit dataset" |
| R-5 | **Metadata filter returns 0 results but unfiltered query has results** | User applied overly restrictive filters | Return message suggesting they broaden filters; optionally fall back to unfiltered results |
| R-6 | **top_k is set very high** (e.g., 500) | Slow retrieval; exceeds Gemini context window | Cap `top_k` at 50; return warning if requested value was reduced |

### 6.2 Synthesizer (Gemini)

| # | Edge Case | Why It Matters | Expected Behavior |
|---|---|---|---|
| S-1 | **Gemini API rate limit or timeout** | Chat response fails | Retry once with backoff; if still failing, return error message to frontend |
| S-2 | **Evidence is genuinely contradictory** (50% say X, 50% say Y) | LLM may synthesize false consensus | Prompt enforces split handling: "Present both sides with counts" |
| S-3 | **Evidence is all the same sentiment** (100% negative) | Risk of bias amplification | Synthesizer states sample composition: "All 20 retrieved items express negative sentiment" |
| S-4 | **User asks a multi-part question** ("Why do users not explore AND what categories do they avoid?") | Single retrieval may not cover both parts | Synthesizer addresses each part separately; retriever may need multiple queries (future enhancement) |
| S-5 | **Retrieved chunks exceed Gemini's context window** (unlikely at top_k=20 but possible with long texts) | API call fails with token limit error | Truncate chunks to fit within context window; prioritize highest-similarity chunks |
| S-6 | **Gemini hallucinates a citation** (invents a source_snippet not in retrieved chunks) | Fabricated evidence in answer | Post-process: validate every cited `item_id` exists in the retrieved set; strip invalid citations |
| S-7 | **SSE connection drops mid-stream** | Frontend shows partial answer | Frontend handles stream interruption gracefully; shows partial text + "Connection lost" message |
| S-8 | **User sends same question twice rapidly** | Two concurrent Gemini calls for identical work | Debounce on frontend (300ms); backend could cache recent queries (optional optimization) |

---

## 7. API Layer (FastAPI)

| # | Edge Case | Why It Matters | Expected Behavior |
|---|---|---|---|
| A-1 | **`POST /api/ingest` called without admin token** | Unauthorized scraping/spending | Return HTTP 401 with `{"error": "Admin authentication required"}` |
| A-2 | **`POST /api/ingest` called while another ingest is already running** | Concurrent pipeline runs could corrupt data | Return HTTP 409 with `{"error": "Ingestion already in progress", "job_id": "..."}` |
| A-3 | **`POST /api/ingest` with invalid source name** (e.g., `"twitter"`) | Source doesn't exist | Return HTTP 422 with `{"error": "Unknown source: twitter. Valid: playstore, appstore, reddit, youtube, forums"}` |
| A-4 | **`POST /api/chat` with empty question string** | No query to process | Return HTTP 422 with `{"error": "Question cannot be empty"}` |
| A-5 | **`POST /api/chat` with question exceeding 2,000 characters** | Unnecessarily long input | Truncate to 2,000 chars; or return HTTP 422 with length error |
| A-6 | **`GET /api/health` when ChromaDB failed to load** | Service is partially up | Return HTTP 503 with `{"status": "degraded", "chroma_loaded": false}` |
| A-7 | **CORS request from unauthorized origin** | Cross-origin attack | Only allow configured Vercel frontend origin; reject others with CORS error |
| A-8 | **Request body is not valid JSON** | FastAPI parse failure | Return HTTP 422 with Pydantic validation error details |
| A-9 | **Server receives extremely high traffic** (unlikely but possible) | Railway free tier overwhelmed | No rate limiting in v1; document as a future enhancement; Railway will throttle naturally |
| A-10 | **`GET /api/ingest/status` when no ingest has ever run** | No job to report on | Return `{"status": "idle", "last_run": null}` |

---

## 8. Frontend (Next.js)

| # | Edge Case | Why It Matters | Expected Behavior |
|---|---|---|---|
| U-1 | **SSE stream takes >30 seconds** (slow Gemini response) | User thinks the app is frozen | Show animated typing indicator; display "Still generating..." after 10s |
| U-2 | **Backend is completely unreachable** (Railway down) | All API calls fail | Show error banner: "Backend is currently unavailable. Please try again later." |
| U-3 | **Response contains no citations** (Gemini didn't cite) | Citation cards section is empty | Hide citation section gracefully; show note: "No specific citations were generated" |
| U-4 | **User pastes a very long question** (5,000+ characters) | Exceeds API limit; UI input overflows | Client-side character limit (2,000); show remaining character count |
| U-5 | **User clicks a seed question button while a response is streaming** | Concurrent SSE streams | Cancel the current stream (AbortController); start new query |
| U-6 | **Browser doesn't support SSE / EventSource** (very old browsers) | Streaming breaks | Polyfill EventSource; or fall back to regular POST with full response |
| U-7 | **Response contains markdown formatting** (headers, bold, lists) | Raw markdown renders as plain text | Parse and render markdown in response bubble (use `react-markdown` or similar) |
| U-8 | **Citation card has a very long source_snippet** (500+ characters) | Card overflows layout | Truncate to 200 characters with "Show more" toggle |
| U-9 | **Network switches from WiFi to mobile mid-stream** | SSE connection may drop | Auto-reconnect logic; display partial response + retry option |
| U-10 | **User refreshes the page mid-conversation** | Chat history is lost | v1: Accept this limitation (no persistence). Future: LocalStorage or session-based history |

---

## 9. Deployment & Infrastructure

| # | Edge Case | Why It Matters | Expected Behavior |
|---|---|---|---|
| D-1 | **Railway Persistent Volume is full** | New ingestion writes fail | Monitor disk usage in `/api/health`; alert when >80% capacity |
| D-2 | **Railway free tier credits exhausted** | Service goes offline | Monitor credit usage; set up billing alerts; document fallback (local-only mode) |
| D-3 | **Vercel build fails due to Next.js version mismatch** | Frontend not deployed | Pin Next.js version in `package.json`; test build locally before push |
| D-4 | **Environment variable missing on Railway** (e.g., `GEMINI_API_KEY` not set) | Synthesizer crashes on first chat query | Validate all required env vars at startup; fail fast with clear error message |
| D-5 | **Docker image exceeds Railway's size limits** | Deployment rejected | Use `python:3.11-slim` base; multi-stage build; exclude `data/` from image |
| D-6 | **`sentence-transformers` model downloads at container startup** (slow cold start) | First request times out | Pre-download model in Dockerfile `RUN` step; cache in image layer |
| D-7 | **Railway restarts the container** (routine maintenance) | In-memory state lost | All state in ChromaDB on Persistent Volume; container is stateless except PV |
| D-8 | **Concurrent deploy while ingest is running** | Background ingest job killed mid-write | ChromaDB upsert is idempotent; partial ingest can be resumed; log incomplete jobs |

---

## 10. Data Quality & Pipeline Integrity

| # | Edge Case | Why It Matters | Expected Behavior |
|---|---|---|---|
| Q-1 | **All reviews from a source are from the same month** | Temporal bias — insights don't reflect trends over time | Funnel report includes timestamp distribution; flag if >80% from single month |
| Q-2 | **A single user posts 50+ reviews** (review bombing) | Skews sentiment and category counts | Dedup layer flags items from same `reviewer_name` with similar text; optional per-user cap |
| Q-3 | **Taxonomy doesn't cover an emergent theme** (e.g., "subscription" isn't a category) | Real signal is lost to `"other"` / `"not stated"` | Insight summary generator scans for `"other"` clusters; surfaces emergent themes |
| Q-4 | **Pipeline is re-run with updated taxonomy** | Old tags are stale; new tags may conflict | Re-extraction overwrites tags (upsert by `item_id`); re-embedding updates vectors |
| Q-5 | **Source provides reviews in reverse chronological order only** | Can't paginate to older reviews efficiently | Accept most-recent-first; document that older reviews may be under-represented |
| Q-6 | **YouTube video about "Blinkit" is actually about a different product** | Irrelevant comments enter the pipeline | Stage 2 LLM extraction sets `relevant: false`; not embedded |
| Q-7 | **Groq and Gemini disagree on relevance** (Groq says relevant, Gemini synthesizes a weak answer) | Inconsistency between extraction and synthesis | Acceptable — they serve different roles; Gemini's synthesis quality is the final gate |

---

## Summary Statistics

| Layer | Edge Cases |
|---|---|
| Ingestion (Play Store, App Store, Reddit, YouTube) | 25 |
| Cleaning | 8 |
| Relevance Filter | 6 |
| Extraction (Groq) | 12 |
| Embedding & Vector Store | 8 |
| RAG Chat (Retriever + Synthesizer) | 14 |
| API (FastAPI) | 10 |
| Frontend (Next.js) | 10 |
| Deployment & Infrastructure | 8 |
| Data Quality & Pipeline Integrity | 7 |
| **Total** | **108** |
