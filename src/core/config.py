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
SPOTIFY_THEME = {
    'background': '#131C25',      # Page background
    'surface': '#1E2A36',         # Card / panel surface
    'primary': '#58C69D',         # Primary accent green
    'accent_light': '#6BD1A6',    # Heading color / light accent
    'accent_dark': '#3B3838',     # Dark secondary accent
    'text_primary': '#FFFCFC',    # Body text
    'text_secondary': '#C8D0D8',  # Cool off-white
    'text_track': '#E8EDF2',      # Track name color
    'text_artist': '#8C96A1',     # Artist name color (cool gray)
    'border': '#313C45',          # Dark border
    'bar_background': '#263342',  # Popularity bar background
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

