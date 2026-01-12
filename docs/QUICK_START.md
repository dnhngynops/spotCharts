# Quick Start Guide

## For New Developers

### Understanding the Codebase

The project is organized into logical modules:

#### **Core Modules** (`src/core/`)
- **config.py**: All configuration settings, environment variables, and constants
- **database.py**: Data persistence layer (placeholder for future implementation)

#### **Integration Modules** (`src/integrations/`)
- **spotify_client.py**: Hybrid Spotify data collector with API + Selenium fallback
- **selenium_spotify_client.py**: Web scraping for editorial playlists (headless browser)
- **google_drive_client.py**: Manages Google Drive uploads
- **email_client.py**: Sends email notifications
- **browser.py** (utils): Chrome WebDriver manager with optimizations

#### **Analytics Modules** (`src/analytics/`)
All modules here are placeholders for future A&R analytics:
- **track_analytics.py**: Individual track performance metrics
- **trend_analyzer.py**: Week-over-week trend analysis
- **discovery_engine.py**: A&R discovery features (emerging artists, breakout tracks)

#### **Reporting Modules** (`src/reporting/`)
- **table_generator.py**: Creates formatted HTML/CSV tables
- **report_generator.py**: Comprehensive report generation (placeholder)

#### **Utilities** (`src/utils/`)
- **helpers.py**: Common helper functions used across modules

---

## Data Collection Overview

### **What Data is Collected**

The system collects comprehensive track metadata from Spotify playlists:

| Data Field | API | Selenium | Description |
|------------|-----|----------|-------------|
| track_id | ✓ | ✓ | Spotify unique identifier |
| track_name | ✓ | ✓ | Song title |
| artist | ✓ | ✓ | Artist name(s) |
| artists (with URLs) | ✗ | ✓ | Structured array with artist links |
| album | ✓ | ✓ | Album name |
| duration | ✓ | ✗ | Track length (MM:SS) |
| popularity | ✓ | ✗ | Spotify popularity score (0-100) |
| spotify_url | ✓ | ✓ | **Track Spotify link** |
| album_image | ✓ | ✗ | **Album artwork URL** |
| release_date | ✓ | ✗ | Release date |
| playlist | ✓ | ✓ | Playlist name |
| position | ✗ | ✓ | Chart position (1-50) |
| explicit | ✗ | ✓ | Explicit content flag |

### **Current Collection Method**

Editorial playlists use **Selenium web scraping** (API returns 404):
- ✅ 100% data accuracy (50/50 tracks per playlist)
- ✅ ~8-9 seconds per playlist
- ✅ Track URLs and artist URLs collected
- ⚠️ Album images, duration, and popularity not available (Selenium limitation)

---

## Running the Application

### 1. Initial Setup

```bash
# Clone the repository
git clone <repo-url>
cd spotifyCharts

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

### 2. Configure Your Playlists

Edit `.env` and add your Spotify playlist IDs:

```bash
PLAYLIST_1_ID=37i9dQZF1DXcBWIGoYBM5M
PLAYLIST_2_ID=37i9dQZF1DX0XUsuxWHRQd
PLAYLIST_3_ID=37i9dQZF1DX4dyzvuaRJ0n
PLAYLIST_4_ID=37i9dQZF1DX4JAvHpjipBk
```

### 3. Run Manually

```bash
python main.py
```

### 4. Verify Output

Check for:
- Generated HTML file in project root
- Upload confirmation to Google Drive
- Email sent to configured recipients

---

## Adding New Features

### Implementing Analytics Modules

1. Navigate to the placeholder file (e.g., `src/analytics/track_analytics.py`)
2. Replace `raise NotImplementedError()` with your implementation
3. Import required dependencies
4. Add configuration to `src/core/config.py` if needed
5. Update `main.py` to use your new feature

### Example: Adding Audio Features

```python
# In src/integrations/spotify_client.py
def get_audio_features(self, track_id: str):
    """Get audio features for a track"""
    return self.client.audio_features(track_id)[0]

# In main.py (after fetching tracks)
for track in tracks:
    features = spotify_client.get_audio_features(track['track_id'])
    track['tempo'] = features['tempo']
    track['energy'] = features['energy']
```

---

## Testing Your Changes

### Manual Testing

```bash
# Test with limited data first
python main.py
```

### Future: Unit Tests

Once test suite is implemented:

```bash
pytest tests/
```

---

## Deployment

### GitHub Actions (Recommended)

The workflow runs automatically every Monday at 9 AM UTC.

**Setup:**
1. Go to your GitHub repository Settings → Secrets
2. Add all environment variables as repository secrets
3. Enable GitHub Actions in your repository
4. The workflow will run on schedule

**Manual Trigger:**
1. Go to Actions tab in GitHub
2. Select "Spotify Charts Automation"
3. Click "Run workflow"

### Local Cron (Alternative)

```bash
# Edit crontab
crontab -e

# Add this line (runs every Monday at 9 AM)
0 9 * * 1 cd /path/to/spotifyCharts && /usr/bin/python3 main.py
```

---

## Common Tasks

### Update Playlist Configuration

Edit `.env`:
```bash
PLAYLIST_1_ID=new_playlist_id
```

### Change Schedule

Edit `.github/workflows/spotify-charts.yml`:
```yaml
schedule:
  - cron: '0 9 * * 1'  # Monday at 9 AM
  # Change to: '0 9 * * 5' for Friday
```

### Add Email Recipients

Edit `.env`:
```bash
EMAIL_TO=person1@example.com,person2@example.com,person3@example.com
```

### Customize Table Appearance

Edit `src/core/config.py`:
```python
TABLE_CONFIG = {
    'include_columns': ['track_name', 'artist', 'popularity'],
    'sort_by': 'popularity',
    'sort_order': 'desc',
}
```

---

## Troubleshooting

### Import Errors

If you see import errors after restructure:
```bash
# Ensure you're importing from src.*
from src.integrations.spotify_client import SpotifyClient
```

### Template Not Found

The table template is in `templates/table_template.html` (root level).
If moved, update path in `src/reporting/table_generator.py`.

### API Rate Limits

Spotify API has rate limits. If you hit them:
- Reduce frequency of runs
- Implement caching (future feature)
- Add delays between API calls

### Google Drive Upload Fails

Common issues:
- Credentials file path incorrect
- OAuth token expired (delete token.pickle and re-authenticate)
- Folder ID doesn't exist or lacks permissions

---

## Next Steps

1. Review the [Development Roadmap](ROADMAP.md)
2. Choose a feature to implement
3. Check placeholder files for implementation hints
4. Start coding!

For questions or issues, please open a GitHub issue.
