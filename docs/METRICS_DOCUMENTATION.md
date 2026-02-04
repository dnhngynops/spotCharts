# Metrics Documentation

## Overview

The system generates two types of reports with calculated metrics:
1. **PDF Reports**: Per-playlist reports with subtitle metrics
2. **HTML Dashboard**: Cross-playlist analytics with interactive features

---

## PDF Report Metrics

### Most Frequent Artists

**Calculation:**
- Counts how many tracks each artist appears in (considering multi-artist collaborations)
- Uses both the structured `artists` list format and fallback to comma-separated string format
- Handles tracks with multiple artists by counting each artist individually

**Display:**
- Shows the **top 3 most frequent artists** in the playlist
- Format: `"Most Frequent Artists: Artist Name 1 (count1), Artist Name 2 (count2), Artist Name 3 (count3)"`
- Example: `"Most Frequent Artists: Olivia Dean (3), Taylor Swift (2), Ella Langley (2)"`

**Location:**
- Displayed in the subtitle section, directly underneath the playlist title
- Visible in both HTML and PDF reports

**Implementation:**
- Calculated in `PDFGenerator._calculate_metrics()` method
- Uses Python's `Counter` from `collections` module for efficient counting

---

## Dashboard Metrics (HTML)

### Summary Cards

| Card | Description | Source |
|------|-------------|--------|
| Total Tracks | Count of all tracks across playlists | `len(all_tracks)` |
| Playlists | Number of monitored playlists | `len(playlist_ids)` |
| Unique Tracks | Deduplicated track count | Track name + artist key dedup |
| Average Popularity | Mean popularity score (0-100) | API enrichment data |
| Explicit Tracks | Count of explicit-flagged tracks | Selenium scraping |
| Unique Genres | Count of distinct genres across all tracks | Artist API batch fetch |

### Top Artists (Global & Per-Playlist)

**Calculation:**
- Counts track appearances per artist across all playlists (global) or within a playlist
- Tracks which playlists each artist appears on
- Collects detailed track lists per artist for dropdown display

**Display:**
- Top 20 artists globally (All Tracks tab), top 10 per playlist
- Each entry shows: artist name, track count badge (clickable), playlist count
- Clicking the track count badge expands a dropdown showing associated tracks with Spotify links

**Implementation:**
- `DashboardGenerator._analyze_artists()` for global stats
- `DashboardGenerator._calculate_playlist_analytics()` for per-playlist stats
- Uses `Counter`, `defaultdict(set)` for playlist tracking, `defaultdict(list)` for track details

### Top Genres (Global & Per-Playlist)

**Calculation:**
- Counts genre frequency across all tracks
- Genres are sourced from Spotify's Artist API (not Track API, which doesn't provide genres)
- Each track inherits genres from all its artists (combined/deduplicated)
- ~54% of tracks receive genre data (some artists have empty genre arrays on Spotify)

**Data Collection:**
- `SpotifyClient._fetch_artist_genres()` collects unique artist IDs from all tracks
- Batch-fetches genres via `self.client.artists(batch)` (up to 50 artists per API call)
- Assigns combined genres to each track as `track['genres']` list

**Display:**
- Top 20 genres globally (All Tracks tab), top 10 per playlist
- Each entry shows: genre name, track count badge (clickable), playlist count
- Clicking the track count badge expands a dropdown showing associated tracks

**Implementation:**
- `DashboardGenerator._analyze_genres()` for global stats
- Per-playlist genre analysis in `_calculate_playlist_analytics()`

### Popularity Stats (Per-Playlist)

**Calculation:**
- Computes average popularity across tracks with valid popularity scores
- Generates dynamic histogram with 5 bins based on actual min-max popularity range
  - Bins are evenly distributed across the data range (not hardcoded 0-20/21-40 etc.)
  - `_build_histogram()` static method handles edge cases (empty data, identical values)
- Each bin shows count and percentage-based bar height (relative to max bin)

**Display:**
- Average popularity score (large centered number)
- "Average Popularity" label
- Popularity range bar with green dot at average position
- Min/max range values displayed at each end
- Visual histogram with labeled axes:
  - Y-axis: "Tracks" (vertical label)
  - X-axis: "Popularity Score"
- CSS flexbox layout with percentage-based bar heights

**Implementation:**
- `DashboardGenerator._build_histogram(pops, num_buckets=5)` calculates dynamic bins
- Histogram data stored as `popularity_histogram` in playlist analytics
- Range bar rendered with `.pop-range-bar`, `.pop-range-fill`, `.pop-range-avg` CSS classes
- Histogram rendered with `.histogram`, `.histogram-col`, `.histogram-bar`, `.histogram-wrapper` CSS classes

### USA vs Global Comparison

**Calculation:**
- Compares tracks between USA Songs and Global Songs playlists
- Categorizes tracks into: USA Only, Both (overlap), Global Only
- Identifies tracks by (track_name, artist) key pairs

**Display:**
- Three boxes showing counts for each category
- Each box is clickable and expands to show the categorized track list
- Boxes expand independently without affecting sibling sizing (`align-items: start`)

**Implementation:**
- `DashboardGenerator._analyze_overlap()` returns counts and track lists
- Track lists include: track name, artist, Spotify URL, chart position

### Playlist Hyperlinks

**Display:**
- Per-playlist tab titles are hyperlinked to their Spotify playlist URL
- Playlist column in the All Tracks table links each entry to its Spotify playlist
- Links constructed from `playlist_id` stored per track during data collection
- `playlist_urls` mapping (playlist name → Spotify URL) built in `generate_dashboard()` and passed to template

### Chart Overlap

**Calculation:**
- Identifies tracks appearing on 2+ playlists
- Groups by track and lists all playlist appearances with positions

**Display:**
- List of overlapping tracks with playlist names and positions

### Explicit Content (Per-Playlist)

**Calculation:**
- Counts explicit-flagged tracks per playlist
- Calculates percentage of total

**Display:**
- Progress bar with percentage and count

---

## Interactive Features

### Track Dropdowns
All "X tracks" badges in Top Artists and Top Genres sections are clickable. Clicking toggles a dropdown list showing the associated tracks with links to Spotify.

**JavaScript:** `toggleDropdown(badge)` function using `badge.closest('li') || badge.closest('.overlap-stat')` for DOM traversal. Supports both `<li>` parents (Top Artists/Genres) and `<div>` parents (USA vs Global overlap stats).

### Tab Navigation
Dashboard uses tab-based navigation: "All Tracks" tab plus one tab per playlist. The `showTab()` JS function updates summary card values (tracks, popularity, explicit count, genres) based on `data-*` attributes on each tab div.

---

## Data Sources

| Metric | Data Source | Method |
|--------|------------|--------|
| Track name, artist, position | Selenium scraping | Always available |
| Explicit flag | Selenium scraping | Always available |
| Popularity score | Spotify Track API | Requires API enrichment |
| Duration | Spotify Track API | Requires API enrichment |
| Album details | Spotify Track API | Requires API enrichment |
| Genres | Spotify Artist API | Batch fetch, ~54% coverage |
| Preview URL | Spotify Track API | Often unavailable |

---

## Future Metrics (Potential Additions)

- **Audio Features**: Tempo, energy, danceability, valence from Spotify Audio Features API
- **New Entries**: Tracks not in previous week's report (requires historical tracking)
- **Trend Velocity**: Week-over-week position movement
- **Artist Growth**: Follower count changes over time
