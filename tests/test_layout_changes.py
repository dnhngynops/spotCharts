#!/usr/bin/env python3
"""
Test script to verify PDF layout changes:
1. Title format: "Spotify" (smaller) + line break + "Playlist Name" (larger)
2. Narrower rank and duration columns
3. Track and popularity columns shifted left
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.integrations.spotify_client import SpotifyClient
from src.reporting.table_generator import TableGenerator
from src.core import config


def test_layout_changes():
    """Test the new PDF layout with single playlist"""
    print("=" * 70)
    print("Testing PDF Layout Changes")
    print("=" * 70)

    # Test with first playlist
    test_playlist_id = config.PLAYLIST_IDS[0]
    print(f"\n📋 Testing with playlist: {test_playlist_id}")

    try:
        # Step 1: Collect tracks
        print("\n1️⃣  Collecting tracks...")
        with SpotifyClient(use_api_enrichment=True, headless=True) as client:
            tracks = client.get_playlist_tracks(test_playlist_id)
            playlist_name = tracks[0].get('playlist', 'Test Playlist') if tracks else 'Test Playlist'
            print(f"   ✓ Collected {len(tracks)} tracks from '{playlist_name}'")

        # Step 2: Generate PDF
        print("\n2️⃣  Generating PDF with new layout...")
        table_generator = TableGenerator()

        output_filename = f"test_layout_{playlist_name.replace(' ', '_')}.pdf"
        pdf_path = table_generator.generate_pdf(
            tracks,
            output_filename,
            playlist_name=playlist_name
        )

        print(f"   ✓ PDF generated: {pdf_path}")

        # Step 3: Verify file
        if os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path) / 1024  # KB
            print(f"\n3️⃣  Verification:")
            print(f"   ✓ File exists: {pdf_path}")
            print(f"   ✓ File size: {file_size:.2f} KB")

            print("\n" + "=" * 70)
            print("✅ Layout Changes to Verify:")
            print("=" * 70)
            print("\n1. Title Format:")
            print("   - 'Spotify' (smaller font, 2.4em)")
            print("   - Line break")
            print("   - Playlist name (larger font, 3.2em)")

            print("\n2. Column Widths:")
            print("   - Rank column: narrower (50px max)")
            print("   - Duration column: narrower (80px max)")
            print("   - Track column: wider (38%, shifted left)")

            print("\n3. Visual Inspection:")
            print("   - Open the PDF and verify the layout")
            print(f"   - File: {os.path.abspath(pdf_path)}")

            return True
        else:
            print("   ❌ PDF file not created")
            return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\nPDF Layout Test")
    print("Testing new layout specifications\n")

    success = test_layout_changes()

    if success:
        print("\n🎉 Test completed! Please open the PDF to verify layout changes.")
        sys.exit(0)
    else:
        print("\n⚠️  Test encountered errors.")
        sys.exit(1)
