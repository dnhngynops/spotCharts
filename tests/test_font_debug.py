"""
Debug script to verify font sizing is being applied correctly
"""
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.integrations.spotify_client import SpotifyClient
from src.reporting.pdf_generator import PDFGenerator
from src.core import config

def main():
    print("=" * 80)
    print("DEBUGGING FONT SIZING IN PDF GENERATION")
    print("=" * 80)

    # Test with a very long playlist name
    long_name = "Very Long Playlist Name That Should Trigger Font Resize Test"
    print(f"\nTest playlist name: \"{long_name}\"")
    print(f"Character count: {len(long_name)}")

    # Create PDF generator and calculate font sizes
    pdf_gen = PDFGenerator()
    spotify_size, playlist_size = pdf_gen._calculate_title_font_size(long_name)

    print(f"\n✓ Font sizes calculated:")
    print(f"  Spotify label: {spotify_size:.4f}em")
    print(f"  Playlist name: {playlist_size:.4f}em")

    # Now let's collect actual tracks and generate HTML to see what gets passed
    print("\n" + "=" * 80)
    print("COLLECTING TRACKS AND GENERATING HTML")
    print("=" * 80)

    playlist_id = config.PLAYLIST_IDS[0]
    with SpotifyClient(use_api_enrichment=True, headless=True) as spotify_client:
        tracks = spotify_client.get_playlist_tracks(playlist_id, long_name)

    print(f"\n✓ Collected {len(tracks)} tracks")

    # Generate HTML content to see what template receives
    html_content = pdf_gen._generate_html_content(tracks, long_name)

    # Check if font sizes are in the HTML
    if f"{spotify_size}em" in html_content:
        print(f"\n✓ Spotify label font size ({spotify_size}em) found in HTML")
    else:
        print(f"\n✗ Spotify label font size ({spotify_size}em) NOT found in HTML")
        print(f"   Searching for default 2.4em...")
        if "2.4em" in html_content:
            print(f"   ✗ PROBLEM: Using default 2.4em instead of calculated {spotify_size}em")

    if f"{playlist_size}em" in html_content:
        print(f"✓ Playlist name font size ({playlist_size}em) found in HTML")
    else:
        print(f"✗ Playlist name font size ({playlist_size}em) NOT found in HTML")
        print(f"   Searching for default 3.2em...")
        if "3.2em" in html_content:
            print(f"   ✗ PROBLEM: Using default 3.2em instead of calculated {playlist_size}em")

    # Save HTML to file for inspection
    output_dir = project_root / 'output'
    os.makedirs(output_dir, exist_ok=True)
    html_file = output_dir / 'debug_font_sizing.html'
    with open(html_file, 'w') as f:
        f.write(html_content)
    print(f"\n✓ HTML saved to: {html_file}")

    # Look for the specific style sections in HTML
    print("\n" + "=" * 80)
    print("EXTRACTING FONT SIZE CSS FROM HTML")
    print("=" * 80)

    # Find spotify-label style
    import re
    spotify_label_match = re.search(r'\.spotify-label\s*{[^}]*font-size:\s*([^;]+);', html_content)
    playlist_name_match = re.search(r'\.playlist-name\s*{[^}]*font-size:\s*([^;]+);', html_content)

    if spotify_label_match:
        print(f"\nSpotify label CSS: font-size: {spotify_label_match.group(1)}")
    else:
        print(f"\n✗ Could not find .spotify-label font-size in CSS")

    if playlist_name_match:
        print(f"Playlist name CSS: font-size: {playlist_name_match.group(1)}")
    else:
        print(f"✗ Could not find .playlist-name font-size in CSS")

    # Now generate the actual PDF
    print("\n" + "=" * 80)
    print("GENERATING PDF")
    print("=" * 80)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    pdf_filename = f'debug_font_sizing_{timestamp}.pdf'
    pdf_path = output_dir / pdf_filename

    pdf_path = pdf_gen.generate_pdf_report(tracks, str(pdf_path), playlist_name=long_name)

    file_size_kb = os.path.getsize(pdf_path) / 1024
    print(f"\n✓ PDF generated: {pdf_path}")
    print(f"  Size: {file_size_kb:.2f} KB")

    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print(f"\nExpected font sizes:")
    print(f"  Spotify label: {spotify_size:.4f}em")
    print(f"  Playlist name: {playlist_size:.4f}em")
    print(f"\nPlease check:")
    print(f"1. HTML file: {html_file}")
    print(f"2. PDF file: {pdf_path}")
    print(f"\nVerify that the playlist name appears smaller than in the short title PDF.")

if __name__ == '__main__':
    main()
