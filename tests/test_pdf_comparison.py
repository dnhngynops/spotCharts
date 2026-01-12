"""
Test to compare single-page vs multi-page PDF generation

This script generates both types of PDFs so you can see the difference.
"""
import os
from datetime import datetime
from src.integrations.spotify_client import SpotifyClient
from src.reporting.table_generator import TableGenerator
from src.core import config


def test_pdf_comparison():
    """Generate both single-page and multi-page PDFs for comparison"""
    print("=" * 70)
    print("Testing Single-Page vs Multi-Page PDF Generation")
    print("=" * 70)

    playlist_id = config.PLAYLIST_IDS[0] if config.PLAYLIST_IDS[0] else "37i9dQZEVXbLp5XoPON0wI"

    print(f"\n📋 Playlist ID: {playlist_id}")
    print("-" * 70)

    try:
        # Fetch tracks
        print("\n1️⃣  Fetching tracks from Spotify playlist...")
        spotify_client = SpotifyClient(headless=True)
        playlist_name = spotify_client.get_playlist_name(playlist_id)
        tracks = spotify_client.get_playlist_tracks(playlist_id, playlist_name)
        print(f"   ✓ Collected {len(tracks)} tracks from {playlist_name}")

        # Generate reports
        print("\n2️⃣  Generating PDFs...")
        table_generator = TableGenerator()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = './test_output'
        os.makedirs(output_dir, exist_ok=True)

        # Generate SINGLE-PAGE PDF
        print("\n   📄 Generating SINGLE-PAGE PDF...")
        single_filename = f'{output_dir}/single_page_{timestamp}.pdf'
        single_path = table_generator.generate_pdf(tracks, single_filename, single_page=True)
        single_size = os.path.getsize(single_path) / 1024
        print(f"   ✓ Single-page PDF: {single_path}")
        print(f"     Size: {single_size:.2f} KB")

        # Generate MULTI-PAGE PDF
        print("\n   📑 Generating MULTI-PAGE PDF...")
        multi_filename = f'{output_dir}/multi_page_{timestamp}.pdf'
        multi_path = table_generator.generate_pdf(tracks, multi_filename, single_page=False)
        multi_size = os.path.getsize(multi_path) / 1024
        print(f"   ✓ Multi-page PDF: {multi_path}")
        print(f"     Size: {multi_size:.2f} KB")

        spotify_client.close()

        # Summary
        print("\n" + "=" * 70)
        print("✅ Comparison Test Complete!")
        print("=" * 70)
        print(f"\n📊 Comparison:")
        print(f"   Tracks: {len(tracks)}")
        print(f"\n   SINGLE-PAGE PDF:")
        print(f"   • File: {single_path}")
        print(f"   • Size: {single_size:.2f} KB")
        print(f"   • Pages: 1 (long scrollable page)")
        print(f"\n   MULTI-PAGE PDF:")
        print(f"   • File: {multi_path}")
        print(f"   • Size: {multi_size:.2f} KB")
        print(f"   • Pages: Multiple (traditional format)")
        print(f"\n💡 Open both files to compare:")
        print(f"   open {single_path}")
        print(f"   open {multi_path}")

        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    if os.uname().sysname == 'Darwin':
        os.environ['DYLD_LIBRARY_PATH'] = '/opt/homebrew/lib:' + os.environ.get('DYLD_LIBRARY_PATH', '')

    success = test_pdf_comparison()
    exit(0 if success else 1)
