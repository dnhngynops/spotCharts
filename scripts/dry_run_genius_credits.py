#!/usr/bin/env python3
"""
Dry run: Genius credit enrichment + role normalization.

Tests three things without touching any database:

  1. normalize_role() — validates our port against backend copy's RoleNormalizer
     on real role strings from backend copy dry-run JSON files.
  2. Live Genius API — fetches credits for one known song (Hozier "Too Sweet").
  3. Pipeline simulation — runs the _upsert_genius_credits() collection logic
     on the live API result and prints exactly what would be written to each
     Supabase table (roles, raw_role_names, credits, song_credits).

Usage:
    python scripts/dry_run_genius_credits.py [--skip-api]

Options:
    --skip-api    Skip the live Genius API call (offline role-normalization
                  test only; useful when GENIUS_ACCESS_TOKEN is not set).
"""

import importlib.util
import os
import re
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sep(title: str, width: int = 72) -> None:
    print(f"\n{'─' * width}")
    print(f"  {title}")
    print(f"{'─' * width}")


def _load_backend_normalizer():
    """Dynamically import RoleNormalizer from backend copy (optional)."""
    backend_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "backend copy", "phases", "phase2", "role_normalizer.py",
    )
    if not os.path.exists(backend_path):
        return None
    try:
        spec = importlib.util.spec_from_file_location("_backend_role_norm", backend_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.RoleNormalizer()
    except Exception as e:
        print(f"  (Could not load backend normalizer: {e})")
        return None


# ---------------------------------------------------------------------------
# Section 1 — Role normalizer comparison
# ---------------------------------------------------------------------------

# Real raw role strings from the backend copy "Too Sweet" by Hozier dry run
# (backend copy/phases/phase2/jsons_for_review/song_5052_too_sweet_*.json)
REFERENCE_ROLES = [
    # (raw_role, expected_canonical_in_our_system)
    ("Writer",                  "Writer"),
    ("Producer",                "Producer"),
    ("Vocals",                  "Vocalist"),
    ("Background Vocals",       "Vocalist"),
    ("Vocal Engineer",          "Engineer"),
    ("Mastering Engineer",      "Mastering Engineer"),
    ("Mixing Engineer",         "Mixing Engineer"),
    ("Engineer",                "Engineer"),
    ("Strings",                 "Instrumentalist"),
    ("Mellotron",               "Instrumentalist"),
    ("Keyboards",               "Instrumentalist"),
    ("Percussion",              "Instrumentalist"),
    ("Bells",                   "Instrumentalist"),
    ("Drums",                   "Instrumentalist"),
    ("Bass",                    "Instrumentalist"),
    ("Label",                   "Publisher"),
    # Additional canonical cases from ROLE_MAPPINGS
    ("songwriter",              "Writer"),
    ("Music Producer",          "Producer"),
    ("co-producer",             "Producer"),
    ("Vocal Producer",          "Vocal Producer"),
    ("mixer",                   "Mixing Engineer"),
    ("mastered by",             "Mastering Engineer"),
    ("Recording Engineer",      "Engineer"),
    ("background vocal",        "Vocalist"),
    ("Guitarist",               "Instrumentalist"),
    ("Music Video Director",    "Director"),
    ("Artwork",                 "Designer"),
    ("Arranger",                "Arranger"),
    ("Programmer",              "Programmer"),
]


def run_normalizer_comparison(backend_normalizer) -> int:
    """
    Test our normalize_role() against expected values and (optionally) the
    backend copy's RoleNormalizer.

    Returns the number of failures.
    """
    from src.utils.role_normalizer import normalize_role, normalize_role_string

    _sep("SECTION 1 — Role normalization comparison")
    print(f"  {'Raw role':<30} {'Ours canonical':<22} {'Expected':<22} {'Backend copy':<22} {'Status'}")
    print(f"  {'-'*30} {'-'*22} {'-'*22} {'-'*22} {'-'*6}")

    failures = 0
    for raw_role, expected in REFERENCE_ROLES:
        our_canonical, our_category = normalize_role(raw_role)
        our_norm_str = normalize_role_string(raw_role)

        # Backend copy comparison
        if backend_normalizer:
            bc_result = backend_normalizer.normalize(raw_role)
            bc_canonical = bc_result[0] if bc_result else "n/a"
        else:
            bc_canonical = "(not loaded)"

        # Pass/fail vs our expected
        if expected is None:
            # We expect a fallback — just check it's not a known canonical
            known_canonicals = {
                "Writer", "Producer", "Vocal Producer", "Engineer",
                "Mixing Engineer", "Mastering Engineer", "Artist",
                "Publisher", "Arranger", "Instrumentalist", "Vocalist",
                "Programmer", "Designer", "Director",
            }
            ok = our_canonical not in known_canonicals
            status = "OK(fb)" if ok else "FAIL"
        else:
            ok = our_canonical == expected
            status = "OK" if ok else "FAIL"

        if not ok:
            failures += 1

        exp_str = expected or "(fallback)"
        print(f"  {raw_role:<30} {our_canonical:<22} {exp_str:<22} {bc_canonical:<22} {status}")

    print(f"\n  Result: {len(REFERENCE_ROLES) - failures}/{len(REFERENCE_ROLES)} passed", end="")
    print(" ✓" if failures == 0 else f"  ({failures} failures)")
    return failures


# ---------------------------------------------------------------------------
# Section 2 — Live Genius API
# ---------------------------------------------------------------------------

def run_genius_api_test() -> Optional[Dict]:
    """
    Fetch credits for "Too Sweet" by Hozier from the live Genius API.
    Returns the credits dict, or None on failure.
    """
    _sep("SECTION 2 — Live Genius API (Too Sweet — Hozier)")
    from src.integrations.genius_client import GeniusClient

    if not GeniusClient.is_configured():
        print("  SKIPPED — GENIUS_ACCESS_TOKEN not configured.")
        return None

    genius = GeniusClient()
    print("  Fetching credits for 'Too Sweet' by Hozier...")
    result = genius.get_credits("Too Sweet", "Hozier")

    if result.get("source") != "genius":
        print(f"  FAILED — source={result.get('source')}, error={result.get('error')}")
        return None

    writers = result.get("writers", [])
    producers = result.get("producers", [])
    others = result.get("other_credits", [])
    print(f"  Genius song ID : {result.get('genius_song_id')}")
    print(f"  Writers        : {len(writers)}")
    for w in writers:
        print(f"    • {w}")
    print(f"  Producers      : {len(producers)}")
    for p in producers:
        print(f"    • {p}")
    print(f"  Other credits  : {len(others)}")
    for oc in others:
        print(f"    • [{oc.get('role')}] {oc.get('name')}")
    return result


# ---------------------------------------------------------------------------
# Section 3 — Pipeline simulation (no Supabase)
# ---------------------------------------------------------------------------

def simulate_pipeline(genius_result: Optional[Dict]) -> None:
    """
    Simulate _upsert_genius_credits() against the given Genius result and
    print what would be written to each Supabase table.

    If genius_result is None, uses the backend copy reference data
    (Too Sweet by Hozier) as a hard-coded mock.
    """
    from src.utils.role_normalizer import (
        canonical_credit_category,
        is_known_canonical,
        normalize_role,
        normalize_role_string,
    )
    from src.utils.name_normalizer import normalize_credit_name

    _sep("SECTION 3 — Pipeline simulation (no Supabase writes)")

    # Build mock tracks + song_id_map
    MOCK_TRACK_ID = "mock_too_sweet_spotify_id"
    MOCK_SONG_DB_ID = 99999  # fake DB primary key

    if genius_result and genius_result.get("source") == "genius":
        gc = genius_result
        print("  Using LIVE Genius result.")
    else:
        # Fall back to backend copy reference data (Too Sweet)
        gc = {
            "source": "genius",
            "genius_song_id": 5052,
            "writers": [
                "Stuart Johnson", "Peter Gonzales", "Tyler Reese",
                "Hozier", "Sergiu Gherman", "Bēkon",
            ],
            "producers": [
                "Peter Gonzales", "Hozier", "Sergiu Gherman",
                "Bēkon", "Chakra (Producer)",
            ],
            "other_credits": [
                {"name": "Hozier",           "role": "Vocals"},
                {"name": "Bēkon",            "role": "Background Vocals"},
                {"name": "Peter Gonzales",   "role": "Vocal Engineer"},
                {"name": "Greg Calbi",       "role": "Mastering Engineer"},
                {"name": "Steve Fallone",    "role": "Mastering Engineer"},
                {"name": "Andrew Scheps",    "role": "Mixing Engineer"},
                {"name": "Chakra (Producer)","role": "Engineer"},
                {"name": "Tyler Reese",      "role": "Engineer"},
                {"name": "Bēkon",            "role": "Strings"},
                {"name": "Bēkon",            "role": "Mellotron"},
                {"name": "Peter Gonzales",   "role": "Keyboards"},
                {"name": "Bēkon",            "role": "Keyboards"},
                {"name": "Peter Gonzales",   "role": "Percussion"},
                {"name": "Stuart Johnson",   "role": "Percussion"},
                {"name": "Peter Gonzales",   "role": "Bells"},
                {"name": "Peter Gonzales",   "role": "Drums"},
                {"name": "Chakra (Producer)","role": "Bass"},
                {"name": "Rubyworks Limited","role": "Label"},
            ],
        }
        print("  Using MOCK data (Too Sweet by Hozier — from backend copy reference).")

    mock_tracks = [{
        "track_id":   MOCK_TRACK_ID,
        "track_name": "Too Sweet",
        "artist":     "Hozier",
        "artists":    [{"id": "mock_hozier_spotify_id", "name": "Hozier", "url": ""}],
        "genius_credits": gc,
    }]
    song_id_map = {MOCK_TRACK_ID: MOCK_SONG_DB_ID}

    # ── Reproduce _upsert_genius_credits collection logic ─────────────────
    unique_credits: Dict[str, tuple] = {}
    raw_roles: Dict[str, tuple] = {}
    song_links: List[tuple] = []

    def _collect(name: str, raw_role: str, track_id: str) -> None:
        if not name or not raw_role or not track_id:
            return
        norm_name = normalize_credit_name(name)
        if not norm_name:
            return
        canonical, category = normalize_role(raw_role)
        if norm_name not in unique_credits:
            unique_credits[norm_name] = (name, canonical_credit_category(canonical))
        if raw_role not in raw_roles:
            raw_roles[raw_role] = (normalize_role_string(raw_role), canonical, category)
        song_links.append((track_id, norm_name, raw_role))

    for t in mock_tracks:
        g = t.get("genius_credits", {})
        if g.get("source") != "genius":
            continue
        tid = t.get("track_id", "")
        for writer in (g.get("writers") or []):
            _collect(writer, "Writer", tid)
        for producer in (g.get("producers") or []):
            _collect(producer, "Producer", tid)
        for oc in (g.get("other_credits") or []):
            _collect(oc.get("name", ""), oc.get("role", ""), tid)

    # ── Print simulated table writes ──────────────────────────────────────

    # Table 1: roles
    print("\n  ┌─ [roles] canonical role rows that would be ensured ─────────────")
    canonical_roles_needed: Dict[str, str] = {}
    for _, (_, canonical, category) in raw_roles.items():
        canonical_roles_needed[canonical] = category
    for canonical, category in sorted(canonical_roles_needed.items()):
        print(f"  │  role_name={canonical!r:<26}  category={category!r}")
    print(f"  └─ {len(canonical_roles_needed)} roles")

    # Table 2: raw_role_names
    print("\n  ┌─ [raw_role_names] raw Genius strings ───────────────────────────")
    print(f"  │  {'raw_role_name':<28} {'normalized_name':<28} {'→ canonical':<22} {'review?'}")
    print(f"  │  {'-'*28} {'-'*28} {'-'*22} {'-'*7}")
    for rr_name, (norm_raw, canonical, _) in sorted(raw_roles.items()):
        is_mapped = is_known_canonical(canonical)
        needs_review = not is_mapped
        print(f"  │  {rr_name:<28} {norm_raw:<28} {canonical:<22} {'yes' if needs_review else 'no'}")
    print(f"  └─ {len(raw_roles)} raw role rows")

    # Table 3: credits
    print("\n  ┌─ [credits] upsert by normalized_name ──────────────────────────")
    print(f"  │  {'name':<28} {'normalized_name':<28} {'credit_category'}")
    print(f"  │  {'-'*28} {'-'*28} {'-'*16}")
    for norm_name, (display_name, credit_cat) in sorted(unique_credits.items()):
        cat_str = credit_cat or "(None)"
        print(f"  │  {display_name:<28} {norm_name:<28} {cat_str}")
    print(f"  └─ {len(unique_credits)} credit rows")

    # Table 4: song_credits (deduplicated by (song_id, credit_id, role_id))
    print("\n  ┌─ [song_credits] junction rows ──────────────────────────────────")
    print(f"  │  {'person (norm_name)':<28} {'raw_role':<28} {'→ canonical'}")
    print(f"  │  {'-'*28} {'-'*28} {'-'*22}")
    seen_links: Set[tuple] = set()
    sc_rows_preview: List[tuple] = []
    for tid, norm_name, raw_role in song_links:
        canonical = raw_roles.get(raw_role, ("", "Unknown", "other"))[1]
        key = (tid, norm_name, canonical)  # deduplicate as (song, person, canonical_role)
        if key not in seen_links:
            seen_links.add(key)
            sc_rows_preview.append((norm_name, raw_role, canonical))
    for norm_name, raw_role, canonical in sorted(sc_rows_preview):
        print(f"  │  {norm_name:<28} {raw_role:<28} {canonical}")
    print(f"  └─ {len(sc_rows_preview)} song_credit rows for song_id={MOCK_SONG_DB_ID}")

    # Summary
    print(f"\n  Summary:")
    print(f"    Unique people       : {len(unique_credits)}")
    print(f"    Unique raw roles    : {len(raw_roles)}")
    print(f"    Canonical roles     : {len(canonical_roles_needed)}")
    print(f"    song_credit rows    : {len(sc_rows_preview)}")
    needs_review_count = sum(
        1 for _, (_, canonical, _) in raw_roles.items()
        if not is_known_canonical(canonical)
    )
    print(f"    Roles needing review: {needs_review_count} "
          f"(mapped={len(raw_roles) - needs_review_count})")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Dry run: Genius credits + role normalization")
    parser.add_argument("--skip-api", action="store_true",
                        help="Skip live Genius API call (offline role test only)")
    args = parser.parse_args()

    print("Genius Credits Dry Run")
    print("======================")

    # Section 1: role normalizer comparison (always runs)
    backend_normalizer = _load_backend_normalizer()
    if backend_normalizer:
        print("  Backend copy RoleNormalizer loaded — will compare side-by-side.")
    else:
        print("  Backend copy RoleNormalizer not found — skipping side-by-side comparison.")

    failures = run_normalizer_comparison(backend_normalizer)

    # Section 2: live Genius API
    genius_result = None
    if not args.skip_api:
        genius_result = run_genius_api_test()
    else:
        _sep("SECTION 2 — Live Genius API")
        print("  SKIPPED (--skip-api)")

    # Section 3: pipeline simulation
    simulate_pipeline(genius_result)

    _sep("DRY RUN COMPLETE")
    if failures:
        print(f"  WARNING: {failures} role normalization test(s) failed — review above.")
    else:
        print("  All role normalization tests passed.")
    print()


if __name__ == "__main__":
    main()
