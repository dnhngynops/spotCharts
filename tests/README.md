# Tests Directory

This directory contains test scripts for the Spotify Charts automation system.

**Convention:** One-off and debug tests should be deleted after use. See `docs/CONVENTIONS.md` (Testing Conventions → One-Off and Debug Tests).

## Structure

```
tests/
├── integration/                    # Integration tests (end-to-end)
│   ├── test_separate_pdfs.py      # Tests separate PDF generation per playlist
│   └── test_final_verification.py # Comprehensive verification (page count, dimensions)
│
└── *.py                            # Unit tests
    ├── test_selenium_primary_api_enrichment.py  # Selenium + API enrichment architecture
    ├── test_playlist_extraction.py # Playlist data extraction
    ├── test_template_validation.py # Template validation
    ├── test_single_playlist.py     # Single-playlist collection + PDF
    ├── test_single_playlist_pdf.py # Single-playlist PDF generation
    ├── test_top_songs_usa.py       # Top Songs USA pipeline
    ├── test_long_title.py          # Long title handling in PDFs
    ├── test_google_drive.py        # Google Drive client
    └── test_google_drive_date_folders.py # Date-based folder creation
```

## Integration Tests

### test_separate_pdfs.py
Tests the complete PDF generation pipeline with all configured playlists.

**Usage:**
```bash
python tests/integration/test_separate_pdfs.py
```

### test_final_verification.py
Comprehensive verification test that validates PDF structure.

**Usage:**
```bash
python tests/integration/test_final_verification.py
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
