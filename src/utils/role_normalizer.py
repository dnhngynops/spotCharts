"""
Credit role normalizer — maps raw Genius role strings to canonical format.

Ported from backend copy/phases/phase2/role_normalizer.py.

Primary entry point: normalize_role(raw_role_string)

Returns (canonical_name, category) where canonical_name is one of the 14
known roles (Writer, Producer, Mixing Engineer, …) and category is one of
'creative', 'technical', 'performance', 'business', or 'other'.

Unrecognised roles return a title-cased safe name with category 'other' so
they are never dropped — just flagged for future review via raw_role_names.
"""

import re
from typing import Optional, Tuple

# ---------------------------------------------------------------------------
# Role mapping table
# canonical_name → ([input patterns…], role_category)
# All patterns are matched case-insensitively after stripping special chars.
# ---------------------------------------------------------------------------
_ROLE_MAPPINGS: dict = {
    'Writer': (
        [
            'writer', 'songwriter', 'composer', 'lyricist', 'co-writer', 'cowriter',
            'song writer', 'music writer', 'lyrics writer', 'song composer',
            'music composer', 'written by', 'written', 'wrote',
            'composed by', 'composed', 'lyrics by',
        ],
        'creative',
    ),
    'Producer': (
        [
            'producer', 'music producer', 'record producer', 'track producer',
            'song producer', 'executive producer', 'co-producer', 'coproducer',
            'co producer', 'produced by', 'producing', 'production',
            'additional production',
        ],
        'creative',
    ),
    'Vocal Producer': (
        [
            'vocal producer', 'vocals producer', 'vocal production',
            'vocals production', 'vocal prod', 'vocals prod',
        ],
        'creative',
    ),
    'Engineer': (
        [
            'engineer', 'recording engineer', 'audio engineer', 'sound engineer',
            'tracking engineer', 'recording', 'tracking', 'record engineer',
        ],
        'technical',
    ),
    'Mixing Engineer': (
        [
            'mixing engineer', 'mix engineer', 'mixer', 'mixing', 'mixed by',
            'mixed', 'audio mixing', 'sound mixing',
        ],
        'technical',
    ),
    'Mastering Engineer': (
        [
            'mastering engineer', 'master engineer', 'mastering', 'mastered by',
            'mastered', 'audio mastering', 'sound mastering',
        ],
        'technical',
    ),
    'Artist': (
        [
            'artist', 'performer', 'performing artist', 'main artist',
            'primary artist', 'featured artist', 'featured', 'feat', 'ft',
            'guest artist', 'guest',
        ],
        'performance',
    ),
    'Publisher': (
        [
            'publisher', 'music publisher', 'publishing', 'publishing company',
            'record label', 'label',
        ],
        'business',
    ),
    'Arranger': (
        [
            'arranger', 'arrangement', 'arranged by', 'arranged', 'arrangements',
        ],
        'creative',
    ),
    'Instrumentalist': (
        [
            'instrumentalist', 'musician', 'player', 'guitarist', 'bassist',
            'drummer', 'keyboardist', 'pianist', 'violinist', 'instrumental',
            'instruments',
            # Common instrument names found in Genius credits
            'bass', 'guitar', 'drums', 'piano', 'keyboards', 'keyboard',
            'strings', 'percussion', 'mellotron', 'horns', 'saxophone', 'sax',
            'harmonica', 'cello', 'violin', 'viola', 'harp', 'mandolin',
            'banjo', 'flute', 'trumpet', 'brass', 'bells', 'synthesizer',
            'synth', 'organ',
        ],
        'performance',
    ),
    'Vocalist': (
        [
            'vocalist', 'singer', 'lead vocal', 'lead vocals', 'vocals',
            'background vocal', 'backing vocal', 'background vocals',
            'backing vocals', 'bg vocals', 'harmony',
        ],
        'performance',
    ),
    'Programmer': (
        [
            'programmer', 'programming', 'programmed by', 'midi programmer',
            'drum programmer', 'synth programmer',
        ],
        'technical',
    ),
    'Designer': (
        [
            'designer', 'artwork', 'album art', 'cover art', 'visual design',
            'graphic design',
        ],
        'creative',
    ),
    'Director': (
        [
            'director', 'music video director', 'mv director', 'video director',
            'directed by',
        ],
        'creative',
    ),
}

# Map canonical role name → credits.credit_category CHECK constraint value.
# Roles not listed here get credit_category = None (NULL) which is allowed.
_CREDIT_CATEGORY_MAP: dict = {
    'Writer': 'writer',
    'Producer': 'producer',
    'Vocal Producer': 'producer',
    'Engineer': 'engineer',
    'Mixing Engineer': 'engineer',
    'Mastering Engineer': 'engineer',
    'Artist': 'artist',
    'Publisher': 'publisher_rep',
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _norm(text: str) -> str:
    """Lowercase, remove special chars, collapse whitespace."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip()


def _build_pattern_map() -> dict:
    """Build a normalised-pattern → (canonical_name, category) lookup dict."""
    result: dict = {}
    for canonical, (patterns, category) in _ROLE_MAPPINGS.items():
        for pattern in patterns:
            norm_pattern = _norm(pattern)
            if norm_pattern not in result:
                result[norm_pattern] = (canonical, category)
    return result


_PATTERN_MAP: dict = _build_pattern_map()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def normalize_role(raw_role: str) -> Tuple[str, str]:
    """
    Map a raw Genius role string to (canonical_name, category).

    Tries exact match, then contains/substring match.
    Falls back to a title-cased safe name with category='other' so unrecognised
    roles are recorded but never silently dropped.

    Args:
        raw_role: Raw role string from Genius (e.g. 'Mixing Engineer',
                  'Background Vocals', 'writer').

    Returns:
        (canonical_name, category) — both are non-empty strings.
    """
    if not raw_role:
        return ('Unknown', 'other')

    ni = _norm(raw_role)
    if not ni:
        return ('Unknown', 'other')

    # Exact match
    if ni in _PATTERN_MAP:
        return _PATTERN_MAP[ni]

    # Partial / substring match
    for pattern, result in _PATTERN_MAP.items():
        if pattern in ni or ni in pattern:
            return result

    # No match — sanitise to title case; flag for future review
    return (ni.title(), 'other')


def normalize_role_string(raw_role: str) -> str:
    """
    Return the normalised string form of a raw role name.

    Used for raw_role_names.normalized_name (the dedup / lookup key stored
    alongside the raw string in the role-normalisation pipeline tables).

    Args:
        raw_role: Raw role string from Genius.

    Returns:
        Lowercase, no-special-chars, whitespace-collapsed string.
    """
    return _norm(raw_role) if raw_role else ''


def canonical_credit_category(canonical_role: str) -> Optional[str]:
    """
    Return the credits.credit_category value for a canonical role, or None.

    None is allowed by the schema CHECK constraint and is preferable to
    an invalid value.
    """
    return _CREDIT_CATEGORY_MAP.get(canonical_role)


def is_known_canonical(name: str) -> bool:
    """Return True when name is one of the 14 known canonical role names."""
    return name in _ROLE_MAPPINGS
