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
GOOGLE_DRIVE_CREDENTIALS_PATH = os.getenv('GOOGLE_DRIVE_CREDENTIALS_PATH', './credentials/google-drive-credentials.json')
GOOGLE_DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID')

# Email Configuration
EMAIL_SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
EMAIL_SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT', '587'))
EMAIL_USERNAME = os.getenv('EMAIL_USERNAME')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_FROM = os.getenv('EMAIL_FROM')
EMAIL_TO = os.getenv('EMAIL_TO', '').split(',') if os.getenv('EMAIL_TO') else []

# Playlist Configuration (4 editorial playlists)
PLAYLIST_IDS = [
    os.getenv('PLAYLIST_1_ID'),
    os.getenv('PLAYLIST_2_ID'),
    os.getenv('PLAYLIST_3_ID'),
    os.getenv('PLAYLIST_4_ID'),
]

# Table Configuration
TABLE_CONFIG = {
    'include_columns': ['track_name', 'album', 'duration', 'popularity', 'playlist'],  # Removed 'artist' - now displayed under track names
    'sort_by': 'popularity',
    'sort_order': 'desc',
    'max_tracks_per_playlist': None,  # None = all tracks
}

# Spotify Theme Colors
SPOTIFY_THEME = {
    'background': '#121212',
    'surface': '#181818',
    'primary': '#1DB954',
    'text_primary': '#FFFFFF',
    'text_secondary': '#B3B3B3',
    'text_track': '#E0E0E0',      # Track name color (lighter than secondary)
    'text_artist': '#888888',     # Artist name color (darker than secondary)
    'border': '#282828',
    'bar_background': '#2a2a2a',  # Popularity bar background
}

# Report Generation Configuration
REPORT_CONFIG = {
    'formats': {
        'html': os.getenv('GENERATE_HTML', 'true').lower() == 'true',  # Generate HTML reports
        'pdf': os.getenv('GENERATE_PDF', 'true').lower() == 'true',    # Generate PDF reports (always single continuous page)
    },
    'output_dir': os.getenv('OUTPUT_DIR', './output'),  # Directory for generated reports
}

