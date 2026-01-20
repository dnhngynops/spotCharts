"""
Test script to generate a PDF with the new improvements and analyze the output
"""
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.integrations.spotify_client import SpotifyClient
from src.reporting.table_generator import TableGenerator
from src.core import config


def test_pdf_generation():
    """Test PDF generation with one playlist"""
    print("=" * 60)
    print("Testing PDF Generation with Improvements")
    print("=" * 60)
    
    # Get first playlist ID
    playlist_id = config.PLAYLIST_IDS[0] if config.PLAYLIST_IDS[0] else None
    if not playlist_id:
        print("Error: No playlist ID configured")
        return
    
    print(f"\n1. Collecting tracks from playlist: {playlist_id}")
    print("   Using Selenium scraping + API enrichment...")
    
    try:
        # Collect tracks
        with SpotifyClient(use_api_enrichment=True, headless=True) as spotify_client:
            tracks = spotify_client.get_playlist_tracks(playlist_id)
            print(f"   ✓ Collected {len(tracks)} tracks")
        
        if not tracks:
            print("   No tracks found. Exiting.")
            return
        
        # Analyze collected data
        print("\n2. Analyzing collected data...")
        sample_track = tracks[0] if tracks else {}
        print(f"   Sample track keys: {list(sample_track.keys())}")
        
        # Check URL availability
        url_stats = {
            'track_urls': sum(1 for t in tracks if t.get('spotify_url')),
            'artist_urls': sum(1 for t in tracks if t.get('artists') and any(a.get('url') for a in (t.get('artists') or []))),
            'album_urls': sum(1 for t in tracks if t.get('album_url')),
            'preview_urls': sum(1 for t in tracks if t.get('preview_url')),
            'popularity_scores': sum(1 for t in tracks if t.get('popularity') is not None),
        }
        
        print(f"\n   URL Collection Stats:")
        print(f"   - Track URLs: {url_stats['track_urls']}/{len(tracks)}")
        print(f"   - Artist URLs: {url_stats['artist_urls']}/{len(tracks)}")
        print(f"   - Album URLs: {url_stats['album_urls']}/{len(tracks)}")
        print(f"   - Preview URLs: {url_stats['preview_urls']}/{len(tracks)}")
        print(f"   - Popularity Scores: {url_stats['popularity_scores']}/{len(tracks)}")
        
        # Show sample track details
        if sample_track:
            print(f"\n   Sample Track Details:")
            print(f"   - Position: {sample_track.get('position')}")
            print(f"   - Track: {sample_track.get('track_name')}")
            print(f"   - Track URL: {sample_track.get('spotify_url', 'N/A')}")
            print(f"   - Artists: {sample_track.get('artist', 'N/A')}")
            artists = sample_track.get('artists', [])
            if artists:
                print(f"   - Artist URLs: {[a.get('url', 'N/A') for a in artists if isinstance(a, dict)]}")
            print(f"   - Album: {sample_track.get('album', 'N/A')}")
            print(f"   - Album URL: {sample_track.get('album_url', 'N/A')}")
            print(f"   - Preview URL: {sample_track.get('preview_url', 'N/A')}")
            print(f"   - Popularity: {sample_track.get('popularity', 'N/A')}")
        
        # Generate PDF
        print("\n3. Generating PDF report...")
        table_generator = TableGenerator()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        playlist_name = tracks[0].get('playlist', 'Test Playlist') if tracks else 'Test Playlist'
        
        # Sanitize playlist name for filename
        safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in playlist_name)
        safe_name = safe_name.strip().replace(' ', '_')
        
        pdf_filename = f'test_{safe_name}_{timestamp}.pdf'
        pdf_file_path = table_generator.generate_pdf(
            tracks,
            pdf_filename,
            playlist_name=playlist_name
        )
        
        print(f"   ✓ PDF generated: {pdf_file_path}")
        
        # Check file exists and get size
        if os.path.exists(pdf_file_path):
            file_size = os.path.getsize(pdf_file_path)
            print(f"   ✓ File size: {file_size:,} bytes ({file_size / 1024:.2f} KB)")
        else:
            print(f"   ✗ Error: PDF file not found at {pdf_file_path}")
            return
        
        print("\n4. PDF Generation Complete!")
        print(f"   File: {pdf_file_path}")
        print(f"   Tracks: {len(tracks)}")
        print(f"   Playlist: {playlist_name}")
        
        print("\n" + "=" * 60)
        print("Test completed successfully!")
        print("=" * 60)
        
        return pdf_file_path
        
    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    test_pdf_generation()
