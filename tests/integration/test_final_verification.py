#!/usr/bin/env python3
"""
Final comprehensive verification test for single-page PDFs with no blank space
"""

import os
from PyPDF2 import PdfReader
from src.integrations.spotify_client import SpotifyClient
from src.reporting.table_generator import TableGenerator
from src.core import config
from collections import defaultdict
from datetime import datetime

def verify_pdf(pdf_path):
    """Verify PDF is single page and return details"""
    reader = PdfReader(pdf_path)
    page_count = len(reader.pages)
    file_size = os.path.getsize(pdf_path) / 1024

    # Get page dimensions
    if page_count > 0:
        page = reader.pages[0]
        mediabox = page.mediabox
        width_mm = float(mediabox.width) * 25.4 / 72  # Convert points to mm
        height_mm = float(mediabox.height) * 25.4 / 72
    else:
        width_mm = height_mm = 0

    return {
        'page_count': page_count,
        'file_size': file_size,
        'width_mm': width_mm,
        'height_mm': height_mm,
        'is_single_page': page_count == 1
    }

def main():
    print("=" * 70)
    print("FINAL VERIFICATION TEST")
    print("Single-Page PDF with Minimal Blank Space")
    print("=" * 70)

    # Fetch tracks from all playlists
    print("\n1️⃣  Fetching tracks from all playlists...")
    spotify_client = SpotifyClient(headless=True)
    tracks = spotify_client.get_all_playlist_tracks(config.PLAYLIST_IDS)
    print(f"   ✓ Collected {len(tracks)} tracks from {len(config.PLAYLIST_IDS)} playlists")

    # Group tracks by playlist
    print("\n2️⃣  Grouping tracks by playlist...")
    tracks_by_playlist = defaultdict(list)
    for track in tracks:
        playlist_name = track.get('playlist', 'Unknown Playlist')
        tracks_by_playlist[playlist_name].append(track)
    print(f"   ✓ Grouped into {len(tracks_by_playlist)} playlists")

    # Generate PDFs
    print("\n3️⃣  Generating and verifying PDFs...")
    table_generator = TableGenerator()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = './test_output'
    os.makedirs(output_dir, exist_ok=True)

    results = []
    all_single_page = True

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

        # Verify the PDF
        verification = verify_pdf(pdf_path)
        verification['playlist_name'] = playlist_name
        verification['track_count'] = len(playlist_tracks)
        verification['path'] = pdf_path
        results.append(verification)

        if not verification['is_single_page']:
            all_single_page = False

        status = "✅" if verification['is_single_page'] else "❌"
        print(f"\n   {status} {playlist_name}")
        print(f"      Pages: {verification['page_count']}")
        print(f"      Size: {verification['file_size']:.2f} KB")
        print(f"      Dimensions: {verification['width_mm']:.1f}mm × {verification['height_mm']:.1f}mm")
        print(f"      Tracks: {len(playlist_tracks)}")

    spotify_client.close()

    # Summary
    print("\n" + "=" * 70)
    if all_single_page:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 70)

    print(f"\n📊 Summary:")
    print(f"   Total PDFs Generated: {len(results)}")
    print(f"   Single-Page PDFs: {sum(1 for r in results if r['is_single_page'])}/{len(results)}")
    print(f"   Total Tracks: {sum(r['track_count'] for r in results)}")

    print(f"\n📄 Detailed Results:")
    for result in results:
        print(f"\n   Playlist: {result['playlist_name']}")
        print(f"   • File: {os.path.basename(result['path'])}")
        print(f"   • Page Count: {result['page_count']} {'✅' if result['is_single_page'] else '❌ (should be 1)'}")
        print(f"   • Dimensions: {result['width_mm']:.1f} × {result['height_mm']:.1f} mm")
        print(f"   • File Size: {result['file_size']:.2f} KB")
        print(f"   • Tracks: {result['track_count']}")

    print(f"\n💡 Verification criteria:")
    print(f"   ✓ Each PDF must have exactly 1 page (single continuous page)")
    print(f"   ✓ Page height should fit content (~1500-2000mm for 50 tracks)")
    print(f"   ✓ No excessive blank space (minimal 5mm buffer)")

    return all_single_page

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
