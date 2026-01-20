"""
Test the layout fixes:
1. Playlist name stays on one line (no wrapping)
2. Track/artist names don't overlap in cells
"""
import sys
import os
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.reporting.pdf_generator import PDFGenerator


def create_test_tracks_with_long_names():
    """Create test data with very long track and artist names to test overlapping"""
    tracks = []

    # Create varied cases to test overlapping
    test_cases = [
        # Case 1: Very long track name
        ("This Is An Extremely Long Track Name That Should Wrap Across Multiple Lines Without Overlapping The Artist Name Below It",
         "Short Artist",
         "Album"),

        # Case 2: Very long artist name
        ("Short Track",
         "This Is An Extremely Long Artist Name With Multiple Words That Should Wrap Properly Without Overlapping With Adjacent Content",
         "Album"),

        # Case 3: Both very long
        ("Another Very Long Track Title With Many Words That Will Definitely Need To Wrap",
         "Very Long Artist Name Featuring Multiple Collaborators With Long Names That Will Also Wrap",
         "Long Album Title"),

        # Case 4: Medium length (control)
        ("Medium Length Track Name", "Medium Artist Name", "Album"),

        # Case 5: Short (control)
        ("Track", "Artist", "Album"),

        # Case 6-15: More varied cases
        ("Beautiful Song Title", "Artist One, Artist Two, Artist Three", "Album"),
        ("X", "Y", "Z"),  # Very short
        ("Track Name With Numbers 1234567890", "Artist & The Band", "Album"),
        ("Song", "Featured Artist, Another Artist, Third Artist, Fourth Artist", "Album"),
        ("Very Long Track That Tests Wrapping Behavior In Detail", "Short", "Album"),
    ]

    for idx, (track_name, artist_name, album_name) in enumerate(test_cases, start=1):
        track = {
            'position': idx,
            'track_name': track_name,
            'artist': artist_name,
            'artists': [{'name': artist_name, 'url': f'https://open.spotify.com/artist/{idx}', 'id': f'artist{idx}'}],
            'album': album_name,
            'album_url': f'https://open.spotify.com/album/{idx}',
            'spotify_url': f'https://open.spotify.com/track/{idx}',
            'track_id': f'track{idx}',
            'explicit': False,
            'playlist': 'Test Playlist',
            'duration': '3:45',
            'duration_ms': 225000,
            'popularity': 75 + (idx % 20),
            'album_image': None,
            'preview_url': None,
            'release_date': '2024-01-01'
        }
        tracks.append(track)

    return tracks


def test_fixes():
    """Test both layout fixes"""

    pdf_gen = PDFGenerator()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Output to project root for test HTML files
    output_dir = project_root / 'output'
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 80)
    print("Testing Layout Fixes")
    print("=" * 80)

    # Test 1: Very long playlist name - should stay on one line
    print("\n1. Testing single-line playlist title...")
    very_long_name = "This Is An Extremely Long Playlist Name That Should Not Wrap But Instead Scale Down To Fit On A Single Line"
    print(f"   Playlist name: '{very_long_name}'")
    print(f"   Length: {len(very_long_name)} characters")

    tracks = create_test_tracks_with_long_names()

    # Calculate font size
    spotify_size, playlist_size = pdf_gen._calculate_title_font_size(very_long_name)
    print(f"   Calculated sizes: Spotify={spotify_size:.3f}em, Playlist={playlist_size:.3f}em")

    html_content = pdf_gen._generate_html_content(tracks, playlist_name=very_long_name)
    html_file = output_dir / f'test_long_title_{timestamp}.html'
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"   ✓ Generated HTML: {html_file}")
    print(f"   → Verify title is on ONE LINE (no wrapping)")

    # Test 2: Normal playlist name with long track/artist names
    print("\n2. Testing track/artist name spacing (no overlapping)...")
    normal_name = "Top Songs - USA"
    tracks2 = create_test_tracks_with_long_names()

    html_content2 = pdf_gen._generate_html_content(tracks2, playlist_name=normal_name)
    html_file2 = output_dir / f'test_no_overlap_{timestamp}.html'
    with open(html_file2, 'w', encoding='utf-8') as f:
        f.write(html_content2)
    print(f"   ✓ Generated HTML: {html_file2}")
    print(f"   → Verify no overlapping between track and artist names")
    print(f"   → Check rows with very long names (rows 1-3)")

    # Test 3: Edge case - maximum length name
    print("\n3. Testing maximum length playlist name...")
    max_name = "X" * 100  # 100 character name
    spotify_size, playlist_size = pdf_gen._calculate_title_font_size(max_name)
    print(f"   Name length: {len(max_name)} characters")
    print(f"   Calculated sizes: Spotify={spotify_size:.3f}em, Playlist={playlist_size:.3f}em")
    print(f"   ✓ Should scale down to {playlist_size:.3f}em (minimum: 1.0em)")

    html_content3 = pdf_gen._generate_html_content(tracks2, playlist_name=max_name)
    html_file3 = output_dir / f'test_max_length_{timestamp}.html'
    with open(html_file3, 'w', encoding='utf-8') as f:
        f.write(html_content3)
    print(f"   ✓ Generated HTML: {html_file3}")

    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"Generated 3 HTML files:")
    print(f"  1. {html_file} - Long playlist name (should be single line)")
    print(f"  2. {html_file2} - Track/artist spacing test (no overlapping)")
    print(f"  3. {html_file3} - Maximum length test (edge case)")
    print("\nOpen these files in your browser to verify:")
    print("  ✓ Playlist titles stay on ONE line (no wrapping)")
    print("  ✓ Track and artist names don't overlap (proper spacing)")
    print("  ✓ Very long names wrap within their cells without overflow")
    print("=" * 80)


if __name__ == '__main__':
    try:
        test_fixes()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
