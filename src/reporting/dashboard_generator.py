"""
Dashboard Generator for Cross-Playlist Analytics

This module generates a combined HTML dashboard that presents analytics
across all collected playlists, providing insights useful for A&R.
"""
import os
import html
from typing import List, Dict, Optional
from datetime import datetime
from collections import Counter, defaultdict
from jinja2 import Template
from src.core import config


class DashboardGenerator:
    """Generate HTML dashboard with cross-playlist analytics"""

    def __init__(self):
        """Initialize dashboard generator with template path"""
        template_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'templates'
        )
        self.template_path = os.path.join(template_dir, 'dashboard_template.html')

    def generate_dashboard(
        self,
        all_tracks: List[Dict],
        output_path: str
    ) -> str:
        """
        Generate HTML dashboard from all collected tracks.

        Args:
            all_tracks: List of all track dictionaries from all playlists
            output_path: Path where HTML should be saved

        Returns:
            Path to the generated HTML file
        """
        # Calculate all analytics
        analytics = self._calculate_analytics(all_tracks)

        # Group tracks by playlist
        tracks_by_playlist = self._group_by_playlist(all_tracks)

        # Sort all_tracks by playlist name, then by position for the "All Tracks" tab
        sorted_all_tracks = sorted(
            all_tracks,
            key=lambda x: (x.get('playlist', ''), x.get('position', 999))
        )

        # Load and render template
        with open(self.template_path, 'r') as f:
            template = Template(f.read())

        html_output = template.render(
            theme=config.SPOTIFY_THEME,
            generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            analytics=analytics,
            tracks_by_playlist=tracks_by_playlist,
            all_tracks=sorted_all_tracks,
            format_track_row=self._format_track_row,
            format_track_row_with_playlist=self._format_track_row_with_playlist
        )

        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_output)

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
        analytics['summary'] = {
            'total_tracks': len(tracks),
            'total_playlists': len(playlists),
            'playlist_names': sorted(playlists),
            'unique_tracks': len(set((t.get('track_name'), t.get('artist')) for t in tracks))
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

        # Per-playlist stats
        analytics['playlist_stats'] = self._analyze_playlists(tracks)

        return analytics

    def _analyze_artists(self, tracks: List[Dict]) -> Dict:
        """Analyze artist frequency and multi-playlist presence"""
        artist_counts = Counter()
        artist_playlists = defaultdict(set)
        artist_urls = {}

        for track in tracks:
            playlist = track.get('playlist', 'Unknown')
            artists = track.get('artists', [])

            if isinstance(artists, list):
                for artist in artists:
                    if isinstance(artist, dict):
                        name = artist.get('name', '')
                        url = artist.get('url', '')
                        if name:
                            artist_counts[name] += 1
                            artist_playlists[name].add(playlist)
                            if url and name not in artist_urls:
                                artist_urls[name] = url

        # Top 15 artists
        top_artists = []
        for name, count in artist_counts.most_common(15):
            top_artists.append({
                'name': name,
                'count': count,
                'playlists': len(artist_playlists[name]),
                'playlist_names': sorted(artist_playlists[name]),
                'url': artist_urls.get(name, '')
            })

        # Artists on 3+ playlists
        multi_playlist = [
            {
                'name': name,
                'count': artist_counts[name],
                'playlists': len(playlists),
                'playlist_names': sorted(playlists),
                'url': artist_urls.get(name, '')
            }
            for name, playlists in artist_playlists.items()
            if len(playlists) >= 3
        ]
        multi_playlist.sort(key=lambda x: (-x['playlists'], -x['count']))

        return {
            'top_artists': top_artists,
            'multi_playlist_artists': multi_playlist[:10]
        }

    def _analyze_overlap(self, tracks: List[Dict]) -> Dict:
        """Analyze track overlap between charts"""
        # Track key -> list of playlists it appears on
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

        # USA vs Global comparison for Songs
        usa_songs = set()
        global_songs = set()
        for track in tracks:
            key = (track.get('track_name', ''), track.get('artist', ''))
            playlist = track.get('playlist', '')
            if 'USA' in playlist and 'Songs' in playlist:
                usa_songs.add(key)
            elif 'Global' in playlist and 'Songs' in playlist:
                global_songs.add(key)

        usa_only = usa_songs - global_songs
        global_only = global_songs - usa_songs
        both = usa_songs & global_songs

        return {
            'multi_chart_tracks': overlap_tracks[:20],
            'usa_global_comparison': {
                'usa_only': len(usa_only),
                'global_only': len(global_only),
                'both': len(both),
                'usa_total': len(usa_songs),
                'global_total': len(global_songs)
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

        # By playlist
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

        # Top 10 most popular tracks
        sorted_by_pop = sorted(
            [t for t in tracks if t.get('popularity')],
            key=lambda x: -x.get('popularity', 0)
        )
        stats['top_tracks'] = sorted_by_pop[:10]

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

        # By playlist
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
                'top_track': max(playlist_tracks, key=lambda x: x.get('popularity', 0)) if playlist_tracks else None
            }

        return stats

    def _group_by_playlist(self, tracks: List[Dict]) -> Dict[str, List[Dict]]:
        """Group tracks by playlist name"""
        grouped = defaultdict(list)
        for track in tracks:
            playlist = track.get('playlist', 'Unknown')
            grouped[playlist].append(track)

        # Sort each playlist by position
        for playlist in grouped:
            grouped[playlist].sort(key=lambda x: x.get('position', 999))

        return dict(grouped)

    def _format_track_row(self, track: Dict) -> str:
        """Format a single track as an HTML table row"""
        position = track.get('position', '')
        track_name = html.escape(str(track.get('track_name', '')))
        track_url = html.escape(str(track.get('spotify_url', ''))) if track.get('spotify_url') else ''
        album = html.escape(str(track.get('album', '')))
        album_url = html.escape(str(track.get('album_url', ''))) if track.get('album_url') else ''
        album_image = html.escape(str(track.get('album_image', ''))) if track.get('album_image') else ''
        duration = html.escape(str(track.get('duration', '')))
        popularity = track.get('popularity', 0)
        is_explicit = track.get('explicit', False)

        # Build artist names with links
        artist_html = ''
        artists = track.get('artists', [])
        if isinstance(artists, list) and artists:
            artist_links = []
            for artist in artists:
                if isinstance(artist, dict):
                    name = html.escape(str(artist.get('name', '')))
                    url = html.escape(str(artist.get('url', ''))) if artist.get('url') else ''
                    if url:
                        artist_links.append(f'<a href="{url}" target="_blank">{name}</a>')
                    else:
                        artist_links.append(name)
                else:
                    artist_links.append(html.escape(str(artist)))
            artist_html = ', '.join(artist_links)
        elif track.get('artist'):
            artist_html = html.escape(str(track.get('artist', '')))

        # Add explicit badge
        explicit_badge = '<span class="explicit-badge">E</span>' if is_explicit else ''

        # Build row HTML
        row = f'<tr>'
        row += f'<td class="position-cell">{position}</td>'

        # Track cell with image
        row += '<td class="track-cell">'
        if album_image:
            row += f'<img src="{album_image}" alt="" class="album-thumb" />'
        row += '<div class="track-details">'
        if track_url:
            row += f'<div class="track-name"><a href="{track_url}" target="_blank">{track_name}</a></div>'
        else:
            row += f'<div class="track-name">{track_name}</div>'
        row += f'<div class="artist-name">{explicit_badge}{artist_html}</div>'
        row += '</div></td>'

        # Album cell
        if album_url:
            row += f'<td><a href="{album_url}" target="_blank">{album}</a></td>'
        else:
            row += f'<td>{album}</td>'

        # Duration
        row += f'<td class="duration-cell">{duration}</td>'

        # Popularity with bar
        pop_width = popularity if popularity else 0
        row += f'<td class="popularity-cell">'
        row += f'<div class="pop-container">'
        row += f'<span class="pop-value">{popularity}</span>'
        row += f'<span class="pop-bar-bg"><span class="pop-bar" style="width: {pop_width}%;"></span></span>'
        row += f'</div></td>'

        row += '</tr>'
        return row

    def _format_track_row_with_playlist(self, track: Dict) -> str:
        """Format a single track as an HTML table row with playlist column"""
        position = track.get('position', '')
        track_name = html.escape(str(track.get('track_name', '')))
        track_url = html.escape(str(track.get('spotify_url', ''))) if track.get('spotify_url') else ''
        album = html.escape(str(track.get('album', '')))
        album_url = html.escape(str(track.get('album_url', ''))) if track.get('album_url') else ''
        album_image = html.escape(str(track.get('album_image', ''))) if track.get('album_image') else ''
        duration = html.escape(str(track.get('duration', '')))
        popularity = track.get('popularity', 0)
        is_explicit = track.get('explicit', False)
        playlist = html.escape(str(track.get('playlist', '')))

        # Shorten playlist name for display
        short_playlist = playlist.replace('Top ', '').replace(' - ', ' ')

        # Build artist names with links
        artist_html = ''
        artists = track.get('artists', [])
        if isinstance(artists, list) and artists:
            artist_links = []
            for artist in artists:
                if isinstance(artist, dict):
                    name = html.escape(str(artist.get('name', '')))
                    url = html.escape(str(artist.get('url', ''))) if artist.get('url') else ''
                    if url:
                        artist_links.append(f'<a href="{url}" target="_blank">{name}</a>')
                    else:
                        artist_links.append(name)
                else:
                    artist_links.append(html.escape(str(artist)))
            artist_html = ', '.join(artist_links)
        elif track.get('artist'):
            artist_html = html.escape(str(track.get('artist', '')))

        # Add explicit badge
        explicit_badge = '<span class="explicit-badge">E</span>' if is_explicit else ''

        # Build row HTML
        row = f'<tr>'
        row += f'<td class="position-cell">{position}</td>'

        # Track cell with image
        row += '<td class="track-cell">'
        if album_image:
            row += f'<img src="{album_image}" alt="" class="album-thumb" />'
        row += '<div class="track-details">'
        if track_url:
            row += f'<div class="track-name"><a href="{track_url}" target="_blank">{track_name}</a></div>'
        else:
            row += f'<div class="track-name">{track_name}</div>'
        row += f'<div class="artist-name">{explicit_badge}{artist_html}</div>'
        row += '</div></td>'

        # Album cell
        if album_url:
            row += f'<td><a href="{album_url}" target="_blank">{album}</a></td>'
        else:
            row += f'<td>{album}</td>'

        # Playlist cell
        row += f'<td style="font-size: 0.85em; color: #888;">{short_playlist}</td>'

        # Duration
        row += f'<td class="duration-cell">{duration}</td>'

        # Popularity with bar
        pop_width = popularity if popularity else 0
        row += f'<td class="popularity-cell">'
        row += f'<div class="pop-container">'
        row += f'<span class="pop-value">{popularity}</span>'
        row += f'<span class="pop-bar-bg"><span class="pop-bar" style="width: {pop_width}%;"></span></span>'
        row += f'</div></td>'

        row += '</tr>'
        return row
