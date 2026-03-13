import { createClient } from '@supabase/supabase-js'
import type { RunData, Track, Artist, Analytics, TopArtist, GenreStat, MultiChartTrack, DurationBucket, CollaborationPair, ReleaseMomentum, AlbumDominance } from './types'

const supabaseUrl     = import.meta.env.VITE_SUPABASE_URL     || ''
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || ''

export const isSupabaseConfigured = Boolean(supabaseUrl && supabaseAnonKey)

if (!isSupabaseConfigured) {
  console.warn(
    'Missing VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY. ' +
    'For local dev: add them to frontend/.env.local. ' +
    'For CI: add SUPABASE_URL and SUPABASE_ANON_KEY to GitHub Actions secrets.'
  )
}

// supabase is used for historical analytics queries (trend arrows, profile modals).
// The anon key is read-only and safe to bundle here — same posture as the current
// Jinja2 dashboard which bakes these values directly into the HTML.
export const supabase = createClient(supabaseUrl, supabaseAnonKey)

export async function fetchDashboardData(): Promise<RunData> {
  // 1. Latest completed scheduled scrape
  const { data: latestScrape, error: scrapeErr } = await supabase
    .from('playlist_scrapes')
    .select('scrape_id, scrape_date, notes')
    .eq('status', 'completed')
    .eq('scrape_type', 'scheduled')
    .order('scrape_id', { ascending: false })
    .limit(1)
    .single()

  if (scrapeErr) throw new Error(`Supabase scrape query failed: ${scrapeErr.message}`)
  if (!latestScrape) throw new Error('No completed scheduled scrapes found in Supabase — run the pipeline first')

  const runId = latestScrape.notes?.match(/run_id=(.+)/)?.[1]
    ?? String(latestScrape.scrape_id)

  // 2. All playlist_songs for this scrape with nested song + playlist + album
  const { data: rawRows, error: rowsErr } = await supabase
    .from('playlist_songs')
    .select(`
      position, song_id, playlist_id,
      songs!inner(
        song_id, spotify_id, title, popularity, explicit,
        duration_ms, preview_url, release_date, spotify_url, album_id,
        albums(album_id, name, spotify_id, spotify_url, image_url)
      ),
      playlists!inner(playlist_id, name, spotify_url, spotify_playlist_id)
    `)
    .eq('scrape_id', latestScrape.scrape_id)
    .order('position', { ascending: true })

  if (rowsErr) throw new Error(`Supabase playlist_songs query failed: ${rowsErr.message}`)
  if (!rawRows) throw new Error('No playlist song data returned for this scrape')

  const songIds = [...new Set(rawRows.map(r => r.song_id))]

  // 3. Fetch ALL credits for all songs (artists, producers, songwriters)
  //    Include role information to display credits as subtext in the tracks table
  const { data: allCreditRows } = await supabase
    .from('song_credits')
    .select('song_id, role_id, credits(credit_id, name, spotify_id, spotify_url, spotify_followers), roles(role_name)')
    .in('song_id', songIds)

  // 4. Genres for all songs
  const { data: genreRows } = await supabase
    .from('song_genres')
    .select('song_id, genres(genre_name)')
    .in('song_id', songIds)

  // 5. Build artist + credit lookup maps
  //    Separate artists (for primary display) from other credits (for subtext)
  const artistsBySongId: Record<number, Artist[]> = {}
  const seenCreditsBySongId: Record<number, Set<string>> = {}
  const followersBySongId: Record<number, number> = {}

  allCreditRows?.forEach(row => {
    const c = row.credits as unknown as Record<string, unknown> | null
    const r = row.roles as unknown as Record<string, unknown> | null
    if (!c) return

    const roleName = r?.['role_name'] as string | null

    // Deduplicate: skip if we've already added this credit for this song.
    // Supabase can return duplicate rows when the same song appears in multiple
    // playlists, causing the joined credit to repeat — resulting in
    // "Bad Bunny, Bad Bunny" etc. We key on credit_id (most precise), with
    // a fallback to spotify_id or name so any duplicate form is caught.
    const dedupKey = String(
      (c['credit_id'] as string | number | null)
        ?? c['spotify_id']
        ?? c['name']
        ?? '__unknown__'
    ) + ':' + (roleName ?? 'unknown')  // Include role in dedup key

    if (!seenCreditsBySongId[row.song_id]) seenCreditsBySongId[row.song_id] = new Set()
    if (seenCreditsBySongId[row.song_id].has(dedupKey)) return
    seenCreditsBySongId[row.song_id].add(dedupKey)

    if (!artistsBySongId[row.song_id]) artistsBySongId[row.song_id] = []
    artistsBySongId[row.song_id].push({
      name: c['name'] as string,
      id: (c['spotify_id'] as string | null) ?? undefined,
      url: (c['spotify_url'] as string | null) ?? undefined,
      role: roleName ?? undefined,
    })

    // Track followers only for primary artists
    if (roleName === 'Artist' && !followersBySongId[row.song_id] && c['spotify_followers']) {
      followersBySongId[row.song_id] = c['spotify_followers'] as number
    }
  })

  const genresBySongId: Record<number, string[]> = {}
  const seenGenresBySongId: Record<number, Set<string>> = {}
  genreRows?.forEach(row => {
    const g = row.genres as unknown as Record<string, unknown> | null
    if (!g?.['genre_name']) return
    const gName = g['genre_name'] as string
    if (!seenGenresBySongId[row.song_id]) seenGenresBySongId[row.song_id] = new Set()
    if (seenGenresBySongId[row.song_id].has(gName)) return
    seenGenresBySongId[row.song_id].add(gName)
    if (!genresBySongId[row.song_id]) genresBySongId[row.song_id] = []
    genresBySongId[row.song_id].push(gName)
  })

  // 6. Best (min) position per song across all playlists
  const minPosBySongId: Record<number, number> = {}
  rawRows.forEach(row => {
    if (minPosBySongId[row.song_id] === undefined || row.position < minPosBySongId[row.song_id]) {
      minPosBySongId[row.song_id] = row.position
    }
  })

  // 7. Build Track objects grouped by playlist; deduplicated all_tracks (best position wins)
  const tracksByPlaylist: Record<string, Track[]> = {}
  const playlistUrls: Record<string, string> = {}
  const allTracksMap: Record<number, Track> = {}

  for (const row of rawRows) {
    const song = row.songs as unknown as Record<string, unknown>
    const playlist = row.playlists as unknown as Record<string, unknown>
    const album = song['albums'] as Record<string, unknown> | null
    const allCredits = artistsBySongId[row.song_id] ?? []

    // Separate performing artists from other credits for display
    const performingArtists = allCredits.filter(a => a.role === 'Artist' || !a.role)
    const artist = performingArtists.map(a => a.name).join(', ') || 'Unknown Artist'

    const track: Track = {
      track_id: song['spotify_id'] as string,
      track_name: song['title'] as string,
      artist,
      artists: allCredits,  // Include ALL credits with role information
      album: (album?.['name'] as string) ?? '',
      album_id: (album?.['spotify_id'] as string) ?? undefined,
      album_image_url: (album?.['image_url'] as string) ?? undefined,
      album_url: (album?.['spotify_url'] as string) ?? undefined,
      spotify_url: (song['spotify_url'] as string) ?? undefined,
      preview_url: (song['preview_url'] as string) ?? undefined,
      playlist: playlist['name'] as string,
      playlist_id: (playlist['spotify_playlist_id'] as string) ?? undefined,
      position: row.position,
      popularity: (song['popularity'] as number) ?? 0,
      duration_ms: (song['duration_ms'] as number) ?? undefined,
      explicit: (song['explicit'] as boolean) ?? false,
      genres: genresBySongId[row.song_id] ?? [],
      rank: row.position,
      release_date: (song['release_date'] as string) ?? undefined,
      artist_followers: followersBySongId[row.song_id] ?? undefined,
      best_position: minPosBySongId[row.song_id],
    }

    const pName = playlist['name'] as string
    if (!tracksByPlaylist[pName]) tracksByPlaylist[pName] = []
    tracksByPlaylist[pName].push(track)
    playlistUrls[pName] = (playlist['spotify_url'] as string) ?? ''

    const existing = allTracksMap[row.song_id]
    if (!existing || row.position < existing.position) {
      allTracksMap[row.song_id] = track
    }
  }

  // Sort by best chart position, then assign a single sequential rank so the
  // "All Tracks" table shows 1, 2, 3… without repeats across playlists.
  const allTracks = Object.values(allTracksMap)
    .sort((a, b) => (a.best_position ?? 999) - (b.best_position ?? 999))
    .map((t, i) => ({ ...t, rank: i + 1 }))

  // 8. Compute analytics from assembled data
  const analytics = buildAnalytics(rawRows, allTracks, tracksByPlaylist, genresBySongId)

  return {
    generated_at: latestScrape.scrape_date ?? new Date().toISOString(),
    current_run_id: runId,
    analytics,
    tracks_by_playlist: tracksByPlaylist,
    all_tracks: allTracks,
    playlist_urls: playlistUrls,
  }
}

function buildAnalytics(
  rawRows: { song_id: number; position: number; songs: unknown; playlists: unknown }[],
  allTracks: Track[],
  tracksByPlaylist: Record<string, Track[]>,
  genresBySongId: Record<number, string[]>
): Analytics {
  const playlistNames = Object.keys(tracksByPlaylist)

  // summary
  const uniqueArtists = new Set(allTracks.map(t => t.artist)).size
  const summary = {
    total_tracks: rawRows.length,
    total_playlists: playlistNames.length,
    playlist_names: playlistNames,
    unique_tracks: allTracks.length,
    unique_artists: uniqueArtists,
  }

  // Pre-build spotify_id → rawRows lookup to avoid O(n²) in artist/overlap computations
  const spotifyIdToRows = new Map<string, typeof rawRows>()
  rawRows.forEach(r => {
    const id = (r.songs as Record<string, unknown>)['spotify_id'] as string
    if (!spotifyIdToRows.has(id)) spotifyIdToRows.set(id, [])
    spotifyIdToRows.get(id)!.push(r)
  })

  // top_artists: count total appearances per primary artist across all rawRows
  const artistMap: Record<string, { count: number; playlists: Set<string>; url: string; tracks: TopArtist['tracks'] }> = {}
  for (const track of allTracks) {
    const name = track.artists[0]?.name ?? track.artist
    if (!name || name === 'Unknown Artist') continue
    if (!artistMap[name]) {
      artistMap[name] = { count: 0, playlists: new Set(), url: track.artists[0]?.url ?? '', tracks: [] }
    }
    const appearances = spotifyIdToRows.get(track.track_id ?? '') ?? []
    artistMap[name].count += appearances.length
    appearances.forEach(r => artistMap[name].playlists.add((r.playlists as Record<string, unknown>)['name'] as string))
    if (artistMap[name].tracks.length < 10) {
      artistMap[name].tracks.push({
        track_name: track.track_name,
        playlist: track.playlist,
        spotify_url: track.spotify_url,
        popularity: track.popularity,
      })
    }
  }

  const topArtistList: TopArtist[] = Object.entries(artistMap)
    .map(([name, d]) => ({
      name,
      count: d.count,
      playlists: d.playlists.size,
      playlist_names: [...d.playlists],
      url: d.url,
      tracks: d.tracks,
      profile_key: name,
    }))
    .sort((a, b) => b.count - a.count)

  // multi_playlist_artists: artists with tracks in 2+ playlists
  const multiPlaylistArtists = topArtistList.filter(a => a.playlists >= 2)

  // chart_overlap: tracks in multiple playlists
  const songPlaylistCounts: Record<number, Set<string>> = {}
  rawRows.forEach(row => {
    const pName = (row.playlists as Record<string, unknown>)['name'] as string
    if (!songPlaylistCounts[row.song_id]) songPlaylistCounts[row.song_id] = new Set()
    songPlaylistCounts[row.song_id].add(pName)
  })

  const multiChartTracks: MultiChartTrack[] = allTracks
    .filter(t => {
      const rows = spotifyIdToRows.get(t.track_id ?? '')
      const sid = rows?.[0]?.song_id
      return sid !== undefined && (songPlaylistCounts[sid]?.size ?? 0) > 1
    })
    .map(t => {
      const rows = spotifyIdToRows.get(t.track_id ?? '') ?? []
      const sid = rows[0]!.song_id
      const appearances = rows.map(r => ({
        playlist: (r.playlists as Record<string, unknown>)['name'] as string,
        position: r.position,
      }))
      return {
        track_name: t.track_name,
        artist: t.artist,
        spotify_url: t.spotify_url,
        album_image: t.album_image_url,
        appearances,
        num_charts: songPlaylistCounts[sid]?.size ?? 1,
      }
    })
    .sort((a, b) => b.num_charts - a.num_charts)

  // usa_global_comparison: heuristic keyword match on playlist names
  const usaKw = ['hot 100', 'usa', 'united states', 'us chart']
  const globalKw = ['global', 'worldwide', 'world chart']
  const usaPlaylists = new Set(playlistNames.filter(n => usaKw.some(kw => n.toLowerCase().includes(kw))))
  const globalPlaylists = new Set(playlistNames.filter(n => globalKw.some(kw => n.toLowerCase().includes(kw))))

  const usaTrackIds = new Set<string | undefined>()
  const globalTrackIds = new Set<string | undefined>()
  usaPlaylists.forEach(p => tracksByPlaylist[p]?.forEach(t => usaTrackIds.add(t.track_id)))
  globalPlaylists.forEach(p => tracksByPlaylist[p]?.forEach(t => globalTrackIds.add(t.track_id)))

  const usa_only_tracks = allTracks.filter(t => usaTrackIds.has(t.track_id) && !globalTrackIds.has(t.track_id))
    .map(t => ({ track_name: t.track_name, artist: t.artist, spotify_url: t.spotify_url }))
  const both_tracks = allTracks.filter(t => usaTrackIds.has(t.track_id) && globalTrackIds.has(t.track_id))
    .map(t => ({ track_name: t.track_name, artist: t.artist, spotify_url: t.spotify_url }))
  const global_only_tracks = allTracks.filter(t => globalTrackIds.has(t.track_id) && !usaTrackIds.has(t.track_id))
    .map(t => ({ track_name: t.track_name, artist: t.artist, spotify_url: t.spotify_url }))

  // popularity_stats
  const popByPlaylist: Record<string, number[]> = {}
  rawRows.forEach(row => {
    const pName = (row.playlists as Record<string, unknown>)['name'] as string
    const pop = ((row.songs as Record<string, unknown>)['popularity'] as number) ?? 0
    if (!popByPlaylist[pName]) popByPlaylist[pName] = []
    popByPlaylist[pName].push(pop)
  })
  const allPops = rawRows.map(r => ((r.songs as Record<string, unknown>)['popularity'] as number) ?? 0)
  const avgOf = (arr: number[]) => arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0
  const minOf = (arr: number[]) => arr.length ? arr.reduce((m, p) => (p < m ? p : m), arr[0]) : 0
  const maxOf = (arr: number[]) => arr.length ? arr.reduce((m, p) => (p > m ? p : m), arr[0]) : 0
  const popularity_stats = {
    overall: { avg: Math.round(avgOf(allPops) * 10) / 10, min: minOf(allPops), max: maxOf(allPops) },
    by_playlist: Object.fromEntries(
      Object.entries(popByPlaylist).map(([p, arr]) => [p, {
        avg: Math.round(avgOf(arr) * 10) / 10,
        min: minOf(arr),
        max: maxOf(arr),
      }])
    ),
  }

  // explicit_stats
  const explicitByPlaylist: Record<string, { explicit: number; total: number }> = {}
  rawRows.forEach(row => {
    const pName = (row.playlists as Record<string, unknown>)['name'] as string
    const isExplicit = ((row.songs as Record<string, unknown>)['explicit'] as boolean) ?? false
    if (!explicitByPlaylist[pName]) explicitByPlaylist[pName] = { explicit: 0, total: 0 }
    explicitByPlaylist[pName].total++
    if (isExplicit) explicitByPlaylist[pName].explicit++
  })
  const totalExplicit = Object.values(explicitByPlaylist).reduce((acc, v) => acc + v.explicit, 0)
  const totalTracks = rawRows.length
  const explicit_stats = {
    total_explicit: totalExplicit,
    total_tracks: totalTracks,
    percentage: totalTracks ? Math.round((totalExplicit / totalTracks) * 1000) / 10 : 0,
    by_playlist: Object.fromEntries(
      Object.entries(explicitByPlaylist).map(([p, v]) => [p, {
        explicit: v.explicit,
        total: v.total,
        percentage: v.total ? Math.round((v.explicit / v.total) * 1000) / 10 : 0,
      }])
    ),
  }

  // genre_stats: count genre occurrences across all songs (using song_id → genres mapping)
  const genreCount: Record<string, { tracks: Set<string>; playlists: Set<string> }> = {}
  rawRows.forEach(row => {
    const genres = genresBySongId[row.song_id] ?? []
    const songSpotifyId = (row.songs as Record<string, unknown>)['spotify_id'] as string
    const pName = (row.playlists as Record<string, unknown>)['name'] as string
    genres.forEach(g => {
      if (!genreCount[g]) genreCount[g] = { tracks: new Set(), playlists: new Set() }
      genreCount[g].tracks.add(songSpotifyId)
      genreCount[g].playlists.add(pName)
    })
  })
  const topGenres: GenreStat[] = Object.entries(genreCount)
    .map(([name, d]) => ({
      name,
      count: d.tracks.size,
      playlists: d.playlists.size,
      tracks: allTracks
        .filter(t => t.genres?.includes(name))
        .slice(0, 10)
        .map(t => ({ track_name: t.track_name, artist: t.artist, playlist: t.playlist, spotify_url: t.spotify_url })),
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 50)

  // playlist_stats
  const playlist_stats: Analytics['playlist_stats'] = {}
  playlistNames.forEach(p => {
    const tracks = tracksByPlaylist[p] ?? []
    const explicit_count = tracks.filter(t => t.explicit).length
    const avg_popularity = tracks.length ? Math.round(avgOf(tracks.map(t => t.popularity)) * 10) / 10 : 0
    playlist_stats[p] = { track_count: tracks.length, explicit_count, avg_popularity }
  })

  // duration_analysis: group tracks by duration buckets
  const durationBuckets: DurationBucket[] = [
    { label: '< 2 min', min_ms: 0, max_ms: 120000, avg_popularity: 0, track_count: 0, tracks: [] },
    { label: '2-3 min', min_ms: 120000, max_ms: 180000, avg_popularity: 0, track_count: 0, tracks: [] },
    { label: '3-4 min', min_ms: 180000, max_ms: 240000, avg_popularity: 0, track_count: 0, tracks: [] },
    { label: '4-5 min', min_ms: 240000, max_ms: 300000, avg_popularity: 0, track_count: 0, tracks: [] },
    { label: '5+ min', min_ms: 300000, max_ms: Infinity, avg_popularity: 0, track_count: 0, tracks: [] },
  ]
  const tracksWithDuration = allTracks.filter(t => t.duration_ms != null && t.duration_ms > 0)
  tracksWithDuration.forEach(t => {
    const bucket = durationBuckets.find(b => t.duration_ms! >= b.min_ms && t.duration_ms! < b.max_ms)
    if (bucket) {
      bucket.track_count++
      bucket.tracks.push({ track_name: t.track_name, artist: t.artist, duration_ms: t.duration_ms, popularity: t.popularity, spotify_url: t.spotify_url })
    }
  })
  durationBuckets.forEach(b => {
    b.avg_popularity = b.tracks.length ? Math.round(avgOf(b.tracks.map(t => t.popularity)) * 10) / 10 : 0
    b.tracks = b.tracks.slice(0, 10)
  })

  // collaboration_network: identify top artist collaboration pairs
  const collaborationMap: Record<string, { count: number; pops: number[]; tracks: CollaborationPair['tracks'] }> = {}
  allTracks.forEach(t => {
    if (!t.artists || t.artists.length < 2) return
    const artistNames = t.artists.filter(a => a.role === 'Artist' || !a.role).map(a => a.name).filter(Boolean).sort()
    if (artistNames.length < 2) return
    for (let i = 0; i < artistNames.length - 1; i++) {
      for (let j = i + 1; j < artistNames.length; j++) {
        const key = `${artistNames[i]}|||${artistNames[j]}`
        if (!collaborationMap[key]) collaborationMap[key] = { count: 0, pops: [], tracks: [] }
        collaborationMap[key].count++
        collaborationMap[key].pops.push(t.popularity)
        if (collaborationMap[key].tracks.length < 10) {
          collaborationMap[key].tracks.push({ track_name: t.track_name, artists: t.artists, popularity: t.popularity, spotify_url: t.spotify_url })
        }
      }
    }
  })
  const collaboration_network: CollaborationPair[] = Object.entries(collaborationMap)
    .map(([key, d]) => {
      const [a1, a2] = key.split('|||')
      return {
        artist1: a1,
        artist2: a2,
        track_count: d.count,
        avg_popularity: d.pops.length ? Math.round(avgOf(d.pops) * 10) / 10 : 0,
        tracks: d.tracks,
      }
    })
    .filter(p => p.track_count >= 1)
    .sort((a, b) => b.track_count - a.track_count || b.avg_popularity - a.avg_popularity)
    .slice(0, 20)

  // release_momentum: group by release year
  const releaseYearMap: Record<number, { count: number; pops: number[]; tracks: ReleaseMomentum['tracks'] }> = {}
  allTracks.forEach(t => {
    if (!t.release_date) return
    const year = parseInt(t.release_date.split('-')[0], 10)
    if (isNaN(year) || year < 1900 || year > 2100) return
    if (!releaseYearMap[year]) releaseYearMap[year] = { count: 0, pops: [], tracks: [] }
    releaseYearMap[year].count++
    releaseYearMap[year].pops.push(t.popularity)
    if (releaseYearMap[year].tracks.length < 10) {
      releaseYearMap[year].tracks.push({ track_name: t.track_name, artist: t.artist, release_date: t.release_date, popularity: t.popularity, spotify_url: t.spotify_url })
    }
  })
  const release_momentum: ReleaseMomentum[] = Object.entries(releaseYearMap)
    .map(([yr, d]) => ({
      year: parseInt(yr, 10),
      track_count: d.count,
      avg_popularity: d.pops.length ? Math.round(avgOf(d.pops) * 10) / 10 : 0,
      tracks: d.tracks,
    }))
    .sort((a, b) => b.year - a.year)
    .slice(0, 15)

  // album_dominance: albums with most tracks charting
  const albumMap: Record<string, {
    album_id?: string;
    album_url?: string;
    album_image?: string;
    artist: string;
    playlists: Set<string>;
    pops: number[];
    tracks: AlbumDominance['tracks']
  }> = {}
  allTracks.forEach(t => {
    if (!t.album) return
    const key = t.album
    if (!albumMap[key]) {
      albumMap[key] = {
        album_id: t.album_id,
        album_url: t.album_url,
        album_image: t.album_image_url,
        artist: t.artist,
        playlists: new Set(),
        pops: [],
        tracks: [],
      }
    }
    const appearances = spotifyIdToRows.get(t.track_id ?? '') ?? []
    appearances.forEach(r => albumMap[key].playlists.add((r.playlists as Record<string, unknown>)['name'] as string))
    albumMap[key].pops.push(t.popularity)
    if (albumMap[key].tracks.length < 10) {
      albumMap[key].tracks.push({ track_name: t.track_name, position: t.position, playlist: t.playlist, popularity: t.popularity, spotify_url: t.spotify_url })
    }
  })
  const album_dominance: AlbumDominance[] = Object.entries(albumMap)
    .map(([album, d]) => ({
      album,
      album_id: d.album_id,
      album_url: d.album_url,
      album_image: d.album_image,
      artist: d.artist,
      track_count: d.tracks.length,
      playlist_count: d.playlists.size,
      playlists: [...d.playlists],
      avg_popularity: d.pops.length ? Math.round(avgOf(d.pops) * 10) / 10 : 0,
      tracks: d.tracks,
    }))
    .filter(a => a.track_count >= 2)
    .sort((a, b) => b.track_count - a.track_count || b.playlist_count - a.playlist_count)
    .slice(0, 20)

  return {
    summary,
    top_artists: topArtistList,
    multi_playlist_artists: multiPlaylistArtists,
    chart_overlap: {
      usa_global_comparison: {
        usa_only: usa_only_tracks.length,
        both: both_tracks.length,
        global_only: global_only_tracks.length,
        usa_total: usaPlaylists.size > 0 ? usaTrackIds.size : undefined,
        global_total: globalPlaylists.size > 0 ? globalTrackIds.size : undefined,
        usa_only_tracks,
        both_tracks,
        global_only_tracks,
      },
      multi_chart_tracks: multiChartTracks,
    },
    popularity_stats,
    explicit_stats,
    genre_stats: { total_unique_genres: Object.keys(genreCount).length, top_genres: topGenres },
    playlist_stats,
    duration_analysis: durationBuckets,
    collaboration_network,
    release_momentum,
    album_dominance,
  }
}
