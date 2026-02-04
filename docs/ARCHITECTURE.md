# Architecture Overview

This document describes the system architecture and data flow for the Spotify Charts automation system.

## System Architecture (v2.0.0)

### Overview

The system follows a **Selenium-Primary + API Enrichment** architecture:

1. **Selenium Web Scraping** (PRIMARY): Collects track names, positions, artists, and URLs
2. **Spotify API Enrichment** (SECONDARY): Adds metadata like popularity, album art, duration
3. **Report Generation**: Creates HTML and PDF reports with collected data
4. **Cloud Integration**: Uploads to Google Drive and sends email notifications

```
┌─────────────────────────────────────────────────────────────────┐
│                     SPOTIFY CHARTS SYSTEM                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: Data Collection (Selenium Primary + API Enrichment)   │
└─────────────────────────────────────────────────────────────────┘
        │
        ├── SELENIUM (Primary Method) ──────────────────────┐
        │   ├── Navigate to Spotify playlist URL            │
        │   ├── Handle cookie banners                       │
        │   ├── Wait for track list to load                 │
        │   ├── Scroll to load all tracks (virtualized)     │
        │   ├── Extract track data:                         │
        │   │   • Track names                               │
        │   │   • Artist names & URLs                       │
        │   │   • Chart positions (1-50)                    │
        │   │   • Spotify track URLs                        │
        │   │   • Explicit flags                            │
        │   │   • Playlist name                             │
        │   └── Returns: List of 50 track dictionaries      │
        │                                                     │
        └── SPOTIFY API (Enrichment Layer) ────────────────┐
            ├── For each track with valid track_id:        │
            │   ├── Call Spotify API: client.track(id)     │
            │   └── Add/fill missing metadata:             │
            │       • Popularity score (0-100)             │
            │       • Preview URL (30s audio clip)          │
            │       • Album image URL                       │
            │       • Duration (ms and formatted)           │
            │       • Release date                          │
            │       • Album name (if missing)               │
            ├── Genre collection (batch):                  │
            │   ├── Collect unique artist IDs from tracks  │
            │   ├── Batch fetch: client.artists(ids)       │
            │   │   (up to 50 artists per API call)        │
            │   └── Assign combined genres to each track   │
            └── Returns: Enriched track dictionaries        │

┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: Report Generation                                      │
└─────────────────────────────────────────────────────────────────┘
        │
        ├── HTML Dashboard (Analytics) ────────────────────────┐
        │   ├── Cross-playlist analytics and insights          │
        │   ├── Summary statistics (cards)                     │
        │   ├── Top artists analysis (with track dropdowns)    │
        │   ├── Top genres analysis (with track dropdowns)     │
        │   ├── Chart overlap detection                        │
        │   ├── USA vs Global comparison (overlay dropdowns)   │
        │   ├── Popularity stats with range bar & histogram    │
        │   ├── Dynamic histogram (bins based on data range)   │
        │   ├── Explicit content statistics                    │
        │   ├── Playlist titles hyperlinked to Spotify         │
        │   ├── Full track listings per playlist               │
        │   ├── Spotify dark theme styling                     │
        │   ├── File: spotify_charts_dashboard_YYYYMMDD_HHMMSS.html │
        │   └── Deployed to GitHub Pages automatically         │
        │                                                     │
        └── PDF Reports (Separate) ────────────────────────┐
            ├── One PDF per playlist                        │
            ├── Title format: "Spotify [playlist name]"     │
            ├── Single continuous page (no pagination)      │
            ├── Auto-sized to content (~1200-1300mm)        │
            ├── Two-pass rendering for precise height       │
            ├── Enhanced features:                          │
            │   • Popularity bars (green visualization)     │
            │   • Album images next to tracks               │
            │   • Hyperlinked tracks/artists/albums         │
            │   • Analytics metrics (total tracks, artists) │
            │   • Clock icon (🕐) for duration              │
            └── Files: PlaylistName_YYYYMMDD_HHMMSS.pdf     │

┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: GitHub Pages Deployment                                │
└─────────────────────────────────────────────────────────────────┘
        │
        ├── Copy dashboard to docs/index.html
        ├── Upload as Pages artifact
        ├── Deploy to GitHub Pages environment
        └── Dashboard accessible at public URL

┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: Google Drive Upload                                    │
└─────────────────────────────────────────────────────────────────┘
        │
        ├── Create date folder (YYYY-MM-DD)
        ├── Upload HTML dashboard
        ├── Upload all PDF reports
        └── Returns file IDs for tracking

┌─────────────────────────────────────────────────────────────────┐
│  STEP 5: Email Notification                                     │
└─────────────────────────────────────────────────────────────────┘
        │
        ├── Attach HTML dashboard
        ├── Attach all PDF reports
        ├── Send summary email with stats
        └── Complete!
```

---

## Data Flow

### 1. Data Collection Flow

```python
# main.py
with SpotifyClient(use_api_enrichment=True, headless=True) as client:
    tracks = client.get_all_playlist_tracks(playlist_ids)
```

**Inside SpotifyClient:**

```python
def get_playlist_tracks(playlist_id, playlist_name):
    # PRIMARY: Selenium scraping
    tracks = _get_playlist_tracks_selenium(playlist_id, playlist_name)
    # Result: 50 tracks with basic info from web scraping

    # SECONDARY: API enrichment (if enabled)
    if use_api_enrichment:
        tracks = _enrich_tracks_with_api(tracks)
        # Result: Same 50 tracks but with added metadata

    return tracks
```

**Track Data Structure After Collection:**

```python
{
    # FROM SELENIUM (Always Present):
    'position': 1,                                    # Chart position
    'track_name': 'End of Beginning',                # Track name
    'artist': 'Djo',                                 # Artist(s) as string
    'artists': [                                     # Artist(s) with URLs
        {'name': 'Djo', 'url': '...', 'id': '...'}
    ],
    'spotify_url': 'https://open.spotify.com/...',  # Track URL
    'explicit': False,                               # Explicit flag
    'playlist': 'Top Songs - USA',                   # Playlist name
    'playlist_id': '37i9dQZEVXbLp5XoPON0wI',        # Playlist ID (for links)

    # FROM API ENRICHMENT (If Available):
    'popularity': 95,                                # Popularity (0-100)
    'duration': '3:29',                              # Formatted duration
    'duration_ms': 209000,                           # Duration in ms
    'album': 'DECIDE',                               # Album name
    'album_image': 'https://...',                    # Album art URL
    'release_date': '2022-09-16',                    # Release date
    'preview_url': 'https://...',                    # 30s preview
    'genres': ['pop', 'indie pop', 'alt z'],         # Genres (from Artist API)
}
```

---

## Component Details

### SpotifyClient (`src/integrations/spotify_client.py`)

**Purpose**: Orchestrate data collection using Selenium + API

**Key Methods**:
- `get_playlist_tracks(playlist_id)`: Main entry point
- `_get_playlist_tracks_selenium(playlist_id)`: Selenium scraping logic
- `_enrich_tracks_with_api(tracks)`: API enrichment logic (includes genre fetching)
- `_fetch_artist_genres(tracks)`: Batch genre collection from Artist API
- `get_all_playlist_tracks(playlist_ids)`: Collect from multiple playlists

**Parameters**:
- `use_api_enrichment` (bool): Enable Spotify API enrichment (default: True)
- `headless` (bool): Run browser in headless mode (default: True)

---

### SeleniumSpotifyClient (`src/integrations/selenium_spotify_client.py`)

**Purpose**: Web scraping implementation

**Key Features**:
- Headless Chrome automation via undetected-chromedriver
- Smart scrolling to handle virtualized track lists
- Cookie banner dismissal
- Stale element recovery
- Position-based deduplication
- Exact 50-track collection for Top 50 playlists

**Performance**:
- ~8-9 seconds per playlist
- ~2 minutes total for 4 playlists
- 100% accuracy (always collects exactly 50 tracks)

---

### DashboardGenerator (`src/reporting/dashboard_generator.py`)

**Purpose**: Generate comprehensive HTML dashboard with cross-playlist analytics

**Key Methods**:
- `generate_dashboard()`: Main entry point - generates complete dashboard HTML
- `_calculate_analytics()`: Orchestrates all analytics calculations
- `_analyze_artists()`: Artist frequency, multi-playlist presence, and per-artist track details
- `_analyze_genres()`: Genre frequency, cross-playlist presence, and per-genre track details
- `_analyze_overlap()`: Track overlap between charts with categorized track lists
- `_analyze_popularity()`: Popularity distribution analysis
- `_analyze_explicit()`: Explicit content distribution
- `_analyze_playlists()`: Per-playlist statistics
- `_calculate_playlist_analytics()`: Per-playlist metrics including genres, histogram, and track details
- `_build_histogram()`: Static method for dynamic histogram bin calculation based on actual data range
- `_format_track_row()`: Formats individual tracks for table display
- `_format_track_row_with_playlist()`: Formats tracks with playlist column (includes Spotify playlist link)

**Analytics Features**:
- Summary statistics (total tracks, playlists, unique tracks, average popularity, explicit count, unique genres)
- Top 20 artists across all charts with track counts, chart appearances, and track dropdowns (top 10 per playlist)
- Top 20 genres across all charts with track counts and track dropdowns (top 10 per playlist)
- Chart overlap (tracks appearing on multiple playlists)
- USA vs Global Songs comparison with overlay dropdowns (expand without affecting container size)
- Popularity stats per playlist: average score, range bar with average dot, dynamic histogram (5 bins)
- Explicit content statistics with percentages
- Playlist titles hyperlinked to their Spotify URLs
- Playlist column in All Tracks table hyperlinked to Spotify
- Full track listings for each playlist

**Output**: Interactive HTML dashboard deployed to GitHub Pages

### PDFGenerator (`src/reporting/pdf_generator.py`)

**Purpose**: Generate single-page PDF reports

**Algorithm**:
1. **Pass 1**: Render HTML with 100000mm tall page (prevents pagination)
2. **Pass 2**: Measure body element height by traversing DOM tree
3. **Pass 3**: Re-render with exact height (content height + 5mm buffer)

**Result**: Single continuous page PDF (~1200-1300mm for 50 tracks)

---

### GoogleDriveClient (`src/integrations/google_drive_client.py`)

**Purpose**: Upload reports to Google Drive with date organization

**Key Methods**:
- `get_or_create_folder(folder_name)`: Find or create folder
- `upload_file(file_path, folder_id)`: Upload file to specific folder

**Folder Structure**:
```
Your Main Folder/
├── 2026-01-11/
│   ├── spotify_charts_20260111_153020.html
│   ├── Top_Songs_-_USA_20260111_153020.pdf
│   ├── Top_Songs_-_Global_20260111_153020.pdf
│   └── ...
├── 2026-01-12/
│   └── ...
```

---

## Why Selenium-Primary Architecture?

### Previous Architecture (v1.2.1)
- **API First**: Try Spotify API, fallback to Selenium on 404
- **Problem**: Editorial playlists return 404, requiring fallback every time
- **Result**: Extra API calls and error handling overhead

### Current Architecture (v2.0.0)
- **Selenium First**: Always use web scraping for data collection
- **API Second**: Only for enrichment (optional, fills missing fields)
- **Benefits**:
  1. More reliable (Selenium works for ALL playlist types)
  2. Faster (no API rate limits for basic data)
  3. Richer metadata when API available
  4. Graceful degradation if API fails
  5. Better separation of concerns

---

## Error Handling

### Selenium Scraping
- **Cookie banners**: Auto-dismissed with multiple selectors
- **Stale elements**: Container re-location and retry logic
- **Scroll failures**: Multiple fallback scroll strategies
- **Timeout**: 25s wait for initial track list load

### API Enrichment
- **Individual track failures**: Continue with scraped data
- **API unavailable**: Gracefully skip enrichment, use Selenium data
- **Rate limiting**: Not an issue (only enriching, not primary collection)

---

## Configuration

### Environment Variables

```bash
# Spotify API (for enrichment)
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret

# Playlists (4 editorial playlists)
PLAYLIST_1_ID=37i9dQZEVXbLp5XoPON0wI  # Top Songs - USA
PLAYLIST_2_ID=37i9dQZEVXbNG2KDcFcKOF  # Top Songs - Global
PLAYLIST_3_ID=37i9dQZEVXbKCOlAmDpukL  # Top Albums - USA
PLAYLIST_4_ID=37i9dQZEVXbJcin9K8o4a8  # Top Albums - Global

# Report formats
GENERATE_HTML=true   # Combined HTML report
GENERATE_PDF=true    # Separate PDFs per playlist

# Google Drive
GOOGLE_DRIVE_CREDENTIALS_PATH=./credentials/google-drive-credentials.json
GOOGLE_DRIVE_FOLDER_ID=your_folder_id

# Email
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_TO=recipient@gmail.com
```

---

## Testing

### Architecture Test
```bash
python tests/test_selenium_primary_api_enrichment.py
```

Verifies:
- Selenium successfully scrapes tracks (primary)
- API successfully enriches metadata (secondary)
- Data structure compatible with report generation
- Both modes work (with and without enrichment)

### Full System Test
```bash
python main.py
```

Tests entire pipeline:
1. Collect 200 tracks (4 playlists × 50 tracks)
2. Generate 1 HTML + 4 PDF reports
3. Upload to Google Drive (date folder)
4. Send email with attachments

---

## Performance Metrics

| Metric | Value |
|--------|-------|
| Playlists | 4 (editorial) |
| Tracks per playlist | 50 (exactly) |
| Total tracks | 200 |
| Scraping time | ~8-9s per playlist |
| Total collection time | ~2 minutes |
| API enrichment time | ~10-15s per playlist |
| Report generation | ~5-10s |
| **Total runtime** | **~3-4 minutes** |

---

## Future Improvements

### Potential Enhancements
1. **Caching**: Cache API enrichment data to reduce API calls
2. **Parallel scraping**: Scrape multiple playlists simultaneously
3. **Incremental updates**: Only scrape changed tracks
4. **More metadata**: Add mood, energy level, audio features
5. **Historical tracking**: Store track movements over time

### Known Limitations
1. **Preview URLs**: Not always available from Spotify API
2. **Virtualized scrolling**: Requires careful scroll logic
3. **Rate limits**: API enrichment subject to Spotify rate limits
4. **Chrome dependency**: Requires Chrome browser installed

---

## Deployment

### Local Execution
```bash
python main.py
```

### GitHub Actions (Scheduled)
- Runs every Thursday at 11 PM PST (7 AM UTC Friday)
- Dashboard automatically deployed to GitHub Pages after each run
- Fully automated (no local machine needed)
- Uses headless Chrome in CI environment
- Uploads to Google Drive automatically
- Sends email notifications

---

**Last Updated**: 2026-02-04
**Version**: 2.1.0
**Architecture**: Selenium-Primary + API Enrichment (with Genre Collection) + Analytics Dashboard
