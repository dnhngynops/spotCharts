"""
Test script to generate PDF report for Top Songs USA playlist only
"""
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.integrations.spotify_client import SpotifyClient
from src.reporting.table_generator import TableGenerator
from src.core import config

def main():
    print("=" * 70)
    print("Testing Spotify Charts - Top Songs USA")
    print("=" * 70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    try:
        # Use only the first playlist (Top Songs USA)
        playlist_id = config.PLAYLIST_IDS[0]
        playlist_name = "Top Songs - USA"

        print(f"Playlist ID: {playlist_id}")
        print(f"Playlist Name: {playlist_name}\n")

        # Step 1: Collect tracks
        print("=" * 70)
        print("STEP 1: Collecting tracks from Spotify playlist")
        print("=" * 70)
        print("Using Selenium scraping (primary) + Spotify API enrichment\n")

        with SpotifyClient(use_api_enrichment=True, headless=True) as spotify_client:
            tracks = spotify_client.get_playlist_tracks(playlist_id, playlist_name)
            print(f"\n✓ Collected {len(tracks)} tracks from '{playlist_name}'")

        if not tracks:
            print("No tracks found. Exiting.")
            return

        # Display sample track data
        print("\nSample track data (first track):")
        print("-" * 70)
        sample_track = tracks[0]
        for key, value in sample_track.items():
            if key == 'playlist_image':
                # Don't print the full base64 image data
                print(f"  {key}: [base64 image data - {len(str(value))} chars]")
            else:
                print(f"  {key}: {value}")
        print("-" * 70)

        # Step 2: Generate PDF report
        print("\n" + "=" * 70)
        print("STEP 2: Generating PDF report")
        print("=" * 70)

        # Create output directory
        output_dir = project_root / 'output'
        os.makedirs(output_dir, exist_ok=True)

        # Generate PDF
        table_generator = TableGenerator()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Sanitize playlist name for filename
        safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in playlist_name)
        safe_name = safe_name.strip().replace(' ', '_')

        pdf_filename = f'{safe_name}_{timestamp}.pdf'
        pdf_file_path = output_dir / pdf_filename

        print(f"Generating PDF: {pdf_filename}")
        print(f"Output path: {pdf_file_path}")

        pdf_path = table_generator.generate_pdf(
            tracks,
            str(pdf_file_path),
            playlist_name=playlist_name
        )

        # Get file size
        file_size_kb = os.path.getsize(pdf_path) / 1024

        print(f"\n✓ PDF generated successfully!")
        print(f"  File: {pdf_path}")
        print(f"  Size: {file_size_kb:.2f} KB")
        print(f"  Tracks: {len(tracks)}")
        print(f"  Format: Single continuous page")

        # Try to get PDF dimensions using PyPDF2 if available
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(pdf_path)
            page = reader.pages[0]
            width_mm = float(page.mediabox.width) * 0.352778  # Convert points to mm
            height_mm = float(page.mediabox.height) * 0.352778
            print(f"  Dimensions: {width_mm:.1f}mm × {height_mm:.1f}mm")
            print(f"  Page count: {len(reader.pages)}")
        except ImportError:
            print("  (Install PyPDF2 to view PDF dimensions)")
        except Exception as e:
            print(f"  (Could not read PDF dimensions: {e})")

        print("\n" + "=" * 70)
        print("✓ Test completed successfully!")
        print("=" * 70)
        print(f"\nYou can open the PDF at: {pdf_path}")

    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == '__main__':
    main()
