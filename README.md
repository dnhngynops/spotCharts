# Spotify Charts Automation

Automated system to fetch tracks from 4 editorial Spotify playlists, generate formatted reports (HTML & PDF), upload to Google Drive, and email the results.

## Features

### **Data Collection (v1.5.0)**
- **Selenium Primary**: Uses web scraping as primary method for maximum reliability
- **API Enrichment**: Spotify API adds metadata (popularity, preview URLs, album art, duration)
- **100% Accuracy**: Collects exactly 50 tracks per playlist (all 4 playlists working perfectly)
- **Lightning Fast**: ~8-9 seconds per playlist (~2 minutes total for 4 playlists)
- **Robust & Reliable**: Multiple fallback strategies prevent collection failures
- **Headless Browser**: Runs invisibly in background with performance optimizations

### **Report Generation (v1.6.0)**
- **Separate Playlist PDFs**: Each playlist generates its own PDF report with "Spotify [playlist name]" title format
- **Single Continuous Page**: PDFs are rendered as one scrollable page with no blank space
- **Enhanced Visual Design**: 
  - Popularity bars with green visualization
  - Album images next to track names
  - Hyperlinked track, artist, and album names
  - Clock icon (🕐) for duration column
  - Bold rank numbers and optimized spacing
- **Analytics Metrics**: Displays total tracks and most frequent artists under title
- **Multi-Format Output**: Generate HTML and/or PDF reports
- **Configurable**: Choose which formats to generate (HTML, PDF, or both)
- **Spotify Theming**: Beautiful dark mode styling maintained across all formats
- **Professional PDFs**: Print-ready reports using WeasyPrint with precise content measurement

### **Data Captured**
- Track names, artists (with profile URLs), albums
- Spotify track URLs (clickable links for every track)
- Chart positions (1-50), explicit flags
- Playlist metadata and timestamps

### **Automation & Delivery (v1.5.0)**
- **Fully Remote**: Runs on GitHub Actions - no need to keep your computer on
- **Custom Scheduling**: Configurable schedule (default: Every Thursday at 11 PM PST)
- **Date-Based Organization**: Reports automatically organized by date in Google Drive
- **Cloud Upload**: Automatic upload to Google Drive with folder creation
- **Email Notifications**: Sends report attachments to configured recipients
- **Fully Automated**: Zero manual intervention required after setup

## Setup

### Prerequisites

- Python 3.8+
- Google Chrome browser (for Selenium web scraping)
- Spotify API credentials (Client ID and Client Secret)
- Google Drive API credentials (OAuth 2.0)
- Email service credentials (Gmail SMTP or other service)
- **For PDF generation**: System libraries (Pango, Cairo, GDK-PixBuf)

### Installation

#### 1. Install system dependencies for PDF generation

**macOS:**
```bash
brew install pango gdk-pixbuf libffi
```

**Ubuntu/Debian:**
```bash
sudo apt-get install libpango-1.0-0 libpangoft2-1.0-0 libgdk-pixbuf2.0-0 libffi-dev libcairo2
```

**Note for macOS users**: You may need to set the library path before running:
```bash
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"
```

#### 2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

#### 3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

#### 4. Set up Google Drive API:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a project and enable Google Drive API
   - Create OAuth 2.0 credentials
   - Download credentials JSON file

#### 5. Set up Spotify API:
   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Create an app
   - Get Client ID and Client Secret

### Configuration

Edit your `.env` file to specify:
- Spotify playlist IDs (4 editorial playlists)
- Google Drive folder ID and credentials path
- Email recipients and SMTP settings
- **Report formats** (HTML, PDF, or both)
- Output directory for generated reports

```bash
# Report Generation Configuration
GENERATE_HTML=true   # Generate HTML reports (true/false)
GENERATE_PDF=true    # Generate PDF reports (true/false) - always single continuous page
OUTPUT_DIR=./output  # Directory for generated reports
```

**PDF Generation Notes:**
- PDFs are always generated as single continuous pages (no multi-page option)
- Each playlist gets its own PDF file (e.g., `Top_Songs_-_USA_20260111.pdf`)
- HTML generates one combined file with all playlists
- PDFs are auto-sized to fit content exactly (no excessive blank space)

## Usage

### Run manually:
```bash
python main.py
```

### Schedule with cron:
```bash
# Edit crontab
crontab -e

# Add line to run daily at 9 AM
0 9 * * * cd /path/to/spotifyCharts && /usr/bin/python3 main.py
```

### Automate with GitHub Actions (Recommended):

**Runs completely remotely - your computer doesn't need to be on!**

**Schedule**: Every Thursday at 11:00 PM PST (7:00 AM UTC Friday)

1. Push code to GitHub repository
2. Configure GitHub Secrets (14 required secrets)
3. Workflow runs automatically on schedule
4. Manual trigger available for testing

**Quick Setup**:
```bash
# Push to GitHub
git add .
git commit -m "Setup Spotify Charts automation"
git push origin main

# Then configure secrets in GitHub repository:
# Settings → Secrets and variables → Actions
```

**Detailed Guides**:
- 📘 [GitHub Actions Setup Guide](docs/GITHUB_ACTIONS_SETUP.md) - Complete configuration instructions
- ✅ [Secrets Checklist](docs/SECRETS_CHECKLIST.md) - Quick reference for all required secrets
- 🏗️ [Architecture Overview](docs/ARCHITECTURE.md) - System design and data flow

See [.github/workflows/spotify-charts-automation.yml](.github/workflows/spotify-charts-automation.yml) for workflow configuration.

## Project Structure

```
spotifyCharts/
├── main.py                          # Main orchestration script
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
├── .gitignore                       # Git ignore rules
├── README.md                        # This file
│
├── src/                             # Source code directory
│   ├── core/                        # Core functionality
│   │   ├── config.py                # Configuration settings
│   │   └── database.py              # Data persistence (placeholder)
│   │
│   ├── integrations/                # External service integrations
│   │   ├── spotify_client.py        # Spotify API integration with Selenium fallback
│   │   ├── selenium_spotify_client.py  # Web scraping for editorial playlists
│   │   ├── google_drive_client.py   # Google Drive API integration
│   │   └── email_client.py          # Email sending functionality
│   │
│   ├── analytics/                   # Analytics modules (placeholders)
│   │   ├── track_analytics.py       # Track performance analytics
│   │   ├── trend_analyzer.py        # Trend analysis
│   │   └── discovery_engine.py      # A&R discovery features
│   │
│   ├── reporting/                   # Report generation
│   │   ├── table_generator.py       # Table generation and formatting
│   │   ├── pdf_generator.py         # PDF report generation (v1.3.0)
│   │   └── report_generator.py      # Comprehensive reports (placeholder)
│   │
│   └── utils/                       # Utility functions
│       ├── browser.py               # Chrome WebDriver manager with optimizations
│       └── helpers.py               # Common helper functions
│
├── scripts/                         # Development utilities
│   └── setup.sh                     # Initial setup script
│
├── tests/                           # Test suite
│   ├── integration/                 # Integration tests
│   │   ├── test_separate_pdfs.py    # PDF generation per playlist test
│   │   └── test_final_verification.py  # Comprehensive verification test
│   └── *.py                         # Various unit and debug tests
│
├── templates/                       # HTML templates
│   └── table_template.html
│
├── docs/                            # Documentation
│   ├── SETUP.md                     # Detailed setup guide
│   ├── CHANGELOG.md                 # Version history
│   ├── ROADMAP.md                   # Development roadmap
│   └── QUICK_START.md               # Quick start guide
│
├── data/                            # Data storage (gitignored)
├── output/                          # Generated reports (gitignored)
├── logs/                            # Application logs (gitignored)
├── credentials/                     # API credentials (gitignored)
│
└── .github/                         # GitHub Actions workflows
    └── workflows/
        └── spotify-charts.yml       # Automation workflow
```

## Recent Updates

**v1.7.1 Cross-Platform PDF Rendering Fix (Jan 2026):**
- **Font Weight Fix**: Track names now use font-weight 600 (was 500) for consistent rendering on Ubuntu/GitHub Actions
- **Gradient Fix**: Pre-blended solid colors replace alpha-based hex colors for email PDF viewer compatibility
- **Result**: PDFs render identically on macOS, Ubuntu, and in email attachments

**v1.4.0 Single-Page PDFs with Playlist Separation (Jan 2026):**
- **Separate Playlist PDFs**: Each playlist now generates its own individual PDF file
- **Playlist Title Integration**: PDF titles display the playlist name, playlist column removed from tables
- **True Single-Page PDFs**: All PDFs rendered as one continuous scrollable page (no pagination)
- **Precise Content Measurement**: PDFs auto-sized to content height with minimal blank space (5mm buffer)
- **Two-Pass Rendering**: Measures content height accurately then renders with exact dimensions
- **Format**: 210mm width × ~1200-1300mm height for 50-track playlists

**v1.3.0 PDF Report Generation (Jan 2025):**
- **Multi-Format Reports**: Generate HTML and/or PDF reports with configurable output
- **PDF Pipeline**: New `pdf_generator.py` module using WeasyPrint for professional PDF generation
- **Configurable Formats**: Environment variables to control HTML/PDF generation independently
- **Spotify Theming Preserved**: Dark mode styling maintained across all report formats
- **GitHub Actions Updated**: Automatic PDF dependency installation in CI/CD workflow
- **Dual Upload**: Both HTML and PDF reports uploaded to Google Drive and emailed

**v1.2.1 Album Playlist Collection Fix (Dec 2024):**
- **Fixed Albums Playlists**: Resolved stale container issue causing under-collection
- **Improved Container Selection**: Now validates containers are actually scrollable before use
- **Robust Scrolling**: Multiple fallback strategies prevent collection failures
- **Test Results**: All playlists (Songs & Albums) now collect exactly 50 tracks ✓
- **Performance**: ~8-9 seconds per playlist with 100% data accuracy
- **Data Improvement**: 40% increase in Album playlist collection (30 → 50 tracks)

**v1.2.0 Collection Accuracy Fix (Dec 2024):**
- **Fixed Songs Playlists**: Now correctly collects exactly 50 tracks (previously 67 due to virtualized scrolling over-collection)
- **Post-Deduplication Trimming**: Implemented smart trimming to return exactly 50 tracks when positions 1-50 are complete
- **Test Results**: Songs playlists (Top Songs USA/Global) now collect exactly 50 tracks ✓

**v1.1.0 Selenium Integration & Performance:**
- **Selenium Web Scraping**: Automatic fallback for editorial playlists (Spotify deprecated API access)
- **Headless Mode**: Browser runs invisibly in background (enabled by default)
- **Performance Optimizations**: 60-70% faster scraping through disabled images/CSS and optimized scrolling
- **Benchmark**: ~2-3 minutes to scrape 4 playlists (~150 tracks total, known limitation with virtualized scrolling)
- **Chrome Driver Management**: Automatic version detection with webdriver-manager fallback

**v1.0.0 Restructure:**
- Reorganized codebase into modular structure under `src/` directory
- Created placeholder modules for future analytics and reporting features
- Updated to weekly scheduling (Monday 9 AM UTC) in GitHub Actions
- Added comprehensive development roadmap in `docs/ROADMAP.md`
- Improved project organization for scalability

See [docs/ROADMAP.md](docs/ROADMAP.md) for planned features and development timeline.

---

## Current System Performance

### **Collection Metrics (v1.2.1)**

| Metric | Value | Status |
|--------|-------|--------|
| **Total Playlists** | 4 editorial playlists | ✅ All working |
| **Tracks per Playlist** | 50/50 (100%) | ✅ Perfect accuracy |
| **Total Tracks** | 200 tracks | ✅ Complete dataset |
| **Collection Time** | ~2 minutes 17 seconds | ✅ Fast |
| **Per Playlist Time** | 8-9 seconds average | ✅ Optimized |
| **Success Rate** | 100% (4/4 playlists) | ✅ Reliable |
| **Data Quality** | Complete metadata + URLs | ✅ Comprehensive |

### **Data Collected Per Track**
- ✅ Track ID, name, album
- ✅ Artist name(s) with Spotify profile URLs
- ✅ Track Spotify URL (clickable link)
- ✅ Chart position (1-50)
- ✅ Explicit content flag
- ✅ Playlist metadata

### **Known Limitations**
- ⚠️ Album images not collected (Selenium - disabled for performance)
- ⚠️ Track duration not available (Selenium limitation)
- ⚠️ Popularity scores not available (Selenium limitation)

*These limitations only affect Selenium-scraped editorial playlists. API-accessible playlists would have complete data.*

---

## Environment Variables

Required environment variables (see `.env.example`):
- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`
- `GOOGLE_DRIVE_CREDENTIALS_PATH` (path to credentials JSON)
- `EMAIL_SMTP_SERVER`
- `EMAIL_SMTP_PORT`
- `EMAIL_USERNAME`
- `EMAIL_PASSWORD`
- `EMAIL_FROM`
- `EMAIL_TO` (comma-separated list)

