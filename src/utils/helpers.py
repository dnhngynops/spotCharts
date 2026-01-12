"""
Utility Helper Functions

Common helper functions used across the application
"""

from datetime import datetime
from typing import List, Dict, Any


def format_duration(ms: int) -> str:
    """
    Convert milliseconds to MM:SS format

    Args:
        ms: Duration in milliseconds

    Returns:
        Formatted duration string (MM:SS)
    """
    seconds = ms // 1000
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes}:{seconds:02d}"


def deduplicate_tracks(tracks: List[Dict], key: str = 'track_id') -> List[Dict]:
    """
    Remove duplicate tracks from list

    Args:
        tracks: List of track dictionaries
        key: Key to use for deduplication

    Returns:
        List with duplicates removed
    """
    seen = set()
    unique_tracks = []
    for track in tracks:
        if track.get(key) not in seen:
            seen.add(track.get(key))
            unique_tracks.append(track)
    return unique_tracks


def get_timestamp(format: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    Get current timestamp as formatted string

    Args:
        format: strftime format string

    Returns:
        Formatted timestamp string
    """
    return datetime.now().strftime(format)


def safe_get(dictionary: Dict, keys: List[str], default: Any = None) -> Any:
    """
    Safely get nested dictionary value

    Args:
        dictionary: Dictionary to search
        keys: List of nested keys
        default: Default value if key not found

    Returns:
        Value if found, else default
    """
    for key in keys:
        if isinstance(dictionary, dict):
            dictionary = dictionary.get(key, default)
        else:
            return default
    return dictionary
