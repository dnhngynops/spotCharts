## Project overview

This repo is an automated Spotify charts reporting system and A&R analytics platform. It:
- Collects tracks from 4–5 configured Spotify editorial playlists
- Uses Selenium web scraping as the primary data source, plus Spotify API enrichment for metadata
- Persists every run to Supabase as the intermediate data store (historical charts, songs, albums, artists)
- Generates an interactive HTML analytics dashboard and per‑playlist PDF reports
- Uploads reports to Google Drive and sends them via email
- Can run locally, via cron, or via GitHub Actions on a schedule

The long-term goal is a full A&R analytics platform: the Supabase database is designed to eventually hold credits, labels, publishers, management, and discovery data sourced from Genius, AllMusic, web scraping, and manual research — not just Spotify chart data.

You should treat the existing `README.md` and `docs/` as the **source of truth** for behavior, architecture, and setup. Prefer to reference or extend those docs instead of re‑explaining things from scratch.

## High‑level architecture

- **Entry point**: `main.py`
  - Orchestrates the full pipeline: collection → enrichment → Supabase persistence → reporting → delivery.
- **Core configuration**: `src/core/config.py`
- **Integrations** (`src/integrations/`):
  - `selenium_spotify_client.py`: scrapes editorial playlists from the Spotify web app.
  - `spotify_client.py`: Spotify Web API + enrichment logic (popularity, genres, album/artist metadata).
  - `supabase_client.py`: writes each pipeline run to Supabase (songs, albums, artists, playlist positions).
  - `google_drive_client.py`: handles Drive upload and folder organization.
  - `email_client.py`: sends report emails and attachments.
- **Apps** (`src/apps/`): One sub-package per distinct product view.
  - `src/apps/shell/layout.py`: shared Jinja2 `Environment` + `FileSystemLoader`; all app generators call `get_env()` from here.
  - `src/apps/charts/generator.py`: `DashboardGenerator` — builds the interactive HTML analytics dashboard.
  - `src/apps/charts/pdf.py`: `PDFGenerator` + `TableGenerator` — generate single‑page, playlist‑specific PDFs using WeasyPrint.
  - `src/apps/deal_projector/generator.py`: `DealProjectorGenerator` stub (future revenue/deal calculator).
  - `src/apps/rosters/generator.py`: `RostersGenerator` stub (future A&R rosters view).
- **Reporting** (`src/reporting/`): Backwards-compatibility shims only — re-export classes from `src.apps.charts.*`. Do not add new logic here.
- **Utilities** (`src/utils/`):
  - `browser.py`: Chrome WebDriver management and Selenium tuning.
  - `helpers.py`: shared helper functions.
- **Templates** (`templates/`): Split by concern.
  - `templates/shell/base.html`: outer shell — full `<head>` CSS, sidebar, `{% include %}` directives for all app views.
  - `templates/charts/dashboard.html`: charts view HTML + JS (included by shell).
  - `templates/charts/table.html`: per-playlist PDF table template (used by WeasyPrint).
  - `templates/deal_projector/projector.html`: deal projector view HTML + JS (included by shell).
  - `templates/components/profile_modal.html`: shared artist/track/album profile modal HTML + JS.
  - `templates/rosters/placeholder.html`, `templates/account/placeholder.html`: coming-soon stubs.
- **Database schema**: `sql/schema.sql` — the Supabase schema (v2.0). Run this once in a new Supabase project to create all tables. See `docs/ARCHITECTURE.md` for schema design details and `docs/SECRETS_CHECKLIST.md` for required env vars.
- **Automation**:
  - Cron examples live in `README.md`.
  - GitHub Actions workflow is in `.github/workflows/spotify-charts-automation.yml`.

When modifying or adding functionality, follow the existing module boundaries (integrations vs apps vs utils) and keep orchestration logic in `main.py` or a dedicated coordinator module. New product views belong in `src/apps/<name>/` with a matching template subtree under `templates/<name>/`.

## How environment and data flow work

- Configuration and secrets come from `.env` (copied from `.env.example`) and from GitHub Actions secrets in CI.
- Raw and intermediate data lives in `data/` and `logs/` (both gitignored).
- **Supabase** is the canonical intermediate store. After each collection run, `SupabaseClient.save_run()` upserts all enriched data into the normalized schema. The dashboard JS client can query Supabase directly for historical analytics.
- Final artifacts:
  - HTML dashboard(s) and PDF reports go into `output/`.
  - GitHub Actions also deploys the latest dashboard to GitHub Pages.
- The pipeline is designed so that:
  1. Selenium/web scraping collects baseline playlist data.
  2. Spotify API enriches that data with additional fields (popularity, duration, genres, album full track listings, artist images/followers, etc.).
  3. `SupabaseClient` persists the enriched data to Supabase in this order: playlists → scrape record → credits (artists) → credit_genres → albums → songs → song_credits → song_genres → playlist_songs.
  4. Reporting modules compute analytics/aggregations and render HTML/PDFs.
  5. Integrations push those artifacts to Drive and email.

If you need to change data structures, make sure the same objects are consistently handled across:
`selenium_spotify_client.py` → `spotify_client.py` (enrichment) → `supabase_client.py` (persistence) → `src/apps/charts/generator.py` / `src/apps/charts/pdf.py`.

## Supabase schema summary (sql/schema.sql)

The schema is normalized and pipeline-first. Key tables written to by the current pipeline:

| Table | Written by pipeline? | Purpose |
|---|---|---|
| `playlists` | Yes | One row per Spotify playlist (or external chart source) |
| `playlist_scrapes` | Yes | One row per pipeline run |
| `songs` | Yes | One row per unique track (keyed by Spotify ID) |
| `albums` | Yes | One row per unique album; includes `all_tracks` JSONB |
| `credits` | Yes | Artists and all industry people (unified entity) |
| `song_credits` | Yes | Song ↔ credit ↔ role junction |
| `song_genres` | Yes | Song ↔ genre junction |
| `credit_genres` | Yes | Artist ↔ genre junction |
| `album_genres` | Future | Album ↔ genre junction |
| `album_credits` | Future | Album-level credits (exec producers, A&R) |
| `playlist_songs` | Yes | Position per track × playlist × run |
| `companies` | Future | Labels, publishers, management firms |
| `representations` | Future | Artist ↔ company relationships |
| `discovery_*` | Future | Web scraping pipeline for A&R intelligence |
| `roles`, `raw_role_names`, `role_mapping_*` | Future | Role normalization pipeline |

Billboard and other external charts are stored as `playlists` rows with `source_type = 'billboard'` (not a separate table).

`supabase_client.py` targets the v2.0 schema in `sql/schema.sql`. Apply that schema once in the Supabase SQL Editor before running the pipeline with Supabase enabled.

## How to run things (for reference)

- **Local run**: `python main.py` (after `pip install -r requirements.txt` and configuring `.env`).
- **Preview/reports utilities** (see `scripts/`):
  - `preview_dashboard.py`: rebuild dashboard from cached or fresh data.
  - `generate_all_pdfs.py`: generate PDFs for all playlists only.
  - `setup.sh` / `run_with_libs.sh`: convenience scripts for local setup and PDF dependencies.
- **CI/CD**:
  - GitHub Actions workflow schedules runs and deploys GitHub Pages.
  - See `docs/GITHUB_ACTIONS_SETUP.md` and `docs/SECRETS_CHECKLIST.md` for details.

You should not change any of the scheduling or deployment behavior without first checking the docs in `docs/` and the existing workflow file.

## Conventions for code changes

- **Languages & tooling**:
  - Python 3.8+ with dependencies in `requirements.txt`.
  - Tests live under `tests/` (with both unit and integration tests).
- **Style & structure**:
  - Keep modules small and focused; avoid putting API, scraping, and reporting code into the same file.
  - Prefer pure functions and small helpers in `src/utils/` where appropriate.
  - Reuse existing helper functions and patterns instead of inventing new ones.
- **Adding dependencies**:
  - Add Python packages to `requirements.txt`.
  - Avoid unnecessary or heavyweight libraries if built‑in or already‑used ones work.

## Sensitive data & safety rules

- Never hard‑code secrets or credentials. All secrets must remain in:
  - `.env` (local only, not committed), or
  - GitHub Actions secrets and credentials files under `credentials/` (gitignored).
- Do not print, log, or expose access tokens, API keys, or passwords.
- Do not modify `.gitignore` to include credential or data paths currently protected.
- Avoid changing anything under `credentials/`, `data/`, `logs/`, or `output/` besides documenting or using them.

## How Claude should behave on this project

- **Understand context first**:
  - Read `README.md` and relevant files under `src/` and `docs/` before large changes.
  - Use the documented architecture instead of guessing at data flow.
- **Preserve behavior**:
  - When refactoring, keep public function signatures and behavior the same unless the user explicitly wants a change.
  - Maintain existing Selenium + API enrichment strategy and the HTML/PDF outputs unless instructed otherwise.
- **Be test‑ and doc‑aware**:
  - Update or add tests under `tests/` when changing behavior.
  - If you add significant new behavior, briefly mention it in `docs/CHANGELOG.md` or other appropriate docs.
- **Be explicit about effects**:
  - Clearly state which modules/functions you modified.
  - If a change affects the pipeline (e.g., playlist collection, enrichment, or reporting), explain the impact end‑to‑end.

Use this file as your primary high‑level guide so you don’t need the user to re‑explain how the system works for each new chat.

