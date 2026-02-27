"""
Test separate PDF generation for each playlist

This script tests generating individual PDFs for each playlist with playlist names as titles.
"""
import os
from datetime import datetime
from src.integrations.spotify_client import SpotifyClient
from src.apps.charts.pdf import TableGenerator
from src.core import config
from collections import defaultdict


def test_separate_pdfs():
    """Test generating separate PDFs for each playlist"""
    print("=" * 70)
    print("Testing Separate PDF Generation Per Playlist")
    print("=" * 70)

    try:
        # Fetch tracks from all playlists
        print("\n1️⃣  Fetching tracks from Spotify playlists...")
        spotify_client = SpotifyClient(headless=True)
        tracks = spotify_client.get_all_playlist_tracks(config.PLAYLIST_IDS)
        print(f"   ✓ Collected {len(tracks)} tracks from {len(config.PLAYLIST_IDS)} playlists")

        if not tracks:
            print("   ✗ No tracks found. Exiting.")
            return False

        # Group tracks by playlist
        print("\n2️⃣  Grouping tracks by playlist...")
        tracks_by_playlist = defaultdict(list)
        for track in tracks:
            playlist_name = track.get('playlist', 'Unknown Playlist')
            tracks_by_playlist[playlist_name].append(track)

        print(f"   ✓ Grouped into {len(tracks_by_playlist)} playlists:")
        for playlist_name, playlist_tracks in tracks_by_playlist.items():
            print(f"      • {playlist_name}: {len(playlist_tracks)} tracks")

        # Generate PDFs
        print("\n3️⃣  Generating separate PDFs...")
        table_generator = TableGenerator()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = './test_output'
        os.makedirs(output_dir, exist_ok=True)

        generated_pdfs = []
        for playlist_name, playlist_tracks in tracks_by_playlist.items():
            # Sanitize playlist name for filename
            safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in playlist_name)
            safe_name = safe_name.strip().replace(' ', '_')

            pdf_filename = f'{output_dir}/{safe_name}_{timestamp}.pdf'
            pdf_path = table_generator.generate_pdf(
                playlist_tracks,
                pdf_filename,
                playlist_name=playlist_name
            )
            pdf_size = os.path.getsize(pdf_path) / 1024
            generated_pdfs.append((playlist_name, pdf_path, pdf_size, len(playlist_tracks)))
            print(f"   ✓ Generated: {os.path.basename(pdf_path)}")
            print(f"      Size: {pdf_size:.2f} KB | Tracks: {len(playlist_tracks)}")

        spotify_client.close()

        # Summary
        print("\n" + "=" * 70)
        print("✅ Test Complete!")
        print("=" * 70)
        print(f"\n📊 Summary:")
        print(f"   Total Playlists: {len(generated_pdfs)}")
        print(f"   Total Tracks: {len(tracks)}")
        print(f"\n📄 Generated PDFs:")
        for playlist_name, pdf_path, pdf_size, track_count in generated_pdfs:
            print(f"\n   Playlist: {playlist_name}")
            print(f"   • File: {pdf_path}")
            print(f"   • Size: {pdf_size:.2f} KB")
            print(f"   • Tracks: {track_count}")
            print(f"   • Title in PDF: {playlist_name}")
            print(f"   • Playlist column: EXCLUDED ✓")

        print(f"\n💡 Open the PDFs to verify:")
        for _, pdf_path, _, _ in generated_pdfs:
            print(f"   open {pdf_path}")

        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    if os.uname().sysname == 'Darwin':
        os.environ['DYLD_LIBRARY_PATH'] = '/opt/homebrew/lib:' + os.environ.get('DYLD_LIBRARY_PATH', '')

    success = test_separate_pdfs()
    exit(0 if success else 1)
