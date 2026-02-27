"""
Name Normalization Utility
==========================
Centralized name normalization for deduplication and consistent DB storage.

Two distinct normalization levels:
- normalize_name()        — lightweight; used for comparison and song titles
- normalize_credit_name() — full cleaning; used for credit/company DB keys (normalized_name column)
"""

import re
from typing import List, Optional


def normalize_name(name: str) -> str:
    """
    Normalize a name for comparison and matching.

    Steps:
    1. Lowercase
    2. Strip leading/trailing whitespace
    3. Collapse multiple spaces to a single space

    Examples:
        >>> normalize_name("  Kanye West  ")
        'kanye west'
        >>> normalize_name("Kanye   West")
        'kanye west'
        >>> normalize_name("Jay-Z")
        'jay-z'
    """
    if not name:
        return ""
    normalized = name.lower().strip()
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized


def normalize_credit_name(name: str) -> str:
    """
    Normalize a credit name (artist, producer, writer, company) for DB storage.

    Used for the normalized_name column in credits and companies — must be
    consistent and unique-safe across scraped and API-sourced data.

    Removes decorative punctuation to prevent duplicates:
      - Double quotes (straight + smart): "Nat "King" Cole" → "nat king cole"
      - Smart single quotes: "D\u2018Angelo" → strip (but straight apostrophes preserved)
      - Parentheses/brackets: "Nat (King) Cole" → "nat king cole"
      - Periods: "A.B.C." → "abc"
      - Exclamation marks: "Wham!" → "wham"
      - Question marks

    Preserves meaningful characters:
      - Hyphens: "Jay-Z" → "jay-z"
      - Straight apostrophes: "D'Angelo" → "d'angelo"
      - Ampersands: "Hall & Oates" → "hall & oates"

    Final form uses '+' as the space separator (URL/key-safe).

    Examples:
        >>> normalize_credit_name("Wham!")
        'wham'
        >>> normalize_credit_name("A.B.C.")
        'abc'
        >>> normalize_credit_name('Nat "King" Cole')
        'nat+king+cole'
        >>> normalize_credit_name("Nat (King) Cole")
        'nat+king+cole'
        >>> normalize_credit_name("D'Angelo")
        "d'angelo"
    """
    if not name:
        return ""

    normalized = name.lower().strip()

    # Remove straight double quotes
    normalized = normalized.replace('"', '')
    # Remove smart double quotes
    normalized = normalized.replace('\u201c', '').replace('\u201d', '')

    # Remove smart single quotes (used as decorative quote marks, not apostrophes)
    # Preserve straight apostrophes (') — part of names like "D'Angelo", "O'Connor"
    normalized = normalized.replace('\u2018', '').replace('\u2019', '')

    # Remove parentheses and brackets
    normalized = re.sub(r'[(\[\])]', ' ', normalized)

    # Remove periods (common in initials like "A.B.C.")
    normalized = normalized.replace('.', '')

    # Remove exclamation marks (e.g., "Wham!")
    normalized = normalized.replace('!', '')

    # Remove question marks
    normalized = normalized.replace('?', '')

    # Collapse whitespace, then replace spaces with '+' for key-safe storage
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    normalized = normalized.replace(' ', '+')

    return normalized


def normalize_song_title(title: str) -> str:
    """
    Normalize a song title for matching and search.

    Same as normalize_name — kept separate to allow future title-specific
    handling (e.g., stripping "(feat. ...)" suffixes, remix labels).
    Does NOT apply '+' substitution; result is for comparison, not a DB key.
    """
    return normalize_name(title)


def are_names_similar(name1: str, name2: str, threshold: float = 0.9) -> bool:
    """
    Check if two names are similar after normalization.

    Currently uses exact match after normalize_name. The threshold parameter
    is reserved for a future upgrade to Levenshtein / Jaro-Winkler scoring.

    Args:
        name1: First name
        name2: Second name
        threshold: Reserved similarity threshold (0.0–1.0)

    Returns:
        True if names match after normalization
    """
    return normalize_name(name1) == normalize_name(name2)


def extract_artist_from_feature(artist_string: str) -> List[str]:
    """
    Split a combined artist string into individual normalized artist names.

    Handles common patterns:
        "Drake feat. 21 Savage"        → ['drake', '21 savage']
        "SZA & Kendrick Lamar"         → ['sza', 'kendrick lamar']
        "Artist A, Artist B, Artist C" — commas NOT split (Tyler, The Creator)
        "Kendrick Lamar featuring"     → ['kendrick lamar']  (trailing sep stripped)

    Note: Comma-separated lists are intentionally not split here because commas
    are part of some artist names (e.g., "Tyler, The Creator"). Callers that
    know the context is a list (e.g., Billboard ingestion) should handle
    comma-splitting separately.

    Args:
        artist_string: Raw combined artist string from scraping or API

    Returns:
        List of normalized artist name strings
    """
    if not artist_string:
        return []

    normalized = normalize_name(artist_string)

    # Strip trailing separator keywords left over after known-band extraction
    trailing_patterns = [
        r'\s+feat\.?$',
        r'\s+ft\.?$',
        r'\s+featuring$',
        r'\s+&$',
        r'\s+and$',
    ]
    for pattern in trailing_patterns:
        normalized = re.sub(pattern, '', normalized)

    # Split on common feature/collaboration separators
    separators = [
        r'\s+feat\.?\s+',
        r'\s+ft\.?\s+',
        r'\s+featuring\s+',
        r'\s+&\s+',
        r'\s+and\s+',
    ]

    artists = [normalized]
    for sep in separators:
        new_artists = []
        for artist in artists:
            new_artists.extend(re.split(sep, artist))
        artists = new_artists

    return [normalize_name(a) for a in artists if a.strip()]
