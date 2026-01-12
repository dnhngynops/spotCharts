"""
External service integrations (Spotify, Google Drive, Email)
"""
from .spotify_client import SpotifyClient
from .google_drive_client import GoogleDriveClient
from .email_client import EmailClient

__all__ = ['SpotifyClient', 'GoogleDriveClient', 'EmailClient']
