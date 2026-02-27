"""
Spotify data collection client using Selenium scraping with API enrichment

This client uses Selenium web scraping as the PRIMARY method for extracting
playlist tracks and chart data. The Spotify API is used only to enrich track
metadata with additional information like album details, preview URLs, and
popularity scores.
"""
import time
from threading import Lock

import requests
import spotipy
from requests.adapters import HTTPAdapter
from spotipy.oauth2 import SpotifyClientCredentials
from typing import List, Dict, Optional
from urllib3.util.retry import Retry

from src.core import config


class SpotifyClient:
    """Client for collecting Spotify data via Selenium with API enrichment"""

    # Class-level rate-limit state shared across all instances in a process
    _rate_limit_lock = Lock()
    _last_request_time: float = 0.0
    _min_request_interval: float = 0.1   # 100 ms → ≤10 req/s
    _consecutive_429s: int = 0
    _max_consecutive_429s: int = 5
    _rate_limit_wait_time: float = 0.0

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
                    session = self._build_session()
                    try:
                        self.client = spotipy.Spotify(
                            client_credentials_manager=client_credentials_manager,
                            requests_session=session,
                        )
                    except TypeError:
                        # Older spotipy versions don't accept requests_session
                        self.client = spotipy.Spotify(
                            client_credentials_manager=client_credentials_manager
                        )
                except Exception as e:
                    print(f"Warning: Failed to initialize Spotify API: {e}. API enrichment disabled.")
                    self.use_api_enrichment = False

        self.headless = headless
        self._selenium_client = None

    @staticmethod
    def _build_session() -> requests.Session:
        """
        Build a requests.Session with retry strategy and per-request timeouts.

        The retry strategy handles transient server errors (5xx) and rate
        limits (429) at the HTTP transport level. Application-level 429
        handling in _handle_rate_limit_error adds exponential backoff on top.
        """
        session = requests.Session()

        retry_strategy = Retry(
            total=2,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20,
        )
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        # Patch session.request to always include a timeout so hung connections
        # don't stall the pipeline indefinitely.
        _original_request = session.request
        def _request_with_timeout(*args, **kwargs):
            kwargs.setdefault("timeout", (5, 15))  # (connect, read) seconds
            return _original_request(*args, **kwargs)
        session.request = _request_with_timeout  # type: ignore[method-assign]

        return session

    def _enforce_rate_limit(self) -> None:
        """Ensure a minimum gap between consecutive Spotify API requests."""
        with self.__class__._rate_limit_lock:
            now = time.time()
            elapsed = now - self.__class__._last_request_time
            wait = self.__class__._min_request_interval - elapsed

            if self.__class__._rate_limit_wait_time > 0:
                wait = max(wait, self.__class__._rate_limit_wait_time)
                self.__class__._rate_limit_wait_time = 0.0

            if wait > 0:
                time.sleep(wait)

            self.__class__._last_request_time = time.time()

    def _handle_rate_limit_error(self, error: Exception) -> bool:
        """
        React to a 429 response with exponential backoff.

        Returns True if the caller should retry, False if it should give up.
        """
        error_str = str(error).lower()
        if '429' not in error_str and 'too many requests' not in error_str:
            with self.__class__._rate_limit_lock:
                self.__class__._consecutive_429s = 0
            return False

        with self.__class__._rate_limit_lock:
            self.__class__._consecutive_429s += 1
            count = self.__class__._consecutive_429s

        if count >= self.__class__._max_consecutive_429s:
            print(f"   ⚠  Spotify: {count} consecutive 429s — giving up on this batch")
            return False

        # Exponential backoff: 1 s, 2 s, 4 s, 8 s, 16 s (capped at 30 s)
        wait = min(2 ** (count - 1), 30)
        print(f"   ⚠  Spotify rate limited (429). Waiting {wait}s before retry…")
        time.sleep(wait)
        with self.__class__._rate_limit_lock:
            self.__class__._rate_limit_wait_time = wait
        return True
    
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
                self._enforce_rate_limit()
                api_track = None
                for attempt in range(3):
                    try:
                        api_track = self.client.track(track_id)
                        with self.__class__._rate_limit_lock:
                            self.__class__._consecutive_429s = 0
                        break
                    except Exception as _e:
                        if attempt < 2 and self._handle_rate_limit_error(_e):
                            continue
                        raise
                if api_track is None:
                    enriched_tracks.append(track)
                    continue

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

                # Add album ID (for grouping/linking)
                if not track.get('album_id') and api_track.get('album', {}).get('id'):
                    track['album_id'] = api_track['album']['id']

                # Add album total tracks count
                if not track.get('album_total_tracks') and api_track.get('album', {}).get('total_tracks'):
                    track['album_total_tracks'] = api_track['album']['total_tracks']

                # Add album type (album, single, compilation)
                if not track.get('album_type') and api_track.get('album', {}).get('album_type'):
                    track['album_type'] = api_track['album']['album_type']

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

        # Fetch and attach artist data from artist endpoints
        print("   Fetching artist data (genres, images, followers)...")
        artist_data_map = self._fetch_artist_data(enriched_tracks)
        genre_count = 0
        artist_enriched_count = 0
        for track in enriched_tracks:
            track_genres = set()
            artists = track.get('artists', [])

            # Get primary artist ID (first artist)
            primary_artist_id = None
            if artists and isinstance(artists[0], dict):
                primary_artist_id = artists[0].get('id')

            # Attach primary artist metadata to track
            if primary_artist_id and primary_artist_id in artist_data_map:
                primary_data = artist_data_map[primary_artist_id]
                track['artist_image'] = primary_data.get('image')
                track['artist_followers'] = primary_data.get('followers', 0)
                track['artist_popularity'] = primary_data.get('popularity', 0)
                artist_enriched_count += 1

            # Collect genres from all artists on the track
            for artist in artists:
                if isinstance(artist, dict) and artist.get('id'):
                    artist_info = artist_data_map.get(artist['id'], {})
                    genres = artist_info.get('genres', [])
                    track_genres.update(genres)

            track['genres'] = list(track_genres)
            if track['genres']:
                genre_count += 1

        print(f"   ✓ Added genres to {genre_count}/{len(enriched_tracks)} tracks")
        print(f"   ✓ Added artist metadata to {artist_enriched_count}/{len(enriched_tracks)} tracks")

        # Fetch and attach album data (full track listings with popularity)
        print("   Fetching album data (full track listings)...")
        album_data_map = self._fetch_album_data(enriched_tracks)
        album_enriched_count = 0
        for track in enriched_tracks:
            album_id = track.get('album_id')
            if album_id and album_id in album_data_map:
                track['album_all_tracks'] = album_data_map[album_id]['tracks']
                album_enriched_count += 1

        print(f"   ✓ Added album track listings to {album_enriched_count}/{len(enriched_tracks)} tracks")

        return enriched_tracks

    def _fetch_artist_data(self, tracks: List[Dict]) -> Dict[str, Dict]:
        """
        Fetch artist data for all unique artists across tracks using batch API calls.

        Collects genres, images, follower counts, and popularity for each artist.

        Args:
            tracks: List of tracks with artist information

        Returns:
            Dict mapping artist_id to artist data dict with keys:
            - genres: list of genre strings
            - image: artist image URL (or None)
            - followers: follower count (int)
            - popularity: artist popularity 0-100 (int)
        """
        # Collect unique artist IDs
        artist_ids = set()
        for track in tracks:
            for artist in track.get('artists', []):
                if isinstance(artist, dict) and artist.get('id'):
                    artist_ids.add(artist['id'])

        if not artist_ids:
            return {}

        artist_data_map = {}
        artist_ids_list = list(artist_ids)

        # Batch fetch (Spotify API supports up to 50 artists per request)
        batch_size = 50
        for i in range(0, len(artist_ids_list), batch_size):
            batch = artist_ids_list[i:i + batch_size]
            try:
                self._enforce_rate_limit()
                response = None
                for attempt in range(3):
                    try:
                        response = self.client.artists(batch)
                        with self.__class__._rate_limit_lock:
                            self.__class__._consecutive_429s = 0
                        break
                    except Exception as _e:
                        if attempt < 2 and self._handle_rate_limit_error(_e):
                            continue
                        raise
                if response is None:
                    raise RuntimeError("artists() returned no response after retries")
                for artist_data in response.get('artists', []):
                    if artist_data:
                        # Extract artist image (first/largest image if available)
                        images = artist_data.get('images', [])
                        image_url = images[0]['url'] if images else None

                        # Extract follower count
                        followers = artist_data.get('followers', {}).get('total', 0)

                        # Extract artist popularity
                        popularity = artist_data.get('popularity', 0)

                        artist_data_map[artist_data['id']] = {
                            'genres': artist_data.get('genres', []),
                            'image': image_url,
                            'followers': followers,
                            'popularity': popularity
                        }
            except Exception as e:
                print(f"   Warning: Failed to fetch data for artist batch: {e}")
                for artist_id in batch:
                    if artist_id not in artist_data_map:
                        artist_data_map[artist_id] = {
                            'genres': [],
                            'image': None,
                            'followers': 0,
                            'popularity': 0
                        }

        print(f"   ✓ Fetched data for {len(artist_data_map)}/{len(artist_ids)} unique artists")
        return artist_data_map

    def _fetch_album_data(self, tracks: List[Dict]) -> Dict[str, Dict]:
        """
        Fetch album data including full track listings for all unique albums.

        Args:
            tracks: List of tracks with album information

        Returns:
            Dict mapping album_id to album data dict with keys:
            - album_name: str
            - album_image: str (URL)
            - album_url: str
            - release_date: str
            - album_type: str (album, single, compilation)
            - total_tracks: int
            - tracks: list of track dicts with {name, id, track_number, duration_ms, popularity, explicit, spotify_url}
        """
        # Collect unique album IDs
        album_ids = set()
        for track in tracks:
            album_id = track.get('album_id')
            if album_id:
                album_ids.add(album_id)

        if not album_ids:
            return {}

        album_data_map = {}
        album_ids_list = list(album_ids)

        # Batch fetch albums (Spotify API supports up to 20 albums per request)
        batch_size = 20
        for i in range(0, len(album_ids_list), batch_size):
            batch = album_ids_list[i:i + batch_size]
            try:
                self._enforce_rate_limit()
                response = None
                for attempt in range(3):
                    try:
                        response = self.client.albums(batch)
                        with self.__class__._rate_limit_lock:
                            self.__class__._consecutive_429s = 0
                        break
                    except Exception as _e:
                        if attempt < 2 and self._handle_rate_limit_error(_e):
                            continue
                        raise
                if response is None:
                    raise RuntimeError("albums() returned no response after retries")
                for album_data in response.get('albums', []):
                    if album_data:
                        album_id = album_data['id']
                        images = album_data.get('images', [])
                        image_url = images[0]['url'] if images else None

                        # Extract all tracks from the album
                        album_tracks = []
                        for item in album_data.get('tracks', {}).get('items', []):
                            track_artists = [a.get('name', '') for a in item.get('artists', [])]
                            album_tracks.append({
                                'name': item.get('name', ''),
                                'id': item.get('id', ''),
                                'track_number': item.get('track_number', 0),
                                'duration_ms': item.get('duration_ms', 0),
                                'explicit': item.get('explicit', False),
                                'spotify_url': item.get('external_urls', {}).get('spotify', ''),
                                'artists': track_artists,
                                'artist': ', '.join(track_artists),
                                'popularity': None  # Will be fetched separately
                            })

                        album_data_map[album_id] = {
                            'album_name': album_data.get('name', ''),
                            'album_image': image_url,
                            'album_url': album_data.get('external_urls', {}).get('spotify', ''),
                            'release_date': album_data.get('release_date', ''),
                            'album_type': album_data.get('album_type', ''),
                            'total_tracks': album_data.get('total_tracks', 0),
                            'tracks': album_tracks
                        }
            except Exception as e:
                print(f"   Warning: Failed to fetch data for album batch: {e}")

        # Now fetch popularity for all album tracks
        # Collect all track IDs that need popularity
        track_ids_to_fetch = []
        track_id_to_album = {}  # Map track_id -> (album_id, track_index)
        for album_id, album_info in album_data_map.items():
            for idx, album_track in enumerate(album_info['tracks']):
                if album_track['id']:
                    track_ids_to_fetch.append(album_track['id'])
                    track_id_to_album[album_track['id']] = (album_id, idx)

        # Batch fetch track popularity (Spotify API supports up to 50 tracks per request)
        if track_ids_to_fetch:
            popularity_batch_size = 50
            for i in range(0, len(track_ids_to_fetch), popularity_batch_size):
                batch = track_ids_to_fetch[i:i + popularity_batch_size]
                try:
                    self._enforce_rate_limit()
                    response = None
                    for attempt in range(3):
                        try:
                            response = self.client.tracks(batch)
                            with self.__class__._rate_limit_lock:
                                self.__class__._consecutive_429s = 0
                            break
                        except Exception as _e:
                            if attempt < 2 and self._handle_rate_limit_error(_e):
                                continue
                            raise
                    if response is None:
                        raise RuntimeError("tracks() returned no response after retries")
                    for track_data in response.get('tracks', []):
                        if track_data:
                            track_id = track_data['id']
                            popularity = track_data.get('popularity', 0)
                            preview_url = track_data.get('preview_url')
                            if track_id in track_id_to_album:
                                album_id, idx = track_id_to_album[track_id]
                                album_data_map[album_id]['tracks'][idx]['popularity'] = popularity
                                album_data_map[album_id]['tracks'][idx]['preview_url'] = preview_url
                except Exception as e:
                    print(f"   Warning: Failed to fetch track popularity batch: {e}")

        print(f"   ✓ Fetched data for {len(album_data_map)}/{len(album_ids)} unique albums")
        return album_data_map

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

                # Store playlist_id on each track for URL generation
                for track in tracks:
                    track['playlist_id'] = playlist_id

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

