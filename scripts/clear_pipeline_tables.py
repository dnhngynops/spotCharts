#!/usr/bin/env python3
"""
Clear all pipeline-written Supabase tables in reverse FK-dependency order.

Run this when you want a clean slate before a fresh pipeline run.
Tables preserved: schema_version, profiles, companies, representation_types,
  teams, rosters, watchlists, watchlist_items, raw_role_names,
  role_mapping_patterns, role_mapping_suggestions, discovery_*.

Usage:
    python scripts/clear_pipeline_tables.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.core import config

if not (config.SUPABASE_URL and config.SUPABASE_SERVICE_KEY):
    print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
    sys.exit(1)

from supabase import create_client
client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)

# Tables written by the pipeline, in reverse FK-dependency order.
# Each entry is (table_name, primary_key_column).
PIPELINE_TABLES = [
    ('playlist_songs',   'playlist_song_id'),
    ('song_genres',      'song_genre_id'),
    ('song_credits',     'song_credit_id'),
    ('credit_genres',    'credit_genre_id'),
    ('playlist_scrapes', 'scrape_id'),
    ('songs',            'song_id'),
    ('albums',           'album_id'),
    ('credits',          'credit_id'),
    ('genres',           'genre_id'),
    ('playlists',        'playlist_id'),
    ('roles',            'role_id'),
]

print("Clearing pipeline tables from Supabase...")
for table, pk in PIPELINE_TABLES:
    result = client.table(table).delete().gte(pk, 0).execute()
    deleted = len(result.data) if result.data else '?'
    print(f"  {table}: {deleted} rows deleted")

print("\nDone. All pipeline tables are empty.")
