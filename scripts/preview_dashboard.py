#!/usr/bin/env python3
"""
Quick script to regenerate the dashboard from cached data for previewing template changes.
Usage: python scripts/preview_dashboard.py
"""
import os
import sys
import json
import subprocess
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Check for cached data
CACHE_FILE = './output/cached_tracks.json'
OUTPUT_DIR = './output'

def load_cached_tracks():
    """Load tracks from cache if available"""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return None

def save_tracks_to_cache(tracks):
    """Save tracks to cache for future use"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(CACHE_FILE, 'w') as f:
        json.dump(tracks, f)
    print(f"   ✓ Cached {len(tracks)} tracks for future previews")

def collect_fresh_tracks():
    """Collect fresh tracks from Spotify"""
    from src.integrations.spotify_client import SpotifyClient
    from src.core import config

    print("   Collecting fresh data from Spotify...")
    with SpotifyClient(use_api_enrichment=True, headless=True) as client:
        tracks = client.get_all_playlist_tracks(config.PLAYLIST_IDS)
    return tracks

def generate_dashboard(tracks):
    """Generate the dashboard HTML"""
    from src.reporting.dashboard_generator import DashboardGenerator

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = os.path.join(OUTPUT_DIR, f'spotify_charts_dashboard_{timestamp}.html')

    generator = DashboardGenerator()
    generator.generate_dashboard(tracks, output_path)

    return output_path

def main():
    print("\n🎵 Dashboard Preview Generator")
    print("=" * 40)

    # Try to use cached data first
    tracks = load_cached_tracks()

    if tracks:
        print(f"   Using cached data ({len(tracks)} tracks)")
    else:
        print("   No cache found, collecting fresh data...")
        tracks = collect_fresh_tracks()
        save_tracks_to_cache(tracks)

    print("\n   Generating dashboard...")
    output_path = generate_dashboard(tracks)
    print(f"   ✓ Dashboard saved to: {output_path}")

    # Open in browser
    print("\n   Opening in browser...")
    subprocess.run(['open', output_path])

    print("\n✓ Done! Modify the template and run again to see changes.")
    print(f"   Template: templates/dashboard_template.html")
    print(f"   To refresh data: rm {CACHE_FILE}")

if __name__ == '__main__':
    main()
