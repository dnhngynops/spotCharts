import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import type { RunData, Track, TopArtist, GenreStat, Analytics } from '../../lib/types'
import { useTrendData } from '../../hooks/useTrendData'
import { fetchDashboardData } from '../../lib/supabaseClient'

import SummaryCards from './SummaryCards'
import PlaylistTabs, { toTabSlug } from './PlaylistTabs'
import TopArtistsList from './TopArtistsList'
import GenresList from './GenresList'
import ChartOverlap from './ChartOverlap'
import PopularityStats from './PopularityStats'
import ExplicitStats from './ExplicitStats'
import TracksTable from './TracksTable'
import { ArtistMomentum } from './ArtistMomentum'
import DurationAnalysis from './DurationAnalysis'
import CollaborationNetwork from './CollaborationNetwork'
import ReleaseMomentum from './ReleaseMomentum'
import AlbumDominance from './AlbumDominance'
import PlaylistPopularityStats from './PlaylistPopularityStats'

import styles from './ChartsView.module.css'

// ── Per-playlist analytics (computed from tracks_by_playlist in data.json) ───

interface PlaylistSummary {
  trackCount: number
  uniqueArtists: number
  avgPopularity: number
  uniqueGenres: number
  explicitCount: number
}

function computePlaylistSummary(tracks: Track[]): PlaylistSummary {
  const artists = new Set<string>()
  const genres = new Set<string>()
  let popSum = 0
  let popCount = 0
  let explicitCount = 0

  tracks.forEach(t => {
    t.artists?.forEach(a => { if (a.name) artists.add(a.name) })
    t.genres?.forEach(g => { if (g) genres.add(g) })
    if (t.popularity) { popSum += t.popularity; popCount++ }
    if (t.explicit) explicitCount++
  })

  return {
    trackCount: tracks.length,
    uniqueArtists: artists.size,
    avgPopularity: popCount ? popSum / popCount : 0,
    uniqueGenres: genres.size,
    explicitCount,
  }
}

interface PlaylistAnalytics {
  topArtists: TopArtist[]
  topGenres: GenreStat[]
  popularityStats: Analytics['popularity_stats']
  explicitStats: Analytics['explicit_stats']
}

function computePlaylistAnalytics(playlistName: string, tracks: Track[]): PlaylistAnalytics {
  // Top artists
  const artistMap: Record<string, { count: number; url: string; tracks: TopArtist['tracks']; profile_key: string }> = {}
  tracks.forEach(t => {
    t.artists?.forEach(a => {
      if (!a.name) return
      if (!artistMap[a.name]) {
        artistMap[a.name] = { count: 0, url: a.url || '', tracks: [], profile_key: a.id || '' }
      }
      artistMap[a.name].count++
      artistMap[a.name].tracks.push({ track_name: t.track_name, playlist: t.playlist, spotify_url: t.spotify_url, popularity: t.popularity })
    })
  })
  const topArtists: TopArtist[] = Object.entries(artistMap)
    .map(([name, d]) => ({ name, count: d.count, playlists: 1, playlist_names: [playlistName], url: d.url, tracks: d.tracks, profile_key: d.profile_key }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10)

  // Top genres
  const genreMap: Record<string, { count: number; tracks: GenreStat['tracks'] }> = {}
  tracks.forEach(t => {
    t.genres?.forEach(g => {
      if (!g) return
      if (!genreMap[g]) genreMap[g] = { count: 0, tracks: [] }
      genreMap[g].count++
      genreMap[g].tracks.push({ track_name: t.track_name, artist: t.artist, playlist: t.playlist, spotify_url: t.spotify_url })
    })
  })
  const topGenres: GenreStat[] = Object.entries(genreMap)
    .map(([name, d]) => ({ name, count: d.count, playlists: 1, tracks: d.tracks }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10)

  // Popularity stats
  const pops = tracks.map(t => t.popularity).filter(p => p > 0)
  const avg = pops.length ? pops.reduce((s, p) => s + p, 0) / pops.length : 0
  const min = pops.length ? Math.min(...pops) : 0
  const max = pops.length ? Math.max(...pops) : 0
  const popularityStats: Analytics['popularity_stats'] = {
    overall: { avg, min, max },
    by_playlist: { [playlistName]: { avg, min, max } },
  }

  // Explicit stats
  const explicit = tracks.filter(t => t.explicit).length
  const total = tracks.length
  const percentage = total ? (explicit / total) * 100 : 0
  const explicitStats: Analytics['explicit_stats'] = {
    total_explicit: explicit,
    total_tracks: total,
    percentage,
    by_playlist: { [playlistName]: { explicit, total, percentage } },
  }

  return { topArtists, topGenres, popularityStats, explicitStats }
}

function buildSummaryCards(
  activeTab: string,
  data: RunData,
  playlistSummaries: Record<string, PlaylistSummary>
) {
  if (activeTab === 'all-tracks') {
    const a = data.analytics
    return [
      { label: 'Unique Tracks',    value: a.summary.unique_tracks },
      { label: 'Unique Artists',   value: a.summary.unique_artists },
      { label: 'Avg Popularity',   value: a.popularity_stats.overall.avg.toFixed(1) },
      { label: 'Unique Genres',    value: a.genre_stats.total_unique_genres },
      { label: 'Explicit Tracks',  value: a.explicit_stats.total_explicit },
    ]
  }

  // Per-playlist tab — look up precomputed summary
  const playlistName = Object.keys(data.tracks_by_playlist).find(
    n => toTabSlug(n) === activeTab
  )
  const s = playlistName ? playlistSummaries[playlistName] : null

  return [
    { label: 'Tracks',           value: s?.trackCount },
    { label: 'Unique Artists',   value: s?.uniqueArtists },
    { label: 'Avg Popularity',   value: s ? s.avgPopularity.toFixed(1) : undefined },
    { label: 'Unique Genres',    value: s?.uniqueGenres },
    { label: 'Explicit Tracks',  value: s?.explicitCount },
  ]
}

// ── Main component ────────────────────────────────────────────────────────────

export default function ChartsView() {
  const [activeTab, setActiveTab] = useState('all-tracks')

  const { data, isLoading, isError } = useQuery<RunData>({
    queryKey: ['runData'],
    queryFn: fetchDashboardData,
    staleTime: 1000 * 60 * 60,  // 1hr — pipeline runs at most once daily
  })

  // Collect all Spotify track IDs for trend data hook
  const allTrackIds = useMemo(() => {
    if (!data) return []
    return [...new Set(data.all_tracks.map(t => t.track_id).filter(Boolean) as string[])]
  }, [data])

  const { data: trendData, isLoading: trendLoading } = useTrendData(data?.current_run_id ?? '', allTrackIds)
  const trendMap = trendData ?? new Map()

  // Precompute per-playlist summaries
  const playlistSummaries = useMemo<Record<string, PlaylistSummary>>(() => {
    if (!data) return {}
    const result: Record<string, PlaylistSummary> = {}
    for (const [name, tracks] of Object.entries(data.tracks_by_playlist)) {
      result[name] = computePlaylistSummary(tracks)
    }
    return result
  }, [data])

  const playlistNames = data ? Object.keys(data.tracks_by_playlist) : []

  const followerMap = useMemo(() => {
    const map = new Map<string, number>()
    if (!data) return map
    data.all_tracks.forEach(track => {
      const primaryId = track.artists?.[0]?.id
      if (primaryId && track.artist_followers != null) {
        if (!map.has(primaryId)) map.set(primaryId, track.artist_followers)
      }
    })
    return map
  }, [data])

  // Resolve which playlist is active (for per-playlist tab)
  const activePlaylistName = useMemo(() => {
    if (!data || activeTab === 'all-tracks') return null
    return playlistNames.find(n => toTabSlug(n) === activeTab) ?? null
  }, [activeTab, data, playlistNames])

  const summaryCards = useMemo(() => {
    if (!data) return []
    return buildSummaryCards(activeTab, data, playlistSummaries)
  }, [activeTab, data, playlistSummaries])

  return (
    <div className={styles.container}>
      {/* Header */}
      <header className={styles.header}>
        <h1><span className={styles.accent}>Spotify</span> Charts Dashboard</h1>
        <p className={styles.subtitle}>Cross-Playlist Analytics &amp; Insights</p>
      </header>

      {isError && (
        <div className={styles.error}>Failed to load dashboard data.</div>
      )}

      {/* Summary cards (update per active tab) */}
      <SummaryCards cards={summaryCards} isLoading={isLoading} />

      {/* Tab bar */}
      {data && (
        <PlaylistTabs
          playlistNames={playlistNames}
          activeTab={activeTab}
          onTabChange={setActiveTab}
        />
      )}

      {/* All Tracks tab */}
      {data && activeTab === 'all-tracks' && (
        <div>
          {/* Analytics grid */}
          <div className={styles.analyticsGrid}>
            <TopArtistsList artists={data.analytics.top_artists} followerMap={followerMap} />
            <GenresList genres={data.analytics.genre_stats.top_genres} />
            <ChartOverlap
              chartOverlap={data.analytics.chart_overlap}
              playlistUrls={data.playlist_urls}
            />
          </div>

          {/* Artist Momentum */}
          <ArtistMomentum
            allTracks={data.all_tracks}
            trendData={trendMap}
            isLoading={trendLoading}
          />

          {/* Popularity + Explicit rows */}
          <div className={styles.statsRow}>
            <PopularityStats popularityStats={data.analytics.popularity_stats} playlistUrls={data.playlist_urls} />
            <ExplicitStats explicitStats={data.analytics.explicit_stats} playlistUrls={data.playlist_urls} />
          </div>

          {/* New Analytics Sections */}
          <DurationAnalysis durationAnalysis={data.analytics.duration_analysis} />
          <CollaborationNetwork collaborationNetwork={data.analytics.collaboration_network} />
          <ReleaseMomentum releaseMomentum={data.analytics.release_momentum} />
          <AlbumDominance albumDominance={data.analytics.album_dominance} />

          {/* All Tracks table */}
          <TracksTable
            tracks={data.all_tracks}
            playlistNames={playlistNames}
            trendData={trendMap}
            showPlaylistFilter
            title="All Tracks"
          />
        </div>
      )}

      {/* Per-playlist tabs */}
      {data && activePlaylistName && (() => {
        const plTracks = data.tracks_by_playlist[activePlaylistName] ?? []
        const plAnalytics = computePlaylistAnalytics(activePlaylistName, plTracks)
        return (
          <div>
            {/* Per-playlist analytics grid */}
            <div className={styles.analyticsGrid}>
              <TopArtistsList artists={plAnalytics.topArtists} title="Top Artists" />
              <GenresList genres={plAnalytics.topGenres} title="Top Genres" />
              <PlaylistPopularityStats tracks={plTracks} />
            </div>

            {/* Per-playlist explicit stats */}
            <ExplicitStats explicitStats={plAnalytics.explicitStats} playlistUrls={data.playlist_urls} />

            <TracksTable
              tracks={plTracks}
              playlistNames={[]}
              trendData={trendMap}
              showPlaylistFilter={false}
              title={activePlaylistName}
            />
          </div>
        )
      })()}

      {/* Footer */}
      {data && (
        <footer className={styles.footer}>
          <p>Generated on {data.generated_at}</p>
          <p>by Danh Nguyen</p>
        </footer>
      )}
    </div>
  )
}
