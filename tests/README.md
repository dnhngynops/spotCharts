# Tests Directory

This directory contains test scripts for the Spotify Charts automation system.

## Structure

```
tests/
├── integration/                    # Integration tests (end-to-end)
│   ├── test_separate_pdfs.py      # Tests separate PDF generation per playlist
│   └── test_final_verification.py # Comprehensive verification (page count, dimensions)
│
└── *.py                            # Unit and debug tests
    ├── test_page_count.py          # PDF page count verification
    ├── test_single_page_only.py    # Single-page PDF test
    ├── test_blank_space_*.py       # Blank space elimination tests
    ├── test_pdf_*.py               # Various PDF generation tests
    ├── test_playlist_extraction.py # Playlist data extraction test
    └── debug_*.py                  # Debug utilities
```

## Integration Tests

### test_separate_pdfs.py
Tests the complete PDF generation pipeline with all 4 playlists.

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
