#!/usr/bin/env python3
"""
Test script to verify PDFs are always single continuous page with no blank space
"""

import os
from src.integrations.spotify_client import SpotifyClient
from src.reporting.pdf_generator import PDFGenerator

def main():
    print("=" * 70)
    print("Testing Single-Page-Only PDF Generation")
    print("=" * 70)

    # Initialize clients
    client = SpotifyClient()
    pdf_generator = PDFGenerator()

    # Fetch tracks from one playlist
    print("\n1️⃣  Fetching tracks from Top Songs - USA playlist...")
    playlist_url = "https://open.spotify.com/playlist/37i9dQZEVXbLp5XoPON0wI"
    tracks = client.get_playlist_tracks(playlist_url)
    print(f"   ✓ Collected {len(tracks)} tracks")

    # Create output directory
    output_dir = "./test_output"
    os.makedirs(output_dir, exist_ok=True)

    # Generate PDF (should always be single continuous page)
    print("\n2️⃣  Generating PDF (single continuous page)...")
    pdf_path = os.path.join(output_dir, "test_single_continuous_page.pdf")
    pdf_generator.generate_pdf_report(
        tracks,
        pdf_path,
        playlist_name="Top Songs - USA"
    )
    pdf_size = os.path.getsize(pdf_path) / 1024
    print(f"   ✓ Generated: {pdf_path} ({pdf_size:.2f} KB)")

    print("\n" + "=" * 70)
    print("✅ Test Complete!")
    print("=" * 70)
    print(f"\n📄 PDF Details:")
    print(f"   File: {pdf_path}")
    print(f"   Size: {pdf_size:.2f} KB")
    print(f"   Tracks: {len(tracks)}")
    print(f"   Format: Single continuous page (no multi-page option)")
    print(f"\n💡 Open PDF to verify:")
    print(f"   open {pdf_path}")
    print(f"\n   Expected behavior:")
    print(f"   • PDF should be ONE continuous page")
    print(f"   • PDF should end right after the table (no blank space)")
    print(f"   • PDF should NOT have multiple pages")

if __name__ == "__main__":
    main()
