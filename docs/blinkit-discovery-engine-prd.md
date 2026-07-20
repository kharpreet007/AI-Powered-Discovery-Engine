# PRD: AI-Powered Discovery Engine — Blinkit User Behavior Insights

**Part of:** Part 1 (Discovery Engine) — precedes any proposed product solution (Part 2)
**Owner:** [Your name]
**Status:** Draft v1

---

## 1. Problem Statement

There's a working hypothesis in quick-commerce product thinking that Blinkit users disproportionately reorder from a narrow set of familiar categories (groceries, daily essentials) and rarely experiment with the newer categories the platform now offers (electronics, beauty, pharmacy, and more). **This hasn't been systematically tested.** Product teams have no evidence-backed understanding of whether this is actually true, and if so, why — the reasoning lives scattered across app store reviews, Reddit threads, and social discussions, in unstructured natural language, at a volume no human team can manually read through.

We need an AI-powered discovery engine that ingests this scattered, unstructured feedback and makes it queryable — turning thousands of individual reviews and comments into evidence-backed answers that confirm, complicate, or refute this hypothesis, so that any proposed product solution (Part 2) is grounded in real user voice rather than assumption.

---

## 2. Objective

Build a working system that can answer, with citations to real user-generated text, questions such as:

1. Why do users repeatedly buy from the same categories?
2. What prevents users from exploring new categories?
3. How do users discover products today?
4. What role do habits play in shopping behavior?
5. What information do users need before trying a new category?
6. What frustrations emerge repeatedly?
7. Which user segments are more likely to experiment?
8. What unmet needs emerge consistently across discussions?

**This system is a research instrument, not the product itself.** Its output feeds the Part 2 problem statement/solution — it does not propose solutions on its own.

---

## 3. Scope

**Timeline constraint: 2-3 days, single owner, built via Antigravity.** This drives a tiered scope below rather than treating all 7 sources as equally committed.

**In scope — Tier 1 (must-ship):**
- App Store reviews, Play Store reviews, Reddit discussions (including broadened quick-commerce queries), and YouTube video comments — all fast to build via existing free libraries/APIs
- Full pipeline against Tier 1 sources: extraction, RAG chat, insight summary
- A RAG-based chat interface where a stakeholder can ask natural-language questions and get answers grounded in cited source snippets
- A byproduct insight summary answering the 8 seed questions directly

**In scope — Tier 2 (best-effort, non-blocking):**
- Community forums and other social media (excluding YouTube, which is Tier 1) — attempted only after Tier 1 ships end-to-end; these rely on unstable scraping, so they're the most likely to consume unplanned time (see Section 13)

**Out of scope:**
- Any recommendation, feature, or UX solution — that's Part 2
- Real-time/streaming ingestion — v1 is a batch snapshot per source, refreshable on demand
- Guaranteeing equal volume across all seven sources — access/cost realities (see Section 6) mean some sources will yield far more data than others; the system should surface this imbalance transparently rather than hide it

---

## 4. Users of This System

- **Primary:** You (as PM/researcher), using the chat to interrogate the data while drafting Part 2
- **Secondary:** Anyone reviewing your work who wants to verify a claim traces back to real user language

---

## 5. Research Taxonomy (drives the extraction step)

Every ingested item gets tagged against this schema so raw text becomes structured, queryable signal:

| Tag category | What it captures |
|---|---|
| `category_mentioned` | Canonical Blinkit category the text refers to (see fixed list below), or `other` / `not stated` |
| `category_tier` | `core` (Fruits & Vegetables, Dairy & Bakery, Snacks & Beverages, Staples/Grocery, Personal Care & Cleaning) or `exploratory` (Electronics & Accessories, Beauty & Skincare, Pharmacy/Health, Baby Care, Pet Care, Stationery & Print, Home & Kitchen tools, Books) — directly powers Q1/Q2 without relying on free-text clustering |
| `behavior_type` | repeat-purchase / habit / one-time-try / abandoned-attempt / never-tried |
| `discovery_channel` | app home feed, search, ad, word-of-mouth, social media, other |
| `barrier_type` | trust/quality doubt, price anchoring, lack of info, delivery/logistics concern, no need perceived, other |
| `frustration` | free-text summary + severity (low/med/high) |
| `unmet_need` | free-text summary of an explicit or implied want |
| `segment_signal` | one of: student, working professional, homemaker/family shopper, elderly/senior, not stated — kept to what's reliably inferable from text, not deep demographic guesswork |
| `sentiment` | positive / neutral / negative |
| `evidence_type` | `direct` (about Blinkit/quick-commerce specifically) or `proxy` (general e-commerce pattern used as a hypothesis signal, not direct evidence) |
| `source_snippet` | the exact excerpt supporting the tags (for citation) |

**Canonical category list** (used to constrain `category_mentioned` — keeps tagging consistent instead of free-text variants like "makeup" vs. "beauty" vs. "cosmetics" fragmenting the count):
- Core: Fruits & Vegetables, Dairy & Bakery, Snacks & Beverages, Staples/Grocery, Personal Care & Cleaning
- Exploratory: Electronics & Accessories, Beauty & Skincare, Pharmacy/Health, Baby Care, Pet Care, Stationery & Print, Home & Kitchen, Books

---

## 6. Data Sources & Access Method

**Constraint: every source below uses free, unauthenticated, or free-tier access only — no paid APIs, no licensed listening tools.**

| Source | Build Tier | Access method (free only) | Notes |
|---|---|---|---|
| App Store reviews | **Tier 1** | `app-store-scraper` / RSS review feeds | Free, no auth, high volume |
| Play Store reviews | **Tier 1** | `google-play-scraper` | Free, no auth, high volume |
| Reddit discussions + Quick-commerce discussions | **Tier 1 (value)** | Arctic Shift + PullPush.io (free, keyless, community-maintained Reddit data mirrors) via [BAScraper](https://github.com/maxjo020418/BAScraper) wrapper — a single connector run with two query sets (Blinkit-branded + broadened quick-commerce terms). Arctic Shift handles subreddit-scoped queries; PullPush handles Reddit-wide queries. Mandatory cross-fallback between the two services. | These are **one connector, not two** — both query sets write to the same raw store keyed by Reddit post/comment ID, so a post matching both queries is stored once and simply carries both query-match tags. This prevents double-counting the same post under two source labels in volume reporting (FR12). **Note:** Reddit has closed self-service developer registration ("Responsible Builder Policy") and .json URL access returns 403 as of May 2026, so PRAW / official API is no longer an option. Both mirrors are volunteer-maintained with no uptime guarantee; data may lag on very recent threads. |
| Community forums | **Tier 2 (best-effort)** | Direct scraping of public forum pages (e.g. Quora, MouthShut, consumer-complaint boards) | No API needed, just public page scraping; no unified connector — built forum-by-forum; expect lower volume per forum |
| YouTube comments | **Tier 1** | YouTube Data API (free quota) on Blinkit-related videos/reviews | YouTube comments are a reliable free proxy for social conversation. Captures direct evidence of user behavior discussed in video reviews. |
| Other Social media conversations | **Tier 2 (best-effort)** | Scraping of publicly visible, unauthenticated posts | X/Twitter's official API is no longer free, so it's excluded |

Given free-only access, expect **Tier 2 sources** to be the thinnest and least reliable — they depend on scraping public pages rather than a stable API, so page-structure changes and rate-limiting are ongoing maintenance risks (see Section 13). Given the 2-3 day timeline, Tier 1 should be built, extracted, and validated end-to-end (through the RAG chat) *before* any Tier 2 work starts — if time runs out, you ship a complete Tier-1-only system rather than a broken 7-source one.

## 7. System Architecture

```
[App Store] [Play Store] [Reddit+QC] [Forums] [Social Media] [Product Reviews]
     Tier1        Tier1       Tier1     Tier2        Tier2           Tier1
        │           │          │          │          │              │
        └─────┬─────┴────┬─────┴───┬──────┴────┬─────┴──────┬───────┘
              ▼
        Ingestion Layer (per-source connector → raw store, deduped by post/item ID → metadata: source, date, rating)
               ▼
        Cleaning Layer (dedup, language detection/translation, spam filter)
               ▼
        Relevance Filter Stage 1 (free, rule-based — see Section 7a) — discards obvious generic noise before any LLM call
               ▼
        Extraction Layer (single LLM call per item → structured tags + `relevant` flag, JSON)
               ▼
        Vector Store (embeddings of `relevant: true` items only, e.g. Chroma)
    ─────────────────────────── everything above runs locally (Section 7b) ───────────────────────────
               ▼
        RAG Chat Layer (retrieval + Gemini synthesis + citations) — deployed to Railway
               ▼
     [Chat UI]  +  [Auto-generated insight summary vs. the 8 questions]
```

### 7a. Relevance Filter (cost & space control)

Raw scraped text is a mix of substantive signal (category/behavior/trust/discovery-relevant) and generic noise (app crashes, "worst app ever," "good service" with no other content) that isn't useful for answering the 8 research questions. Filtering happens *before* embedding, since embeddings (not raw text storage) are the actual space driver, and at this project's target volume (500-1000 items/source) a second model adds engineering overhead without a meaningful cost saving.

**Stage 1 — free, rule-based filter (no LLM call):**
- Discard items below a length threshold (e.g. <20-30 characters) with no canonical category name (Section 5) present
- Discard items matching only app-technical vocabulary (crash, lag, freeze, login/OTP/payment failure) **and** containing no behavior-signal words (try, first time, always order, compare, trust, quality, brand)
- Anything ambiguous passes through to Stage 2 rather than being guessed on

**Stage 2 — single extraction call, one model:**
No separate classifier. The same Section 5 extraction prompt/model adds one more output field, `relevant: true/false`, alongside the usual tags. Items surviving Stage 1 all get this one LLM call; only items tagged `relevant: true` get embedded into the vector store. This keeps the whole pipeline to a single model rather than introducing a second one for a marginal saving at this volume.

**Important exception:** delivery/logistics complaints are not blanket-discarded as noise — they're a legitimate `barrier_type` value when tied to a category decision (e.g. "won't order meat, delivery's too slow" is category-avoidance signal). The filter criterion is "does this touch a category/behavior/discovery/trust signal," not "is this a complaint."

**Nothing is deleted** — raw text and full tags for all ingested items (including `relevant: false` ones) stay in the raw/tagged store for audit/reprocessing if filter criteria need tuning later. Only `relevant: true` items proceed to embedding.

### 7b. Deployment Architecture

Ingestion, cleaning, the relevance filter, extraction, and embedding can run **locally via CLI, or directly on the deployed backend (Railway)** via an API endpoint. The pipeline is built as a shared core module.

The backend deployed to Railway serves the RAG Chat Layer (retrieval + Gemini synthesis) and exposes authenticated endpoints to trigger live ingestion. It relies on a Persistent Volume for ChromaDB to store data across deploys.

Note on risk: Scraping from Railway's datacenter IPs carries a high risk of being blocked by anti-bot detection (unlike residential home IPs). Additionally, running heavy ingestion work on the server consumes compute credits. For these reasons, local ingestion is still supported and recommended for bulk backfilling, while server-side ingestion enables on-demand live refreshes.

**Suggested stack:** Python + FastAPI backend, Groq API (e.g., Llama-3) for extraction, Gemini API for RAG synthesis, Chroma as the vector store (built locally, deployed as a static snapshot), a lightweight chat frontend.

---

## 8. Functional Requirements

| # | Requirement |
|---|---|
| FR1 | System ingests Blinkit reviews from Play Store and App Store via public scraping libraries (Tier 1) |
| FR2 | System ingests Reddit posts/comments via a single connector run using Arctic Shift (subreddit-scoped queries) and PullPush (Reddit-wide queries), with mandatory cross-fallback between services. Both Blinkit-branded and broadened quick-commerce query sets write to the same raw store, deduped by post/comment ID so a post matching both isn't double-counted (Tier 1 by value, unofficial access) |
| FR3 | System ingests community forum content (e.g. Quora, MouthShut, consumer-complaint boards) via per-forum connectors (Tier 2, best-effort) |
| FR4 | System ingests other social media conversations via free channels only — scraping of publicly accessible, unauthenticated posts — with no paid API or licensed tool (Tier 2, best-effort) |
| FR5 | System ingests YouTube comments via the YouTube Data API (free quota) on Blinkit-related videos/reviews (Tier 1) |
| FR6 | System detects non-English content (notably Hinglish/code-mixed and regional-language text) and normalizes/translates it before taxonomy tagging, rather than silently dropping or mis-tagging it |
| FR7 | Every ingested item is tagged against the Section 5 taxonomy via LLM extraction, stored as structured JSON, using the canonical category list (not free-text categories) |
| FR7a | Before embedding, every item passes through the Relevance Filter (Section 7a): a free rule-based Stage 1, then a single extraction call that tags the item *and* sets `relevant: true/false`. Only `relevant: true` items are embedded; raw text and tags for `relevant: false` items are retained but not embedded |
| FR7b | The ingestion pipeline is a shared core module that runs both locally (producing a vector store snapshot) and on the deployed Railway backend (writing to a persistent volume), supporting both bulk local ingest and live server ingest via an authenticated API. |
| FR8 | Tagged items are embedded and stored in a vector database for semantic retrieval |
| FR9 | A chat interface accepts natural-language questions and returns an answer synthesized from retrieved items, distinguishing `direct` evidence from `proxy` evidence (e.g. "general e-commerce pattern, not Blinkit-specific") whenever proxy-tagged items are used |
| FR10 | Every chat answer includes citations/links back to the specific source snippets used, tagged with which source it came from |
| FR11 | System can generate a standalone summary answering all 8 seed research questions on demand |
| FR12 | System reports, per source, the full funnel — raw ingested → passed relevance filter → fully tagged — so gaps or heavy filtering in one channel are visible rather than silently backfilled by others |
| FR13 | When retrieved evidence is split or contradictory on a question, the chat presents the split (with relative frequency) rather than synthesizing a false consensus |

---

## 9. Non-Functional Requirements

- **Zero paid-API dependency:** every ingestion connector must run on free/unauthenticated access; if a source can't reach meaningful volume this way, that's a documented gap, not a reason to add a paid API
- **Legal/ToS disclosure:** scraping App Store, Play Store, and forum pages sits in a ToS gray area for most of these platforms. This build is for personal research/case-study purposes only, not commercial redistribution — this should be stated explicitly wherever the output is shared, rather than left implicit
- **Cost awareness:** batch extraction (LLM calls) should use Groq for high-throughput and low cost, while the RAG synthesis utilizes Gemini to keep reasoning quality high but spend reasonable
- **Data provenance:** every stored item retains source, timestamp, and original text — no summarization at ingestion time
- **Privacy:** no PII beyond what's already public in the review/comment; no attempt to de-anonymize users
- **Transparency of coverage:** since volume will vary a lot by source (Section 6), the system should report per-source counts alongside any insight, so a thin source doesn't get silently treated as equally strong evidence as a deep one

---

## 10. Success Criteria

- Chat can answer all 8 seed questions with at least 3 distinct cited examples each
- Retrieval is topically relevant (spot-check: manually verify 10 random Q&A pairs against source data)
- Insight summary surfaces at least one theme *not* explicitly asked about in the 8 seed questions (validates the taxonomy catches emergent signal, not just what we went looking for)
- Any quantified claim in an answer states its sample size (e.g. "12 of 40 reviews mention...") — a thin Tier 2 source should never read with the same confidence as a deep Tier 1 one
- At least one test question with genuinely mixed evidence returns a split answer rather than a false consensus

---

## 11. Build Plan (mapped to Antigravity specs — 2-3 days, stretchable if needed)

**Day 0 — Account/API setup (before any coding starts)**
Register a YouTube Data API key (for Tier 1). Reddit no longer requires API registration — the connector uses keyless community mirrors (Arctic Shift + PullPush). Do API key setup first and separately from coding time — approval/verification can have unpredictable delay outside your control, and it shouldn't sit on the critical path once building begins.

**Day 1 — Tier 1 ingestion + extraction**
1. **Spec A1 — Core Ingestion:** connectors for Play Store, App Store, Reddit (merged brand + broadened queries, deduped), YouTube; raw storage schema with per-source metadata
2. **Spec B — Extraction Pipeline:** taxonomy-driven LLM tagging (canonical categories, `evidence_type`, `segment_signal` enum, `relevant` flag per Section 7a), language detection/translation for non-English text, structured JSON output
3. **Dry-run gate — before scaling up:** run Spec A1 + Spec B end-to-end on a small sample (~20-30 items per Tier 1 source) *before* ingesting the full target volume. Spot-check the tagged output: are categories firing correctly, is `evidence_type` distinguishing direct vs. proxy correctly, is the `relevant` flag discarding the right things? Fix taxonomy/prompt issues here, on ~100 items, rather than discovering them after ingesting thousands. Only once this looks right, scale to the full 500-1000/source target

**Day 2 — RAG chat + validation**
4. **Spec C — RAG Chat Interface:** embedding, vector store, retrieval + synthesis with citations tagged by source and `evidence_type`, chat UI — built locally, then deployed per Section 7b
5. Validate end-to-end against Tier 1 data only: run the Section 10 success criteria in full. This is the point where you have a complete, demoable system even if nothing else gets built

**Day 3 — Insight summary, then Tier 2 if time allows**
6. **Spec D — Insight Summary:** on-demand report generation against the 8 seed questions, with per-source volume reporting
7. **Spec A2 — Tier 2 (best-effort):** community forums and other social connectors, only if Day 1-2 finished with room to spare — feed into the same Spec B/C pipeline rather than a separate one

If Day 3 runs out before Spec A2, ship the Tier-1-only system and document Tier 2 as a documented gap (Section 12), not a failure — a working 5-source system beats a broken 7-source one.

---

## 12. Assumptions & Constraints

- Single owner, 2-3 day build via Antigravity — scope is tiered accordingly (Section 3); Tier 2 sources are explicitly non-blocking
- All sources must be reached through free/unauthenticated access — no paid APIs or licensed listening tools anywhere in the pipeline
- **Recency window:** ingest reviews/posts from roughly the last 12-18 months only — older content may describe an app version or category assortment that no longer exists
- Expected volume varies significantly across sources — Tier 1 sources are stable and high-volume, while Tier 2 (dependent on page scraping rather than a stable API) will likely be thinner if attempted
- Volume target: enough per source (suggest 500–1000+ items where access allows) to make thematic patterns credible rather than anecdotal; sources that can't hit this should be labeled directional rather than conclusive in the insight output
- **No second reviewer:** the taxonomy is validated by spot-check only (Section 13), not an independent reviewer — acceptable for a single-owner build, but worth stating rather than implying rigor that isn't there
- Architecture favors simplicity (local vector store, no distributed infra) over production scale

---

## 13. Open Risks

- Reddit signal specific to Blinkit may be thinner than Play/App Store reviews — the merged query set (Section 6) helps, but volume should still be checked early rather than assumed
- Both Reddit data mirrors (Arctic Shift, PullPush) are volunteer-maintained community projects with no uptime guarantee. If both are simultaneously unreachable, the ingestion run should fail gracefully and report zero Reddit items in the per-source funnel (FR12), rather than silently proceeding as if Reddit data were included
- Archive mirrors may lag on very recent Reddit threads (hours to days); the most recent 1–7 days of posts may be absent. The 12–18 month recency window means this rarely matters, but it should be documented as a known limitation
- Tier 2 (community forums, other social) sourcing depends on scraping public pages without an API — pages can change structure, rate-limit, or block scraping entirely; if a Tier 2 connector breaks mid-build, the fallback is to drop it and document the gap, not burn remaining time debugging it under deadline pressure
- If Tier 2 is attempted and succeeds, coverage will still be visibly thinner than Tier 1 — the insight output should say so rather than implying even coverage across all sources
- Combining sources of very different volume and quality (a few hundred forum/social posts vs. thousands of app reviews) risks over-weighting whichever source is largest — retrieval/synthesis should be checked for this bias, not just assumed to average out
- Scraping from Railway's datacenter IPs carries a high risk of anti-bot blocking (e.g., Cloudflare on Reddit/Play Store). If server-side ingestion fails consistently, a paid proxy rotation service (e.g., BrightData, ScraperAPI) will need to be integrated.
- LLM tagging quality depends on taxonomy clarity — plan to spot-check and iterate the taxonomy after the first batch, not just build it once and move on
- The Relevance Filter (Section 7a) trades completeness for cost/space savings — an overly aggressive Stage 1 rule (e.g. discarding all delivery-complaint language) could silently drop real `barrier_type` signal. Spot-check a sample of *discarded* items early, not just the ones that survived, to confirm the filter isn't cutting real signal
