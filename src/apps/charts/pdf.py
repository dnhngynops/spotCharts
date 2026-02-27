"""
Charts PDF & Table Generator

Handles HTML table generation and WeasyPrint PDF conversion for
per-playlist chart reports. Template lives at templates/charts/table.html.
"""
import os
import html
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime
from jinja2 import Template
from src.core import config

# Absolute path to templates/charts/table.html
# This file lives at src/apps/charts/pdf.py, so we go up 4 levels to project root.
_TEMPLATE_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..', 'templates', 'charts', 'table.html')
)


class PDFGenerator:
    """Generate PDF reports from track data using WeasyPrint"""

    def __init__(self):
        self.template_path = _TEMPLATE_PATH

    def generate_pdf_from_html(self, html_content: str, output_path: str) -> str:
        """Convert HTML content to PDF as a single continuous page."""
        from weasyprint import HTML, CSS

        try:
            doc_html = HTML(string=html_content)

            temp_css = CSS(string='''
                @page {
                    size: 210mm 100000mm;
                    margin: 0;
                }
                body { margin: 0; padding: 0; }
            ''')

            document = doc_html.render(stylesheets=[temp_css])

            max_y = 0
            if len(document.pages) > 0:
                page = document.pages[0]

                def find_and_measure_content(box):
                    nonlocal max_y
                    tag = getattr(box, 'element_tag', None)
                    if tag == 'body':
                        content_bottom = box.position_y + box.height
                        if content_bottom > max_y:
                            max_y = content_bottom
                        return
                    for child in box.children:
                        find_and_measure_content(child)

                find_and_measure_content(page._page_box)

            content_height_mm = (max_y / 96 * 25.4) + 5

            final_css = CSS(string=f'''
                @page {{
                    size: 210mm {content_height_mm}mm;
                    margin: 0;
                }}
                body {{ margin: 0; padding: 0; }}
                .container {{ page-break-inside: avoid; }}
                table, tbody, tr, td, th {{ page-break-inside: avoid; }}
            ''')

            doc_html.write_pdf(output_path, stylesheets=[final_css])
            return output_path

        except Exception as e:
            raise Exception(f"Failed to generate PDF: {e}")

    def generate_pdf_report(
        self,
        tracks: List[Dict],
        filename: str = 'spotify_charts.pdf',
        playlist_name: Optional[str] = None
    ) -> str:
        """Generate a PDF report directly from track data."""
        html_content = self._generate_html_content(tracks, playlist_name)
        return self.generate_pdf_from_html(html_content, filename)

    def save_pdf_file(
        self,
        tracks: List[Dict],
        filename: str = 'spotify_charts.pdf',
        output_dir: Optional[str] = None,
        playlist_name: Optional[str] = None
    ) -> str:
        """Generate and save PDF report to file."""
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, filename)
        else:
            filepath = filename
        return self.generate_pdf_report(tracks, filepath, playlist_name=playlist_name)

    def _calculate_metrics(self, tracks: List[Dict]) -> List[Dict]:
        """Calculate metrics for the playlist (e.g., most frequent artists)."""
        from collections import Counter

        metrics = []
        artist_counts = Counter()
        for track in tracks:
            artists = track.get('artists', [])
            if isinstance(artists, list):
                for artist in artists:
                    artist_name = artist.get('name', '') if isinstance(artist, dict) else str(artist)
                    if artist_name:
                        artist_counts[artist_name] += 1
            elif track.get('artist'):
                for name in str(track.get('artist', '')).split(','):
                    name = name.strip()
                    if name:
                        artist_counts[name] += 1

        if artist_counts:
            top_artists = artist_counts.most_common(3)
            artist_url_map = {}
            for track in tracks:
                for artist in track.get('artists', []):
                    if isinstance(artist, dict):
                        name = artist.get('name', '')
                        url = artist.get('url', '')
                        if name and url:
                            artist_url_map[name] = url

            artist_links = []
            for name, count in top_artists:
                artist_url = artist_url_map.get(name, '')
                escaped_name = html.escape(name)
                if artist_url:
                    artist_links.append(
                        f'<a href="{html.escape(artist_url)}" target="_blank">{escaped_name}</a> ({count})'
                    )
                else:
                    artist_links.append(f"{escaped_name} ({count})")

            metrics.append({
                'label': 'Most Frequent Artists',
                'value': ', '.join(artist_links)
            })

        return metrics

    def _format_table_html(self, tracks: List[Dict]) -> str:
        """Format tracks data into an HTML table with hyperlinks and popularity bars."""
        columns = config.TABLE_CONFIG['include_columns']

        column_display = {
            'track_name': 'TRACK',
            'artist': 'ARTIST',
            'album': 'ALBUM',
            'duration': '🕐',
            'popularity': 'POPULARITY',
        }

        header_html = '<thead><tr><th>#</th>'
        for col in columns:
            if col == 'artist':
                continue
            if col in ['track_name', 'album', 'duration', 'popularity']:
                header_html += f'<th>{column_display.get(col, col.upper())}</th>'
        header_html += '</tr></thead>'

        body_html = '<tbody>'
        for idx, track in enumerate(tracks, start=1):
            position = track.get('position', idx)
            preview_url = html.escape(str(track.get('preview_url', ''))) if track.get('preview_url') else ''
            track_url = html.escape(str(track.get('spotify_url', ''))) if track.get('spotify_url') else ''
            track_name = html.escape(str(track.get('track_name', 'Unknown Track')))

            body_html += '<tr>'
            body_html += f'<td class="position-cell"><span class="position-number">{position}</span></td>'

            if 'track_name' in columns:
                body_html += '<td>'
                album_image_url = track.get('album_image', '')

                artist_names_html = ''
                is_explicit = track.get('explicit', False)
                artists = track.get('artists', [])
                if isinstance(artists, list) and len(artists) > 0:
                    artist_links = []
                    for artist in artists:
                        if isinstance(artist, dict):
                            aname = html.escape(str(artist.get('name', '')))
                            aurl = html.escape(str(artist.get('url', ''))) if artist.get('url') else ''
                            artist_links.append(
                                f'<a href="{aurl}" target="_blank">{aname}</a>' if aurl else aname
                            )
                        else:
                            artist_links.append(html.escape(str(artist)))
                    artist_names_html = ', '.join(artist_links)
                elif track.get('artist'):
                    artist_names_html = html.escape(str(track.get('artist', '')))

                if is_explicit and artist_names_html:
                    artist_names_html = f'<span class="explicit-badge">E</span>{artist_names_html}'

                if album_image_url:
                    body_html += '<div class="track-with-image">'
                    body_html += f'<img src="{html.escape(str(album_image_url))}" alt="Album art" class="album-image" />'
                    body_html += '<div class="track-info">'
                    body_html += (
                        f'<div class="track-name"><a href="{track_url}" target="_blank">{track_name}</a></div>'
                        if track_url else f'<div class="track-name">{track_name}</div>'
                    )
                    if artist_names_html:
                        body_html += f'<div class="artist-names">{artist_names_html}</div>'
                    body_html += '</div></div>'
                else:
                    body_html += '<div class="track-info">'
                    body_html += (
                        f'<div class="track-name"><a href="{track_url}" target="_blank">{track_name}</a></div>'
                        if track_url else f'<div class="track-name">{track_name}</div>'
                    )
                    if artist_names_html:
                        body_html += f'<div class="artist-names">{artist_names_html}</div>'
                    body_html += '</div>'
                body_html += '</td>'

            if 'album' in columns:
                album_name = html.escape(str(track.get('album', '')))
                album_url = html.escape(str(track.get('album_url', ''))) if track.get('album_url') else ''
                if album_url and album_name:
                    body_html += f'<td><a href="{album_url}" target="_blank">{album_name}</a></td>'
                else:
                    body_html += f'<td>{album_name or "Unknown Album"}</td>'

            if 'duration' in columns:
                body_html += f'<td>{html.escape(str(track.get("duration", "N/A")))}</td>'

            if 'popularity' in columns:
                popularity = track.get('popularity')
                if popularity is not None:
                    pv = int(popularity)
                    pw = (pv / 100) * 100
                    body_html += (
                        '<td style="vertical-align: middle;">'
                        '<div class="popularity-cell">'
                        f'<span class="popularity-value">{pv}</span>'
                        '<span class="popularity-bar-container">'
                        f'<span class="popularity-bar" style="width: {pw}%; background-color: #1DB954;"></span>'
                        '</span></div></td>'
                    )
                else:
                    body_html += '<td style="vertical-align: middle;">N/A</td>'

            body_html += '</tr>'

        body_html += '</tbody>'
        return f'<table class="spotify-table" id="spotify-charts-table">{header_html}{body_html}</table>'

    def _calculate_title_font_size(self, playlist_name: Optional[str]) -> tuple:
        """Return fixed font sizes for consistent title appearance across all PDFs."""
        return (1.8, 2.2)

    def _generate_html_content(self, tracks: List[Dict], playlist_name: Optional[str] = None) -> str:
        """Generate HTML content from track data."""
        metrics = self._calculate_metrics(tracks)
        tracks = sorted(tracks, key=lambda x: x.get('position', 999))
        table_html = self._format_table_html(tracks)
        spotify_size, playlist_size = self._calculate_title_font_size(playlist_name)

        with open(self.template_path, 'r') as f:
            template = Template(f.read())

        return template.render(
            table_html=table_html,
            theme=config.SPOTIFY_THEME,
            generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            total_tracks=len(tracks),
            playlist_name=playlist_name,
            metrics=metrics,
            title_spotify_size=spotify_size,
            title_playlist_size=playlist_size
        )


class TableGenerator:
    """Generate formatted tables and PDFs from track data"""

    def __init__(self):
        self.template_path = _TEMPLATE_PATH
        self._pdf = PDFGenerator()

    def generate_html_table(self, tracks: List[Dict]) -> str:
        """Generate an HTML table with Spotify theming."""
        df = pd.DataFrame(tracks)
        columns = config.TABLE_CONFIG['include_columns']
        available_columns = [col for col in columns if col in df.columns]
        df = df[available_columns]

        if config.TABLE_CONFIG.get('sort_by') and config.TABLE_CONFIG['sort_by'] in df.columns:
            ascending = config.TABLE_CONFIG.get('sort_order', 'desc') == 'asc'
            df = df.sort_values(by=config.TABLE_CONFIG['sort_by'], ascending=ascending)

        df = df.reset_index(drop=True)
        df.index = df.index + 1

        with open(self.template_path, 'r') as f:
            template = Template(f.read())

        table_html = df.to_html(
            classes='spotify-table',
            table_id='spotify-charts-table',
            escape=False,
            index=True
        )

        return template.render(
            table_html=table_html,
            theme=config.SPOTIFY_THEME,
            generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            total_tracks=len(df)
        )

    def generate_csv(self, tracks: List[Dict], filename: str = None) -> str:
        """Generate a CSV file from track data."""
        df = pd.DataFrame(tracks)
        columns = config.TABLE_CONFIG['include_columns']
        available_columns = [col for col in columns if col in df.columns]
        df = df[available_columns]

        if config.TABLE_CONFIG.get('sort_by') and config.TABLE_CONFIG['sort_by'] in df.columns:
            ascending = config.TABLE_CONFIG.get('sort_order', 'desc') == 'asc'
            df = df.sort_values(by=config.TABLE_CONFIG['sort_by'], ascending=ascending)

        if filename:
            df.to_csv(filename, index=False)
            return filename
        return df.to_csv(index=False)

    def save_html_file(self, tracks: List[Dict], filename: str = 'spotify_charts.html') -> str:
        """Generate and save HTML table to file."""
        html_content = self.generate_html_table(tracks)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return filename

    def generate_pdf(
        self,
        tracks: List[Dict],
        filename: str = 'spotify_charts.pdf',
        playlist_name: Optional[str] = None
    ) -> str:
        """Generate a PDF report from track data as a single continuous page."""
        return self._pdf.generate_pdf_report(tracks, filename, playlist_name=playlist_name)

    def save_pdf_file(
        self,
        tracks: List[Dict],
        filename: str = 'spotify_charts.pdf',
        output_dir: Optional[str] = None,
        playlist_name: Optional[str] = None
    ) -> str:
        """Generate and save PDF report to file as a single continuous page."""
        return self._pdf.save_pdf_file(tracks, filename, output_dir, playlist_name=playlist_name)
