# Tests Directory

This directory contains test scripts for the Spotify Charts automation system.

**Convention:** One-off and debug tests should be deleted after use. See `docs/CONVENTIONS.md` (Testing Conventions).

## Structure

```
tests/
├── integration/                           # Integration tests (end-to-end)
│   ├── test_separate_pdfs.py             # Tests separate PDF generation per playlist
│   └── test_final_verification.py        # Comprehensive verification (page count, dimensions)
│
├── test_selenium_primary_api_enrichment.py  # Selenium + API enrichment architecture
├── test_playlist_extraction.py              # Playlist data extraction
├── test_template_validation.py              # Template validation
├── test_google_drive.py                     # Google Drive client
├── test_google_drive_date_folders.py        # Date-based folder creation
├── conftest.py                              # pytest configuration
└── __init__.py                              # Package init
```

## Running Tests

### Prerequisites
Set library path for macOS (if using WeasyPrint):
```bash
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"
```

### Run Integration Tests
```bash
python tests/integration/test_separate_pdfs.py
python tests/integration/test_final_verification.py
```

### Run Architecture Test
```bash
python tests/test_selenium_primary_api_enrichment.py
```

### Run All Tests (pytest)
```bash
pytest tests/ -v
```
