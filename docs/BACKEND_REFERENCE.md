# Backend Reference: A&R Analytics Platform

> **Location**: `backend copy/` (gitignored; do not commit)
> **Purpose**: A companion A&R data backend that shares the same Supabase schema family. Contains production-ready modules we can port into `src/` incrementally to expand this system toward the full A&R analytics vision described in `docs/ARCHITECTURE.md`.

---

## What It Is

A **4-phase music industry data pipeline** targeting:
- 26 years of Billboard Hot 100 history (~132K chart entries, ~3K unique songs)
- Spotify editorial playlists (19 playlists, ~1,500-2,000 songs)
- Genius API credits (writers, producers, engineers — targeting 50K-200K songs at scale)
- Automated representation discovery: labels, publishers, management, booking agents

This is effectively the "future state" of our current `main.py` pipeline. The long-term roadmap in `CLAUDE.md` explicitly targets credits, labels, publishers, management, and discovery data — all of which are already implemented or scaffolded in the backend copy.

---

## Directory Map

```
backend copy/
├── config/settings.py              # Env vars (Supabase, Spotify, Genius, logging)
├── database/
│   ├── connection.py               # Supabase singleton client
│   ├── migrations/001-012_*.sql    # Full migration history (28 tables)
│   ├── docs/SCHEMA.md              # 28-table schema reference + 6 views
│   └── functions/                  # SQL helper functions (e.g. get_random_songs)
├── shared/
│   ├── apis/spotify_client.py      # Enhanced Spotify client (retry, backoff, genres)
│   ├── apis/genius_client.py       # Genius API wrapper (credits, descriptions)
│   ├── credit_processing/entity_classifier.py  # Company vs individual detection
│   └── utils/
│       ├── name_normalizer.py      # Deduplication via normalized names
│       └── album_filter.py         # Intelligent album filtering
├── phases/
│   ├── phase1/                     # Billboard + Playlist ingestion (85% complete)
│   │   ├── billboard_ingestion.py  # Multi-artist parser (50+ patterns, known bands)
│   │   ├── artist_confidence_scorer.py  # 0-100 confidence scores
│   │   ├── step1_collect_basic_data.py
│   │   └── step2_enrich_spotify_data.py
│   ├── phase2/                     # Credits & Discography (scaffolded, not started)
│   │   ├── credit_extraction.py    # Genius API extraction
│   │   ├── discography_collector.py
│   │   └── role_normalizer.py
│   ├── phase3/                     # Genre Classification (future)
│   └── phase4/                     # Representation Discovery (core complete, ~90%)
│       ├── run_discovery.py        # CLI entry point
│       ├── search/
│       │   ├── search_queries.py   # 13 artist search query templates
│       │   ├── publication_detector.py  # Multi-factor publication scoring
│       │   └── stealth_browser.py  # Selenium + Chrome profile (bot bypass)
│       ├── extractors/
│       │   ├── patterns.py         # 31+ regex patterns
│       │   ├── pattern_extractor.py
│       │   └── wikipedia_scraper.py
│       ├── adapters/
│       │   ├── discovery_adapter.py        # CRUD: discovery_urls, extractions
│       │   └── representation_adapter.py   # CRUD: companies, representations
│       └── config/data/
│           ├── publishers.json     # 31 known publishers
│           ├── excluded_domains.json  # 30 excluded domains
│           └── music_publication_domains.json  # 21 music publications
├── scripts/
│   ├── process_billboard_parallel.py  # 4-process parallel ingestion
│   └── deduplicate_songs.py
└── data/
    ├── playlists.txt               # 19 Spotify editorial playlists
    └── billboard/                  # 2000-2025 Billboard JSON files
```

---

## Capability Comparison

| Capability | Our System (`src/`) | Backend Copy | Integration Path |
|---|---|---|---|
| Spotify playlist scraping | ✅ Selenium + API | ✅ Similar | Reference for improvements |
| Spotify API enrichment | ✅ Basic | ✅ Enhanced (retry, backoff) | Port retry logic to `spotify_client.py` |
| Billboard ingestion | ❌ | ✅ 26y, 132K entries | Port `phase1/billboard_ingestion.py` |
| Multi-artist parsing | Basic | ✅ 50+ patterns, confidence scoring | Port `billboard_ingestion.py` parser |
| Name deduplication | Basic | ✅ `normalize_credit_name()` + DB unique constraint | Port `name_normalizer.py` |
| Song credits (writers, producers) | ❌ | ✅ Genius API (`phase2/`) | Port `genius_client.py` + `credit_extraction.py` |
| Role normalization | ❌ | ✅ Scaffolded (`role_normalizer.py`) | Port role normalization system |
| Genre classification | Spotify genres only | ✅ Planned Phase 3 | Reference for Phase 3 design |
| Company/label data | ❌ | ✅ `companies` + `representations` tables | Port schema + `representation_adapter.py` |
| Representation discovery | ❌ | ✅ Phase 4 (Google search + regex) | Port `phase4/` discovery system |
| Entity classification | ❌ | ✅ `entity_classifier.py` | Port to `src/utils/` |
| Confidence scoring | ❌ | ✅ 0-100 per entry | Port `artist_confidence_scorer.py` |
| Parallel processing | ❌ | ✅ 4-process Billboard ingestion | Reference pattern for future scale |
| Wikipedia scraping | ❌ | ✅ `wikipedia_scraper.py` | Port to `src/integrations/` |

---

## Data Model Differences

### Backend Copy: Unified Credits Table
```
credits          (id, name, normalized_name, spotify_id, primary_role, ...)
song_credits     (song_id, credit_id, role_id, confidence, ...)
roles            (id, canonical_name, role_type)
raw_role_names   (role text → canonical role mapping)
```

### Our System: Separate Artist Handling
Current pipeline tracks artists inline on songs. The backend copy's `credits` table unifies artists, producers, writers, and engineers into one entity — this is the target schema for `sql/schema.sql`.

### Backend Copy: Company / Representation Layer
```
companies        (id, name, company_type: label|publisher|management|booking)
representations  (artist_id, company_id, role, start_date, confidence, source_url)
company_staff    (company_id, credit_id, role)
```
These map directly to `Future` rows in our `sql/schema.sql` table list.

### Backend Copy: Discovery System
```
discovery_urls         (credit_id, url, category, confidence, ...)
discovery_extractions  (url_id, pattern_type, extracted_value, confidence, ...)
discovery_search_logs  (credit_id, query, results_count, ...)
```

---

## Integrations Available

| Service | Backend Copy File | Our Equivalent |
|---|---|---|
| Spotify API (enhanced) | `shared/apis/spotify_client.py` | `src/integrations/spotify_client.py` |
| Genius API | `shared/apis/genius_client.py` | None yet |
| Google Search (headless) | `phases/phase4/search/stealth_browser.py` | None yet |
| Wikipedia scraping | `phases/phase4/extractors/wikipedia_scraper.py` | None yet |
| Supabase (advanced) | `database/connection.py` | `src/integrations/supabase_client.py` |

---

## Recommended Integration Order

These are ordered by value delivered vs. complexity:

### 1. Port Enhanced Spotify Client Utilities (Low effort, high value)
- Retry logic + exponential backoff from `shared/apis/spotify_client.py`
- Better rate limit handling for enrichment step

### 2. Port Name Normalization (Low effort, high value)
- `shared/utils/name_normalizer.py` → `src/utils/name_normalizer.py`
- Prevents duplicate credits/artists in Supabase

### 3. Add Genius API Integration (Medium effort, high value)
- `shared/apis/genius_client.py` → `src/integrations/genius_client.py`
- Enables song credits (writers, producers) for Phase 2

### 4. Port Multi-Artist Parser + Confidence Scorer (Medium effort)
- `phases/phase1/billboard_ingestion.py` parser
- `phases/phase1/artist_confidence_scorer.py`
- These plug into existing artist parsing in our pipeline

### 5. Billboard Historical Ingestion (Medium effort, high value)
- `phases/phase1/` pipeline scripts + data files
- Expands from editorial playlists → full historical chart context

### 6. Company / Representation Schema + Adapter (High effort, high value)
- Apply `database/migrations/009_add_representation_system.sql` to our Supabase
- Port `phases/phase4/adapters/representation_adapter.py`

### 7. Phase 4 Representation Discovery (High effort, high value)
- Full `phases/phase4/` discovery system
- Delivers automated label/publisher/management discovery per artist

---

## Key Files to Read First When Implementing

When starting any of the integration steps above, read these first:

- `backend copy/database/docs/SCHEMA.md` — full 28-table schema reference
- `backend copy/shared/apis/genius_client.py` — Genius API patterns
- `backend copy/phases/phase1/billboard_ingestion.py` — multi-artist parsing
- `backend copy/phases/phase4/run_discovery.py` — Phase 4 entry point
- `backend copy/phases/phase4/PHASE4_PROGRESS_SUMMARY.md` — current status
- `backend copy/shared/utils/name_normalizer.py` — deduplication logic

---

## Environment Variables Needed (Backend Copy Additions)

These are in `.env.example` but not yet wired up in our pipeline:

```bash
# Genius API (for credits extraction)
GENIUS_ACCESS_TOKEN=

# Phase 4 discovery
GOOGLE_SEARCH_ENABLED=false
CHROME_PROFILE_PATH=
```

---

## Notes

- The backend copy targets the **same Supabase project** (same credentials). The migration files are the authoritative schema evolution path.
- `sql/schema.sql` in our repo is the v2.0 base. The backend copy's `migrations/009-012` add the representation, discovery, and role normalization layers on top.
- Do not commit the `backend copy/` folder — keep it gitignored. Reference it locally; port code into `src/` when ready.
