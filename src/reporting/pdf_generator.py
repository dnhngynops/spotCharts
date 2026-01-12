"""
PDF Report Generator using WeasyPrint

This module handles the conversion of HTML reports to PDF format,
maintaining Spotify theming and styling from the HTML templates.
"""
import os
from typing import List, Dict, Optional
from datetime import datetime
from jinja2 import Template
from weasyprint import HTML, CSS
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

    def _generate_html_content(self, tracks: List[Dict], playlist_name: Optional[str] = None) -> str:
        """
        Generate HTML content from track data (same as TableGenerator)

        Args:
            tracks: List of track dictionaries
            playlist_name: Optional playlist name for the report title

        Returns:
            HTML string
        """
        import pandas as pd

        # Convert to DataFrame
        df = pd.DataFrame(tracks)

        # Select and order columns (exclude 'playlist' column)
        columns = config.TABLE_CONFIG['include_columns']
        available_columns = [col for col in columns if col in df.columns and col != 'playlist']
        df = df[available_columns]

        # Sort if configured
        if config.TABLE_CONFIG.get('sort_by') and config.TABLE_CONFIG['sort_by'] in df.columns:
            ascending = config.TABLE_CONFIG.get('sort_order', 'desc') == 'asc'
            df = df.sort_values(by=config.TABLE_CONFIG['sort_by'], ascending=ascending)

        # Reset index
        df = df.reset_index(drop=True)
        df.index = df.index + 1  # Start numbering from 1

        # Load HTML template
        with open(self.template_path, 'r') as f:
            template = Template(f.read())

        # Prepare data for template
        table_html = df.to_html(
            classes='spotify-table',
            table_id='spotify-charts-table',
            escape=False,
            index=True
        )

        # Render template
        html_output = template.render(
            table_html=table_html,
            theme=config.SPOTIFY_THEME,
            generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            total_tracks=len(df),
            playlist_name=playlist_name
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
