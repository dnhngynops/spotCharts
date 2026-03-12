# Development Roadmap

This document outlines the planned features and enhancements for the Spotify Charts Automation system, specifically tailored for music A&R use cases.

## Current Status (v3.5.0)

### ✅ Fully Implemented Features

**Data Collection**
- Selenium-primary scraping with Spotify API enrichment
- 100% collection accuracy (50 tracks per playlist)
- Genre data via Spotify Artist API (~54% coverage)
- Track popularity, duration, album images, explicit flags

**Backend / Persistence**
- Supabase (PostgreSQL) as canonical data store — normalized schema v2.0 (`sql/schema.sql`)
- `SupabaseClient` persists playlists, scrapes, songs, albums, artists, credits, genres, playlist positions per run
- Genius API integration for writer/producer/engineer credits (`src/integrations/genius_client.py`)
- Role normalization (`src/utils/role_normalizer.py`) and name normalization (`src/utils/name_normalizer.py`)
- Entity classifier for person vs company detection (`src/utils/entity_classifier.py`)
- Company/representation CRUD layer (`src/integrations/representation_client.py`)
- Three-path credit upsert handling dual unique constraints on `credits` table (v3.3.0)

**Jinja2 HTML Dashboard** (`templates/`)
- Interactive analytics dashboard deployed to GitHub Pages
- On-demand Supabase profile fetching (artist/track/album modals, lazy per-playlist analytics)
- Cross-playlist chart overlap, genre breakdowns, popularity histograms, explicit distribution
- Per-playlist PDF reports via WeasyPrint

**React Dashboard** (`frontend/`) — Vite + React + TypeScript
- Full port of Jinja2 dashboard functionality into component-based React app
- Supabase live queries for trend badges (▲▼NEW) and profile modal data
- Three rounds of visual parity fixes completed (v3.3.0–v3.5.0); All Tracks tab now closely mirrors Jinja2
- Album modal: charting track row highlights, popularity distribution mini bar chart
- All Tracks tab: track/artist/album names are dual-purpose Spotify `<a>` links (modal on click, Spotify on Ctrl/Cmd+click)
- Popularity and Explicit stats cards: teal hover lift effect, even grid distribution, playlist names hyperlinked to Spotify
- Filter bar: teal hover on toggle/reset buttons, no browser outline rings
- Deployed independently at `http://localhost:5173` (dev); production deploy TBD
- Remaining parity work: per-playlist tabs, ChartOverlap section, ProfileModal, CollapsibleList, Dashboard Header, Summary Cards

**Automation**
- GitHub Actions workflow (weekly, Thursday 11 PM PST)
- Google Drive upload + email delivery
- GitHub Pages deployment of latest Jinja2 dashboard

### 📊 Data Collection Capabilities
- Track IDs, names, artists (with URLs), albums
- Spotify track URLs (clickable links)
- Artist profile URLs (Selenium collection)
- Chart positions (1-50)
- Explicit content flags
- Playlist metadata and playlist IDs (for hyperlinking)
- **Genre data** (from Artist API, ~54% coverage)
- Popularity scores, duration, album images (API enrichment)
- Song credits: writers, producers, engineers via Genius API

### 📈 Dashboard Analytics
- Summary cards (tracks, playlists, unique tracks, average popularity, explicit count, unique genres)
- Top 20 artists with track count dropdowns (All Tracks tab); top 10 per playlist
- Top 20 genres with track count dropdowns (All Tracks tab); top 10 per playlist
- Popularity stats with range bar and dynamic histogram (labeled axes)
- USA vs Global comparison with overlay dropdowns
- Chart overlap detection with multi-chart track listings
- Explicit content distribution
- Playlist titles hyperlinked to Spotify
- Artist/track/album profile modals with on-demand Supabase fetching

---

## Phase 1: Analytics Foundation (v2.0.0)

**Priority: High**
**Status:** Not started (v1.1.0 and v1.2.x focused on collection accuracy)

### 1.1 Data Persistence Layer
**File:** [src/core/database.py](../src/core/database.py)

- [ ] Implement SQLite database for historical data
- [ ] Create schema for playlist snapshots
- [ ] Track history storage (track appearances over time)
- [ ] Artist and album metadata caching
- [ ] Database migration utilities

**Impact:** Enables trend analysis and historical comparisons

### 1.2 Track Analytics
**File:** [src/analytics/track_analytics.py](../src/analytics/track_analytics.py)

- [ ] Fetch audio features from Spotify API (tempo, energy, danceability, etc.)
- [ ] Individual track performance metrics
- [ ] Cross-playlist presence tracking
- [ ] Popularity trend calculation
- [ ] Release date analysis

**Impact:** Provides deeper insights into track characteristics

### 1.3 Weekly Scheduling
**File:** [.github/workflows/spotify-charts.yml](../.github/workflows/spotify-charts.yml)

- [ ] Change cron schedule from daily to weekly
- [ ] Add configurable schedule options
- [ ] Implement manual trigger with parameters

**Impact:** Aligns with weekly A&R workflow

---

## Phase 2: Trend Analysis & Discovery (v1.2.0)

**Priority: High**
**Timeline: After Phase 1**

### 2.1 Trend Analyzer
**File:** [src/analytics/trend_analyzer.py](../src/analytics/trend_analyzer.py)

- [ ] Week-over-week change detection (new entries, drops, position shifts)
- [ ] Playlist velocity metrics (track movement speed)
- [ ] Artist trending analysis (increasing presence)
- [x] Genre collection and display (implemented v2.0.0 via Artist API)
- [ ] Genre trend identification (requires historical tracking)
- [ ] Momentum scoring system

**Impact:** Identify rising tracks and artists early

### 2.2 Discovery Engine
**File:** [src/analytics/discovery_engine.py](../src/analytics/discovery_engine.py)

- [ ] New artist identification (first-time appearances)
- [ ] Independent artist detection (follower count thresholds)
- [ ] Breakout track pattern recognition
- [ ] Collaboration network mapping
- [ ] Market signal detection (geographic, genre crossover)

**Impact:** Core A&R discovery functionality

### 2.3 Enhanced Reporting
**File:** [src/reporting/report_generator.py](../src/reporting/report_generator.py)

- [ ] Executive summary generation
- [ ] Key metrics dashboard
- [ ] Top 10 trending tracks/artists
- [ ] New discoveries section
- [ ] Visual charts and graphs (matplotlib/plotly)

**Impact:** Digestible, actionable reports for stakeholders

---

## Phase 3: Advanced Analytics (v2.0.0)

**Priority: Medium**
**Timeline: Future**

### 3.1 Predictive Analytics
- [ ] Machine learning model for breakout prediction
- [ ] Track success probability scoring
- [ ] Genre classification and trend forecasting
- [ ] Optimal playlist placement suggestions

### 3.2 Multi-Source Integration
- [ ] YouTube Music trending data
- [ ] TikTok viral sound tracking
- [ ] SoundCloud emerging artist metrics
- [ ] Shazam discovery charts
- [ ] Chart aggregation (Billboard, etc.)

### 3.3 Advanced Visualizations
- [ ] Interactive web dashboard (Flask/Streamlit)
- [ ] Real-time playlist monitoring
- [ ] Network graphs (collaboration, genre relationships)
- [ ] Geographic heatmaps
- [ ] Custom filtering and exploration tools

---

## Phase 4: Collaboration & Workflow (v2.1.0)

**Priority: Low**
**Timeline: Future**

### 4.1 Alert System
- [ ] Configurable alert rules (follower thresholds, velocity triggers)
- [ ] Slack/Discord integration for notifications
- [ ] Email alerts for high-priority discoveries
- [ ] SMS notifications (Twilio integration)

### 4.2 Team Features
- [ ] Internal notes and annotations on tracks/artists
- [ ] Collaborative rating system
- [ ] Contact management (artist, label, manager info)
- [ ] Export to CRM systems

### 4.3 Enhanced Exports
- [ ] PDF reports with executive summary
- [ ] Multi-tab Excel workbooks (by playlist, artist, trends)
- [ ] Google Sheets live dashboards
- [ ] PowerPoint presentation generation
- [ ] API endpoint for custom integrations

---

## Technical Improvements

### Code Quality
- [ ] Unit test coverage (pytest)
- [ ] Integration tests for API clients
- [ ] Code documentation (docstrings)
- [ ] Type hints throughout codebase
- [ ] Linting and formatting (black, flake8)

### Performance
- [ ] Async/await for API calls (aiohttp)
- [ ] Caching layer for Spotify API responses
- [ ] Database query optimization
- [ ] Parallel processing for analytics

### Infrastructure
- [ ] Docker containerization
- [ ] Cloud deployment options (AWS Lambda, Google Cloud Functions)
- [ ] Scalable database (PostgreSQL option)
- [ ] CI/CD pipeline enhancements
- [ ] Monitoring and logging (Sentry, CloudWatch)

---

## A&R-Specific Enhancements

### Discovery Intelligence
- [ ] Label affiliation lookup (MusicBrainz integration)
- [ ] Producer/songwriter credit tracking
- [ ] Similar artist recommendations
- [ ] Genre migration pattern analysis
- [ ] Regional market breakout detection

### Competitive Analysis
- [ ] Competitor playlist tracking
- [ ] Market share analysis by label/artist
- [ ] Release strategy pattern identification
- [ ] Feature collaboration frequency analysis

### Data Enrichment
- [ ] Social media metrics (Instagram, TikTok followers)
- [ ] Streaming platform comparison (Spotify vs Apple Music)
- [ ] Concert/tour data integration (Songkick, Bandsintown)
- [ ] Press coverage tracking
- [ ] Radio airplay data

---

## Getting Started with Development

### Next Steps for Contributors

1. **Implement Database Layer** (Phase 1.1)
   - Start with [src/core/database.py](../src/core/database.py)
   - Create SQLite schema for snapshots
   - Add save/retrieve methods

2. **Add Audio Features** (Phase 1.2)
   - Extend [src/integrations/spotify_client.py](../src/integrations/spotify_client.py)
   - Add `get_audio_features()` method
   - Update track data structure

3. **Build Trend Analyzer** (Phase 2.1)
   - Implement [src/analytics/trend_analyzer.py](../src/analytics/trend_analyzer.py)
   - Compare weekly snapshots
   - Calculate velocity metrics

4. **Create Report Generator** (Phase 2.3)
   - Implement [src/reporting/report_generator.py](../src/reporting/report_generator.py)
   - Design executive summary template
   - Add visualization components

### Development Guidelines

- Follow existing code structure and naming conventions
- Add comprehensive docstrings for all functions
- Write unit tests for new features
- Update this roadmap as features are completed
- Document API rate limits and quota considerations

---

## Questions or Suggestions?

If you have ideas for new features or improvements, please open an issue or submit a pull request!
