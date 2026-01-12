"""
Table generation and formatting with Spotify theming
"""
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime
from jinja2 import Template
from src.core import config
import os


class TableGenerator:
    """Generate formatted tables from track data"""

    def __init__(self):
        # Template is now in root templates directory
        template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'templates')
        self.template_path = os.path.join(template_dir, 'table_template.html')
    
    def generate_html_table(self, tracks: List[Dict]) -> str:
        """
        Generate an HTML table with Spotify theming
        
        Args:
            tracks: List of track dictionaries
            
        Returns:
            HTML string of the formatted table
        """
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(tracks)
        
        # Select and order columns
        columns = config.TABLE_CONFIG['include_columns']
        available_columns = [col for col in columns if col in df.columns]
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
            total_tracks=len(df)
        )
        
        return html_output
    
    def generate_csv(self, tracks: List[Dict], filename: str = None) -> str:
        """
        Generate a CSV file from track data
        
        Args:
            tracks: List of track dictionaries
            filename: Optional filename (if None, returns CSV string)
            
        Returns:
            CSV file path or CSV string
        """
        df = pd.DataFrame(tracks)
        
        # Select columns
        columns = config.TABLE_CONFIG['include_columns']
        available_columns = [col for col in columns if col in df.columns]
        df = df[available_columns]
        
        # Sort if configured
        if config.TABLE_CONFIG.get('sort_by') and config.TABLE_CONFIG['sort_by'] in df.columns:
            ascending = config.TABLE_CONFIG.get('sort_order', 'desc') == 'asc'
            df = df.sort_values(by=config.TABLE_CONFIG['sort_by'], ascending=ascending)
        
        if filename:
            df.to_csv(filename, index=False)
            return filename
        else:
            return df.to_csv(index=False)
    
    def save_html_file(self, tracks: List[Dict], filename: str = 'spotify_charts.html') -> str:
        """
        Generate and save HTML table to file

        Args:
            tracks: List of track dictionaries
            filename: Output filename

        Returns:
            Path to saved file
        """
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
        """
        Generate a PDF report from track data as a single continuous page

        Args:
            tracks: List of track dictionaries
            filename: Output filename
            playlist_name: Optional playlist name for the report title

        Returns:
            Path to saved PDF file
        """
        from src.reporting.pdf_generator import PDFGenerator

        pdf_generator = PDFGenerator()
        return pdf_generator.generate_pdf_report(tracks, filename, playlist_name=playlist_name)

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
        from src.reporting.pdf_generator import PDFGenerator

        pdf_generator = PDFGenerator()
        return pdf_generator.save_pdf_file(tracks, filename, output_dir, playlist_name=playlist_name)

