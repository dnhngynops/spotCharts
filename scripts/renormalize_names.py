#!/usr/bin/env python3
"""
Backfill normalized name columns across credits, songs, and albums.

Re-applies the project's name_normalizer functions to every existing row
and reports (or commits) rows where the stored value differs from the
freshly computed one.

    credits.normalized_name  → normalize_credit_name(name)
    songs.normalized_title   → normalize_name(title)
    albums.normalized_name   → normalize_name(name)

Usage:
    python scripts/renormalize_names.py            # dry run — shows what would change
    python scripts/renormalize_names.py --apply    # commit changes to Supabase
"""

import argparse
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.core import config
from src.utils.name_normalizer import normalize_credit_name, normalize_name

_PAGE_SIZE = 1000  # PostgREST default max rows per request


def _get_client():
    if not (config.SUPABASE_URL and config.SUPABASE_SERVICE_KEY):
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
        sys.exit(1)
    from supabase import create_client
    return create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)


def _fetch_all(client, table: str, columns: str) -> list:
    """Paginate through a table and return all rows."""
    rows = []
    offset = 0
    while True:
        batch = (
            client.table(table)
            .select(columns)
            .range(offset, offset + _PAGE_SIZE - 1)
            .execute()
            .data or []
        )
        rows.extend(batch)
        if len(batch) < _PAGE_SIZE:
            break
        offset += _PAGE_SIZE
    return rows


# ---------------------------------------------------------------------------
# Per-table renormalization
# ---------------------------------------------------------------------------

def renormalize_credits(client, apply: bool) -> None:
    print("\n── credits ───────────────────────────────────────────────────")

    rows = _fetch_all(client, 'credits', 'credit_id, name, normalized_name')
    print(f"  Fetched {len(rows)} rows")

    # Compute what each normalized_name should be
    updates = []
    unchanged = 0
    for row in rows:
        new_val = normalize_credit_name(row.get('name') or '')
        if row.get('normalized_name') != new_val:
            updates.append({
                'credit_id': row['credit_id'],
                'name':      row.get('name') or '',
                'old':       row.get('normalized_name'),
                'new':       new_val,
            })
        else:
            unchanged += 1

    print(f"  Unchanged : {unchanged}")
    print(f"  To update : {len(updates)}")

    # Collision check — two credits whose names normalize to the same value
    # would violate the UNIQUE constraint on normalized_name.
    all_norms: dict[int, str] = {
        row['credit_id']: normalize_credit_name(row.get('name') or '')
        for row in rows
    }
    by_norm: dict[str, list[int]] = defaultdict(list)
    for cid, norm in all_norms.items():
        by_norm[norm].append(cid)

    collisions = {norm: ids for norm, ids in by_norm.items() if len(ids) > 1}
    if collisions:
        print(f"\n  ⚠  COLLISION WARNING — {len(collisions)} normalized values map to "
              f"multiple credits (would violate UNIQUE constraint):")
        id_to_name = {row['credit_id']: row.get('name', '') for row in rows}
        for norm, ids in collisions.items():
            names = [id_to_name[i] for i in ids]
            print(f"     '{norm}'  ←  {names}")
        collision_ids = {cid for ids in collisions.values() for cid in ids}
        updates = [u for u in updates if u['credit_id'] not in collision_ids]
        print(f"  Updates after skipping collisions: {len(updates)}")

    if not updates:
        print("  Nothing to update.")
        return

    print("\n  Sample changes (first 5):")
    for u in updates[:5]:
        print(f"    [{u['credit_id']}] '{u['name']}'"
              f"\n        '{u['old']}' → '{u['new']}'")

    if not apply:
        print("\n  [DRY RUN] Pass --apply to commit.")
        return

    applied = errors = 0
    for u in updates:
        try:
            client.table('credits').update(
                {'normalized_name': u['new']}
            ).eq('credit_id', u['credit_id']).execute()
            applied += 1
        except Exception as exc:
            print(f"  ERROR credit_id={u['credit_id']} ({u['name']}): {exc}")
            errors += 1

    print(f"  ✓ Applied {applied} updates  ({errors} errors)")


def renormalize_songs(client, apply: bool) -> None:
    print("\n── songs ─────────────────────────────────────────────────────")

    rows = _fetch_all(client, 'songs', 'song_id, title, normalized_title')
    print(f"  Fetched {len(rows)} rows")

    updates = []
    unchanged = 0
    for row in rows:
        new_val = normalize_name(row.get('title') or '')
        if row.get('normalized_title') != new_val:
            updates.append({
                'song_id': row['song_id'],
                'title':   row.get('title') or '',
                'old':     row.get('normalized_title'),
                'new':     new_val,
            })
        else:
            unchanged += 1

    print(f"  Unchanged : {unchanged}")
    print(f"  To update : {len(updates)}")

    if not updates:
        print("  Nothing to update.")
        return

    print("\n  Sample changes (first 5):")
    for u in updates[:5]:
        print(f"    [{u['song_id']}] '{u['title']}'"
              f"\n        '{u['old']}' → '{u['new']}'")

    if not apply:
        print("\n  [DRY RUN] Pass --apply to commit.")
        return

    applied = errors = 0
    for u in updates:
        try:
            client.table('songs').update(
                {'normalized_title': u['new']}
            ).eq('song_id', u['song_id']).execute()
            applied += 1
        except Exception as exc:
            print(f"  ERROR song_id={u['song_id']} ({u['title']}): {exc}")
            errors += 1

    print(f"  ✓ Applied {applied} updates  ({errors} errors)")


def renormalize_albums(client, apply: bool) -> None:
    print("\n── albums ────────────────────────────────────────────────────")

    rows = _fetch_all(client, 'albums', 'album_id, name, normalized_name')
    print(f"  Fetched {len(rows)} rows")

    updates = []
    unchanged = 0
    for row in rows:
        new_val = normalize_name(row.get('name') or '')
        if row.get('normalized_name') != new_val:
            updates.append({
                'album_id': row['album_id'],
                'name':     row.get('name') or '',
                'old':      row.get('normalized_name'),
                'new':      new_val,
            })
        else:
            unchanged += 1

    print(f"  Unchanged : {unchanged}")
    print(f"  To update : {len(updates)}")

    if not updates:
        print("  Nothing to update.")
        return

    print("\n  Sample changes (first 5):")
    for u in updates[:5]:
        print(f"    [{u['album_id']}] '{u['name']}'"
              f"\n        '{u['old']}' → '{u['new']}'")

    if not apply:
        print("\n  [DRY RUN] Pass --apply to commit.")
        return

    applied = errors = 0
    for u in updates:
        try:
            client.table('albums').update(
                {'normalized_name': u['new']}
            ).eq('album_id', u['album_id']).execute()
            applied += 1
        except Exception as exc:
            print(f"  ERROR album_id={u['album_id']} ({u['name']}): {exc}")
            errors += 1

    print(f"  ✓ Applied {applied} updates  ({errors} errors)")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Backfill normalized name columns in Supabase"
    )
    parser.add_argument(
        '--apply', action='store_true',
        help='Commit changes to the database (default: dry run)'
    )
    args = parser.parse_args()

    print("=" * 62)
    print("Renormalize Names — Supabase backfill")
    print(f"Mode: {'APPLY (writing changes)' if args.apply else 'DRY RUN (read-only)'}")
    print("=" * 62)

    client = _get_client()

    renormalize_credits(client, apply=args.apply)
    renormalize_songs(client, apply=args.apply)
    renormalize_albums(client, apply=args.apply)

    print("\nDone.")


if __name__ == '__main__':
    main()
