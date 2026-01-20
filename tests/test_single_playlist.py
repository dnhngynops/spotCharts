"""
Test script to generate a PDF report for Top Songs - USA playlist
This will test all the layout improvements we made.
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
    """Generate PDF for Top Songs - USA"""
    print("=" * 80)
    print("Testing PDF Generation with Layout Improvements")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Get the Top Songs - USA playlist ID
        playlist_id = config.PLAYLIST_IDS[0]  # First playlist is Top Songs - USA

        if not playlist_id:
            print("\n✗ Error: PLAYLIST_1_ID not configured in .env file")
            return

        print(f"\nPlaylist ID: {playlist_id}")
        print("\n1. Collecting tracks from Top Songs - USA...")
        print("   Using Selenium scraping (primary) + Spotify API enrichment")

        # Collect tracks using Selenium + API enrichment
        with SpotifyClient(use_api_enrichment=True, headless=True) as spotify_client:
            tracks = spotify_client.get_playlist_tracks(playlist_id, "Top Songs - USA")
            print(f"   ✓ Collected {len(tracks)} tracks")

        if not tracks:
            print("   ✗ No tracks found. Exiting.")
            return

        # Display some info about collected tracks
        print(f"\n   Sample tracks collected:")
        for i, track in enumerate(tracks[:3], 1):
            track_name = track.get('track_name', 'Unknown')
            artist = track.get('artist', 'Unknown')
            popularity = track.get('popularity', 'N/A')
            print(f"      {i}. {track_name} - {artist} (Popularity: {popularity})")

        # Generate PDF
        print("\n2. Generating PDF report...")
        table_generator = TableGenerator()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Create output directory if needed
        output_dir = project_root / 'output'
        os.makedirs(output_dir, exist_ok=True)

        playlist_name = tracks[0].get('playlist', 'Top Songs - USA')
        safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in playlist_name)
        safe_name = safe_name.strip().replace(' ', '_')

        pdf_filename = f'{safe_name}_{timestamp}.pdf'
        pdf_file_path = table_generator.generate_pdf(
            tracks,
            pdf_filename,
            playlist_name=playlist_name
        )

        print(f"   ✓ PDF generated: {pdf_file_path}")
        print(f"   ✓ Total tracks in PDF: {len(tracks)}")

        # Check file size
        if os.path.exists(pdf_file_path):
            file_size = os.path.getsize(pdf_file_path) / 1024  # Convert to KB
            print(f"   ✓ File size: {file_size:.1f} KB")

        print("\n" + "=" * 80)
        print("Test Complete!")
        print("=" * 80)
        print("\nPlease review the generated PDF to verify:")
        print("1. ✓ Metrics (Total Tracks, Most Frequent Artists) align with table left edge")
        print("2. ✓ Playlist title fits properly (scales down if needed)")
        print("3. ✓ Track/artist name spacing is consistent across all rows")
        print("4. ✓ Long track/artist names wrap without overlapping")
        print(f"\nGenerated file: {pdf_file_path}")
        print("=" * 80)

    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == '__main__':
    main()
