"""
Test PDF generation with real playlist data

This script extracts tracks from a single Spotify playlist
and generates both HTML and PDF reports to verify the complete pipeline.
"""
import os
from datetime import datetime
from src.integrations.spotify_client import SpotifyClient
from src.reporting.table_generator import TableGenerator
from src.core import config


def test_single_playlist_pdf():
    """Test PDF generation with a real playlist"""
    print("=" * 70)
    print("Testing PDF Generation with Real Playlist Data")
    print("=" * 70)

    # Use the first playlist from config, or a default
    playlist_id = config.PLAYLIST_IDS[0] if config.PLAYLIST_IDS[0] else "37i9dQZEVXbLp5XoPON0wI"

    print(f"\n📋 Playlist ID: {playlist_id}")
    print("-" * 70)

    try:
        # Step 1: Fetch tracks from Spotify
        print("\n1️⃣  Fetching tracks from Spotify playlist...")
        spotify_client = SpotifyClient(headless=True)

        # Get playlist name first
        playlist_name = spotify_client.get_playlist_name(playlist_id)
        print(f"   📝 Playlist Name: {playlist_name}")

        # Fetch tracks
        tracks = spotify_client.get_playlist_tracks(playlist_id, playlist_name)
        print(f"   ✓ Collected {len(tracks)} tracks")

        if not tracks:
            print("   ✗ No tracks found. Exiting.")
            return False

        # Display sample track data
        print("\n   Sample track data (first track):")
        sample = tracks[0]
        for key, value in sample.items():
            if key == 'artists' and isinstance(value, list):
                print(f"     {key}: {[a.get('name') for a in value]}")
            else:
                print(f"     {key}: {value}")

        # Step 2: Generate reports
        print("\n2️⃣  Generating reports...")
        table_generator = TableGenerator()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Create output directory
        output_dir = './test_output'
        os.makedirs(output_dir, exist_ok=True)

        # Generate HTML
        print("   📄 Generating HTML report...")
        html_filename = f'{output_dir}/test_playlist_{timestamp}.html'
        html_path = table_generator.save_html_file(tracks, html_filename)
        html_size = os.path.getsize(html_path) / 1024  # KB
        print(f"   ✓ HTML generated: {html_path}")
        print(f"     Size: {html_size:.2f} KB")

        # Generate PDF
        print("\n   📑 Generating PDF report...")
        pdf_filename = f'{output_dir}/test_playlist_{timestamp}.pdf'
        pdf_path = table_generator.generate_pdf(tracks, pdf_filename)
        pdf_size = os.path.getsize(pdf_path) / 1024  # KB
        print(f"   ✓ PDF generated: {pdf_path}")
        print(f"     Size: {pdf_size:.2f} KB")

        # Close Selenium client
        spotify_client.close()

        # Summary
        print("\n" + "=" * 70)
        print("✅ Test Complete!")
        print("=" * 70)
        print(f"\n📊 Summary:")
        print(f"   Playlist: {playlist_name}")
        print(f"   Tracks: {len(tracks)}")
        print(f"   HTML: {html_path} ({html_size:.2f} KB)")
        print(f"   PDF:  {pdf_path} ({pdf_size:.2f} KB)")
        print(f"\n💡 You can now open these files to verify formatting:")
        print(f"   open {html_path}")
        print(f"   open {pdf_path}")

        return True

    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    # Set library path for macOS
    if os.uname().sysname == 'Darwin':  # macOS
        os.environ['DYLD_LIBRARY_PATH'] = '/opt/homebrew/lib:' + os.environ.get('DYLD_LIBRARY_PATH', '')

    success = test_single_playlist_pdf()
    exit(0 if success else 1)
