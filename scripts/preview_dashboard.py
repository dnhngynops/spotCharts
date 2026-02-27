#!/usr/bin/env python3
"""
Quick script to regenerate the dashboard for previewing template changes.

Usage:
  python scripts/preview_dashboard.py                # use cached data (or scrape Spotify)
  python scripts/preview_dashboard.py --from-supabase  # pull from latest Supabase scrape
  python scripts/preview_dashboard.py -s               # shorthand
"""
import os
import sys
import json
import argparse
import subprocess
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CACHE_FILE = './output/cached_tracks.json'
OUTPUT_DIR = './output'


def load_cached_tracks():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return None


def save_tracks_to_cache(tracks):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(CACHE_FILE, 'w') as f:
        json.dump(tracks, f)
    print(f"   ✓ Cached {len(tracks)} tracks for future previews")


def collect_fresh_tracks():
    from src.integrations.spotify_client import SpotifyClient
    from src.core import config

    print("   Collecting fresh data from Spotify...")
    with SpotifyClient(use_api_enrichment=True, headless=True) as client:
        tracks = client.get_all_playlist_tracks(config.PLAYLIST_IDS)
    return tracks


def collect_from_supabase():
    from src.integrations.supabase_client import SupabaseClient

    if not SupabaseClient.is_configured():
        print("   ✗ Supabase is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env")
        sys.exit(1)

    print("   Fetching latest scrape from Supabase...")
    client = SupabaseClient()
    return client.fetch_latest_tracks()


def generate_dashboard(tracks):
    from src.apps.charts.generator import DashboardGenerator

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = os.path.join(OUTPUT_DIR, f'spotify_charts_dashboard_{timestamp}.html')

    generator = DashboardGenerator()
    generator.generate_dashboard(tracks, output_path)
    return output_path


def main():
    parser = argparse.ArgumentParser(description='Dashboard Preview Generator')
    parser.add_argument(
        '--from-supabase', '-s',
        action='store_true',
        help='Pull data from the latest Supabase scrape instead of local cache/Spotify',
    )
    args = parser.parse_args()

    print("\n🎵 Dashboard Preview Generator")
    print("=" * 40)

    if args.from_supabase:
        tracks = collect_from_supabase()
        if not tracks:
            print("   ✗ No data found in Supabase. Run the pipeline at least once first.")
            sys.exit(1)
        print(f"   ✓ Loaded {len(tracks)} tracks from Supabase (latest scrape)")
    else:
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

    print("\n   Opening in browser...")
    subprocess.run(['open', output_path])

    print("\n✓ Done!")
    if args.from_supabase:
        print("   Source: Supabase (latest scrape)")
        print("   To use cached/Spotify data instead, run without -s")
    else:
        print("   Template: templates/shell/base.html (+ app views in templates/charts/, templates/deal_projector/, etc.)")
        print(f"   To refresh data: rm {CACHE_FILE}")
        print("   To pull from Supabase: python scripts/preview_dashboard.py --from-supabase")


if __name__ == '__main__':
    main()
