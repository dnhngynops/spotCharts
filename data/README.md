# Data Directory

This directory stores persistent data for the Spotify Charts automation system.

## Contents

- **Database files**: SQLite database files (.db) for historical tracking
- **Snapshots**: JSON snapshots of weekly playlist data
- **Cache**: Cached API responses to reduce rate limit usage

## File Structure

```
data/
├── spotify_charts.db          # Main SQLite database (future)
├── snapshots/                 # Weekly playlist snapshots (future)
│   ├── 2024-01-01.json
│   ├── 2024-01-08.json
│   └── ...
└── cache/                     # Cached API responses (future)
    └── ...
```

## Notes

- This directory is gitignored to prevent committing sensitive or large data files
- Database files should be backed up regularly
- Old snapshots can be archived after a certain period
