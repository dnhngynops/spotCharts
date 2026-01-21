"""
PDF Report Generator using WeasyPrint

This module handles the conversion of HTML reports to PDF format,
maintaining Spotify theming and styling from the HTML templates.
"""
import os
import html
from typing import List, Dict, Optional
from datetime import datetime
from jinja2 import Template
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from src.core import config


class PDFGenerator:
    """Generate PDF reports from track data using WeasyPrint"""

    def __init__(self):
        """Initialize PDF generator with template paths"""
        template_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'templates'
        )
        self.template_path = os.path.join(template_dir, 'table_template.html')

    def generate_pdf_from_html(
        self,
        html_content: str,
        output_path: str
    ) -> str:
        """
        Convert HTML content to PDF as a single continuous page

        Args:
            html_content: HTML string to convert
            output_path: Path where PDF should be saved

        Returns:
            Path to the generated PDF file
        """
        try:
            # Create HTML object
            html = HTML(string=html_content)

            # Two-pass approach to create a true single-page PDF:
            # Pass 1: Render with very tall page to ensure content doesn't paginate, then measure
            temp_css = CSS(string='''
                @page {
                    size: 210mm 100000mm;  /* Very tall page to prevent pagination */
                    margin: 0;
                }
                body {
                    margin: 0;
                    padding: 0;
                }
            ''')

            # Render to get document layout (should be single page due to tall height)
            document = html.render(stylesheets=[temp_css])

            # Calculate actual content height by finding the body element
            # Since we used a very tall page, all content should be on page 1
            max_y = 0
            if len(document.pages) > 0:
                page = document.pages[0]  # Only check first page since content should all be there

                def find_and_measure_content(box):
                    nonlocal max_y
                    # Look for body or html tag - these contain the actual content
                    tag = getattr(box, 'element_tag', None)

                    # If this is the body element, measure its actual height
                    if tag == 'body':
                        # Body contains the actual content height
                        content_bottom = box.position_y + box.height
                        if content_bottom > max_y:
                            max_y = content_bottom
                        return  # Don't need to go deeper once we found body

                    # Keep looking for body in children
                    for child in box.children:
                        find_and_measure_content(child)

                # Start searching from the page's root box
                find_and_measure_content(page._page_box)

            # Convert pixels to mm and add small buffer (5mm)
            content_height_mm = (max_y / 96 * 25.4) + 5

            # Pass 2: Render with exact height to create single continuous page
            final_css = CSS(string=f'''
                @page {{
                    size: 210mm {content_height_mm}mm;  /* Exact height for content */
                    margin: 0;
                }}
                body {{
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    page-break-inside: avoid;
                }}
                table, tbody, tr, td, th {{
                    page-break-inside: avoid;
                }}
            ''')

            html.write_pdf(output_path, stylesheets=[final_css])

            return output_path

        except Exception as e:
            raise Exception(f"Failed to generate PDF: {e}")

    def generate_pdf_report(
        self,
        tracks: List[Dict],
        filename: str = 'spotify_charts.pdf',
        playlist_name: Optional[str] = None
    ) -> str:
        """
        Generate a PDF report directly from track data as a single continuous page

        Args:
            tracks: List of track dictionaries
            filename: Output filename for the PDF
            playlist_name: Optional playlist name for the report title

        Returns:
            Path to the generated PDF file
        """
        # First, generate HTML content using the same template
        html_content = self._generate_html_content(tracks, playlist_name)

        # Convert HTML to PDF (always single continuous page)
        return self.generate_pdf_from_html(html_content, filename)

    def _calculate_metrics(self, tracks: List[Dict]) -> List[Dict]:
        """
        Calculate metrics for the playlist (e.g., most frequent artists)
        
        Args:
            tracks: List of track dictionaries
            
        Returns:
            List of metric dictionaries with 'label' and 'value' keys
        """
        from collections import Counter
        
        metrics = []
        
        # Count artist appearances
        artist_counts = Counter()
        for track in tracks:
            artists = track.get('artists', [])
            if isinstance(artists, list):
                for artist in artists:
                    if isinstance(artist, dict):
                        artist_name = artist.get('name', '')
                    else:
                        artist_name = str(artist)
                    if artist_name:
                        artist_counts[artist_name] += 1
            elif track.get('artist'):
                # Fallback to string format
                artist_names = [a.strip() for a in str(track.get('artist', '')).split(',')]
                for name in artist_names:
                    if name:
                        artist_counts[name] += 1
        
        # Get top 3 artists with hyperlinks
        if artist_counts:
            top_artists = artist_counts.most_common(3)
            if top_artists:
                # Build artist list with hyperlinks - need to find artist URLs from tracks
                artist_links = []
                # Create a mapping of artist names to URLs
                artist_url_map = {}
                for track in tracks:
                    artists = track.get('artists', [])
                    if isinstance(artists, list):
                        for artist in artists:
                            if isinstance(artist, dict):
                                artist_name = artist.get('name', '')
                                artist_url = artist.get('url', '')
                                if artist_name and artist_url:
                                    artist_url_map[artist_name] = artist_url
                
                for name, count in top_artists:
                    artist_url = artist_url_map.get(name, '')
                    if artist_url:
                        escaped_name = html.escape(name)
                        escaped_url = html.escape(artist_url)
                        artist_links.append(f'<a href="{escaped_url}" target="_blank">{escaped_name}</a> ({count})')
                    else:
                        escaped_name = html.escape(name)
                        artist_links.append(f"{escaped_name} ({count})")
                
                top_artist_str = ', '.join(artist_links)
                metrics.append({
                    'label': 'Most Frequent Artists',
                    'value': top_artist_str
                })
        
        return metrics
    
    def _format_table_html(self, tracks: List[Dict]) -> str:
        """
        Format tracks data into HTML table with hyperlinks, popularity bars, and play buttons
        
        Args:
            tracks: List of track dictionaries
            
        Returns:
            HTML string for the table
        """
        # Determine which columns to include
        columns = config.TABLE_CONFIG['include_columns']
        
        # Build table header
        header_html = '<thead><tr>'
        header_html += '<th>#</th>'  # Position column
        
        # Map column names to display names
        column_display = {
            'track_name': 'TRACK',
            'artist': 'ARTIST',
            'album': 'ALBUM',
            'duration': '🕐',  # Clock icon for duration
            'popularity': 'POPULARITY',
        }
        
        for col in columns:
            # Skip artist column - will be displayed under track names
            if col == 'artist':
                continue
            if col in ['track_name', 'album', 'duration', 'popularity'] and col != 'playlist':
                display_name = column_display.get(col, col.upper())
                header_html += f'<th>{display_name}</th>'
        
        header_html += '</tr></thead>'
        
        # Build table body
        body_html = '<tbody>'
        
        for idx, track in enumerate(tracks, start=1):
            position = track.get('position', idx)
            preview_url = html.escape(str(track.get('preview_url', ''))) if track.get('preview_url') else ''
            track_url = html.escape(str(track.get('spotify_url', ''))) if track.get('spotify_url') else ''
            track_name = html.escape(str(track.get('track_name', 'Unknown Track')))
            
            body_html += '<tr>'
            
            # Position column - just bold number, no play button
            body_html += '<td class="position-cell">'
            body_html += f'<span class="position-number">{position}</span>'
            body_html += '</td>'
            
            # Track column with hyperlink, album image, and artist names underneath
            if 'track_name' in columns:
                body_html += '<td>'
                album_image_url = track.get('album_image', '')
                
                # Get artist names for display under track name
                artist_names_html = ''
                is_explicit = track.get('explicit', False)
                artists = track.get('artists', [])
                if isinstance(artists, list) and len(artists) > 0:
                    artist_links = []
                    for artist in artists:
                        if isinstance(artist, dict):
                            artist_name = html.escape(str(artist.get('name', '')))
                            artist_url = html.escape(str(artist.get('url', ''))) if artist.get('url') else ''
                            if artist_url:
                                artist_links.append(f'<a href="{artist_url}" target="_blank">{artist_name}</a>')
                            else:
                                artist_links.append(artist_name)
                        else:
                            artist_links.append(html.escape(str(artist)))
                    artist_names_html = ', '.join(artist_links)
                elif track.get('artist'):
                    # Fallback to string format
                    artist_names_html = html.escape(str(track.get('artist', '')))

                # Prepend explicit badge if track is explicit
                if is_explicit and artist_names_html:
                    artist_names_html = f'<span class="explicit-badge">E</span>{artist_names_html}'
                
                # Build track display with album image and track info
                if album_image_url:
                    escaped_image_url = html.escape(str(album_image_url))
                    body_html += '<div class="track-with-image">'
                    body_html += f'<img src="{escaped_image_url}" alt="Album art" class="album-image" />'
                    body_html += '<div class="track-info">'
                    # Track name
                    if track_url:
                        body_html += f'<div class="track-name"><a href="{track_url}" target="_blank">{track_name}</a></div>'
                    else:
                        body_html += f'<div class="track-name">{track_name}</div>'
                    # Artist names underneath in lighter gray
                    if artist_names_html:
                        body_html += f'<div class="artist-names">{artist_names_html}</div>'
                    body_html += '</div></div>'
                else:
                    # No album image, just track info
                    body_html += '<div class="track-info">'
                    if track_url:
                        body_html += f'<div class="track-name"><a href="{track_url}" target="_blank">{track_name}</a></div>'
                    else:
                        body_html += f'<div class="track-name">{track_name}</div>'
                    if artist_names_html:
                        body_html += f'<div class="artist-names">{artist_names_html}</div>'
                    body_html += '</div>'
                body_html += '</td>'
            
            # Album column with hyperlink
            if 'album' in columns:
                body_html += '<td>'
                album_name = html.escape(str(track.get('album', '')))
                album_url = html.escape(str(track.get('album_url', ''))) if track.get('album_url') else ''
                if album_url and album_name:
                    body_html += f'<a href="{album_url}" target="_blank">{album_name}</a>'
                elif album_name:
                    body_html += album_name
                else:
                    body_html += 'Unknown Album'
                body_html += '</td>'
            
            # Duration column
            if 'duration' in columns:
                duration = html.escape(str(track.get('duration', 'N/A')))
                body_html += f'<td>{duration}</td>'
            
            # Popularity column with bar (inline layout)
            if 'popularity' in columns:
                popularity = track.get('popularity')
                if popularity is not None:
                    popularity_value = int(popularity)
                    popularity_width = (popularity_value / 100) * 100  # Percentage width
                    # Use explicit green color for PDF compatibility
                    body_html += '<td style="vertical-align: middle;">'
                    body_html += '<div class="popularity-cell">'
                    body_html += f'<span class="popularity-value">{popularity_value}</span>'
                    body_html += '<span class="popularity-bar-container">'
                    body_html += f'<span class="popularity-bar" style="width: {popularity_width}%; background-color: #1DB954;"></span>'
                    body_html += '</span>'
                    body_html += '</div></td>'
                else:
                    body_html += '<td style="vertical-align: middle;">N/A</td>'
            
            body_html += '</tr>'
        
        body_html += '</tbody>'
        
        return f'<table class="spotify-table" id="spotify-charts-table">{header_html}{body_html}</table>'
    
    def _measure_text_width(self, text: str, font_size_em: float) -> float:
        """
        Measure actual rendered width of text using WeasyPrint's layout engine.

        Args:
            text: The text to measure
            font_size_em: Font size in em units

        Returns:
            Width in pixels
        """
        # Create a minimal HTML document with the text
        # Use exact same font and styling as the actual title
        test_html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                }}
                .measure {{
                    font-size: {font_size_em}em;
                    font-weight: 700;
                    white-space: nowrap;
                    display: inline-block;
                }}
            </style>
        </head>
        <body>
            <span class="measure">{html.escape(text)}</span>
        </body>
        </html>
        '''

        # Render the HTML to measure the element
        doc = HTML(string=test_html).render()

        # Get the first page and find the span element
        if len(doc.pages) > 0:
            page = doc.pages[0]

            # Traverse the page box tree to find the text width
            def find_text_width(box):
                # Look for the span element with class 'measure'
                if hasattr(box, 'element_tag') and box.element_tag == 'span':
                    return box.width

                # Recursively search children
                for child in box.children:
                    width = find_text_width(child)
                    if width is not None:
                        return width

                return None

            width = find_text_width(page._page_box)
            if width is not None:
                return width

        # Fallback: estimate if measurement fails
        return len(text) * 32.0

    def _calculate_title_font_size(self, playlist_name: Optional[str]) -> tuple:
        """
        Return fixed font sizes for consistent title appearance across all PDFs.

        The 4 editorial playlists have similar name lengths (16-18 chars):
        - "Top Songs - USA" (16 chars)
        - "Top Songs - Global" (18 chars)
        - "Top Albums - USA" (16 chars)
        - "Top Albums - Global" (18 chars)

        Fixed sizes ensure visual consistency across all reports.
        Reduced from (2.4, 3.2) to (2.0, 2.6) to (1.8, 2.2) to prevent text cutoff at PDF edges,
        especially for longer playlist names like "Top Albums - Global".

        Args:
            playlist_name: The playlist name (unused, kept for API compatibility)

        Returns:
            Tuple of (spotify_label_size, playlist_name_size) in em units
        """
        # Fixed sizes for consistent appearance across all PDFs
        # Reduced sizes to prevent text cutoff at PDF edges (especially "Top Albums - Global")
        # These values fit all 4 editorial playlist names comfortably within 210mm width
        return (1.8, 2.2)

    def _generate_html_content(self, tracks: List[Dict], playlist_name: Optional[str] = None) -> str:
        """
        Generate HTML content from track data with enhanced formatting

        Args:
            tracks: List of track dictionaries
            playlist_name: Optional playlist name for the report title

        Returns:
            HTML string
        """
        # Calculate metrics
        metrics = self._calculate_metrics(tracks)

        # Sort tracks by position (maintain rank order 1-50) instead of config sort
        # This ensures tracks are displayed in their chart ranking order
        tracks = sorted(
            tracks,
            key=lambda x: x.get('position', 999)  # Default to 999 if no position
        )

        # Format table HTML with hyperlinks, popularity bars, etc.
        table_html = self._format_table_html(tracks)

        # Calculate dynamic title font sizes based on playlist name length
        spotify_size, playlist_size = self._calculate_title_font_size(playlist_name)

        # Load HTML template
        with open(self.template_path, 'r') as f:
            template_content = f.read()
            template = Template(template_content)

        # Render template with dynamic font sizes
        html_output = template.render(
            table_html=table_html,
            theme=config.SPOTIFY_THEME,
            generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            total_tracks=len(tracks),
            playlist_name=playlist_name,
            metrics=metrics,
            title_spotify_size=spotify_size,
            title_playlist_size=playlist_size
        )

        return html_output

    def save_pdf_file(
        self,
        tracks: List[Dict],
        filename: str = 'spotify_charts.pdf',
        output_dir: Optional[str] = None,
        playlist_name: Optional[str] = None
    ) -> str:
        """
        Generate and save PDF report to file as a single continuous page

        Args:
            tracks: List of track dictionaries
            filename: Output filename
            output_dir: Optional output directory (defaults to current directory)
            playlist_name: Optional playlist name for the report title

        Returns:
            Path to saved PDF file
        """
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, filename)
        else:
            filepath = filename

        return self.generate_pdf_report(tracks, filepath, playlist_name=playlist_name)
