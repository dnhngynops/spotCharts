"""
Spotify data collection client using Selenium scraping with API enrichment

This client uses Selenium web scraping as the PRIMARY method for extracting
playlist tracks and chart data. The Spotify API is used only to enrich track
metadata with additional information like album details, preview URLs, and
popularity scores.
"""
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from typing import List, Dict, Optional
from src.core import config


class SpotifyClient:
    """Client for collecting Spotify data via Selenium with API enrichment"""

    def __init__(self, use_api_enrichment: bool = True, headless: bool = True):
        """
        Initialize Spotify client

        Args:
            use_api_enrichment: Enable Spotify API enrichment for track metadata
            headless: Run Selenium in headless mode (no visible browser)
        """
        # Initialize Spotify API client for enrichment (optional)
        self.use_api_enrichment = use_api_enrichment
        self.client = None

        if use_api_enrichment:
            if not config.SPOTIFY_CLIENT_ID or not config.SPOTIFY_CLIENT_SECRET:
                print("Warning: Spotify API credentials not configured. API enrichment disabled.")
                self.use_api_enrichment = False
            else:
                try:
                    client_credentials_manager = SpotifyClientCredentials(
                        client_id=config.SPOTIFY_CLIENT_ID,
                        client_secret=config.SPOTIFY_CLIENT_SECRET
                    )
                    self.client = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
                except Exception as e:
                    print(f"Warning: Failed to initialize Spotify API: {e}. API enrichment disabled.")
                    self.use_api_enrichment = False

        self.headless = headless
        self._selenium_client = None
    
    def get_playlist_tracks(self, playlist_id: str, playlist_name: Optional[str] = None) -> List[Dict]:
        """
        Fetch all tracks from a Spotify playlist using Selenium scraping

        Uses Selenium as PRIMARY method, then enriches track data with Spotify API.

        Args:
            playlist_id: Spotify playlist ID
            playlist_name: Optional playlist name for labeling

        Returns:
            List of track dictionaries with relevant information
        """
        # PRIMARY METHOD: Use Selenium to scrape playlist tracks (includes playlist image)
        print(f"Scraping playlist {playlist_id} using Selenium...")
        tracks = self._get_playlist_tracks_selenium(playlist_id, playlist_name)

        # ENRICHMENT: Use Spotify API to add metadata for each track
        if self.use_api_enrichment and self.client:
            print(f"Enriching {len(tracks)} tracks with Spotify API metadata...")
            tracks = self._enrich_tracks_with_api(tracks)
            
            # Playlist image is already included from Selenium scraping, but try API as fallback
            if not tracks[0].get('playlist_image') if tracks else None:
                try:
                    playlist = self.client.playlist(playlist_id)
                    if playlist.get('images') and len(playlist['images']) > 0:
                        playlist_image = playlist['images'][0]['url']
                        for track in tracks:
                            track['playlist_image'] = playlist_image
                except Exception:
                    pass  # API playlist access not available for editorial playlists

        return tracks
    
    def get_playlist_name(self, playlist_id: str) -> str:
        """
        Get the name of a playlist

        Since we're using Selenium as primary method, the playlist name
        will be extracted during track scraping.
        """
        # Placeholder name - will be replaced during Selenium scraping
        return f"Playlist {playlist_id}"

    def _get_playlist_tracks_selenium(self, playlist_id: str, playlist_name: Optional[str] = None) -> List[Dict]:
        """
        Fetch playlist tracks using Selenium web scraping

        Args:
            playlist_id: Spotify playlist ID
            playlist_name: Optional playlist name

        Returns:
            List of track dictionaries
        """
        if self._selenium_client is None:
            from src.integrations.selenium_spotify_client import SeleniumSpotifyClient
            self._selenium_client = SeleniumSpotifyClient(
                headless=self.headless,
                logger=None
            )

        return self._selenium_client.get_playlist_tracks(playlist_id, playlist_name)

    def _enrich_tracks_with_api(self, tracks: List[Dict]) -> List[Dict]:
        """
        Enrich track data with Spotify API metadata

        Takes tracks scraped by Selenium and adds additional metadata from API:
        - Album details (if missing)
        - Artist information (if missing)
        - Preview URLs
        - Popularity scores
        - Duration (if missing)
        - Release dates
        - Album images

        Args:
            tracks: List of tracks from Selenium scraping

        Returns:
            Enriched tracks with API metadata
        """
        enriched_tracks = []
        enriched_count = 0
        failed_count = 0

        for track in tracks:
            track_id = track.get('track_id')

            # Skip enrichment if no track ID
            if not track_id:
                enriched_tracks.append(track)
                continue

            try:
                # Fetch full track data from Spotify API
                api_track = self.client.track(track_id)

                # Enrich with API data (only fill in missing fields)
                if not track.get('album') and api_track.get('album'):
                    track['album'] = api_track['album']['name']

                # Add album URL (if not already present)
                if not track.get('album_url') and api_track.get('album', {}).get('external_urls', {}).get('spotify'):
                    track['album_url'] = api_track['album']['external_urls']['spotify']

                if not track.get('duration_ms') and api_track.get('duration_ms'):
                    track['duration_ms'] = api_track['duration_ms']
                    track['duration'] = self._format_duration(api_track['duration_ms'])

                if not track.get('popularity') and api_track.get('popularity') is not None:
                    track['popularity'] = api_track['popularity']

                # Add preview URL (usually not available via scraping)
                # Always set preview_url, even if None (so we can check if it exists)
                track['preview_url'] = api_track.get('preview_url') or None

                # Add album image (if not already present)
                if not track.get('album_image') and api_track.get('album', {}).get('images'):
                    track['album_image'] = api_track['album']['images'][0]['url']

                # Add release date (if not already present)
                if not track.get('release_date') and api_track.get('album', {}).get('release_date'):
                    track['release_date'] = api_track['album']['release_date']

                # Add artist details if needed
                if api_track.get('artists'):
                    # Keep scraped artist names but add IDs if available
                    for i, api_artist in enumerate(api_track['artists']):
                        if i < len(track.get('artists', [])):
                            track['artists'][i]['id'] = api_artist.get('id')
                            track['artists'][i]['url'] = api_artist.get('external_urls', {}).get('spotify')

                enriched_count += 1

            except Exception as e:
                # If API enrichment fails, keep the scraped data
                print(f"   Warning: Failed to enrich track '{track.get('track_name')}': {e}")
                failed_count += 1

            enriched_tracks.append(track)

        print(f"   ✓ Enriched {enriched_count}/{len(tracks)} tracks successfully ({failed_count} failed)")
        return enriched_tracks

    def get_all_playlist_tracks(self, playlist_ids: List[str]) -> List[Dict]:
        """
        Fetch tracks from multiple playlists
        
        Args:
            playlist_ids: List of Spotify playlist IDs
            
        Returns:
            Combined list of tracks from all playlists
        """
        all_tracks = []
        
        for playlist_id in playlist_ids:
            if not playlist_id:
                continue
            try:
                playlist_name = self.get_playlist_name(playlist_id)
                tracks = self.get_playlist_tracks(playlist_id, playlist_name)
                
                # Limit tracks per playlist if configured
                if config.TABLE_CONFIG['max_tracks_per_playlist']:
                    tracks = tracks[:config.TABLE_CONFIG['max_tracks_per_playlist']]
                
                all_tracks.extend(tracks)
            except Exception as e:
                print(f"Error fetching playlist {playlist_id}: {e}")
                continue
        
        return all_tracks
    
    @staticmethod
    def _format_duration(ms: int) -> str:
        """Convert milliseconds to MM:SS format"""
        if ms is None:
            return "N/A"
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"

    def close(self):
        """Close any open Selenium sessions"""
        if self._selenium_client:
            self._selenium_client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

