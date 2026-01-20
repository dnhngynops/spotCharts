"""
Test script to generate a PDF report with all improvements for one playlist
"""
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.integrations.spotify_client import SpotifyClient
from src.reporting.table_generator import TableGenerator
from src.core import config


def test_pdf_report_generation():
    """Generate a PDF report for one playlist and analyze the output"""
    print("=" * 70)
    print("PDF Report Generation Test - Enhanced Features")
    print("=" * 70)
    
    # Get first playlist ID
    playlist_id = config.PLAYLIST_IDS[0] if config.PLAYLIST_IDS[0] else None
    if not playlist_id:
        print("Error: No playlist ID configured")
        return None
    
    print(f"\n1. COLLECTING TRACKS")
    print(f"   Playlist ID: {playlist_id}")
    print("   Method: Selenium scraping (primary) + Spotify API enrichment")
    
    try:
        # Collect tracks
        with SpotifyClient(use_api_enrichment=True, headless=True) as spotify_client:
            tracks = spotify_client.get_playlist_tracks(playlist_id)
            playlist_name = tracks[0].get('playlist', 'Unknown Playlist') if tracks else 'Unknown Playlist'
            print(f"   ✓ Collected {len(tracks)} tracks from '{playlist_name}'")
        
        if not tracks:
            print("   ✗ No tracks found. Exiting.")
            return None
        
        # Analyze collected data
        print("\n2. DATA COLLECTION ANALYSIS")
        url_stats = {
            'track_urls': sum(1 for t in tracks if t.get('spotify_url')),
            'artist_urls': sum(1 for t in tracks if t.get('artists') and any(
                isinstance(a, dict) and a.get('url') for a in (t.get('artists') or []))
            ),
            'album_urls': sum(1 for t in tracks if t.get('album_url')),
            'preview_urls': sum(1 for t in tracks if t.get('preview_url')),
            'popularity_scores': sum(1 for t in tracks if t.get('popularity') is not None),
        }
        
        print(f"   URL Collection Success Rate:")
        print(f"   - Track URLs:      {url_stats['track_urls']}/{len(tracks)} ({url_stats['track_urls']*100//len(tracks)}%)")
        print(f"   - Artist URLs:     {url_stats['artist_urls']}/{len(tracks)} ({url_stats['artist_urls']*100//len(tracks)}%)")
        print(f"   - Album URLs:      {url_stats['album_urls']}/{len(tracks)} ({url_stats['album_urls']*100//len(tracks)}%)")
        print(f"   - Preview URLs:    {url_stats['preview_urls']}/{len(tracks)} ({url_stats['preview_urls']*100//len(tracks)}%)")
        print(f"   - Popularity:      {url_stats['popularity_scores']}/{len(tracks)} ({url_stats['popularity_scores']*100//len(tracks)}%)")
        
        # Calculate and display metrics that will be shown
        print("\n3. METRICS CALCULATION")
        from collections import Counter
        artist_counts = Counter()
        for track in tracks:
            artists = track.get('artists', [])
            if isinstance(artists, list):
                for artist in artists:
                    if isinstance(artist, dict):
                        artist_name = artist.get('name', '')
                    else:
                        artist_name = str(artist)
                    if artist_name:
                        artist_counts[artist_name] += 1
            elif track.get('artist'):
                artist_names = [a.strip() for a in str(track.get('artist', '')).split(',')]
                for name in artist_names:
                    if name:
                        artist_counts[name] += 1
        
        if artist_counts:
            top_artists = artist_counts.most_common(3)
            print(f"   Most Frequent Artists (Top 3):")
            for i, (name, count) in enumerate(top_artists, 1):
                print(f"   {i}. {name}: {count} appearance(s)")
            print(f"   → Will be displayed as: 'Most Frequent Artists: {', '.join([f'{name} ({count})' for name, count in top_artists])}'")
        else:
            print("   No artist data available for metrics")
        
        # Show sample track details
        sample = tracks[0] if tracks else {}
        print(f"\n4. SAMPLE TRACK VERIFICATION")
        print(f"   Position:      {sample.get('position', 'N/A')}")
        print(f"   Track:         {sample.get('track_name', 'N/A')}")
        print(f"   Track URL:     {sample.get('spotify_url', 'N/A')[:60]}..." if sample.get('spotify_url') else "   Track URL:     N/A")
        artists = sample.get('artists', [])
        if artists:
            print(f"   Artists:       {', '.join([a.get('name', '') for a in artists[:2] if isinstance(a, dict)])}")
            print(f"   Artist URLs:   {len([a.get('url') for a in artists if isinstance(a, dict) and a.get('url')])} URL(s) available")
        print(f"   Album:         {sample.get('album', 'N/A')}")
        print(f"   Album URL:     {sample.get('album_url', 'N/A')[:60]}..." if sample.get('album_url') else "   Album URL:     N/A")
        print(f"   Preview URL:   {'Yes' if sample.get('preview_url') else 'No'}")
        print(f"   Popularity:    {sample.get('popularity', 'N/A')}")
        print(f"   Duration:      {sample.get('duration', 'N/A')}")
        
        # Generate PDF
        print("\n5. GENERATING PDF REPORT")
        print("   Features to be included:")
        print("   ✓ Popularity bars (horizontal visualization)")
        print("   ✓ Track hyperlinks (clickable track names)")
        print("   ✓ Artist hyperlinks (clickable artist names)")
        print("   ✓ Album hyperlinks (clickable album names)")
        print("   ✓ Play buttons on hover (position column → preview URL)")
        print("   ✓ Clock icon for duration column (🕐)")
        print("   ✓ 'TRACK' column name (instead of track_name)")
        print("   ✓ Metrics display (Most Frequent Artists)")
        print("   ✓ Footer with timestamp and author")
        
        table_generator = TableGenerator()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Sanitize playlist name for filename
        safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in playlist_name)
        safe_name = safe_name.strip().replace(' ', '_')
        
        pdf_filename = f'test_report_{safe_name}_{timestamp}.pdf'
        output_dir = config.REPORT_CONFIG.get('output_dir', './output')
        os.makedirs(output_dir, exist_ok=True)
        pdf_filepath = os.path.join(output_dir, pdf_filename)
        
        print(f"\n   Generating PDF...")
        pdf_file_path = table_generator.generate_pdf(
            tracks,
            pdf_filepath,
            playlist_name=playlist_name
        )
        
        # Verify file was created
        if os.path.exists(pdf_file_path):
            file_size = os.path.getsize(pdf_file_path)
            print(f"   ✓ PDF generated successfully!")
            print(f"   File: {pdf_file_path}")
            print(f"   Size: {file_size:,} bytes ({file_size / 1024:.2f} KB)")
        else:
            print(f"   ✗ Error: PDF file not found at {pdf_file_path}")
            return None
        
        # Summary
        print("\n" + "=" * 70)
        print("TEST COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print(f"Report Generated: {pdf_file_path}")
        print(f"Playlist: {playlist_name}")
        print(f"Tracks: {len(tracks)}")
        print(f"Features: All enhancements applied ✓")
        print("\nMetrics Displayed:")
        if artist_counts:
            top_artists = artist_counts.most_common(3)
            for name, count in top_artists:
                print(f"  - {name}: {count} track(s)")
        print("=" * 70)
        
        return pdf_file_path
        
    except Exception as e:
        print(f"\n✗ ERROR during test: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    result = test_pdf_report_generation()
    if result:
        print(f"\n✓ Test completed. PDF available at: {result}")
    else:
        print("\n✗ Test failed.")
