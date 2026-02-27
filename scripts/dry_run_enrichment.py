#!/usr/bin/env python3
"""
Dry run: collect one playlist with full enrichment and print album/artist (and track) values.
No reports, uploads, or email. Use to inspect what the extended enrichment returns.

Usage: python scripts/dry_run_enrichment.py [--playlist-index N] [--max-tracks N] [--save-json]
  --playlist-index N   Use Nth playlist from config (0-based, default 0)
  --max-tracks N       Only enrich first N tracks per playlist (default 5 for speed)
  --save-json          Also save full track list to output/dry_run_enrichment_*.json
"""
import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Keys we care about for "enrichment" (album + artist + track API)
ENRICHMENT_KEYS = [
    # Track API
    'track_id', 'track_name', 'artist', 'artists', 'position', 'playlist', 'playlist_id',
    'popularity', 'duration', 'duration_ms', 'preview_url', 'explicit', 'spotify_url',
    # Album (from Track API album object)
    'album', 'album_id', 'album_url', 'album_image', 'release_date',
    'album_total_tracks', 'album_type',
    # Artist (from Artist API batch)
    'artist_image', 'artist_followers', 'artist_popularity', 'genres',
]


def get_enrichment_subset(track: dict) -> dict:
    """Return only enrichment-related keys for display (values as-is)."""
    return {k: track.get(k) for k in ENRICHMENT_KEYS if k in track}


def main():
    parser = argparse.ArgumentParser(description='Dry run enrichment: see album/artist values')
    parser.add_argument('--playlist-index', type=int, default=0, help='Playlist index in config (0-based)')
    parser.add_argument('--max-tracks', type=int, default=5, help='Max tracks to collect per playlist (for speed)')
    parser.add_argument('--save-json', action='store_true', help='Save full tracks to output/dry_run_enrichment_*.json')
    args = parser.parse_args()

    from src.core import config
    from src.integrations.spotify_client import SpotifyClient

    playlist_ids = config.PLAYLIST_IDS
    if not playlist_ids:
        print("No playlist IDs configured. Set PLAYLIST_1_ID etc. in .env")
        sys.exit(1)
    if args.playlist_index >= len(playlist_ids):
        print(f"Playlist index {args.playlist_index} out of range (have {len(playlist_ids)} playlists)")
        sys.exit(1)

    pid = playlist_ids[args.playlist_index]
    print("Dry run: enrichment only (no reports, upload, or email)")
    print(f"Playlist index: {args.playlist_index}, ID: {pid}")
    print(f"Limiting to first {args.max_tracks} tracks for speed.\n")

    with SpotifyClient(use_api_enrichment=True, headless=True) as client:
        tracks = client.get_playlist_tracks(pid, None)
        for t in tracks:
            t['playlist_id'] = pid
        # Limit to first N for dry run
        tracks = tracks[: args.max_tracks]

    if not tracks:
        print("No tracks collected.")
        return

    # All keys present across all tracks
    all_keys = set()
    for t in tracks:
        all_keys.update(t.keys())
    print("--- All keys present on tracks ---")
    for k in sorted(all_keys):
        print(f"  {k}")
    print()

    # Enrichment-specific sample (first 3 tracks)
    print("--- Enrichment values (first 3 tracks) ---")
    for i, track in enumerate(tracks[:3], start=1):
        sub = get_enrichment_subset(track)
        print(f"\n--- Track {i}: {sub.get('track_name', '?')} — {sub.get('artist', '?')} ---")
        for k, v in sub.items():
            if k == 'artists' and isinstance(v, list):
                print(f"  {k}: {json.dumps(v, indent=4)}")
            else:
                print(f"  {k}: {v}")
    print()

    # One-liner summary for each track (album + artist fields only)
    print("--- One-line summary per track (album + artist enrichment) ---")
    for i, t in enumerate(tracks, start=1):
        album = t.get('album') or '-'
        album_id = t.get('album_id') or '-'
        release = t.get('release_date') or '-'
        artist_fol = t.get('artist_followers')
        artist_fol = f"{artist_fol:,}" if isinstance(artist_fol, int) else str(artist_fol)
        artist_pop = t.get('artist_popularity', '-')
        genres = t.get('genres') or []
        genres_str = ", ".join(genres[:5]) if genres else "-"
        print(f"  {i}. album={album} | album_id={album_id} | release={release} | "
              f"artist_followers={artist_fol} | artist_popularity={artist_pop} | genres=[{genres_str}]")
    print()

    if args.save_json:
        out_dir = config.REPORT_CONFIG.get('output_dir', './output') or './output'
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, f"dry_run_enrichment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(tracks, f, indent=2, ensure_ascii=False)
        print(f"Full track list saved to: {path}")

    print("Done.")


if __name__ == '__main__':
    main()
