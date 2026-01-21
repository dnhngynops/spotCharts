# Directory Structure Guide

This document provides a complete overview of the project's directory structure and organization.

## Root Level

```
spotifyCharts/
├── main.py                 # Main orchestration script (entry point)
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (gitignored)
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules
├── README.md               # Project overview and documentation
│
├── src/                    # Source code (all application code)
├── tests/                  # Test suite (all test files)
├── templates/              # HTML templates
├── docs/                   # Documentation files
├── scripts/                # Development utilities
│
├── credentials/            # API credentials (gitignored)
├── data/                   # Data storage (gitignored)
├── output/                 # Generated reports (gitignored)
└── logs/                   # Application logs (gitignored)
```

## Source Code (`src/`)

All application source code organized by functionality:

```
src/
├── __init__.py
│
├── core/                          # Core functionality
│   ├── __init__.py
│   ├── config.py                  # Configuration settings and environment variables
│   └── database.py                # Data persistence (placeholder)
│
├── integrations/                  # External service integrations
│   ├── __init__.py
│   ├── spotify_client.py          # Spotify API + Selenium hybrid client
│   ├── selenium_spotify_client.py # Selenium web scraping for editorial playlists
│   ├── google_drive_client.py     # Google Drive API integration
│   └── email_client.py            # Email sending via SMTP
│
├── reporting/                     # Report generation modules
│   ├── __init__.py
│   ├── table_generator.py         # HTML table generation and formatting
│   ├── pdf_generator.py           # PDF report generation (WeasyPrint)
│   └── report_generator.py        # Comprehensive reports (placeholder)
│
├── analytics/                     # Analytics modules (placeholders for future)
│   ├── __init__.py
│   ├── track_analytics.py         # Track performance metrics
│   ├── trend_analyzer.py          # Trend analysis
│   └── discovery_engine.py        # A&R discovery features
│
└── utils/                         # Utility functions
    ├── __init__.py
    ├── browser.py                 # Chrome WebDriver manager
    └── helpers.py                 # Common helper functions
```

## Tests (`tests/`)

Test suite organized by test type:

```
tests/
├── README.md                      # Test documentation
│
├── integration/                   # Integration tests (end-to-end)
│   ├── test_separate_pdfs.py      # Tests separate PDF generation per playlist
│   └── test_final_verification.py # Comprehensive verification test
│
└── *.py                           # Unit and debug tests
    ├── test_page_count.py         # PDF page count verification
    ├── test_single_page_only.py   # Single-page PDF test
    ├── test_blank_space_*.py      # Blank space elimination tests
    ├── test_pdf_*.py              # Various PDF generation tests
    ├── test_playlist_extraction.py# Playlist data extraction test
    └── debug_*.py                 # Debug utilities
```

## Documentation (`docs/`)

Project documentation and guides:

```
docs/
├── ARCHITECTURE.md                # System architecture and data flow
├── CHANGELOG.md                   # Version history and changes
├── CONVENTIONS.md                 # Code and documentation conventions
├── DIRECTORY_STRUCTURE.md         # This file
├── GITHUB_ACTIONS_SETUP.md        # GitHub Actions automation setup
├── GOOGLE_DRIVE_SETUP.md          # Google Drive OAuth configuration
├── METRICS_DOCUMENTATION.md       # Metrics and analytics documentation
├── QUICK_START.md                 # Quick start guide for developers
├── ROADMAP.md                     # Development roadmap and future features
├── SECRETS_CHECKLIST.md           # GitHub Secrets reference
└── SETUP.md                       # Detailed setup instructions
```

## Templates (`templates/`)

HTML templates for report generation:

```
templates/
└── table_template.html            # Main table template with Spotify theming
```

## Scripts (`scripts/`)

Development and setup utilities:

```
scripts/
├── setup.sh                       # Initial setup script
├── generate_all_pdfs.py           # Generate PDF reports for all playlists
└── run_with_libs.sh               # Wrapper script to run Python with WeasyPrint library path
```

## GitHub Actions (`.github/`)

CI/CD automation workflows:

```
.github/
└── workflows/
    └── spotify-charts.yml         # Weekly automation workflow
```

## Data Directories (Gitignored)

These directories store runtime data and are excluded from version control:

```
credentials/                       # API credentials
├── google-drive-credentials.json  # Google Drive OAuth credentials
└── token.pickle                   # Cached OAuth tokens

data/                              # Data storage
└── (SQLite databases, JSON snapshots - future)

output/                            # Generated reports
├── *.html                         # HTML reports
└── *.pdf                          # PDF reports

logs/                              # Application logs
└── *.log                          # Runtime logs
```

## Key Files

### Configuration
- **`.env`**: Environment variables (credentials, settings)
- **`.env.example`**: Template for environment variables
- **`src/core/config.py`**: Application configuration loaded from `.env`

### Entry Point
- **`main.py`**: Main orchestration script that runs the full pipeline

### Dependencies
- **`requirements.txt`**: Python package dependencies

### Version Control
- **`.gitignore`**: Specifies files/directories to exclude from git

## Import Patterns

All imports use absolute paths from the `src/` directory:

```python
# Core configuration
from src.core import config

# Integrations
from src.integrations.spotify_client import SpotifyClient
from src.integrations.google_drive_client import GoogleDriveClient
from src.integrations.email_client import EmailClient

# Reporting
from src.reporting.table_generator import TableGenerator
from src.reporting.pdf_generator import PDFGenerator

# Utils
from src.utils.browser import BrowserManager
```

## Directory Purpose Summary

| Directory | Purpose | Gitignored |
|-----------|---------|------------|
| `src/` | Application source code | No |
| `tests/` | Test suite | No |
| `templates/` | HTML templates | No |
| `docs/` | Documentation | No |
| `scripts/` | Development utilities | No |
| `credentials/` | API credentials | Yes |
| `data/` | Data storage | Yes |
| `output/` | Generated reports | Yes |
| `logs/` | Application logs | Yes |
| `.github/` | CI/CD workflows | No |

## Navigation Tips

- **To modify data collection**: See `src/integrations/`
- **To change report formatting**: See `src/reporting/` and `templates/`
- **To add new features**: Add modules to appropriate `src/` subdirectory
- **To configure settings**: Edit `.env` and `src/core/config.py`
- **To run tests**: Execute scripts in `tests/` directory
- **To understand changes**: Read `docs/CHANGELOG.md`
- **To plan features**: Review `docs/ROADMAP.md`

## Best Practices

1. **Keep tests separate**: All test files go in `tests/` directory
2. **Use absolute imports**: Always import from `src.*` paths
3. **Document changes**: Update `docs/CHANGELOG.md` for significant changes
4. **Follow structure**: Place new code in appropriate `src/` subdirectory
5. **Ignore outputs**: Never commit files from `output/`, `logs/`, or `data/`

---

This structure is designed for:
- **Clarity**: Easy to navigate and understand
- **Scalability**: Room for growth without restructuring
- **Maintainability**: Clear separation of concerns
- **Testability**: Tests isolated from source code
- **Documentation**: Everything is well-documented
