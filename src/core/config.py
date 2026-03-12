"""
Configuration settings for Spotify Charts automation
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Spotify API Configuration
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

# Google Drive Configuration
GOOGLE_DRIVE_ENABLED          = os.getenv('GOOGLE_DRIVE_ENABLED', 'false').lower() == 'true'
GOOGLE_DRIVE_CREDENTIALS_PATH = os.getenv('GOOGLE_DRIVE_CREDENTIALS_PATH', './credentials/google-drive-credentials.json')
GOOGLE_DRIVE_FOLDER_ID        = os.getenv('GOOGLE_DRIVE_FOLDER_ID')

# Email Configuration
EMAIL_SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
EMAIL_SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT', '587'))
EMAIL_USERNAME = os.getenv('EMAIL_USERNAME')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_FROM = os.getenv('EMAIL_FROM')
EMAIL_TO = os.getenv('EMAIL_TO', '').split(',') if os.getenv('EMAIL_TO') else []

# Playlist Configuration (editorial playlists; add PLAYLIST_6_ID, etc. in config + .env if needed)
PLAYLIST_IDS = [
    os.getenv('PLAYLIST_1_ID'),
    os.getenv('PLAYLIST_2_ID'),
    os.getenv('PLAYLIST_3_ID'),
    os.getenv('PLAYLIST_4_ID'),
    os.getenv('PLAYLIST_5_ID'),
]
# Filter out None/empty so optional 5th+ playlists don't break the pipeline
PLAYLIST_IDS = [pid for pid in PLAYLIST_IDS if pid and str(pid).strip()]

# Table Configuration
TABLE_CONFIG = {
    'include_columns': ['track_name', 'album', 'duration', 'popularity', 'playlist'],  # Removed 'artist' - now displayed under track names
    'sort_by': 'popularity',
    'sort_order': 'desc',
    'max_tracks_per_playlist': None,  # None = all tracks
}

# Milk & Honey LA Theme Colors
# Source of truth: spotify-dashboard-figma-spec.html (Figma Spec v1)
# Mirror of frontend/src/index.css :root tokens — keep both in sync.
SPOTIFY_THEME = {
    # Backgrounds
    'background':    '#131C25',   # --bg          Page body
    'surface':       '#1E2A36',   # --surface      Cards, section panels
    'sidebar_bg':    '#07131D',   # --sidebar-bg   Sidebar
    'bar_background':'#263342',   # --bar-bg       Progress/popularity bar track
    'header_top':    '#1C242B',   # --header-top   Dashboard header gradient start
    'header_mid':    '#121D26',   # --header-mid   Dashboard header gradient mid
    # Text
    'text_primary':  '#C8D0D8',   # --text-primary  Body text
    'text_bright':   '#E8EDF2',   # --text-bright   Track names, emphasis
    'text_muted':    '#8C96A1',   # --text-muted    Secondary / meta
    # Brand / Accent
    'primary':       '#58C69D',   # --primary        Primary teal accent
    'accent_light':  '#6BD1A6',   # --accent-light   Heading teal
    'brand_green_raw':'#6CCA98',  # --brand-green-raw Active nav, trend-up badges
    # Semantic
    'danger':        '#E74C3C',   # --danger         Explicit content bar
    'trend_down':    '#E84393',   # --trend-down     Trending-down badge
    # Borders
    'border':        '#313C45',   # --border         Input / hard borders
    # Legacy aliases used by Jinja2 templates — do not remove
    'text_track':    '#E8EDF2',   # = text_bright
    'text_artist':   '#8C96A1',   # = text_muted
    'text_secondary':'#C8D0D8',   # = text_primary
}

# Genius API (song credits: writers, producers, engineers)
GENIUS_ACCESS_TOKEN = os.getenv('GENIUS_ACCESS_TOKEN')

# Supabase Configuration (intermediate data storage + historical analytics)
SUPABASE_URL         = os.getenv('SUPABASE_URL')           # Project URL
SUPABASE_ANON_KEY    = os.getenv('SUPABASE_ANON_KEY')      # Read-only; safe to embed in JS
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')   # Write; server-side only, never expose in HTML

# Report Generation Configuration
REPORT_CONFIG = {
    'formats': {
        'html': os.getenv('GENERATE_HTML', 'true').lower() == 'true',  # Generate HTML reports
        'pdf': os.getenv('GENERATE_PDF', 'true').lower() == 'true',    # Generate PDF reports (always single continuous page)
    },
    'output_dir': os.getenv('OUTPUT_DIR', './output'),  # Directory for generated reports
}

