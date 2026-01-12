#!/usr/bin/env python3
"""
Test to count pages in generated PDF and diagnose multi-page issue
"""

import os
from PyPDF2 import PdfReader
from src.integrations.spotify_client import SpotifyClient
from src.reporting.pdf_generator import PDFGenerator

def count_pdf_pages(pdf_path):
    """Count number of pages in a PDF file"""
    reader = PdfReader(pdf_path)
    return len(reader.pages)

def main():
    print("=" * 70)
    print("PDF Page Count Diagnostic Test")
    print("=" * 70)

    # Initialize clients
    client = SpotifyClient()
    pdf_generator = PDFGenerator()

    # Fetch tracks
    print("\n1️⃣  Fetching tracks...")
    playlist_url = "https://open.spotify.com/playlist/37i9dQZEVXbLp5XoPON0wI"
    tracks = client.get_playlist_tracks(playlist_url)
    print(f"   ✓ Collected {len(tracks)} tracks")

    # Create output directory
    output_dir = "./test_output"
    os.makedirs(output_dir, exist_ok=True)

    # Generate PDF
    print("\n2️⃣  Generating PDF...")
    pdf_path = os.path.join(output_dir, "test_page_count.pdf")
    pdf_generator.generate_pdf_report(
        tracks,
        pdf_path,
        playlist_name="Top Songs - USA"
    )
    pdf_size = os.path.getsize(pdf_path) / 1024
    print(f"   ✓ Generated: {pdf_path} ({pdf_size:.2f} KB)")

    # Count pages
    print("\n3️⃣  Analyzing PDF structure...")
    page_count = count_pdf_pages(pdf_path)

    print(f"\n   📄 Number of pages in PDF: {page_count}")

    if page_count == 1:
        print(f"   ✅ SUCCESS: PDF is a single continuous page!")
    else:
        print(f"   ❌ ISSUE: PDF has {page_count} pages (should be 1)")
        print(f"\n   The problem is likely that content is still breaking across pages")
        print(f"   despite setting the correct page height.")

    print("\n" + "=" * 70)
    print("Diagnostic Complete")
    print("=" * 70)
    print(f"\n💡 Open PDF to verify visually:")
    print(f"   open {pdf_path}")

if __name__ == "__main__":
    main()
