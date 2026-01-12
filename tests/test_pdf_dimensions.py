#!/usr/bin/env python3
"""
Test script to analyze PDF dimensions and identify blank space sources
"""

import os
from src.integrations.spotify_client import SpotifyClient
from src.reporting.pdf_generator import PDFGenerator
from weasyprint import HTML, CSS

def main():
    print("=" * 70)
    print("Analyzing PDF Dimensions and Blank Space")
    print("=" * 70)

    # Initialize clients
    client = SpotifyClient()
    pdf_generator = PDFGenerator()

    # Fetch tracks from one playlist
    print("\n1️⃣  Fetching tracks...")
    playlist_url = "https://open.spotify.com/playlist/37i9dQZEVXbLp5XoPON0wI"
    tracks = client.get_playlist_tracks(playlist_url)
    print(f"   ✓ Collected {len(tracks)} tracks")

    # Create output directory
    output_dir = "./test_output"
    os.makedirs(output_dir, exist_ok=True)

    # Generate HTML content
    print("\n2️⃣  Generating HTML content...")
    html_content = pdf_generator._generate_html_content(tracks, "Top Songs - USA")

    # Render with current approach to measure
    print("\n3️⃣  Measuring content with current approach...")
    html = HTML(string=html_content)

    temp_css = CSS(string='''
        @page {
            size: 210mm 100000mm;
            margin: 0;
        }
        body {
            margin: 0;
            padding: 0;
        }
    ''')

    document = html.render(stylesheets=[temp_css])

    total_height = 0
    for i, page in enumerate(document.pages):
        print(f"   Page {i+1}: {page.height}px (height)")
        total_height += page.height

    total_height_mm = (total_height / 96 * 25.4) + 10
    print(f"\n   Total content height: {total_height}px = {total_height_mm:.2f}mm")

    # Test with minimized padding CSS
    print("\n4️⃣  Testing with minimized padding...")

    minimal_padding_css = CSS(string='''
        @page {
            size: 210mm 100000mm;
            margin: 0;
        }
        * {
            margin: 0 !important;
            padding: 0 !important;
        }
        body {
            padding: 10px !important;
        }
        .container {
            padding: 20px !important;
        }
    ''')

    document2 = html.render(stylesheets=[minimal_padding_css])
    total_height2 = sum(page.height for page in document2.pages)
    total_height_mm2 = (total_height2 / 96 * 25.4) + 10

    print(f"   With minimal padding: {total_height2}px = {total_height_mm2:.2f}mm")
    print(f"   Difference: {total_height - total_height2}px = {(total_height_mm - total_height_mm2):.2f}mm")

    # Generate PDF with minimal padding
    print("\n5️⃣  Generating PDF with optimized padding...")
    test_path = os.path.join(output_dir, "test_minimal_padding.pdf")

    final_css = CSS(string=f'''
        @page {{
            size: 210mm {total_height_mm2}mm;
            margin: 0;
        }}
        * {{
            margin: 0 !important;
            padding: 0 !important;
        }}
        body {{
            padding: 10px !important;
        }}
        .container {{
            padding: 20px !important;
        }}
        .header {{
            margin-bottom: 20px !important;
            padding-bottom: 15px !important;
        }}
        .footer {{
            margin-top: 20px !important;
            padding-top: 15px !important;
        }}
    ''')

    html.write_pdf(test_path, stylesheets=[final_css])
    pdf_size = os.path.getsize(test_path) / 1024

    print(f"   ✓ Generated: {test_path} ({pdf_size:.2f} KB)")

    print("\n" + "=" * 70)
    print("✅ Analysis Complete!")
    print("=" * 70)
    print(f"\n📊 Results:")
    print(f"   Original height: {total_height_mm:.2f}mm")
    print(f"   Optimized height: {total_height_mm2:.2f}mm")
    print(f"   Space saved: {(total_height_mm - total_height_mm2):.2f}mm")
    print(f"\n💡 Open PDF to verify:")
    print(f"   open {test_path}")

if __name__ == "__main__":
    main()
