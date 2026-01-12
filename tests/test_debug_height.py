#!/usr/bin/env python3
"""
Debug script to check actual content height measurement
"""

import os
from src.integrations.spotify_client import SpotifyClient
from weasyprint import HTML, CSS

def main():
    print("=" * 70)
    print("Debug Content Height Measurement")
    print("=" * 70)

    # Initialize client
    client = SpotifyClient()

    # Fetch tracks
    print("\n1️⃣  Fetching tracks...")
    playlist_url = "https://open.spotify.com/playlist/37i9dQZEVXbLp5XoPON0wI"
    tracks = client.get_playlist_tracks(playlist_url)
    print(f"   ✓ Collected {len(tracks)} tracks")

    # Generate HTML content (simplified version)
    from src.reporting.pdf_generator import PDFGenerator
    pdf_gen = PDFGenerator()
    html_content = pdf_gen._generate_html_content(tracks, "Top Songs - USA")

    print("\n2️⃣  Rendering with 100000mm page...")
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

    print(f"   Pages rendered: {len(document.pages)}")

    if len(document.pages) > 0:
        page = document.pages[0]
        print(f"   Page height: {page.height}px")

        # Traverse and find max Y
        max_y = 0
        element_count = 0

        def get_max_y(box, depth=0):
            nonlocal max_y, element_count
            element_count += 1

            bottom_y = box.position_y + box.height

            if depth < 3:  # Show first few levels
                print(f"   {'  ' * depth}Box: y={box.position_y:.1f} h={box.height:.1f} bottom={bottom_y:.1f} tag={getattr(box, 'element_tag', 'unknown')}")

            if bottom_y > max_y:
                max_y = bottom_y

            for child in box.children:
                get_max_y(child, depth + 1)

        print(f"\n3️⃣  Traversing element tree...")
        get_max_y(page._page_box)

        print(f"\n   Elements traversed: {element_count}")
        print(f"   Max Y position: {max_y:.2f}px")
        print(f"   Max Y in mm: {(max_y / 96 * 25.4):.2f}mm")
        print(f"   Final height (with 5mm buffer): {(max_y / 96 * 25.4) + 5:.2f}mm")

if __name__ == "__main__":
    main()
