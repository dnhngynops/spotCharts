"""
Genius API Client
=================
Extracts song credits (writers, producers, engineers) and genre context
from the Genius API.

Primary entry point: GeniusClient.get_credits(title, artist)

Returns a dict with:
    source          — 'genius' or 'failed'
    writers         — list of writer names (from writer_artists field)
    producers       — list of producer names (from producer_artists field)
    other_credits   — list of {name, role} dicts (exact Genius role names preserved)
    genius_song_id  — int

Role names are preserved verbatim from Genius to feed the future role
normalisation pipeline (Migration 012 in the backend schema).

Rate limiting: 200 ms between requests (≤ 5 req/s), exponential backoff on 429.
"""

import re
import time
import requests
from typing import List, Dict, Optional

from src.core import config


class GeniusClient:
    """Client for extracting credits and genre context from Genius."""

    BASE_URL = "https://api.genius.com"

    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token or config.GENIUS_ACCESS_TOKEN

        if not self.access_token:
            print("   Warning: GENIUS_ACCESS_TOKEN not set — Genius will be unavailable")

        # Rate-limiting state
        self._last_request_time: float = 0.0
        self._min_request_interval: float = 0.2  # 200 ms → ≤ 5 req/s
        self._rate_limit_delay: int = 30          # seconds to wait on 429
        self._consecutive_429s: int = 0
        self._max_consecutive_429s: int = 3

    @classmethod
    def is_configured(cls) -> bool:
        """Return True when a Genius access token is available."""
        return bool(config.GENIUS_ACCESS_TOKEN)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_credits(self, title: str, artist: str) -> Dict:
        """
        Extract credits (writers, producers, etc.) for a song.

        Args:
            title:  Song title as returned by Spotify.
            artist: Primary artist name.

        Returns:
            {
                'source':        'genius' | 'failed',
                'writers':       [...],          # from writer_artists field
                'producers':     [...],          # from producer_artists field
                'other_credits': [{'name', 'role'}, ...],  # exact Genius roles
                'genius_song_id': int | None,
                'error':         str (only on failure)
            }
        """
        if not self.access_token:
            return {'source': 'failed', 'error': 'No Genius access token'}

        try:
            song_data = self.search_song(title, artist)
            if not song_data:
                return {'source': 'failed', 'error': 'Song not found on Genius'}

            song_id = song_data.get('id')
            if not song_id:
                return {'source': 'failed', 'error': 'No song ID in Genius result'}

            credits = self._get_enhanced_credits(song_id)
            if credits:
                return credits

            return {'source': 'failed', 'error': 'Failed to extract credits'}

        except Exception as e:
            return {'source': 'failed', 'error': str(e)}

    def search_song(self, song_title: str, artist_name: str) -> Optional[Dict]:
        """
        Search for a song on Genius using multiple query strategies.

        Returns the best matching song result dict, or None.
        """
        if not self.access_token:
            return None

        headers = {'Authorization': f'Bearer {self.access_token}'}

        for query in self._generate_search_queries(song_title, artist_name):
            try:
                self._rate_limit()
                response = requests.get(
                    f"{self.BASE_URL}/search",
                    headers=headers,
                    params={'q': query},
                    timeout=10,
                )

                if self._handle_rate_limit(response):
                    continue  # retry after waiting

                response.raise_for_status()
                hits = response.json().get('response', {}).get('hits', [])

                for hit in hits:
                    result = hit.get('result', {})
                    if result.get('type') == 'song' or (result.get('title') and result.get('primary_artist')):
                        genius_title = result.get('title', '')
                        genius_artist = result.get('primary_artist', {}).get('name', '')
                        if self._is_good_match(genius_title, genius_artist, song_title, artist_name):
                            return result

            except Exception:
                continue  # try next query strategy

        return None

    def search_artist(self, artist_name: str) -> Optional[Dict]:
        """Search for an artist and return full artist details."""
        if not self.access_token:
            return None

        headers = {'Authorization': f'Bearer {self.access_token}'}
        try:
            self._rate_limit()
            response = requests.get(
                f"{self.BASE_URL}/search",
                headers=headers,
                params={'q': artist_name},
                timeout=10,
            )
            response.raise_for_status()
            hits = response.json().get('response', {}).get('hits', [])
            if not hits:
                return None

            artist_info = hits[0].get('result', {}).get('primary_artist', {})
            if not artist_info or 'id' not in artist_info:
                return None

            return self._get_artist_details(artist_info['id'])

        except requests.exceptions.RequestException as e:
            self._log_request_error(e, 'search_artist')
            return None

    def get_song_info(self, song_id: int) -> Optional[Dict]:
        """Get the full song object from Genius by numeric ID."""
        if not self.access_token:
            return None

        headers = {'Authorization': f'Bearer {self.access_token}'}
        try:
            self._rate_limit()
            response = requests.get(
                f"{self.BASE_URL}/songs/{song_id}",
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            return response.json().get('response', {}).get('song', {})
        except Exception as e:
            print(f"   Warning: Genius get_song_info({song_id}) failed: {e}")
            return None

    # ------------------------------------------------------------------
    # Credits extraction
    # ------------------------------------------------------------------

    def _get_enhanced_credits(self, song_id: int) -> Optional[Dict]:
        """
        Fetch and parse all credit fields from the Genius song endpoint.

        Preserves exact role names from Genius so the future role-normalisation
        pipeline (Migration 012) can map them to canonical roles.
        """
        if not self.access_token:
            return None

        try:
            self._rate_limit()
            headers = {'Authorization': f'Bearer {self.access_token}'}
            response = requests.get(
                f"{self.BASE_URL}/songs/{song_id}",
                headers=headers,
                timeout=10,
            )

            if self._handle_rate_limit(response):
                return self._get_enhanced_credits(song_id)  # retry

            response.raise_for_status()
            song_data = response.json().get('response', {}).get('song', {})

            writers: set = set()
            producers: set = set()
            other_credits: list = []

            # Method 1: song_credits field (specific roles, exact names)
            for credit in song_data.get('song_credits', []):
                name = credit.get('name', '').strip()
                role = credit.get('role', '').strip()  # keep exact capitalisation
                if name and role:
                    other_credits.append({'name': name, 'role': role})

            # Method 2: producer_artists field (generic "Producer" role)
            for producer in song_data.get('producer_artists', []):
                name = producer.get('name', '').strip()
                if name:
                    producers.add(name)

            # Method 3: writer_artists field (generic "Writer" role)
            for writer in song_data.get('writer_artists', []):
                name = writer.get('name', '').strip()
                if name:
                    writers.add(name)

            # Method 4: custom_performances (additional labelled credits)
            for perf in song_data.get('custom_performances', []):
                label = perf.get('label', '').strip()  # exact label preserved
                for artist in perf.get('artists', []):
                    name = artist.get('name', '').strip()
                    if name and label:
                        other_credits.append({'name': name, 'role': label})

            return {
                'source': 'genius',
                'writers': list(writers),
                'producers': list(producers),
                'other_credits': other_credits,
                'genius_song_id': song_id,
            }

        except requests.exceptions.RequestException as e:
            self._log_request_error(e, f'_get_enhanced_credits({song_id})')
            return None
        except Exception as e:
            print(f"   Warning: Genius credits extraction failed: {e}")
            return None

    # ------------------------------------------------------------------
    # Search helpers
    # ------------------------------------------------------------------

    def _generate_search_queries(self, title: str, artist: str) -> List[str]:
        """
        Return ordered search query variants to maximise Genius match rate.

        Order: (1) clean title + main artist, (2) reversed, (3) original title
        if cleaning changed it, (4) simplified (no special chars).
        """
        clean_title = self.clean_title_for_search(title)
        main_artist = re.sub(
            r'\s+(feat\.?|featuring|ft\.?|with|f/)\s+.*$', '',
            artist.split(',')[0].split('&')[0].strip(),
            flags=re.IGNORECASE,
        ).strip()

        candidates = [
            f"{clean_title} {main_artist}",
            f"{main_artist} {clean_title}",
        ]
        if title != clean_title:
            candidates.append(f"{title} {main_artist}")

        simplified = re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', ' ', clean_title)).strip()
        if simplified != clean_title:
            candidates.append(f"{simplified} {main_artist}")

        seen: set = set()
        unique: list = []
        for q in candidates:
            if q and q not in seen:
                seen.add(q)
                unique.append(q)

        return unique or [f"{title} {artist}"]

    def clean_title_for_search(self, title: str) -> str:
        """
        Strip feature clauses, remaster labels, and version tags from a title
        to improve Genius search accuracy.
        """
        patterns = [
            r'\s*\(with\s+.*?\)',
            r'\s*\(feat\.?\s+.*?\)',
            r'\s*\(featuring\s+.*?\)',
            r'\s*\(ft\.?\s+.*?\)',
            r'\s*\(f/\s+.*?\)',
            r'\s*\(x\s+.*?\)',
            r'\s*-\s*Remastered.*$',
            r'\s*\(Remastered.*?\)',
            r'\s*-\s*.*?Remaster.*$',
            r'\s*-\s*.*?Version.*$',
            r'\s*\(.*?Version.*?\)',
            r'\s*-\s*From\s+".*?".*$',
            r'\s*\(From\s+".*?".*?\)',
            r'\s*-\s*featured\s+in.*$',
            r'\s*\(featured\s+in.*?\)',
            r'\s*-\s*From\s+the.*$',
            r'\s*\(From\s+the.*?\)',
            r'\s*-\s*.*?Radio.*$',
            r'\s*\(.*?Radio.*?\)',
            r'\s*-\s*.*?Mix.*$',
            r'\s*\(.*?Mix.*?\)',
        ]
        cleaned = title
        for p in patterns:
            cleaned = re.sub(p, '', cleaned, flags=re.IGNORECASE)

        # Normalise censored words so Genius can match them
        cleaned = re.sub(r'\bb\*+h\b', 'bitch', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\ba\*+\b', 'ass', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\bs\*+t\b', 'shit', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\bf\*+k\b', 'fuck', cleaned, flags=re.IGNORECASE)

        return re.sub(r'\s+', ' ', cleaned).strip()

    def _is_good_match(
        self,
        genius_title: str,
        genius_artist: str,
        original_title: str,
        original_artist: str,
    ) -> bool:
        """
        Return True when the Genius result is a genuine match (not a cover,
        translation, remix, or karaoke version).
        """
        gt = self.clean_title_for_search(genius_title).lower()
        ot = self.clean_title_for_search(original_title).lower()
        ga = genius_artist.lower()

        main_artist = re.sub(
            r'\s+(feat\.?|featuring|ft\.?|with|f/)\s+.*$', '',
            original_artist.split(',')[0].split('&')[0].strip(),
            flags=re.IGNORECASE,
        ).strip().lower()

        title_match = ot in gt or gt in ot or ot == gt
        artist_match = (
            main_artist in ga
            or ga in main_artist
            or any(w in ga for w in main_artist.split() if len(w) > 2)
        )

        skip = ['translation', 'srpski', 'cover', 'remix', '8-bit', 'karaoke', 'prevod']
        if any(w in gt for w in skip):
            return False
        if any(w in ga for w in ['translation', 'srpski', 'genius', 'prevod']):
            return False

        return title_match and artist_match

    # ------------------------------------------------------------------
    # Rate limiting
    # ------------------------------------------------------------------

    def _rate_limit(self) -> None:
        """Sleep if needed to stay within the 5 req/s target."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()

    def _handle_rate_limit(self, response: requests.Response) -> bool:
        """
        Handle a 429 response with exponential backoff.

        Returns True if the caller should retry, False if it should give up.
        """
        if response.status_code != 429:
            self._consecutive_429s = 0
            return False

        self._consecutive_429s += 1
        if self._consecutive_429s >= self._max_consecutive_429s:
            print(f"   Warning: Genius rate-limited {self._consecutive_429s}x — giving up on this request")
            return False

        retry_after = int(response.headers.get('Retry-After', self._rate_limit_delay))
        wait = min(retry_after * (2 ** (self._consecutive_429s - 1)), 300)
        print(f"   Warning: Genius 429 — waiting {wait}s (attempt {self._consecutive_429s})")
        time.sleep(wait)
        return True

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_artist_details(self, artist_id: int) -> Optional[Dict]:
        """Fetch full artist object from Genius by numeric ID."""
        if not self.access_token:
            return None

        headers = {'Authorization': f'Bearer {self.access_token}'}
        try:
            self._rate_limit()
            response = requests.get(
                f"{self.BASE_URL}/artists/{artist_id}",
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            return response.json().get('response', {}).get('artist', {})
        except requests.exceptions.RequestException as e:
            self._log_request_error(e, f'_get_artist_details({artist_id})')
            return None

    @staticmethod
    def _log_request_error(exc: Exception, context: str) -> None:
        """Print a concise warning for an HTTP error."""
        resp = getattr(exc, 'response', None)
        if resp is not None:
            status = resp.status_code
            if status == 401:
                print("   Warning: Genius API — invalid access token (401)")
            elif status == 429:
                print(f"   Warning: Genius API — rate limited (429) in {context}")
            else:
                print(f"   Warning: Genius API error {status} in {context}: {exc}")
        else:
            print(f"   Warning: Genius request failed in {context}: {exc}")
