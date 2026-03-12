/** Mirrors the track dicts produced by the Python pipeline. */
export interface Artist {
  name: string
  id?: string
  url?: string
  role?: string
}

export interface Track {
  track_id?: string
  track_name: string
  artist: string
  artists: Artist[]
  album: string
  album_id?: string
  album_image_url?: string
  album_url?: string
  spotify_url?: string
  preview_url?: string
  playlist: string
  playlist_id?: string
  position: number
  popularity: number
  duration_ms?: number
  explicit: boolean
  genres?: string[]
  rank?: number
  release_date?: string
  artist_followers?: number
  best_position?: number
}

export interface TopArtist {
  name: string
  count: number
  playlists: number
  playlist_names: string[]
  url: string
  tracks: Pick<Track, 'track_name' | 'playlist' | 'spotify_url' | 'popularity'>[]
  profile_key: string
}

export interface GenreStat {
  name: string
  count: number
  playlists: number
  tracks: Pick<Track, 'track_name' | 'artist' | 'playlist' | 'spotify_url'>[]
}

export interface OverlapTrack {
  track_name: string
  artist: string
  spotify_url?: string
  position?: number
}

export interface MultiChartTrack {
  track_name: string
  artist: string
  spotify_url?: string
  album_image?: string
  appearances: { playlist: string; position: number }[]
  num_charts: number
}

export interface DurationBucket {
  label: string
  min_ms: number
  max_ms: number
  avg_popularity: number
  track_count: number
  tracks: Pick<Track, 'track_name' | 'artist' | 'duration_ms' | 'popularity' | 'spotify_url'>[]
}

export interface CollaborationPair {
  artist1: string
  artist2: string
  track_count: number
  avg_popularity: number
  tracks: Pick<Track, 'track_name' | 'artists' | 'popularity' | 'spotify_url'>[]
}

export interface ReleaseMomentum {
  year: number
  track_count: number
  avg_popularity: number
  tracks: Pick<Track, 'track_name' | 'artist' | 'release_date' | 'popularity' | 'spotify_url'>[]
}

export interface AlbumDominance {
  album: string
  album_id?: string
  album_url?: string
  album_image?: string
  artist: string
  track_count: number
  playlist_count: number
  playlists: string[]
  avg_popularity: number
  tracks: Pick<Track, 'track_name' | 'position' | 'playlist' | 'popularity' | 'spotify_url'>[]
}

export interface Analytics {
  summary: {
    total_tracks: number
    total_playlists: number
    playlist_names: string[]
    unique_tracks: number
    unique_artists: number
  }
  top_artists: TopArtist[]
  multi_playlist_artists: TopArtist[]
  chart_overlap: {
    usa_global_comparison: {
      usa_only: number
      both: number
      global_only: number
      usa_total?: number
      global_total?: number
      usa_only_tracks: OverlapTrack[]
      both_tracks: OverlapTrack[]
      global_only_tracks: OverlapTrack[]
    }
    multi_chart_tracks: MultiChartTrack[]
  }
  popularity_stats: {
    overall: { avg: number; min: number; max: number }
    by_playlist: Record<string, { avg: number; min: number; max: number }>
  }
  explicit_stats: {
    total_explicit: number
    total_tracks?: number
    percentage?: number
    by_playlist: Record<string, { explicit: number; total: number; percentage: number }>
  }
  genre_stats: {
    total_unique_genres: number
    top_genres: GenreStat[]
  }
  playlist_stats: Record<string, {
    track_count?: number
    explicit_count?: number
    avg_popularity?: number
  }>
  duration_analysis: DurationBucket[]
  collaboration_network: CollaborationPair[]
  release_momentum: ReleaseMomentum[]
  album_dominance: AlbumDominance[]
}

/** Shape of frontend/public/data.json written by the Python pipeline. */
export interface RunData {
  generated_at: string
  current_run_id: string
  analytics: Analytics
  tracks_by_playlist: Record<string, Track[]>
  all_tracks: Track[]
  playlist_urls: Record<string, string>
}

// ── Profile modal types (fetched on-demand from Supabase) ────────────────────

export interface ArtistTrack {
  track_name: string
  track_id: string
  playlist: string
  position: number
  popularity: number
  explicit: boolean
  spotify_url: string
  preview_url: string
  album: string
  album_url: string
  album_image: string
}

export interface ArtistProfile {
  name: string
  id: string
  url: string
  image: string
  followers: number
  genres: string[]
  chart_count: number
  playlist_names: string[]
  track_appearances: number
  tracks: ArtistTrack[]
  avg_track_popularity: number
  explicit_count: number
}

export interface AlbumTrackInfo {
  track_name: string
  track_number: number
  duration_ms: number
  explicit: boolean
  spotify_url: string
  is_charting: boolean
  chart_positions: { playlist: string; position: number }[]
  preview_url: string
  popularity: number
}

export interface TrackProfile {
  track_name: string
  track_id: string
  artist: string
  artists: { name: string; id?: string }[]
  album: string
  album_id: string
  album_url: string
  album_image: string
  release_date: string
  duration_ms: number
  explicit: boolean
  popularity: number
  genres: string[]
  spotify_url: string
  preview_url: string
  chart_positions: { playlist: string; position: number }[]
  best_position: number
  charts_count: number
  _all_tracks_for_album: AlbumTrackInfo[]
}

export interface ChartingTrack {
  track_name: string
  track_id: string
  playlist: string
  position: number
  popularity: number
  explicit: boolean
  spotify_url: string
  preview_url: string
}

export interface AlbumProfile {
  album: string
  album_id: string
  album_url: string
  album_image: string
  artist: string
  release_date: string
  album_type: string
  total_tracks: number
  charting_tracks: ChartingTrack[]
  charting_track_count: number
  playlists_reached: string[]
  avg_popularity: number
  all_tracks: (AlbumTrackInfo & { track_id?: string })[]
}

export type TrendInfo = {
  badge: 'new' | 'up' | 'down' | 'same'
  delta: number
  weeksOnChart: number
  peakPos: number
}
