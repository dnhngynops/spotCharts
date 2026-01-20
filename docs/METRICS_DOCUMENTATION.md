# Metrics Documentation

## Overview

The PDF reports display calculated metrics underneath the playlist title to provide quick insights about the playlist composition.

## Calculated Metrics

### Most Frequent Artists

**Calculation:**
- Counts how many tracks each artist appears in (considering multi-artist collaborations)
- Uses both the structured `artists` list format and fallback to comma-separated string format
- Handles tracks with multiple artists by counting each artist individually

**Display:**
- Shows the **top 3 most frequent artists** in the playlist
- Format: `"Most Frequent Artists: Artist Name 1 (count1), Artist Name 2 (count2), Artist Name 3 (count3)"`
- Example: `"Most Frequent Artists: Olivia Dean (3), Taylor Swift (2), Ella Langley (2)"`

**Location:**
- Displayed in the subtitle section, directly underneath the playlist title
- Visible in both HTML and PDF reports

**Implementation:**
- Calculated in `PDFGenerator._calculate_metrics()` method
- Uses Python's `Counter` from `collections` module for efficient counting
- Handles edge cases:
  - Tracks without artist data
  - Mixed artist formats (list vs string)
  - Empty or missing artist names

## Future Metrics (Potential Additions)

The metrics system is designed to be extensible. Potential future metrics could include:

- **Average Popularity**: Mean popularity score across all tracks
- **Most Popular Track**: Highest popularity score
- **Total Duration**: Sum of all track durations
- **Average Duration**: Mean track length
- **Genre Distribution**: If genre data becomes available
- **Explicit Content Count**: Number of explicit tracks
- **New Entries**: Tracks that weren't in previous week's report (requires historical tracking)

## Usage in Reports

The metrics are automatically calculated and displayed for each playlist PDF report. The metrics section appears between the playlist title and the data table, providing context before users dive into the track listing.
