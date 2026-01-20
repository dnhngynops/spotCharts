"""
Test script to verify HTML layout improvements (HTML can be opened in browser):
1. Metrics align with table left edge
2. Long title text scales down to fit
3. Track/artist name spacing is consistent (no overlapping)
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.reporting.pdf_generator import PDFGenerator
from datetime import datetime


def create_test_tracks(playlist_name):
    """Create test data with various track/artist name lengths"""
    tracks = []

    # Test data with varying name lengths to test spacing
    test_cases = [
        # Short names
        ("Song 1", "Artist A", "Album 1"),
        # Medium names
        ("This Is A Medium Length Track Name", "Artist With Medium Name", "Album Title Here"),
        # Long track name
        ("This Is A Very Long Track Name That Should Wrap But Not Overlap", "Short Artist", "Album"),
        # Long artist name
        ("Short Track", "This Is A Very Long Artist Name With Multiple Words That Should Wrap Properly", "Album"),
        # Both long
        ("Another Very Long Track Title That Tests Wrapping Behavior",
         "Multiple Artists Including Very Long Names That Should Not Overlap With Track",
         "A Very Long Album Title As Well"),
        # Multiple short entries to test consistency
        ("Track A", "Artist B", "Album C"),
        ("Track D", "Artist E", "Album F"),
        ("Track G", "Artist H", "Album I"),
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
            'playlist': playlist_name,
            'duration': '3:45',
            'duration_ms': 225000,
            'popularity': 75 + (idx % 20),
            'album_image': None,
            'preview_url': None,
            'release_date': '2024-01-01'
        }
        tracks.append(track)

    return tracks


def test_html_layout():
    """Test HTML generation with layout improvements"""

    pdf_gen = PDFGenerator()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    print("=" * 80)
    print("Testing HTML Layout Improvements")
    print("=" * 80)

    # Test 1: Metrics alignment with table
    print("\n1. Testing metrics alignment with table left edge...")
    test_tracks_1 = create_test_tracks("Test Playlist - Short Name")
    html_content_1 = pdf_gen._generate_html_content(test_tracks_1, playlist_name="Test Playlist - Short Name")
    html_file_1 = f'test_metrics_alignment_{timestamp}.html'
    with open(html_file_1, 'w', encoding='utf-8') as f:
        f.write(html_content_1)
    print(f"   ✓ Generated: {html_file_1}")
    print("   → Check that 'Total Tracks' and 'Most Frequent Artists' align with table's left edge")

    # Test 2: Long title text scaling
    print("\n2. Testing long title text scaling...")
    very_long_name = "This Is An Extremely Long Playlist Name That Should Scale Down To Fit The Available Width Without Being Cut Off Or Overflowing"
    test_tracks_2 = create_test_tracks(very_long_name)

    # Calculate expected font size
    spotify_size, playlist_size = pdf_gen._calculate_title_font_size(very_long_name)
    print(f"   Original playlist name length: {len(very_long_name)} characters")
    print(f"   Calculated font sizes: Spotify={spotify_size:.2f}em, Playlist={playlist_size:.2f}em")

    html_content_2 = pdf_gen._generate_html_content(test_tracks_2, playlist_name=very_long_name)
    html_file_2 = f'test_long_title_{timestamp}.html'
    with open(html_file_2, 'w', encoding='utf-8') as f:
        f.write(html_content_2)
    print(f"   ✓ Generated: {html_file_2}")
    print("   → Check that full title is visible and fits within the table width")

    # Test 3: Track/artist name spacing consistency
    print("\n3. Testing track/artist name spacing consistency...")
    test_tracks_3 = create_test_tracks("Spacing Test Playlist")
    html_content_3 = pdf_gen._generate_html_content(test_tracks_3, playlist_name="Spacing Test Playlist")
    html_file_3 = f'test_spacing_consistency_{timestamp}.html'
    with open(html_file_3, 'w', encoding='utf-8') as f:
        f.write(html_content_3)
    print(f"   ✓ Generated: {html_file_3}")
    print("   → Check that:")
    print("      - Track names and artist names have equal spacing between them across all rows")
    print("      - Long names wrap properly without overlapping")
    print("      - Row heights adjust to content but maintain consistent internal spacing")

    # Test 4: Normal playlist name (control test)
    print("\n4. Testing normal playlist name (control)...")
    test_tracks_4 = create_test_tracks("Top Songs - USA")
    html_content_4 = pdf_gen._generate_html_content(test_tracks_4, playlist_name="Top Songs - USA")
    html_file_4 = f'test_normal_title_{timestamp}.html'
    with open(html_file_4, 'w', encoding='utf-8') as f:
        f.write(html_content_4)
    print(f"   ✓ Generated: {html_file_4}")
    print("   → Verify this looks normal with default font sizes")

    # Verify font size calculation logic
    print("\n5. Verifying font size calculation logic...")
    test_names = [
        ("Short", 2.4, 3.2),  # Should use default
        ("Medium Length Playlist Name Here", 2.4, 3.2),  # Should use default
        ("This Is A Very Long Playlist Name That Exceeds The Maximum Width", None, None),  # Should scale down
    ]

    for name, expected_spotify, expected_playlist in test_names:
        spotify_size, playlist_size = pdf_gen._calculate_title_font_size(name)
        print(f"   Name: '{name[:50]}...' ({len(name)} chars)")
        print(f"      Calculated: Spotify={spotify_size:.2f}em, Playlist={playlist_size:.2f}em")
        if expected_spotify and expected_playlist:
            if abs(spotify_size - expected_spotify) < 0.01 and abs(playlist_size - expected_playlist) < 0.01:
                print(f"      ✓ Matches expected defaults")
            else:
                print(f"      ✗ Expected: Spotify={expected_spotify}em, Playlist={expected_playlist}em")
        else:
            if spotify_size < 2.4 and playlist_size < 3.2:
                print(f"      ✓ Correctly scaled down")
            else:
                print(f"      ✗ Should have scaled down but didn't")

    print("\n" + "=" * 80)
    print("Test Summary:")
    print("=" * 80)
    print(f"✓ Generated 4 test HTML files in current directory")
    print(f"✓ Files created:")
    print(f"   - {html_file_1} (metrics alignment)")
    print(f"   - {html_file_2} (long title scaling)")
    print(f"   - {html_file_3} (spacing consistency)")
    print(f"   - {html_file_4} (control/normal)")
    print("\nOpen these HTML files in your browser to verify:")
    print("1. Metrics (Total Tracks, Most Frequent Artists) align with table left edge (15px from left)")
    print("2. Long playlist titles scale down to fit without cutoff")
    print("3. Track/artist name spacing is equal across all rows without overlapping")
    print("=" * 80)


if __name__ == '__main__':
    try:
        test_html_layout()
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
