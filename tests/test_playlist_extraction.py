"""
Test script to extract and display playlist tracks
"""
import sys
import logging
from datetime import datetime
from src.integrations.spotify_client import SpotifyClient
from src.core import config

# Configure logging to show progress
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

def format_track_info(track, index):
    """Format track information for display"""
    artist = track.get('artist', 'Unknown Artist')
    track_name = track.get('track_name', 'Unknown Track')
    album = track.get('album', 'Unknown Album')
    duration = track.get('duration', 'N/A')
    popularity = track.get('popularity', 'N/A')
    playlist = track.get('playlist', 'Unknown Playlist')
    
    return f"{index:3d}. {track_name} - {artist} | Album: {album} | Duration: {duration} | Popularity: {popularity} | Playlist: {playlist}"

def main():
    """Test playlist extraction"""
    print("=" * 80)
    print("SPOTIFY CHARTS - PLAYLIST EXTRACTION TEST")
    print("=" * 80)
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Check configuration
    print("Configuration Check:")
    print(f"  Spotify Client ID: {'✓ Configured' if config.SPOTIFY_CLIENT_ID else '✗ Missing'}")
    print(f"  Spotify Client Secret: {'✓ Configured' if config.SPOTIFY_CLIENT_SECRET else '✗ Missing'}")
    print(f"  Playlist IDs configured: {len([p for p in config.PLAYLIST_IDS if p])}/4")
    print()
    
    # Display configured playlists
    print("Configured Playlists:")
    for i, playlist_id in enumerate(config.PLAYLIST_IDS, 1):
        if playlist_id:
            print(f"  Playlist {i}: {playlist_id}")
        else:
            print(f"  Playlist {i}: Not configured")
    print()
    
    # Check if we have required configuration
    if not config.SPOTIFY_CLIENT_ID or not config.SPOTIFY_CLIENT_SECRET:
        print("ERROR: Spotify credentials not configured!")
        print("Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env file")
        sys.exit(1)
    
    if not any(config.PLAYLIST_IDS):
        print("ERROR: No playlist IDs configured!")
        print("Please set PLAYLIST_1_ID through PLAYLIST_4_ID in .env file")
        sys.exit(1)
    
    # Initialize Spotify client
    print("Initializing Spotify client...")
    try:
        spotify_client = SpotifyClient(headless=True)
        print("✓ Spotify client initialized\n")
        print("NOTE: Progress will be logged below. This may take 2-3 minutes per playlist.\n")
    except Exception as e:
        print(f"✗ Failed to initialize Spotify client: {e}")
        sys.exit(1)
    
    # Fetch tracks from all playlists
    print("=" * 80)
    print("FETCHING TRACKS FROM PLAYLISTS")
    print("=" * 80)
    print("This may take 2-3 minutes for 4 playlists...\n")
    
    try:
        all_tracks = spotify_client.get_all_playlist_tracks(config.PLAYLIST_IDS)
        print(f"\n✓ Successfully fetched {len(all_tracks)} tracks total\n")
    except Exception as e:
        print(f"\n✗ Error fetching tracks: {e}")
        spotify_client.close()
        sys.exit(1)
    finally:
        spotify_client.close()
    
    # Group tracks by playlist
    tracks_by_playlist = {}
    for track in all_tracks:
        playlist_name = track.get('playlist', 'Unknown Playlist')
        if playlist_name not in tracks_by_playlist:
            tracks_by_playlist[playlist_name] = []
        tracks_by_playlist[playlist_name].append(track)
    
    # Display results
    print("=" * 80)
    print("EXTRACTION RESULTS")
    print("=" * 80)
    print(f"\nTotal Tracks Found: {len(all_tracks)}")
    print(f"Playlists Processed: {len(tracks_by_playlist)}\n")
    
    # Display tracks by playlist
    for playlist_name, tracks in tracks_by_playlist.items():
        print("-" * 80)
        print(f"PLAYLIST: {playlist_name}")
        print(f"Tracks: {len(tracks)}")
        print("-" * 80)
        
        # Sort by position if available, otherwise by track name
        sorted_tracks = sorted(tracks, key=lambda t: (
            t.get('position', 9999),
            t.get('track_name', '')
        ))
        
        for idx, track in enumerate(sorted_tracks[:20], 1):  # Show first 20 tracks per playlist
            print(format_track_info(track, idx))
        
        if len(tracks) > 20:
            print(f"... and {len(tracks) - 20} more tracks")
        print()
    
    # Summary statistics
    print("=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    
    # Popularity statistics (only for tracks with popularity data)
    tracks_with_popularity = [t for t in all_tracks if t.get('popularity') is not None]
    if tracks_with_popularity:
        popularities = [t['popularity'] for t in tracks_with_popularity]
        avg_popularity = sum(popularities) / len(popularities)
        max_popularity = max(popularities)
        min_popularity = min(popularities)
        
        print(f"\nPopularity Stats (for {len(tracks_with_popularity)} tracks with data):")
        print(f"  Average: {avg_popularity:.1f}")
        print(f"  Maximum: {max_popularity}")
        print(f"  Minimum: {min_popularity}")
    
    # Duration statistics
    tracks_with_duration = [t for t in all_tracks if t.get('duration') and t.get('duration') != 'N/A']
    if tracks_with_duration:
        print(f"\nTracks with duration data: {len(tracks_with_duration)}")
    
    # Data source breakdown
    api_tracks = [t for t in all_tracks if t.get('popularity') is not None]
    scraped_tracks = [t for t in all_tracks if t.get('popularity') is None]
    
    print(f"\nData Source Breakdown:")
    print(f"  API Fetched: {len(api_tracks)} tracks")
    print(f"  Web Scraped: {len(scraped_tracks)} tracks")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETED SUCCESSFULLY")
    print("=" * 80)

if __name__ == '__main__':
    main()
