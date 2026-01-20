"""
Test script to verify HTML formatting without PDF generation
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.reporting.pdf_generator import PDFGenerator

# Sample track data for testing
sample_tracks = [
    {
        'position': 1,
        'track_name': 'Test Track 1',
        'spotify_url': 'https://open.spotify.com/track/test1',
        'artists': [
            {'name': 'Artist A', 'url': 'https://open.spotify.com/artist/a'},
            {'name': 'Artist B', 'url': 'https://open.spotify.com/artist/b'}
        ],
        'artist': 'Artist A, Artist B',
        'album': 'Test Album',
        'album_url': 'https://open.spotify.com/album/test',
        'duration': '3:45',
        'popularity': 95,
        'preview_url': 'https://p.scdn.co/mp3-preview/test1',
        'playlist': 'Test Playlist'
    },
    {
        'position': 2,
        'track_name': 'Test Track 2',
        'spotify_url': 'https://open.spotify.com/track/test2',
        'artists': [{'name': 'Artist C', 'url': 'https://open.spotify.com/artist/c'}],
        'artist': 'Artist C',
        'album': 'Another Album',
        'album_url': 'https://open.spotify.com/album/test2',
        'duration': '4:20',
        'popularity': 88,
        'preview_url': 'https://p.scdn.co/mp3-preview/test2',
        'playlist': 'Test Playlist'
    },
    {
        'position': 3,
        'track_name': 'Test Track 3',
        'spotify_url': 'https://open.spotify.com/track/test3',
        'artists': [{'name': 'Artist A', 'url': 'https://open.spotify.com/artist/a'}],
        'artist': 'Artist A',
        'album': 'Test Album',
        'album_url': 'https://open.spotify.com/album/test',
        'duration': '2:30',
        'popularity': 75,
        'preview_url': None,
        'playlist': 'Test Playlist'
    }
]

def test_html_generation():
    """Test HTML generation"""
    print("Testing HTML generation...")
    
    pdf_generator = PDFGenerator()
    
    # Generate HTML content
    html_content = pdf_generator._generate_html_content(sample_tracks, "Test Playlist")
    
    # Save to file for inspection
    output_file = 'test_output.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ HTML generated and saved to {output_file}")
    print(f"✓ HTML length: {len(html_content)} characters")
    
    # Check for key features
    checks = {
        'Popularity bars': 'popularity-bar' in html_content,
        'Play buttons': 'play-button' in html_content,
        'Track hyperlinks': 'spotify.com/track' in html_content,
        'Artist hyperlinks': 'spotify.com/artist' in html_content,
        'Album hyperlinks': 'spotify.com/album' in html_content,
        'TRACK column': '<th>TRACK</th>' in html_content,
        'Metrics section': 'Most Frequent Artists' in html_content,
        'Footer with author': 'Danh Nguyen' in html_content,
    }
    
    print("\nFeature checks:")
    for feature, present in checks.items():
        status = "✓" if present else "✗"
        print(f"  {status} {feature}")
    
    all_present = all(checks.values())
    if all_present:
        print("\n✓ All features present in HTML!")
    else:
        print("\n✗ Some features missing")
    
    return html_content

if __name__ == '__main__':
    test_html_generation()
