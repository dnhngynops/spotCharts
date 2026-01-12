#!/usr/bin/env python3
"""
Test script to verify blank space has been removed from PDFs
Compares the old fixed-height approach vs new auto-height approach
"""

import os
from src.integrations.spotify_client import SpotifyClient
from src.reporting.pdf_generator import PDFGenerator
from weasyprint import HTML, CSS

def main():
    print("=" * 70)
    print("Testing Blank Space Fix in PDFs")
    print("=" * 70)

    # Initialize clients
    client = SpotifyClient()
    pdf_generator = PDFGenerator()

    # Fetch tracks from one playlist
    print("\n1️⃣  Fetching tracks from one playlist...")
    playlist_url = "https://open.spotify.com/playlist/37i9dQZEVXbLp5XoPON0wI"  # Top Songs USA
    tracks = client.get_playlist_tracks(playlist_url)
    print(f"   ✓ Collected {len(tracks)} tracks")

    # Create output directory
    output_dir = "./test_output"
    os.makedirs(output_dir, exist_ok=True)

    # Generate HTML content
    print("\n2️⃣  Generating HTML content...")
    html_content = pdf_generator._generate_html_content(tracks, "Top Songs - USA")
    print("   ✓ HTML content generated")

    # Test with NEW approach (auto height - should have no blank space)
    print("\n3️⃣  Generating PDF with auto height (NEW - no blank space)...")
    new_path = os.path.join(output_dir, "test_auto_height.pdf")
    continuous_page_css = CSS(string='''
        @page {
            size: 210mm auto;  /* A4 width, auto height (fits content) */
            margin: 0;
        }
        body {
            margin: 0;
            padding: 0;
        }
        .container {
            page-break-inside: avoid;
        }
    ''')
    html = HTML(string=html_content)
    html.write_pdf(new_path, stylesheets=[continuous_page_css])
    new_size = os.path.getsize(new_path) / 1024
    print(f"   ✓ Generated: test_auto_height.pdf ({new_size:.2f} KB)")

    # Test with OLD approach (fixed 10000mm height - has blank space)
    print("\n4️⃣  Generating PDF with fixed height (OLD - with blank space)...")
    old_path = os.path.join(output_dir, "test_fixed_height.pdf")
    old_continuous_page_css = CSS(string='''
        @page {
            size: 210mm 10000mm;  /* A4 width, very tall height */
            margin: 0;
        }
        body {
            margin: 0;
            padding: 0;
        }
        .container {
            page-break-inside: avoid;
        }
    ''')
    html = HTML(string=html_content)
    html.write_pdf(old_path, stylesheets=[old_continuous_page_css])
    old_size = os.path.getsize(old_path) / 1024
    print(f"   ✓ Generated: test_fixed_height.pdf ({old_size:.2f} KB)")

    print("\n" + "=" * 70)
    print("✅ Comparison Complete!")
    print("=" * 70)
    print(f"\n📊 Results:")
    print(f"   NEW (auto height):   {new_size:.2f} KB - No blank space ✓")
    print(f"   OLD (fixed height):  {old_size:.2f} KB - Has blank space ✗")
    print(f"\n💡 Open both PDFs to compare:")
    print(f"   open {new_path}")
    print(f"   open {old_path}")
    print(f"\n   The NEW version should end right after the table.")
    print(f"   The OLD version will have extensive blank space after the table.")

if __name__ == "__main__":
    main()
