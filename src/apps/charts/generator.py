"""
Charts Dashboard Generator

Generates the interactive HTML dashboard (shell/base.html + included app views)
from enriched Spotify playlist track data.
"""
import os
import html
import json
from typing import List, Dict, Optional
from datetime import datetime
from collections import Counter, defaultdict
from src.apps.shell.layout import get_env
from src.core import config


class DashboardGenerator:
    """Generate HTML dashboard with cross-playlist analytics"""

    def __init__(self):
        """Initialize dashboard generator with Jinja2 environment"""
        self.env = get_env()

    def generate_data_json(
        self,
        all_tracks: List[Dict],
        output_path: str,
        run_id: str = ''
    ) -> str:
        """
        Serialize pipeline analytics to a JSON file for the React dashboard.

        Writes the same data that generate_dashboard() passes to Jinja2,
        serialized as JSON so the React app can fetch it at runtime.
        Shape mirrors the RunData TypeScript interface in frontend/src/lib/types.ts.

        Args:
            all_tracks: List of all track dictionaries from all playlists
            output_path: Path where data.json should be saved
            run_id: Optional run identifier (becomes current_run_id in the JSON)

        Returns:
            Path to the generated JSON file
        """
        analytics = self._calculate_analytics(all_tracks)
        tracks_by_playlist = {
            pl: [self._normalize_track_for_json(t) for t in tracks]
            for pl, tracks in self._group_by_playlist(all_tracks).items()
        }
        sorted_all_tracks = [
            self._normalize_track_for_json(t)
            for t in self._build_deduplicated_ranked_all_tracks(all_tracks)
        ]

        playlist_urls = {}
        for track in all_tracks:
            pl_name = track.get('playlist', '')
            pl_id = track.get('playlist_id', '')
            if pl_name and pl_id and pl_name not in playlist_urls:
                playlist_urls[pl_name] = f'https://open.spotify.com/playlist/{pl_id}'

        payload = {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
            'current_run_id': run_id,
            'analytics': analytics,
            'tracks_by_playlist': tracks_by_playlist,
            'all_tracks': sorted_all_tracks,
            'playlist_urls': playlist_urls,
        }

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, default=str)

        return output_path

    def generate_dashboard(
        self,
        all_tracks: List[Dict],
        output_path: str,
        run_id: str = ''
    ) -> str:
        """
        Generate HTML dashboard from all collected tracks.

        Args:
            all_tracks: List of all track dictionaries from all playlists
            output_path: Path where HTML should be saved
            run_id: Optional run identifier for Supabase historical layer

        Returns:
            Path to the generated HTML file
        """
        # Calculate all analytics
        analytics = self._calculate_analytics(all_tracks)

        # Group tracks by playlist
        tracks_by_playlist = self._group_by_playlist(all_tracks)

        # Calculate per-playlist analytics for tab-specific insights
        playlist_analytics = {}
        for playlist_name, playlist_tracks in tracks_by_playlist.items():
            playlist_analytics[playlist_name] = self._calculate_playlist_analytics(
                playlist_tracks, playlist_name
            )

        # Deduplicate tracks and assign ranks for All Tracks tab
        sorted_all_tracks = self._build_deduplicated_ranked_all_tracks(all_tracks)

        # Build playlist name -> Spotify URL mapping
        playlist_urls = {}
        for track in all_tracks:
            pl_name = track.get('playlist', '')
            pl_id = track.get('playlist_id', '')
            if pl_name and pl_id and pl_name not in playlist_urls:
                playlist_urls[pl_name] = f'https://open.spotify.com/playlist/{pl_id}'

        # Load and render template via the shared Jinja2 environment
        template = self.env.get_template('shell/base.html')

        html_output = template.render(
            theme=config.SPOTIFY_THEME,
            generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            analytics=analytics,
            playlist_analytics=playlist_analytics,
            tracks_by_playlist=tracks_by_playlist,
            all_tracks=sorted_all_tracks,
            playlist_urls=playlist_urls,
            format_track_row=self._format_track_row,
            format_track_row_with_playlist=self._format_track_row_with_playlist,
            # Supabase config — safe anon key only; service key never exposed here
            supabase_url=config.SUPABASE_URL or '',
            supabase_anon_key=config.SUPABASE_ANON_KEY or '',
            current_run_id=run_id,
        )

        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_output)

        # Release large structures so GC can reclaim memory sooner (helps on low-RAM)
        del html_output
        del analytics, playlist_analytics, tracks_by_playlist, sorted_all_tracks

        return output_path

    def _calculate_analytics(self, tracks: List[Dict]) -> Dict:
        """
        Calculate cross-playlist analytics.

        Returns dict with:
        - summary: overall stats
        - top_artists: most frequent artists
        - chart_overlap: tracks on multiple charts
        - popularity_stats: popularity analysis by playlist
        - explicit_stats: explicit content analysis
        - playlist_stats: per-playlist breakdowns
        """
        analytics = {}

        # Summary stats
        playlists = set(t.get('playlist', '') for t in tracks)

        # Count unique artists across all tracks
        all_artists = set()
        for track in tracks:
            artists = track.get('artists', [])
            if isinstance(artists, list):
                for artist in artists:
                    if isinstance(artist, dict) and artist.get('name'):
                        all_artists.add(artist.get('name'))

        # Use same deduplication key as All Tracks table (track_id or name+artist+url)
        _unique_keys = set()
        for t in tracks:
            tid = (t.get('track_id') or '').strip()
            if tid:
                _unique_keys.add(tid)
            else:
                _unique_keys.add((
                    (t.get('track_name') or '').strip(),
                    (t.get('artist') or '').strip(),
                    (t.get('spotify_url') or '').strip()
                ))
        analytics['summary'] = {
            'total_tracks': len(tracks),
            'total_playlists': len(playlists),
            'playlist_names': sorted(playlists),
            'unique_tracks': len(_unique_keys),
            'unique_artists': len(all_artists)
        }

        # Top artists across all playlists
        artist_data = self._analyze_artists(tracks)
        analytics['top_artists'] = artist_data['top_artists']
        analytics['multi_playlist_artists'] = artist_data['multi_playlist_artists']

        # Chart overlap analysis
        analytics['chart_overlap'] = self._analyze_overlap(tracks)

        # Popularity analysis
        analytics['popularity_stats'] = self._analyze_popularity(tracks)

        # Explicit content analysis
        analytics['explicit_stats'] = self._analyze_explicit(tracks)

        # Genre analysis
        analytics['genre_stats'] = self._analyze_genres(tracks)

        # Per-playlist stats
        analytics['playlist_stats'] = self._analyze_playlists(tracks)

        return analytics

    def _analyze_artists(self, tracks: List[Dict]) -> Dict:
        """Analyze artist frequency and multi-playlist presence"""
        artist_counts = Counter()
        artist_playlists = defaultdict(set)
        artist_urls = {}
        artist_ids = {}
        artist_tracks = defaultdict(list)

        for track in tracks:
            playlist = track.get('playlist', 'Unknown')
            artists = track.get('artists', [])

            if isinstance(artists, list):
                for artist in artists:
                    if isinstance(artist, dict):
                        name = artist.get('name', '')
                        url = artist.get('url', '')
                        aid = artist.get('id', '')
                        if name:
                            artist_counts[name] += 1
                            artist_playlists[name].add(playlist)
                            if url and name not in artist_urls:
                                artist_urls[name] = url
                            if aid and name not in artist_ids:
                                artist_ids[name] = aid
                            artist_tracks[name].append({
                                'track_name': track.get('track_name', ''),
                                'playlist': playlist,
                                'spotify_url': track.get('spotify_url', ''),
                                'popularity': track.get('popularity', 0)
                            })

        # Top 20 artists
        top_artists = []
        for name, count in artist_counts.most_common(20):
            aid = artist_ids.get(name, '')
            top_artists.append({
                'name': name,
                'count': count,
                'playlists': len(artist_playlists[name]),
                'playlist_names': sorted(artist_playlists[name]),
                'url': artist_urls.get(name, ''),
                'tracks': artist_tracks.get(name, []),
                'profile_key': aid if aid else self._slugify(name)
            })

        # Artists on 3+ playlists
        multi_playlist = [
            {
                'name': name,
                'count': artist_counts[name],
                'playlists': len(playlists),
                'playlist_names': sorted(playlists),
                'url': artist_urls.get(name, ''),
                'tracks': artist_tracks.get(name, []),
                'profile_key': artist_ids.get(name, '') or self._slugify(name)
            }
            for name, playlists in artist_playlists.items()
            if len(playlists) >= 3
        ]
        multi_playlist.sort(key=lambda x: (-x['playlists'], -x['count']))

        return {
            'top_artists': top_artists,
            'multi_playlist_artists': multi_playlist[:10]
        }

    def _analyze_genres(self, tracks: List[Dict]) -> Dict:
        """Analyze genre frequency and cross-playlist presence"""
        genre_counts = Counter()
        genre_playlists = defaultdict(set)
        genre_tracks = defaultdict(list)

        for track in tracks:
            playlist = track.get('playlist', 'Unknown')
            for genre in track.get('genres', []):
                if genre:
                    genre_counts[genre] += 1
                    genre_playlists[genre].add(playlist)
                    artist = track.get('artist') or ', '.join(
                        a.get('name', '') for a in track.get('artists', [])
                        if isinstance(a, dict) and a.get('name')
                    )
                    genre_tracks[genre].append({
                        'track_name': track.get('track_name', ''),
                        'artist': artist,
                        'playlist': playlist,
                        'spotify_url': track.get('spotify_url', ''),
                        'popularity': track.get('popularity', 0)
                    })

        top_genres = []
        for genre, count in genre_counts.most_common(20):
            top_genres.append({
                'name': genre,
                'count': count,
                'playlists': len(genre_playlists[genre]),
                'playlist_names': sorted(genre_playlists[genre]),
                'tracks': genre_tracks.get(genre, [])
            })

        return {
            'top_genres': top_genres,
            'total_unique_genres': len(genre_counts)
        }

    def _analyze_overlap(self, tracks: List[Dict]) -> Dict:
        """Analyze track overlap between charts"""
        track_playlists = defaultdict(list)
        track_data = {}

        for track in tracks:
            key = (track.get('track_name', ''), track.get('artist', ''))
            playlist = track.get('playlist', '')
            track_playlists[key].append({
                'playlist': playlist,
                'position': track.get('position', 0)
            })
            if key not in track_data:
                track_data[key] = track

        # Find tracks on multiple playlists
        overlap_tracks = []
        for key, appearances in track_playlists.items():
            if len(appearances) > 1:
                track = track_data[key]
                overlap_tracks.append({
                    'track_name': track.get('track_name', ''),
                    'artist': track.get('artist', ''),
                    'spotify_url': track.get('spotify_url', ''),
                    'album_image': track.get('album_image', ''),
                    'appearances': appearances,
                    'num_charts': len(appearances)
                })

        overlap_tracks.sort(key=lambda x: -x['num_charts'])

        usa_songs = set()
        global_songs = set()
        songs_data = {}
        for track in tracks:
            key = (track.get('track_name', ''), track.get('artist', ''))
            playlist = track.get('playlist', '')
            pl_upper = playlist.upper()
            if 'USA' in pl_upper or 'BILLBOARD' in pl_upper:
                usa_songs.add(key)
                if key not in songs_data:
                    songs_data[key] = track
            elif 'GLOBAL' in pl_upper:
                global_songs.add(key)
                if key not in songs_data:
                    songs_data[key] = track

        usa_only = usa_songs - global_songs
        global_only = global_songs - usa_songs
        both = usa_songs & global_songs

        def _track_list(keys):
            result = []
            for key in sorted(keys, key=lambda k: songs_data.get(k, {}).get('position', 999)):
                t = songs_data.get(key, {})
                artist = t.get('artist') or ', '.join(
                    a.get('name', '') for a in t.get('artists', [])
                    if isinstance(a, dict) and a.get('name')
                ) or key[1]
                result.append({
                    'track_name': t.get('track_name', key[0]),
                    'artist': artist,
                    'spotify_url': t.get('spotify_url', ''),
                    'position': t.get('position', 0)
                })
            return result

        return {
            'multi_chart_tracks': overlap_tracks[:20],
            'usa_global_comparison': {
                'usa_only': len(usa_only),
                'global_only': len(global_only),
                'both': len(both),
                'usa_total': len(usa_songs),
                'global_total': len(global_songs),
                'usa_only_tracks': _track_list(usa_only),
                'global_only_tracks': _track_list(global_only),
                'both_tracks': _track_list(both)
            }
        }

    def _analyze_popularity(self, tracks: List[Dict]) -> Dict:
        """Analyze popularity distribution"""
        all_pops = [t.get('popularity', 0) for t in tracks if t.get('popularity')]

        stats = {
            'overall': {
                'avg': sum(all_pops) / len(all_pops) if all_pops else 0,
                'max': max(all_pops) if all_pops else 0,
                'min': min(all_pops) if all_pops else 0
            },
            'by_playlist': {}
        }

        playlists = set(t.get('playlist', '') for t in tracks)
        for playlist in playlists:
            pops = [t.get('popularity', 0) for t in tracks
                    if t.get('playlist') == playlist and t.get('popularity')]
            if pops:
                stats['by_playlist'][playlist] = {
                    'avg': sum(pops) / len(pops),
                    'max': max(pops),
                    'min': min(pops)
                }

        return stats

    def _analyze_explicit(self, tracks: List[Dict]) -> Dict:
        """Analyze explicit content distribution"""
        stats = {
            'total_explicit': sum(1 for t in tracks if t.get('explicit')),
            'total_tracks': len(tracks),
            'percentage': 0,
            'by_playlist': {}
        }

        if stats['total_tracks'] > 0:
            stats['percentage'] = (stats['total_explicit'] / stats['total_tracks']) * 100

        playlists = set(t.get('playlist', '') for t in tracks)
        for playlist in playlists:
            playlist_tracks = [t for t in tracks if t.get('playlist') == playlist]
            explicit = sum(1 for t in playlist_tracks if t.get('explicit'))
            total = len(playlist_tracks)
            stats['by_playlist'][playlist] = {
                'explicit': explicit,
                'total': total,
                'percentage': (explicit / total * 100) if total > 0 else 0
            }

        return stats

    def _analyze_playlists(self, tracks: List[Dict]) -> Dict:
        """Generate per-playlist statistics"""
        stats = {}
        playlists = set(t.get('playlist', '') for t in tracks)

        for playlist in playlists:
            playlist_tracks = [t for t in tracks if t.get('playlist') == playlist]
            pops = [t.get('popularity', 0) for t in playlist_tracks if t.get('popularity')]

            stats[playlist] = {
                'track_count': len(playlist_tracks),
                'explicit_count': sum(1 for t in playlist_tracks if t.get('explicit')),
                'avg_popularity': sum(pops) / len(pops) if pops else 0,
            }

        return stats

    def _calculate_playlist_analytics(self, tracks: List[Dict], playlist_name: str) -> Dict:
        """Calculate analytics for a single playlist (for tab-specific insights)"""
        analytics = {}

        artist_counts = Counter()
        artist_urls = {}
        artist_ids = {}
        artist_tracks = defaultdict(list)

        for track in tracks:
            artists = track.get('artists', [])
            if isinstance(artists, list):
                for artist in artists:
                    if isinstance(artist, dict):
                        name = artist.get('name', '')
                        url = artist.get('url', '')
                        aid = artist.get('id', '')
                        if name:
                            artist_counts[name] += 1
                            if url and name not in artist_urls:
                                artist_urls[name] = url
                            if aid and name not in artist_ids:
                                artist_ids[name] = aid
                            artist_tracks[name].append({
                                'track_name': track.get('track_name', ''),
                                'spotify_url': track.get('spotify_url', ''),
                                'popularity': track.get('popularity', 0)
                            })

        pops = [t.get('popularity', 0) for t in tracks if t.get('popularity')]
        explicit_count = sum(1 for t in tracks if t.get('explicit'))

        analytics['summary'] = {
            'track_count': len(tracks),
            'unique_artists': len(artist_counts),
            'avg_popularity': sum(pops) / len(pops) if pops else 0,
            'max_popularity': max(pops) if pops else 0,
            'min_popularity': min(pops) if pops else 0,
            'explicit_count': explicit_count,
            'explicit_percentage': (explicit_count / len(tracks) * 100) if tracks else 0
        }

        analytics['top_artists'] = [
            {
                'name': name,
                'count': count,
                'url': artist_urls.get(name, ''),
                'tracks': artist_tracks.get(name, []),
                'profile_key': artist_ids.get(name, '') or self._slugify(name)
            }
            for name, count in artist_counts.most_common(10)
        ]

        genre_counts = Counter()
        genre_tracks = defaultdict(list)
        for track in tracks:
            for genre in track.get('genres', []):
                if genre:
                    genre_counts[genre] += 1
                    artist = track.get('artist') or ', '.join(
                        a.get('name', '') for a in track.get('artists', [])
                        if isinstance(a, dict) and a.get('name')
                    )
                    genre_tracks[genre].append({
                        'track_name': track.get('track_name', ''),
                        'artist': artist,
                        'spotify_url': track.get('spotify_url', ''),
                        'popularity': track.get('popularity', 0)
                    })
        analytics['top_genres'] = [
            {'name': genre, 'count': count, 'tracks': genre_tracks.get(genre, [])}
            for genre, count in genre_counts.most_common(10)
        ]
        analytics['summary']['unique_genres'] = len(genre_counts)

        analytics['popularity_histogram'] = self._build_histogram(pops)

        if tracks:
            top_track = max(tracks, key=lambda x: x.get('popularity') or 0)
            analytics['top_track'] = {
                'name': top_track.get('track_name', ''),
                'artist': top_track.get('artist', ''),
                'popularity': top_track.get('popularity', 0),
                'spotify_url': top_track.get('spotify_url', ''),
                'album_image': top_track.get('album_image', '')
            }
        else:
            analytics['top_track'] = None

        return analytics

    def _normalize_track_for_json(self, track: Dict) -> Dict:
        """Map Python pipeline field names to React-expected aliases."""
        row = dict(track)
        if row.get('album_image') and not row.get('album_image_url'):
            row['album_image_url'] = row['album_image']
        return row

    def _group_by_playlist(self, tracks: List[Dict]) -> Dict[str, List[Dict]]:
        """Group tracks by playlist name"""
        grouped = defaultdict(list)
        for track in tracks:
            playlist = track.get('playlist', 'Unknown')
            grouped[playlist].append(track)

        for playlist in grouped:
            grouped[playlist].sort(key=lambda x: x.get('position', 999))

        return dict(grouped)

    def _build_deduplicated_ranked_all_tracks(self, tracks: List[Dict]) -> List[Dict]:
        """
        Deduplicate tracks (one row per unique track) and assign ranks using a composite score.

        Composite score uses (equal weight):
        - Number of chart appearances
        - Average chart appearance ranking
        - Track popularity score
        - Playlist average popularity score
        """
        playlist_avg_pop = {}
        for track in tracks:
            pl = track.get('playlist', '')
            if pl and pl not in playlist_avg_pop:
                pops = [t.get('popularity', 0) for t in tracks if t.get('playlist') == pl and t.get('popularity')]
                playlist_avg_pop[pl] = sum(pops) / len(pops) if pops else 0

        groups = defaultdict(list)
        for track in tracks:
            tid = (track.get('track_id') or '').strip()
            if tid:
                key = tid
            else:
                name = (track.get('track_name') or '').strip()
                artist = (track.get('artist') or '').strip()
                url = (track.get('spotify_url') or '').strip()
                key = (name, artist, url)
            groups[key].append(track)

        ranked = []
        for _key, appearances in groups.items():
            canonical = max(
                appearances,
                key=lambda t: (
                    1 if t.get('track_id') else 0,
                    1 if t.get('album_image') else 0,
                    t.get('popularity') or 0,
                    -(t.get('position') or 999),
                ),
            )

            num_charts = len(appearances)
            positions = [t.get('position') for t in appearances if t.get('position') and t.get('position') > 0]
            avg_position = sum(positions) / len(positions) if positions else 50
            best_position = min(positions) if positions else None
            track_pop = max((t.get('popularity') or 0) for t in appearances)
            playlists_seen = [str(t.get('playlist', '')).strip() for t in appearances if t.get('playlist')]
            playlists_seen = [p for p in playlists_seen if p]
            playlist_avg_for_track = (
                sum(playlist_avg_pop.get(pl, 0) for pl in playlists_seen) / len(playlists_seen)
                if playlists_seen else 0
            )

            max_playlists = max(1, len(playlist_avg_pop))
            chart_norm = (num_charts / max_playlists) * 100
            position_norm = max(0, (51 - avg_position) / 50.0 * 100)
            pop_norm = min(100, track_pop)
            playlist_avg_norm = min(100, playlist_avg_for_track)

            composite = 0.25 * chart_norm + 0.25 * position_norm + 0.25 * pop_norm + 0.25 * playlist_avg_norm

            row = dict(canonical)
            row['position'] = None
            row['best_position'] = best_position
            row['_composite'] = composite
            row['_num_charts'] = num_charts
            row['_avg_position'] = avg_position
            row['popularity'] = track_pop
            row['playlist'] = ','.join(sorted(set(playlists_seen))) if playlists_seen else ''
            ranked.append(row)

        ranked.sort(key=lambda t: (-t['_composite'], t['_avg_position'], -t.get('popularity', 0)))
        for i, row in enumerate(ranked, start=1):
            row['position'] = i
            del row['_composite']
            del row['_num_charts']
            del row['_avg_position']

        return ranked

    def _track_profile_key(self, track: Dict) -> str:
        """Unique key for track profile (track_id or slug of name+artist)."""
        tid = (track.get('track_id') or '').strip()
        if tid:
            return tid
        name = (track.get('track_name') or '').strip()
        artist = (track.get('artist') or '').strip()
        return self._slugify(f"{name}-{artist}")

    def _album_profile_key(self, track: Dict) -> str:
        """Unique key for album profile (album_id or slug of album+artist)."""
        aid = (track.get('album_id') or '').strip()
        if aid:
            return aid
        album = (track.get('album') or '').strip()
        artist = (track.get('artist') or '').strip()
        return self._slugify(f"{album}-{artist}")

    def _artist_profile_key(self, artist: Dict) -> str:
        """Unique key for artist profile (artist id or slug of name)."""
        if isinstance(artist, dict):
            aid = (artist.get('id') or '').strip()
            if aid:
                return aid
            return self._slugify(str(artist.get('name', '')))
        return self._slugify(str(artist))

    def _format_track_row(self, track: Dict) -> str:
        """Format a single track as an HTML table row (with profile-link data for modals)."""
        position = track.get('position', '')
        track_name = html.escape(str(track.get('track_name', '')))
        track_url = html.escape(str(track.get('spotify_url', ''))) if track.get('spotify_url') else ''
        album = html.escape(str(track.get('album', '')))
        album_url = html.escape(str(track.get('album_url', ''))) if track.get('album_url') else ''
        album_image = html.escape(str(track.get('album_image', ''))) if track.get('album_image') else ''
        _dur = track.get('duration', '') or ''
        if not _dur and track.get('duration_ms'):
            _ms = int(track['duration_ms'])
            _dur = f"{_ms // 60000}:{(_ms % 60000) // 1000:02d}"
        duration = html.escape(_dur)
        popularity = track.get('popularity', 0)
        is_explicit = track.get('explicit', False)

        track_key = html.escape(self._track_profile_key(track))
        album_key = html.escape(self._album_profile_key(track))
        track_id_attr = html.escape(str(track.get('track_id', '')))
        playlist_attr = html.escape(str(track.get('playlist', '')))

        artist_html = ''
        artists = track.get('artists', [])
        if isinstance(artists, list) and artists:
            artist_links = []
            for artist in artists:
                if isinstance(artist, dict):
                    name = html.escape(str(artist.get('name', '')))
                    url = html.escape(str(artist.get('url', ''))) if artist.get('url') else ''
                    artist_key = html.escape(self._artist_profile_key(artist))
                    if url:
                        artist_links.append(
                            f'<a href="{url}" target="_blank" class="profile-link" data-type="artist" data-id="{artist_key}">{name}</a>'
                        )
                    else:
                        artist_links.append(
                            f'<span class="profile-link" data-type="artist" data-id="{artist_key}">{name}</span>'
                        )
                else:
                    artist_links.append(html.escape(str(artist)))
            artist_html = ', '.join(artist_links)
        elif track.get('artist'):
            artist_html = html.escape(str(track.get('artist', '')))

        explicit_badge = '<span class="explicit-badge">E</span>' if is_explicit else ''

        row = f'<tr data-track-id="{track_id_attr}" data-playlist="{playlist_attr}">'
        row += f'<td class="position-cell">{position}</td>'

        row += '<td class="track-cell"><div class="track-cell-inner">'
        if album_image:
            row += f'<img src="{album_image}" alt="" class="album-thumb" />'
        row += '<div class="track-details">'
        if track_url:
            row += f'<div class="track-name"><a href="{track_url}" target="_blank" class="profile-link" data-type="track" data-id="{track_key}">{track_name}</a></div>'
        else:
            row += f'<div class="track-name"><span class="profile-link" data-type="track" data-id="{track_key}">{track_name}</span></div>'
        row += f'<div class="artist-name">{explicit_badge}{artist_html}</div>'
        row += '</div></div></td>'

        if album_url:
            row += f'<td><a href="{album_url}" target="_blank" class="profile-link" data-type="album" data-id="{album_key}">{album}</a></td>'
        else:
            row += f'<td><span class="profile-link" data-type="album" data-id="{album_key}">{album}</span></td>'

        row += f'<td class="duration-cell">{duration}</td>'

        pop_width = popularity if popularity else 0
        row += f'<td class="popularity-cell">'
        row += f'<div class="pop-container">'
        row += f'<span class="pop-value">{popularity}</span>'
        row += f'<span class="pop-bar-bg"><span class="pop-bar" style="width: {pop_width}%;"></span></span>'
        row += f'</div></td>'

        row += '</tr>'
        return row

    @staticmethod
    def _build_histogram(pops: list, num_buckets: int = 5) -> list:
        """Build histogram buckets dynamically based on the actual popularity range."""
        if not pops:
            return []

        lo = min(pops)
        hi = max(pops)

        if lo == hi:
            return [{'label': str(lo), 'min': lo, 'max': hi, 'count': len(pops), 'pct': 100}]

        span = hi - lo
        step = span / num_buckets

        buckets = []
        for i in range(num_buckets):
            b_min = lo + i * step
            b_max = lo + (i + 1) * step
            label_min = int(round(b_min)) if i > 0 else int(b_min)
            label_max = int(round(b_max))
            buckets.append({
                'label': f'{label_min}–{label_max}',
                'min': b_min,
                'max': b_max,
                'count': 0,
            })

        for p in pops:
            idx = int((p - lo) / step)
            if idx >= num_buckets:
                idx = num_buckets - 1
            buckets[idx]['count'] += 1

        max_count = max(b['count'] for b in buckets) or 1
        for b in buckets:
            b['pct'] = round(b['count'] / max_count * 100)

        return buckets

    @staticmethod
    def _slugify(text: str) -> str:
        """Convert text to a URL-safe slug for use as keys"""
        import re
        text = text.lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[\s_-]+', '-', text)
        return text[:100]

    def _format_track_row_with_playlist(self, track: Dict) -> str:
        """Format a track as an HTML table row for All Tracks tab (with profile-link data for modals)."""
        position = track.get('position', '')
        position_num = 999
        if position is not None and position != '':
            try:
                position_num = int(position)
            except (TypeError, ValueError):
                pass
        track_name = html.escape(str(track.get('track_name', '')))
        track_url = html.escape(str(track.get('spotify_url', ''))) if track.get('spotify_url') else ''
        album = html.escape(str(track.get('album', '')))
        album_url = html.escape(str(track.get('album_url', ''))) if track.get('album_url') else ''
        album_image = html.escape(str(track.get('album_image', ''))) if track.get('album_image') else ''
        _dur = track.get('duration', '') or ''
        if not _dur and track.get('duration_ms'):
            _ms = int(track['duration_ms'])
            _dur = f"{_ms // 60000}:{(_ms % 60000) // 1000:02d}"
        duration = html.escape(_dur)
        popularity = track.get('popularity', 0)
        is_explicit = track.get('explicit', False)
        playlist = html.escape(str(track.get('playlist', '')))

        track_key = html.escape(self._track_profile_key(track))
        album_key = html.escape(self._album_profile_key(track))

        artist_html = ''
        artists = track.get('artists', [])
        if isinstance(artists, list) and artists:
            artist_links = []
            for artist in artists:
                if isinstance(artist, dict):
                    name = html.escape(str(artist.get('name', '')))
                    url = html.escape(str(artist.get('url', ''))) if artist.get('url') else ''
                    artist_key = html.escape(self._artist_profile_key(artist))
                    if url:
                        artist_links.append(
                            f'<a href="{url}" target="_blank" class="profile-link" data-type="artist" data-id="{artist_key}">{name}</a>'
                        )
                    else:
                        artist_links.append(
                            f'<span class="profile-link" data-type="artist" data-id="{artist_key}">{name}</span>'
                        )
                else:
                    artist_links.append(html.escape(str(artist)))
            artist_html = ', '.join(artist_links)
        elif track.get('artist'):
            artist_html = html.escape(str(track.get('artist', '')))

        explicit_badge = '<span class="explicit-badge">E</span>' if is_explicit else ''

        artist_text = html.escape(str(track.get('artist', '')).lower())
        duration_ms = track.get('duration_ms', 0) or 0
        genres_json = html.escape(json.dumps(track.get('genres', [])))
        track_id_attr = html.escape(str(track.get('track_id', '')))

        row = (
            f'<tr'
            f' data-track-id="{track_id_attr}"'
            f' data-position="{position_num}"'
            f' data-track="{html.escape(str(track.get("track_name", "")).lower())}"'
            f' data-artist="{artist_text}"'
            f' data-album="{html.escape(str(track.get("album", "")).lower())}"'
            f' data-playlist="{playlist}"'
            f' data-duration-ms="{duration_ms}"'
            f' data-popularity="{popularity}"'
            f' data-explicit="{"true" if is_explicit else "false"}"'
            f' data-genres="{genres_json}"'
            f'>'
        )
        row += f'<td class="position-cell">{position}</td>'

        row += '<td class="track-cell"><div class="track-cell-inner">'
        if album_image:
            row += f'<img src="{album_image}" alt="" class="album-thumb" />'
        row += '<div class="track-details">'
        if track_url:
            row += f'<div class="track-name"><a href="{track_url}" target="_blank" class="profile-link" data-type="track" data-id="{track_key}">{track_name}</a></div>'
        else:
            row += f'<div class="track-name"><span class="profile-link" data-type="track" data-id="{track_key}">{track_name}</span></div>'
        row += f'<div class="artist-name">{explicit_badge}{artist_html}</div>'
        row += '</div></div></td>'

        if album_url:
            row += f'<td><a href="{album_url}" target="_blank" class="profile-link" data-type="album" data-id="{album_key}">{album}</a></td>'
        else:
            row += f'<td><span class="profile-link" data-type="album" data-id="{album_key}">{album}</span></td>'

        row += f'<td class="duration-cell">{duration}</td>'

        pop_width = popularity if popularity else 0
        row += f'<td class="popularity-cell">'
        row += f'<div class="pop-container">'
        row += f'<span class="pop-value">{popularity}</span>'
        row += f'<span class="pop-bar-bg"><span class="pop-bar" style="width: {pop_width}%;"></span></span>'
        row += f'</div></td>'

        row += '</tr>'
        return row
