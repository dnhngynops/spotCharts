# Changelog

All notable changes to the Spotify Charts automation project.

---

## [1.7.1] - 2026-01-21

### Fixed - Cross-Platform PDF Rendering Consistency

- **Track Name Font Weight**: Changed from `font-weight: 500` to `font-weight: 600`
  - Issue: Track names and artist names appeared identical in GitHub Actions (Ubuntu) PDFs
  - Cause: Ubuntu lacks Helvetica Neue font which supports weight 500 (Medium)
  - Ubuntu falls back to DejaVu Sans which only has weights 400 and 700
  - Weight 500 was falling back to 400, making tracks and artists look the same
  - Solution: Weight 600 renders distinctly bolder on both macOS and Ubuntu

- **Gradient Rendering in Email PDF Viewers**: Replaced alpha-based colors with pre-blended solid colors
  - Issue: Gradient appeared as solid green block when PDFs downloaded from email
  - Cause: 8-digit hex colors (e.g., `#1a4a2ecc`) use PDF transparency features
  - Email PDF viewers have limited transparency group support
  - Solution: Pre-computed solid colors that simulate the alpha-blended appearance

  | Stop | Old (alpha) | New (pre-blended) |
  |------|-------------|-------------------|
  | 0% | `#1a4a2e` | `#1a4a2e` |
  | 2% | `#1a4a2ecc` | `#194029` |
  | 5% | `#1a4a2e66` | `#182c20` |
  | 8% | `#1a4a2e33` | `#18221c` |
  | 12% | `#1a4a2e15` | `#181c19` |
  | 18%+ | `#181818` | `#181818` |

### Technical Changes
- **Template Updates** (`templates/table_template.html`):
  - Line 195: `.track-name` font-weight changed from 500 to 600
  - Lines 27-35: Gradient now uses pre-blended solid colors instead of alpha hex values
  - Removed dynamic `gradient_color` variable support (was unused)
  - Added comments explaining the pre-blended color approach

### Benefits
- PDFs now render consistently across macOS, Ubuntu, and email PDF viewers
- Track names are visually distinct from artist names on all platforms
- Gradient effect preserved without relying on PDF transparency features
- Reduced PDF complexity (fewer XObject references and transparency groups)

---

## [1.7.0] - 2026-01-20

### Changed - Visual Styling Enhancements
- **Spotify-Style Gradient Background**: Added vertical gradient that flows from header through track rows
  - Gradient starts with customizable color at top (default: dark green `#1a4a2e`)
  - Rapid fade: 100% → 80% → 40% → 20% → 8% opacity within first 18% of container
  - Transitions smoothly to surface color, concentrated near title area
  - Matches Spotify's signature gradient effect from playlist artwork

- **Gray Title Text**: Changed title from green (`theme.primary`) to theme gray (`theme.text_secondary` / `#B3B3B3`)
  - "Spotify" label and playlist name now display in light gray
  - Consistent with Spotify's secondary text color throughout the theme
  - Provides softer visual appearance against the gradient background

- **Semi-Transparent Table Elements**: Table rows allow gradient to show through
  - Table header: `rgba(0, 0, 0, 0.2)` - subtle darkening
  - Table rows: `rgba(0, 0, 0, 0.1)` - very subtle darkening
  - Table background: fully transparent
  - Softer borders: `rgba(255, 255, 255, 0.1)` for subtle separators

### Technical Changes
- **Template Updates** (`templates/table_template.html`):
  - Added `gradient_color` template variable for customizable gradient base color
  - Changed `.container` background from solid to linear gradient
  - Updated `.header h1`, `.spotify-label`, `.playlist-name` colors to `{{ theme.text_secondary }}`
  - Changed `.spotify-table`, `thead`, `tbody tr` to transparent/semi-transparent backgrounds
  - Updated border colors to use rgba for softer appearance

### Benefits
- More authentic Spotify visual appearance
- Gradient creates visual interest and depth
- Gray title provides softer, more cohesive appearance
- Professional, polished report aesthetic

---

## [1.6.0] - 2026-01-12

### Changed - PDF Report Enhancements
- **Title Format**: Changed from playlist name only to "Spotify [playlist name]" format
  - Removed playlist image display next to title
  - Simplified header design for cleaner appearance
- **Popularity Column**: Fixed right margin to match left side padding
  - Ensures proper spacing and prevents content cutoff
  - All columns now have consistent padding (15px)

### Technical Changes
- **Template Updates** (`templates/table_template.html`):
  - Removed `.playlist-image` CSS and image display logic
  - Updated title format in template: `Spotify {{ playlist_name }}`
  - Adjusted table cell padding to ensure symmetric margins
  - Fixed container padding and box-sizing for proper layout

- **PDF Generator** (`src/reporting/pdf_generator.py`):
  - Removed `playlist_image` parameter from template rendering
  - Simplified template rendering logic

### Benefits
- Cleaner, more professional title format
- Consistent column spacing prevents content cutoff
- Improved visual hierarchy and readability

---

## [1.5.0] - 2026-01-12

### Added - GitHub Actions Automation
- **Automated Scheduling**: GitHub Actions workflow for weekly automation
  - Schedule: Every Thursday at 11:00 PM PST (7:00 AM UTC Friday)
  - Manual trigger available for testing
  - Runs completely remotely (no local machine needed)

- **Workflow Features**:
  - Automatic Chrome installation for Selenium
  - System dependencies pre-installed (WeasyPrint libraries)
  - Environment configuration via GitHub Secrets (14 secrets)
  - Date-based Google Drive folder creation
  - Email notifications with report attachments
  - Error logging and artifact upload on failure
  - ~3-4 minutes execution time per run

- **Documentation**:
  - Created `docs/GITHUB_ACTIONS_SETUP.md` - Complete setup guide with troubleshooting
  - Created `docs/SECRETS_CHECKLIST.md` - Quick reference for all 14 required secrets
  - Created `docs/ARCHITECTURE.md` - Comprehensive system architecture documentation
  - Created `.github/workflows/spotify-charts-automation.yml` - Workflow definition

### Changed - Architecture Refactor
- **Selenium as Primary Method**: Web scraping is now the PRIMARY data collection method
  - Previously: Spotify API first, Selenium fallback for 404 errors
  - Now: Selenium scraping first for all playlists (100% reliable for editorial playlists)
  - Guarantees consistent data collection across all playlist types

- **API Enrichment Layer**: Spotify API used ONLY for enriching track metadata
  - Adds popularity scores, preview URLs, album images, duration
  - Fills in missing data that Selenium cannot scrape
  - Optional and configurable via `use_api_enrichment` parameter
  - Falls back gracefully if API enrichment fails

### Technical Changes
- **SpotifyClient Refactor** (`src/integrations/spotify_client.py`):
  - Changed `use_selenium_fallback` parameter to `use_api_enrichment`
  - Removed API-first logic from `get_playlist_tracks()`
  - Added `_enrich_tracks_with_api()` method for metadata enrichment
  - Simplified `get_playlist_name()` (now extracted during Selenium scraping)
  - Changed default `headless=True` for better performance

- **Main Pipeline** (`main.py`):
  - Updated initialization: `SpotifyClient(use_api_enrichment=True, headless=True)`
  - Added context manager usage for proper resource cleanup
  - Updated console output to reflect new architecture

- **Documentation Updates**:
  - Updated README.md to reflect Selenium-primary architecture
  - Added architecture test: `tests/test_selenium_primary_api_enrichment.py`

### Benefits
- More reliable data collection (Selenium works for all playlist types)
- Faster scraping (no API rate limits for basic data)
- Richer metadata when API is available (popularity, previews, album art)
- Graceful degradation if API enrichment fails
- Better separation of concerns (scraping vs. enrichment)

---

## [1.4.0] - 2026-01-11

### Added
- **Separate Playlist PDFs**: Each playlist now generates its own individual PDF file
  - Filenames include sanitized playlist name and timestamp (e.g., `Top_Songs_-_USA_20260111_210000.pdf`)
  - PDF title displays playlist name (e.g., "🎵 Top Songs - USA")
  - Playlist column removed from tables (redundant since title identifies playlist)

- **True Single-Page PDFs**: All PDFs rendered as one continuous scrollable page
  - No pagination or page breaks - content flows continuously
  - Precise content measurement using two-pass rendering approach
  - Auto-sized to exact content height with 5mm buffer (no excessive blank space)

- **Advanced PDF Height Calculation**: Intelligent content measurement system
  - Pass 1: Renders with 100000mm tall page to prevent pagination during measurement
  - Pass 2: Measures body element height accurately by traversing DOM tree
  - Pass 3: Re-renders with exact calculated dimensions (210mm × ~1200-1300mm for 50 tracks)
  - Prevents both multi-page splitting and excessive blank space

### Changed
- **PDF Generator Architecture** (`src/reporting/pdf_generator.py`):
  - Removed `single_page` parameter from all methods (always single-page now)
  - Implemented `find_and_measure_content()` to locate and measure body element
  - Updated measurement logic to target body height instead of page box height
  - Reduced buffer from 10mm to 5mm for tighter fit

- **Table Generator Updates** (`src/reporting/table_generator.py`):
  - Removed `single_page` parameter from `generate_pdf()` and `save_pdf_file()`
  - Updated method signatures for simplified API

- **Main Pipeline** (`main.py`):
  - Changed from single combined PDF to separate PDF per playlist
  - Added track grouping by playlist using `defaultdict`
  - Implemented filename sanitization for playlist names
  - HTML still generates one combined file with all playlists

- **Configuration** (`src/core/config.py`):
  - Removed `pdf_single_page` configuration option (no longer needed)
  - Updated REPORT_CONFIG to remove single-page toggle

- **Environment Variables** (`.env.example`):
  - Removed `PDF_SINGLE_PAGE` variable
  - Updated comments to clarify PDFs are always single continuous page

### Fixed
- **Multi-Page PDF Issue**: PDFs were splitting across multiple pages despite correct height
  - Root cause: Measurement pass used A4 page causing content to paginate, then measuring across multiple paginated pages
  - Solution: Changed to 100000mm tall page during measurement to keep all content on one page

- **Excessive Blank Space**: PDFs had 100000mm of blank space after content
  - Root cause: Was measuring page box height (100000mm) instead of actual body content height
  - Solution: Implemented body element targeting in measurement logic
  - Result: PDFs now sized to ~1200-1300mm for 50 tracks (down from 100000mm)

### Testing
- Created comprehensive test suite in `tests/` directory
  - `tests/integration/test_separate_pdfs.py`: Full 4-playlist PDF generation test
  - `tests/integration/test_final_verification.py`: Page count and dimension verification
  - All tests verify single-page format and proper dimensions

- Test results: 4 PDFs generated successfully
  - Page count: 1 per PDF (verified with PyPDF2)
  - Dimensions: 210.0mm × 1208-1268mm (varies by playlist content)
  - File sizes: ~109-110 KB per 50-track PDF
  - No blank space beyond 5mm buffer

### Project Structure
- **Reorganized Tests**: Moved all test files to `tests/` directory
  - Integration tests in `tests/integration/`
  - Removed test output files and logs from root directory
  - Updated `.gitignore` for new test structure

---

## [1.3.0] - 2025-01-11

### Added
- **PDF Report Generation**: New PDF pipeline for generating professional, print-ready reports
  - New module: `src/reporting/pdf_generator.py` using WeasyPrint library
  - Converts HTML templates to PDF while maintaining Spotify theming
  - Methods: `generate_pdf_from_html()`, `generate_pdf_report()`, `save_pdf_file()`

- **Multi-Format Report Support**: Configurable output formats
  - Generate HTML only, PDF only, or both formats simultaneously
  - New environment variables: `GENERATE_HTML`, `GENERATE_PDF`, `OUTPUT_DIR`
  - Configuration in `src/core/config.py` via `REPORT_CONFIG` dictionary

- **Enhanced TableGenerator**: Extended with PDF generation capabilities
  - New method: `generate_pdf()` for direct PDF generation from track data
  - New method: `save_pdf_file()` with optional output directory parameter
  - Seamless integration with existing HTML generation workflow

- **Updated GitHub Actions Workflow**: Automatic PDF dependency installation
  - Added step to install WeasyPrint system dependencies (Pango, Cairo, GDK-PixBuf)
  - Environment variables for report format configuration
  - Artifact upload now includes both HTML and PDF files

- **System Dependencies Documentation**: Comprehensive setup instructions
  - macOS: Homebrew installation commands for required libraries
  - Linux: apt-get installation commands for Ubuntu/Debian
  - Library path configuration notes for macOS users

### Changed
- **Main Pipeline**: Updated orchestration to support multiple report formats
  - Now generates both HTML and PDF reports based on configuration
  - Uploads all generated formats to Google Drive
  - Attaches all formats to email notifications
  - Email body dynamically reflects generated formats

- **Environment Configuration**: New `.env` variables for report generation
  - `GENERATE_HTML`: Enable/disable HTML generation (default: true)
  - `GENERATE_PDF`: Enable/disable PDF generation (default: true)
  - `OUTPUT_DIR`: Output directory for generated reports (default: ./output)

- **.gitignore Updates**: Added patterns for generated reports
  - Ignores `*.html` and `*.pdf` at root level
  - Preserves `templates/*.html` files
  - Prevents accidental commit of generated reports

### Dependencies
- Added `weasyprint>=60.0` for PDF generation
- System dependencies required:
  - macOS: pango, gdk-pixbuf, libffi (via Homebrew)
  - Linux: libpango-1.0-0, libpangoft2-1.0-0, libgdk-pixbuf2.0-0, libffi-dev, libcairo2

### Testing
- Created `test_pdf_generation.py` script for PDF pipeline validation
- Verified PDF generation with sample data (3 tracks)
- Confirmed Spotify theming preservation in PDF output
- File size verification: ~101KB per PDF

---

## [1.2.1] - 2024-12-12

### Fixed
- **Albums Playlist Under-Collection**: Resolved critical issue where Albums playlists collected only 30 tracks instead of 50
  - Root cause: Stale element errors caused re-location to non-scrollable containers in complex Album DOM structures
  - Solution: Enhanced container selection with scrollability validation and multiple fallback strategies
  - Implementation: `selenium_spotify_client.py` lines 240-322, 386-470
  - Test results: All playlists (Songs & Albums) now collect exactly 50 tracks ✓

### Added
- **Improved Container Selection**: `_locate_scroll_container()` now validates containers are scrollable (`scrollHeight > clientHeight`) before selection
- **Container Validation**: Added validation when re-locating containers after stale element errors
- **Robust Scrolling Method**: New `_scroll_container()` helper with three fallback strategies:
  1. Direct `scrollTop` manipulation (primary)
  2. `scrollBy()` API (alternative)
  3. Window scroll (last resort)
- **Better Error Logging**: Detailed warnings when non-scrollable containers detected

### Changed
- Container selection now prioritizes first scrollable container instead of last matching element
- Reduced scroll wait time from 0.5s to 0.2s after successful scroll (performance improvement)
- Enhanced error handling with multiple recovery strategies

### Performance
- Collection time: ~8-9 seconds per playlist (down from 2-4 minutes)
- Data accuracy: 100% (all playlists collect exactly 50 tracks)
- Total tracks collected: 200 (was 160 with broken Albums collection)

---

## [1.2.0] - 2024-12-12

### Fixed
- **Songs Playlist Over-Collection**: Fixed issue where Songs playlists collected 67 tracks instead of 50
  - Root cause: Spotify's virtualized scrolling loaded positions 50-67 simultaneously in single scroll iteration
  - Solution: Post-deduplication trimming returns exactly 50 tracks when positions 1-50 are complete
  - Implementation: `selenium_spotify_client.py` lines 483-503
  - Test results: Top Songs USA and Top Songs Global now collect exactly 50 tracks ✓

### Changed
- Increased scroll timeout from 240s to 600s for better collection coverage
- Enhanced deduplication logic with global `seen_track_ids` tracking
- Added early exit validation to stop scrolling when 50 positions collected

---

## [1.1.0] - 2024-12-08

### Added
- **Selenium Web Scraping**: Automatic fallback for editorial playlists (Spotify deprecated API access)
- **Headless Browser Mode**: Chrome runs invisibly in background for faster scraping
- **Performance Optimizations**: Disabled image/CSS loading, optimized scroll strategy (60-70% faster)
- Chrome WebDriver automatic management with version detection

### Changed
- Scraping benchmark: ~2-3 minutes for 4 playlists
- Known limitation: Collects ~24-45 tracks per playlist due to Spotify's virtualized scrolling

---

## [1.0.0] - 2024-12-01

### Overview

The Spotify Charts automation project has been restructured to support future A&R analytics features and improve code organization.

---

## What Changed

### Directory Structure

**Before:**
```
spotifyCharts/
├── main.py
├── config.py
├── spotify_client.py
├── google_drive_client.py
├── email_client.py
├── table_generator.py
└── templates/
```

**After:**
```
spotifyCharts/
├── main.py                          # Main orchestration (updated imports)
├── src/                             # NEW: Source code directory
│   ├── core/                        # Configuration and database
│   ├── integrations/                # Spotify, Drive, Email clients
│   ├── analytics/                   # Analytics modules (placeholders)
│   ├── reporting/                   # Report generation
│   └── utils/                       # Helper functions
├── templates/                       # HTML templates
├── data/                            # NEW: Database and snapshots
├── output/                          # NEW: Generated reports
├── logs/                            # NEW: Application logs
├── tests/                           # NEW: Unit tests (future)
└── docs/                            # NEW: Documentation
    ├── ROADMAP.md                   # Development roadmap
    └── QUICK_START.md               # Developer guide
```

### File Movements

| Old Location | New Location |
|-------------|-------------|
| `config.py` | `src/core/config.py` |
| `spotify_client.py` | `src/integrations/spotify_client.py` |
| `google_drive_client.py` | `src/integrations/google_drive_client.py` |
| `email_client.py` | `src/integrations/email_client.py` |
| `table_generator.py` | `src/reporting/table_generator.py` |

### New Files Created

#### Placeholder Modules (Future Implementation)
- `src/core/database.py` - Data persistence layer
- `src/analytics/track_analytics.py` - Track performance metrics
- `src/analytics/trend_analyzer.py` - Trend analysis
- `src/analytics/discovery_engine.py` - A&R discovery features
- `src/reporting/report_generator.py` - Comprehensive reports
- `src/utils/helpers.py` - Common utilities

#### Documentation
- `docs/ROADMAP.md` - Feature roadmap and development timeline
- `docs/QUICK_START.md` - Developer quick start guide
- `RESTRUCTURE_SUMMARY.md` - This file
- `data/README.md` - Data directory documentation
- `output/README.md` - Output directory documentation
- `logs/README.md` - Logs directory documentation
- `tests/README.md` - Tests directory documentation

#### Package Initialization
- `src/__init__.py`
- `src/core/__init__.py`
- `src/integrations/__init__.py`
- `src/analytics/__init__.py`
- `src/reporting/__init__.py`
- `src/utils/__init__.py`

### Code Updates

#### Import Path Changes

**main.py:**
```python
# Before
from spotify_client import SpotifyClient
from table_generator import TableGenerator
import config

# After
from src.integrations.spotify_client import SpotifyClient
from src.reporting.table_generator import TableGenerator
from src.core import config
```

**All module files:**
```python
# Before
import config

# After
from src.core import config
```

#### GitHub Actions

Changed from daily to weekly schedule:
```yaml
# Before
- cron: '0 9 * * *'  # Daily at 9 AM

# After
- cron: '0 9 * * 1'  # Monday at 9 AM (Weekly)
```

### .gitignore Updates

Added entries for new directories:
```
*.pdf
*.xlsx
output/
logs/
data/*.db
data/*.json
```

---

## Breaking Changes

### Import Statements

If you have custom scripts that import from this project, update imports:

```python
# Old imports (broken)
from spotify_client import SpotifyClient

# New imports (correct)
from src.integrations.spotify_client import SpotifyClient
```

### File Paths

Template path resolution updated in `table_generator.py` to account for new directory structure.

---

## What Stayed the Same

- All existing functionality remains intact
- Environment variable configuration (`.env.example`)
- HTML template design
- Google Drive and email integration
- Spotify API integration
- Configuration options in `config.py`

---

## Testing the Restructure

### Syntax Validation

All Python files have been validated for correct syntax:
```bash
python -m py_compile main.py
python -m py_compile src/integrations/*.py
python -m py_compile src/reporting/*.py
python -m py_compile src/core/*.py
```

### Recommended Testing Steps

1. **Test imports:**
   ```bash
   python -c "from src.integrations.spotify_client import SpotifyClient; print('OK')"
   ```

2. **Test configuration:**
   ```bash
   python -c "from src.core import config; print(config.SPOTIFY_THEME)"
   ```

3. **Run full automation:**
   ```bash
   python main.py
   ```

---

## Next Steps for Development

### Immediate (Phase 1)

1. **Implement Database Layer** (`src/core/database.py`)
   - SQLite schema for playlist snapshots
   - Historical data storage
   - Week-over-week comparison queries

2. **Add Audio Features** (`src/integrations/spotify_client.py`)
   - Fetch tempo, energy, danceability, etc.
   - Extend track data structure

3. **Enable Weekly Comparison** (`src/analytics/trend_analyzer.py`)
   - Compare current vs. previous week
   - Identify new/dropped tracks
   - Calculate velocity metrics

### Mid-term (Phase 2)

4. **Build Discovery Engine** (`src/analytics/discovery_engine.py`)
   - Emerging artist identification
   - Breakout track detection
   - Collaboration analysis

5. **Create Comprehensive Reports** (`src/reporting/report_generator.py`)
   - Executive summary
   - Visual analytics (charts/graphs)
   - PDF and Excel exports

### Long-term (Phase 3+)

6. **Advanced Features**
   - Predictive analytics (ML)
   - Multi-source integration (TikTok, YouTube)
   - Interactive dashboards
   - Team collaboration features

See [docs/ROADMAP.md](docs/ROADMAP.md) for complete feature timeline.

---

## Benefits of This Restructure

### Organization
- Clear separation of concerns
- Logical module grouping
- Easy to navigate codebase

### Scalability
- Room for new analytics modules
- Placeholder files guide future development
- Clean namespace separation

### Maintainability
- Modular design reduces coupling
- Easier to test individual components
- Better code reusability

### Documentation
- Comprehensive roadmap for future features
- Quick start guide for new developers
- README files explain each directory

### A&R Focus
- Structured to support analytics needs
- Placeholder modules for discovery features
- Clear path to advanced reporting

---

## Migration Checklist

- [x] Create new directory structure
- [x] Move files to appropriate locations
- [x] Update import statements
- [x] Create __init__.py files
- [x] Update GitHub Actions workflow
- [x] Change to weekly scheduling
- [x] Update .gitignore
- [x] Create placeholder modules
- [x] Write documentation (README, ROADMAP, QUICK_START)
- [x] Validate Python syntax
- [ ] Test full automation run (requires API credentials)
- [ ] Verify Google Drive upload works
- [ ] Verify email sending works

---

## Questions or Issues?

- Review [docs/QUICK_START.md](docs/QUICK_START.md) for common tasks
- Check [docs/ROADMAP.md](docs/ROADMAP.md) for feature plans
- Open a GitHub issue for bugs or questions

---

**Restructure completed successfully!** The project is now organized and ready for future A&R analytics implementation.
