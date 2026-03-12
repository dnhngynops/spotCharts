"""
Supabase client for intermediate data storage and historical analytics.

Writes enriched track data to the v2.0 normalised schema after each pipeline
run so that:
  - Every run's chart data is persisted permanently.
  - The dashboard JS client can fetch historical positions, trend arrows, and
    peak positions without re-running the pipeline.

Tables written (in FK-dependency order):
   1. playlists        — upsert by spotify_playlist_id
   2. playlist_scrapes — insert one row per run (→ scrape_id)
   3. genres           — upsert by genre_name
   4. credits          — upsert artists by spotify_id
   5. credit_genres    — upsert artist ↔ genre links
   6. albums           — upsert by spotify_id (+ all_tracks JSONB)
   7. songs            — upsert by spotify_id, FK → album_id
   8. song_credits     — upsert song ↔ artist junction
   9. song_genres      — upsert song ↔ genre junction
  10. playlist_songs   — insert position observation (playlist × song × scrape)

Schema: sql/schema.sql (v2.0)
"""
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

from src.core import config
from src.utils.name_normalizer import normalize_credit_name, normalize_name
from src.utils.role_normalizer import (
    canonical_credit_category,
    is_known_canonical,
    normalize_role,
    normalize_role_string,
)

logger = logging.getLogger(__name__)

_BATCH_SIZE = 500
_ARTIST_ROLE_NAME = 'Artist'


class SupabaseClient:
    """Write enriched chart data to the Supabase v2.0 schema after each pipeline run."""

    def __init__(self):
        if not self.is_configured():
            raise RuntimeError(
                "Supabase is not configured. "
                "Set SUPABASE_URL and SUPABASE_SERVICE_KEY in your .env file."
            )
        # Import here so the rest of the codebase doesn't hard-depend on the
        # supabase package when credentials are absent.
        from supabase import create_client
        self._client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)

    @classmethod
    def is_configured(cls) -> bool:
        """Return True when the required env vars are present."""
        return bool(config.SUPABASE_URL and config.SUPABASE_SERVICE_KEY)

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def fetch_latest_tracks(self) -> List[Dict]:
        """
        Read the most recent scrape run from Supabase and reconstruct the flat
        track list that DashboardGenerator.generate_dashboard() expects.

        Joins (in order):
          playlist_songs → songs → albums
          playlist_songs → playlists
          song_credits   → credits   (artists)
          song_genres    → genres

        Returns:
            List of track dicts in the same format produced by SpotifyClient.
        """
        # 1. Latest completed scrape
        scrape_result = (
            self._client.table('playlist_scrapes')
            .select('scrape_id, scrape_date, completed_at')
            .order('scrape_id', desc=True)
            .limit(1)
            .execute()
        )
        if not scrape_result.data:
            logger.warning("Supabase fetch: no scrapes found.")
            return []

        scrape = scrape_result.data[0]
        scrape_id = scrape['scrape_id']
        logger.info("Supabase fetch: scrape_id=%s (%s)", scrape_id, scrape.get('scrape_date', ''))

        # 2. playlist_songs with nested song + album + playlist
        ps_result = (
            self._client.table('playlist_songs')
            .select(
                'position, song_id, '
                'playlists(name, spotify_playlist_id), '
                'songs('
                '  song_id, spotify_id, title, duration_ms, explicit,'
                '  popularity, preview_url, spotify_url, release_date,'
                '  albums(spotify_id, name, album_type, total_tracks, image_url, spotify_url, all_tracks)'
                ')'
            )
            .eq('scrape_id', scrape_id)
            .execute()
        )
        rows = ps_result.data or []
        if not rows:
            logger.warning("Supabase fetch: scrape_id=%s has no playlist_songs rows.", scrape_id)
            return []

        song_db_ids = [row['song_id'] for row in rows if row.get('song_id')]

        # 3. Artists: song_credits → credits (filter explicitly by 'Artist' role on the song)
        role_result = self._client.table('roles').select('role_id').eq('role_name', _ARTIST_ROLE_NAME).execute()
        artist_role_id = role_result.data[0]['role_id'] if role_result.data else None

        query = (
            self._client.table('song_credits')
            .select(
                'song_id, '
                'credits!inner(spotify_id, name, spotify_url, spotify_image_url,'
                '        spotify_followers, spotify_popularity)'
            )
            .in_('song_id', song_db_ids)
        )
        if artist_role_id:
            query = query.eq('role_id', artist_role_id)
        
        credits_result = query.execute()
        credits_by_song: Dict[int, List[Dict]] = {}
        for sc in (credits_result.data or []):
            cred = sc.get('credits') or {}
            if cred:
                credits_by_song.setdefault(sc['song_id'], []).append(cred)

        # 4. Genres: song_genres → genres
        genres_result = (
            self._client.table('song_genres')
            .select('song_id, genres(genre_name)')
            .in_('song_id', song_db_ids)
            .execute()
        )
        genres_by_song: Dict[int, List[str]] = {}
        for sg in (genres_result.data or []):
            gname = (sg.get('genres') or {}).get('genre_name')
            if gname:
                genres_by_song.setdefault(sg['song_id'], []).append(gname)

        # 5. Reconstruct flat track dicts
        tracks: List[Dict] = []
        for row in rows:
            song     = row.get('songs') or {}
            album    = song.get('albums') or {}
            playlist = row.get('playlists') or {}
            song_db_id   = row.get('song_id')
            artists_raw  = credits_by_song.get(song_db_id, [])
            primary      = artists_raw[0] if artists_raw else {}

            artists = []
            seen_artist_ids = set()
            for a in artists_raw:
                # Use spotify_id if available, fallback to name to deduplicate
                aid = a.get('spotify_id') or a.get('name') or ''
                if aid and aid not in seen_artist_ids:
                    seen_artist_ids.add(aid)
                    artists.append({
                        'id':   a.get('spotify_id') or '',
                        'name': a.get('name') or '',
                        'url':  a.get('spotify_url') or '',
                    })

            tracks.append({
                'track_id':           song.get('spotify_id') or '',
                'track_name':         song.get('title') or '',
                'artists':            artists,
                'album':              album.get('name') or '',
                'album_id':           album.get('spotify_id') or '',
                'album_url':          album.get('spotify_url') or '',
                'album_image':        album.get('image_url') or '',
                'album_type':         album.get('album_type') or '',
                'album_total_tracks': album.get('total_tracks'),
                'album_all_tracks':   album.get('all_tracks'),
                'release_date':       str(song.get('release_date') or ''),
                'duration_ms':        song.get('duration_ms'),
                'explicit':           bool(song.get('explicit', False)),
                'popularity':         song.get('popularity'),
                'preview_url':        song.get('preview_url') or '',
                'spotify_url':        song.get('spotify_url') or '',
                'genres':             genres_by_song.get(song_db_id, []),
                'playlist':           playlist.get('name') or '',
                'playlist_id':        playlist.get('spotify_playlist_id') or '',
                'position':           row.get('position'),
                'artist_image':       primary.get('spotify_image_url') or '',
                'artist_followers':   primary.get('spotify_followers'),
                'artist_popularity':  primary.get('spotify_popularity'),
            })

        logger.info("Supabase fetch: returning %d tracks from scrape_id=%s", len(tracks), scrape_id)
        return tracks

    def save_run(self, run_id: str, tracks: List[Dict], scrape_type: str = 'scheduled') -> None:
        """
        Persist a complete pipeline run to the v2.0 schema.

        Args:
            run_id:      Unique run identifier (timestamp string from main.py,
                         e.g. "20260218_143022").
            tracks:      Fully enriched track list produced by SpotifyClient.
            scrape_type: 'scheduled' for CI/cron runs, 'manual' for local dev runs.
        """
        if not tracks:
            logger.warning("Supabase: save_run called with empty track list — skipping.")
            return

        # ── Index unique entities from the track list ──────────────────────
        playlists_seen: Dict[str, str] = {}      # {spotify_playlist_id: name}
        artists_seen: Dict[str, Dict] = {}        # {spotify_artist_id: artist_dict}
        artist_enrichment: Dict[str, Dict] = {}   # {spotify_artist_id: {image,followers,pop}}
        genres_seen: Set[str] = set()             # genre_name strings
        albums_seen: Dict[str, Dict] = {}         # {spotify_album_id: first_track}

        for t in tracks:
            pid = t.get('playlist_id') or ''
            if pid and t.get('playlist'):
                playlists_seen[pid] = t['playlist']

            for a in (t.get('artists') or []):
                aid = a.get('id') or ''
                if aid:
                    artists_seen[aid] = a

            # artist_image / artist_followers / artist_popularity are for the
            # primary (first) artist only — Spotify's track-level API does not
            # return per-artist breakdown.
            primary = (t.get('artists') or [{}])[0]
            primary_id = primary.get('id') or ''
            if primary_id and primary_id not in artist_enrichment:
                artist_enrichment[primary_id] = {
                    'image': t.get('artist_image') or None,
                    'followers': t.get('artist_followers'),
                    'popularity': t.get('artist_popularity'),
                }

            for g in (t.get('genres') or []):
                if g:
                    genres_seen.add(g.strip())

            album_spotify_id = t.get('album_id') or ''
            if album_spotify_id and album_spotify_id not in albums_seen:
                albums_seen[album_spotify_id] = t

        # ── Write in FK-dependency order ────────────────────────────────────
        playlist_db_ids = self._upsert_playlists(playlists_seen)
        logger.info("Supabase: %d playlists upserted", len(playlist_db_ids))

        scrape_id = self._insert_scrape(run_id, playlists_seen, tracks, scrape_type)
        logger.info("Supabase: playlist_scrape inserted (scrape_id=%s)", scrape_id)

        artist_role_id = self._ensure_role(_ARTIST_ROLE_NAME, 'creative')

        genre_id_map = self._upsert_genres(genres_seen)
        logger.info("Supabase: %d genres ready", len(genre_id_map))

        credit_id_map = self._upsert_credits(artists_seen, artist_enrichment)
        logger.info("Supabase: %d credits upserted", len(credit_id_map))

        self._upsert_credit_genres(tracks, credit_id_map, genre_id_map)

        album_id_map = self._upsert_albums(albums_seen)
        logger.info("Supabase: %d albums upserted", len(album_id_map))

        song_id_map = self._upsert_songs(tracks, album_id_map)
        logger.info("Supabase: %d songs upserted", len(song_id_map))

        self._upsert_song_credits(tracks, song_id_map, credit_id_map, artist_role_id)
        self._upsert_song_genres(tracks, song_id_map, genre_id_map)

        try:
            self._upsert_genius_credits(tracks, song_id_map)
        except Exception as e:
            logger.warning("Supabase: Genius credits persistence failed (non-fatal): %s", e)

        self._insert_playlist_songs(tracks, playlist_db_ids, song_id_map, scrape_id)

        logger.info(
            "Supabase: run %s complete — %d tracks across %d playlists",
            run_id, len(tracks), len(playlists_seen),
        )

    # -------------------------------------------------------------------------
    # Step helpers
    # -------------------------------------------------------------------------

    def _upsert_playlists(self, playlists_seen: Dict[str, str]) -> Dict[str, int]:
        """Upsert playlist rows; return {spotify_playlist_id: playlist_id}."""
        if not playlists_seen:
            return {}
        rows = [
            {
                'spotify_playlist_id': pid,
                'name': name,
                'source_type': 'spotify_editorial',
                'spotify_url': f'https://open.spotify.com/playlist/{pid}',
                'updated_at': _now(),
            }
            for pid, name in playlists_seen.items()
        ]
        result = self._client.table('playlists').upsert(
            rows, on_conflict='spotify_playlist_id'
        ).execute()
        return {r['spotify_playlist_id']: r['playlist_id'] for r in result.data}

    def _insert_scrape(
        self,
        run_id: str,
        playlists_seen: Dict[str, str],
        tracks: List[Dict],
        scrape_type: str = 'scheduled',
    ) -> int:
        """Insert a playlist_scrapes row for this run; return the scrape_id."""
        unique_tracks = len({_extract_track_id(t) for t in tracks if _extract_track_id(t)})
        result = self._client.table('playlist_scrapes').insert({
            'scrape_date': _now(),
            'scrape_type': scrape_type,
            'status': 'completed',
            'total_playlists': len(playlists_seen),
            'total_songs': unique_tracks,
            'notes': f'run_id={run_id}',
            'started_at': _now(),
            'completed_at': _now(),
        }).execute()
        return result.data[0]['scrape_id']

    def _ensure_role(self, role_name: str, category: str) -> int:
        """Return role_id for role_name, inserting the row if it does not exist."""
        result = (
            self._client.table('roles')
            .select('role_id')
            .eq('role_name', role_name)
            .limit(1)
            .execute()
        )
        if result.data:
            return result.data[0]['role_id']
        insert_result = self._client.table('roles').insert(
            {'role_name': role_name, 'category': category, 'display_order': 0}
        ).execute()
        return insert_result.data[0]['role_id']

    def _upsert_genres(self, genres_seen: Set[str]) -> Dict[str, int]:
        """
        Upsert genres; return {genre_name: genre_id}.

        Uses ignore_duplicates=True because the genres table has no updated_at
        column to bump on conflict. Fetches all matching rows afterwards to
        build the complete ID map (including pre-existing genres).
        """
        if not genres_seen:
            return {}
        self._client.table('genres').upsert(
            [{'genre_name': g} for g in genres_seen],
            on_conflict='genre_name',
            ignore_duplicates=True,
        ).execute()
        result = (
            self._client.table('genres')
            .select('genre_id, genre_name')
            .in_('genre_name', list(genres_seen))
            .execute()
        )
        return {r['genre_name']: r['genre_id'] for r in result.data}

    def _upsert_credits(
        self,
        artists_seen: Dict[str, Dict],
        artist_enrichment: Dict[str, Dict],
    ) -> Dict[str, int]:
        """Upsert credit rows for all artists; return {spotify_artist_id: credit_id}.

        The credits table has two independent unique constraints (spotify_id,
        normalized_name).  A naive batch upsert on one constraint can fail when
        the other constraint is also violated by a different existing row (e.g. a
        Genius-created stub without a spotify_id).  This method handles three
        explicit paths to avoid batch-level conflicts:

          1. Row already exists by spotify_id  → UPDATE by spotify_id (batch)
          2. Row exists by normalized_name only (Genius stub, no spotify_id)
                                               → UPDATE by normalized_name (individual)
          3. Truly new row                     → INSERT (batch)
        """
        if not artists_seen:
            return {}
        rows = []
        for aid, a in artists_seen.items():
            enrich = artist_enrichment.get(aid, {})
            artist_url = a.get('url') or f'https://open.spotify.com/artist/{aid}'
            rows.append({
                'name': a.get('name') or '',
                'normalized_name': normalize_credit_name(a.get('name') or ''),
                'credit_category': 'artist',
                'creative': True,
                'spotify_id': aid,
                'spotify_url': artist_url,
                'spotify_image_url': enrich.get('image'),
                'spotify_followers': enrich.get('followers'),
                'spotify_popularity': enrich.get('popularity'),
                'updated_at': _now(),
            })

        all_spotify_ids = [r['spotify_id'] for r in rows]

        # ── Query 1: fetch existing rows by spotify_id (incl. stored norm name) ─
        sid_result = (
            self._client.table('credits')
            .select('credit_id, spotify_id, normalized_name')
            .in_('spotify_id', all_spotify_ids)
            .execute()
        )
        existing_by_sid: Dict[str, Dict] = {
            r['spotify_id']: r for r in (sid_result.data or [])
        }

        # ── Classify into existing vs new ─────────────────────────────────────
        update_rows: List[Dict] = []
        new_rows:    List[Dict] = []
        for row in rows:
            if row['spotify_id'] in existing_by_sid:
                # Preserve the stored normalized_name to avoid mutating it.
                # The display `name` field is still refreshed from Spotify.
                # Changing normalized_name risks colliding with Genius stubs that
                # already hold the new value (e.g. Spotify returning "Jaÿ-Z"
                # one run and "JAY-Z" the next).
                r = dict(row)
                r['normalized_name'] = existing_by_sid[row['spotify_id']]['normalized_name']
                update_rows.append(r)
            else:
                new_rows.append(row)

        # ── Path 1: batch upsert existing rows (no normalized_name change) ────
        if update_rows:
            self._client.table('credits').upsert(
                update_rows, on_conflict='spotify_id'
            ).execute()

        # ── Query 2: Genius stubs for remaining new rows ──────────────────────
        if new_rows:
            new_norm_names = [r['normalized_name'] for r in new_rows]
            genius_result = (
                self._client.table('credits')
                .select('credit_id, normalized_name')
                .in_('normalized_name', new_norm_names)
                .is_('spotify_id', 'null')
                .execute()
            )
            genius_norms = {r['normalized_name'] for r in (genius_result.data or [])}
        else:
            genius_norms = set()

        merge_rows  = [r for r in new_rows if r['normalized_name'] in genius_norms]
        insert_rows = [r for r in new_rows if r['normalized_name'] not in genius_norms]

        # ── Path 2: individual UPDATE for Genius stubs (add spotify_id) ───────
        for row in merge_rows:
            self._client.table('credits').update({
                'name':               row['name'],
                'credit_category':    row['credit_category'],
                'spotify_id':         row['spotify_id'],
                'spotify_url':        row['spotify_url'],
                'spotify_image_url':  row['spotify_image_url'],
                'spotify_followers':  row['spotify_followers'],
                'spotify_popularity': row['spotify_popularity'],
                'updated_at':         row['updated_at'],
            }).eq('normalized_name', row['normalized_name']).execute()

        # ── Path 3: batch INSERT truly new rows ───────────────────────────────
        if insert_rows:
            self._client.table('credits').insert(insert_rows).execute()

        # ── Fetch back all credit_ids by spotify_id ───────────────────────────
        result = (
            self._client.table('credits')
            .select('credit_id, spotify_id')
            .in_('spotify_id', all_spotify_ids)
            .execute()
        )
        return {r['spotify_id']: r['credit_id'] for r in (result.data or [])}

    def _upsert_credit_genres(
        self,
        tracks: List[Dict],
        credit_id_map: Dict[str, int],
        genre_id_map: Dict[str, int],
    ) -> None:
        """
        Upsert artist ↔ genre links via credit_genres.

        NOTE: track['genres'] is the combined genre list from all artists on
        the track. Spotify's track-level API does not expose per-artist genre
        breakdown, so genres are assigned to all artists on each track as an
        approximation.
        """
        rows: List[Dict] = []
        seen: Set[tuple] = set()
        for t in tracks:
            for g in (t.get('genres') or []):
                gid = genre_id_map.get(g.strip())
                if not gid:
                    continue
                for a in (t.get('artists') or []):
                    cid = credit_id_map.get(a.get('id') or '')
                    if not cid:
                        continue
                    key = (cid, gid)
                    if key not in seen:
                        seen.add(key)
                        rows.append({
                            'credit_id': cid,
                            'genre_id': gid,
                            'source': 'spotify_artist',
                        })
        self._batch_upsert(
            'credit_genres', rows,
            on_conflict='credit_id,genre_id',
            ignore_duplicates=True,
        )

    def _upsert_albums(self, albums_seen: Dict[str, Dict]) -> Dict[str, int]:
        """Upsert album rows; return {spotify_album_id: album_id}."""
        if not albums_seen:
            return {}
        rows = [
            {
                'spotify_id': aid,
                'spotify_url': t.get('album_url') or None,
                'name': t.get('album') or '',
                'normalized_name': normalize_name(t.get('album') or ''),
                'album_type': _normalise_album_type(t.get('album_type')),
                'release_date': _parse_date(t.get('release_date')),
                'total_tracks': t.get('album_total_tracks'),
                'image_url': t.get('album_image') or None,
                'all_tracks': t.get('album_all_tracks') or None,
                'updated_at': _now(),
            }
            for aid, t in albums_seen.items()
        ]
        result = self._client.table('albums').upsert(
            rows, on_conflict='spotify_id'
        ).execute()
        return {r['spotify_id']: r['album_id'] for r in result.data}

    def _upsert_songs(
        self, tracks: List[Dict], album_id_map: Dict[str, int]
    ) -> Dict[str, int]:
        """
        Upsert song rows (deduplicated by track_id);
        return {spotify_track_id: song_id}.
        """
        unique: Dict[str, Dict] = {}
        for t in tracks:
            tid = _extract_track_id(t)
            if tid and tid not in unique:
                unique[tid] = t
        if not unique:
            return {}
        rows = [
            {
                'spotify_id': tid,
                'spotify_url': t.get('spotify_url') or None,
                'title': t.get('track_name') or '',
                'normalized_title': normalize_name(t.get('track_name') or ''),
                'album_id': album_id_map.get(t.get('album_id') or '') or None,
                'duration_ms': t.get('duration_ms'),
                'explicit': bool(t.get('explicit', False)),
                'popularity': t.get('popularity'),
                'preview_url': t.get('preview_url') or None,
                'release_date': _parse_date(t.get('release_date')),
                'updated_at': _now(),
            }
            for tid, t in unique.items()
        ]
        result = self._client.table('songs').upsert(
            rows, on_conflict='spotify_id'
        ).execute()
        return {r['spotify_id']: r['song_id'] for r in result.data}

    def _upsert_song_credits(
        self,
        tracks: List[Dict],
        song_id_map: Dict[str, int],
        credit_id_map: Dict[str, int],
        artist_role_id: int,
    ) -> None:
        """Upsert song ↔ artist junction rows via song_credits."""
        rows: List[Dict] = []
        seen: Set[tuple] = set()
        for t in tracks:
            sid = song_id_map.get(_extract_track_id(t))
            if not sid:
                continue
            for a in (t.get('artists') or []):
                cid = credit_id_map.get(a.get('id') or '')
                if not cid:
                    continue
                key = (sid, cid, artist_role_id)
                if key not in seen:
                    seen.add(key)
                    rows.append({
                        'song_id': sid,
                        'credit_id': cid,
                        'role_id': artist_role_id,
                    })
        self._batch_upsert(
            'song_credits', rows,
            on_conflict='song_id,credit_id,role_id',
            ignore_duplicates=True,
        )

    def _upsert_song_genres(
        self,
        tracks: List[Dict],
        song_id_map: Dict[str, int],
        genre_id_map: Dict[str, int],
    ) -> None:
        """Upsert song ↔ genre junction rows via song_genres."""
        rows: List[Dict] = []
        seen: Set[tuple] = set()
        for t in tracks:
            sid = song_id_map.get(_extract_track_id(t))
            if not sid:
                continue
            for g in (t.get('genres') or []):
                gid = genre_id_map.get(g.strip())
                if not gid:
                    continue
                key = (sid, gid)
                if key not in seen:
                    seen.add(key)
                    rows.append({
                        'song_id': sid,
                        'genre_id': gid,
                        'source': 'spotify_artist',
                    })
        self._batch_upsert(
            'song_genres', rows,
            on_conflict='song_id,genre_id',
            ignore_duplicates=True,
        )

    def _upsert_genius_credits(
        self,
        tracks: List[Dict],
        song_id_map: Dict[str, int],
    ) -> None:
        """
        Persist Genius writer / producer / other credits as song_credits rows.

        Credits are upserted by normalized_name (no spotify_id).  Canonical
        roles are ensured in the roles table.  Raw role strings are written to
        raw_role_names so the future role-normalisation pipeline can map them.
        song_credits rows receive both role_id (canonical) and raw_role_id.

        This method is additive: it never modifies existing artist credits and
        is always called inside a try/except in save_run() so failures are
        non-fatal.
        """
        # ── Step 1: collect unique credits, raw roles, and song links ────────
        # unique_credits: normalized_name → (display_name, credit_category | None)
        unique_credits: Dict[str, tuple] = {}
        # raw_roles: raw_role_name → (normalized_raw_string, canonical_name, role_category)
        raw_roles: Dict[str, tuple] = {}
        # song_links: (spotify_track_id, person_normalized_name, raw_role_name)
        song_links: List[tuple] = []

        def _collect(name: str, raw_role: str, track_id: str) -> None:
            if not name or not raw_role or not track_id:
                return
            norm_name = normalize_credit_name(name)
            if not norm_name:
                return
            canonical, category = normalize_role(raw_role)
            if norm_name not in unique_credits:
                unique_credits[norm_name] = (name, canonical_credit_category(canonical))
            if raw_role not in raw_roles:
                raw_roles[raw_role] = (normalize_role_string(raw_role), canonical, category)
            song_links.append((track_id, norm_name, raw_role))

        for t in tracks:
            gc = t.get('genius_credits')
            if not gc or gc.get('source') != 'genius':
                continue
            tid = _extract_track_id(t)
            if not tid or tid not in song_id_map:
                continue
            for writer in (gc.get('writers') or []):
                _collect(writer, 'Writer', tid)
            for producer in (gc.get('producers') or []):
                _collect(producer, 'Producer', tid)
            for oc in (gc.get('other_credits') or []):
                _collect(oc.get('name', ''), oc.get('role', ''), tid)

        if not unique_credits:
            logger.info("Supabase: no Genius credits to persist (no enriched tracks).")
            return

        # ── Step 2: ensure canonical roles exist and build role_id_map ───────
        role_id_map: Dict[str, int] = {}
        for _raw, (_, canonical, category) in raw_roles.items():
            if canonical not in role_id_map:
                role_id_map[canonical] = self._ensure_role(canonical, category)

        # ── Step 3: upsert raw_role_names, then fetch back IDs ───────────────
        rr_rows = []
        for raw_role_name, (norm_raw, canonical, _) in raw_roles.items():
            rid = role_id_map.get(canonical)
            is_mapped = is_known_canonical(canonical)  # True when pattern matched a known role
            rr_rows.append({
                'raw_role_name': raw_role_name,
                'normalized_name': norm_raw,
                'primary_role_id': rid,
                'mapping_confidence': 0.95 if is_mapped else None,
                'mapping_method': 'pattern_match' if is_mapped else None,
                'needs_review': not is_mapped,
            })
        self._client.table('raw_role_names').upsert(
            rr_rows,
            on_conflict='raw_role_name',
            ignore_duplicates=True,
        ).execute()
        rr_result = (
            self._client.table('raw_role_names')
            .select('raw_role_id, raw_role_name')
            .in_('raw_role_name', list(raw_roles.keys()))
            .execute()
        )
        raw_role_id_map: Dict[str, int] = {
            r['raw_role_name']: r['raw_role_id'] for r in (rr_result.data or [])
        }

        # ── Step 4: upsert credits by normalized_name, then fetch back IDs ───
        # ignore_duplicates=True preserves existing artist rows untouched.
        cr_rows = [
            {
                'name': display_name,
                'normalized_name': norm_name,
                'credit_category': credit_cat,
                'creative': True,
                'updated_at': _now(),
            }
            for norm_name, (display_name, credit_cat) in unique_credits.items()
        ]
        self._client.table('credits').upsert(
            cr_rows,
            on_conflict='normalized_name',
            ignore_duplicates=True,
        ).execute()
        cr_result = (
            self._client.table('credits')
            .select('credit_id, normalized_name')
            .in_('normalized_name', list(unique_credits.keys()))
            .execute()
        )
        genius_credit_id_map: Dict[str, int] = {
            r['normalized_name']: r['credit_id'] for r in (cr_result.data or [])
        }

        # ── Step 5: upsert song_credits with role_id + raw_role_id ──────────
        sc_rows: List[Dict] = []
        seen: Set[tuple] = set()
        for tid, norm_name, raw_role in song_links:
            sid = song_id_map.get(tid)
            cid = genius_credit_id_map.get(norm_name)
            canonical = raw_roles.get(raw_role, ('', 'Unknown', 'other'))[1]
            rid = role_id_map.get(canonical)
            raw_rid = raw_role_id_map.get(raw_role)
            if not sid or not cid or not rid:
                continue
            key = (sid, cid, rid)
            if key not in seen:
                seen.add(key)
                row: Dict = {'song_id': sid, 'credit_id': cid, 'role_id': rid}
                if raw_rid:
                    row['raw_role_id'] = raw_rid
                sc_rows.append(row)

        self._batch_upsert(
            'song_credits', sc_rows,
            on_conflict='song_id,credit_id,role_id',
            ignore_duplicates=True,
        )
        logger.info(
            "Supabase: Genius credits — %d people, %d raw roles, %d song_credit links",
            len(genius_credit_id_map), len(raw_role_id_map), len(sc_rows),
        )

    def _insert_playlist_songs(
        self,
        tracks: List[Dict],
        playlist_db_ids: Dict[str, int],
        song_id_map: Dict[str, int],
        scrape_id: int,
    ) -> None:
        """Insert playlist_songs position observations for this scrape."""
        rows: List[Dict] = []
        seen: Set[tuple] = set()
        for t in tracks:
            sid = song_id_map.get(_extract_track_id(t))
            pid = playlist_db_ids.get(t.get('playlist_id') or '')
            if not sid or not pid:
                continue
            key = (pid, sid, scrape_id)
            if key not in seen:
                seen.add(key)
                rows.append({
                    'playlist_id': pid,
                    'song_id': sid,
                    'scrape_id': scrape_id,
                    'position': t.get('position') or None,
                })
        self._batch_upsert(
            'playlist_songs', rows,
            on_conflict='playlist_id,song_id,scrape_id',
            ignore_duplicates=True,
        )

    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------

    def _batch_upsert(
        self,
        table: str,
        rows: List[Dict],
        on_conflict: str,
        ignore_duplicates: bool = False,
    ) -> None:
        """Upsert rows into table in chunks of _BATCH_SIZE."""
        for i in range(0, len(rows), _BATCH_SIZE):
            self._client.table(table).upsert(
                rows[i:i + _BATCH_SIZE],
                on_conflict=on_conflict,
                ignore_duplicates=ignore_duplicates,
            ).execute()


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    """Return the current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _extract_track_id(track: Dict) -> str:
    """
    Return the Spotify track ID from a track dict.

    Prefers track['track_id']; falls back to parsing track['spotify_url']
    when track_id is absent.
    """
    tid = track.get('track_id') or ''
    if not tid:
        url = track.get('spotify_url') or ''
        parts = url.rstrip('/').split('/')
        if len(parts) >= 2 and parts[-2] == 'track':
            tid = parts[-1].split('?')[0]
    return tid


def _parse_date(date_str: Optional[str]) -> Optional[str]:
    """
    Normalise a Spotify release date string to YYYY-MM-DD.

    Spotify may return 'YYYY', 'YYYY-MM', or 'YYYY-MM-DD'; the schema
    column is a PostgreSQL date type that requires a full YYYY-MM-DD.
    """
    if not date_str:
        return None
    parts = date_str.split('-')
    if len(parts) == 1:
        return f"{parts[0]}-01-01"
    if len(parts) == 2:
        return f"{parts[0]}-{parts[1]}-01"
    return date_str


def _normalise_album_type(album_type: Optional[str]) -> Optional[str]:
    """Map raw Spotify album_type to the CHECK constraint values in the schema."""
    if not album_type:
        return None
    t = album_type.lower()
    return t if t in ('album', 'single', 'compilation', 'ep') else None
