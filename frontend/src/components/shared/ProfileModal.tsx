import { useEffect, useRef, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { supabase, fetchDashboardData } from '../../lib/supabaseClient'
import { useModal } from '../../contexts/ModalContext'
import type {
  ArtistProfile,
  TrackProfile,
  AlbumProfile,
  ArtistTrack,
  AlbumTrackInfo,
  RunData,
} from '../../lib/types'
import styles from './ProfileModal.module.css'

// ── Supabase fetch helpers (1:1 port from profile_modal.html) ────────────────

async function getScrapeId(): Promise<{ db: typeof supabase; scrapeId: number } | null> {
  const { data: runs, error } = await supabase
    .from('playlist_scrapes')
    .select('scrape_id, scrape_date, notes')
    .eq('status', 'completed')
    .eq('scrape_type', 'scheduled')
    .order('scrape_date', { ascending: false })
    .limit(1)
  if (error || !runs || runs.length === 0) return null
  return { db: supabase, scrapeId: runs[0].scrape_id }
}

async function fetchArtistProfile(spotifyId: string): Promise<ArtistProfile | null> {
  const ctx = await getScrapeId()
  if (!ctx) return null
  const { db, scrapeId } = ctx

  const { data: credit, error: e1 } = await db
    .from('credits')
    .select('credit_id, name, spotify_id, spotify_image_url, spotify_followers, credit_genres(genres(genre_name)), song_credits(song_id)')
    .eq('spotify_id', spotifyId)
    .single()
  if (e1 || !credit) return null

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const songIds = ((credit.song_credits as any[]) || []).map((sc: any) => sc.song_id)
  let playlistSongs: unknown[] = []
  if (songIds.length > 0) {
    const { data: ps } = await db
      .from('playlist_songs')
      .select('song_id, position, playlists(name), songs(spotify_id, title, popularity, explicit, preview_url, spotify_url, albums(name, spotify_url, image_url))')
      .in('song_id', songIds)
      .eq('scrape_id', scrapeId)
    playlistSongs = ps || []
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const playlists = [...new Set((playlistSongs as any[]).map(ps => ps.playlists?.name).filter(Boolean))]
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const tracks: ArtistTrack[] = (playlistSongs as any[]).map(ps => ({
    track_name:  ps.songs?.title        || '',
    track_id:    ps.songs?.spotify_id   || '',
    playlist:    ps.playlists?.name     || '',
    position:    ps.position             || 0,
    popularity:  ps.songs?.popularity   || 0,
    explicit:    ps.songs?.explicit      || false,
    spotify_url: ps.songs?.spotify_url  || '',
    preview_url: ps.songs?.preview_url  || '',
    album:       ps.songs?.albums?.name       || '',
    album_url:   ps.songs?.albums?.spotify_url || '',
    album_image: ps.songs?.albums?.image_url  || '',
  }))

  return {
    name:     credit.name,
    id:       credit.spotify_id,
    url:      `https://open.spotify.com/artist/${credit.spotify_id}`,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    image:    (credit as any).spotify_image_url || '',
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    followers: (credit as any).spotify_followers || 0,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    genres: ((credit.credit_genres as any[]) || []).map((g: any) => g.genres?.genre_name).filter(Boolean).sort(),
    chart_count: playlists.length,
    playlist_names: (playlists as string[]).sort(),
    track_appearances: tracks.length,
    tracks: tracks.sort((a, b) => (a.playlist > b.playlist ? 1 : a.playlist < b.playlist ? -1 : 0) || a.position - b.position),
    avg_track_popularity: tracks.length ? tracks.reduce((s, t) => s + t.popularity, 0) / tracks.length : 0,
    explicit_count: tracks.filter(t => t.explicit).length,
  }
}

async function fetchTrackProfile(spotifyId: string): Promise<TrackProfile | null> {
  const ctx = await getScrapeId()
  if (!ctx) return null
  const { db, scrapeId } = ctx

  const { data: song, error: e1 } = await db
    .from('songs')
    .select('song_id, spotify_id, title, explicit, popularity, preview_url, spotify_url, release_date, duration_ms, albums(album_id, spotify_id, name, image_url, spotify_url, album_type, total_tracks, all_tracks), song_genres(genres(genre_name)), song_credits(credits(name, spotify_id))')
    .eq('spotify_id', spotifyId)
    .single()
  if (e1 || !song) return null

  let chartPositions: { playlist: string; position: number }[] = []
  const { data: pos } = await db
    .from('playlist_songs')
    .select('position, playlists(name)')
    .eq('song_id', song.song_id)
    .eq('scrape_id', scrapeId)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  chartPositions = ((pos || []) as any[]).map(p => ({
    playlist: p.playlists?.name || '',
    position: p.position,
  })).sort((a, b) => a.position - b.position)

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const album = (song.albums as any) || {}
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const artistCredits = ((song.song_credits as any[]) || []).map((sc: any) => sc.credits).filter(Boolean)
  const primaryArtist = artistCredits[0]?.name || ''

  const rawAllTracks = album.all_tracks || []
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const processedAllTracks: AlbumTrackInfo[] = rawAllTracks.map((t: any) => ({
    track_name:      t.name         || '',
    track_number:    t.track_number || 0,
    duration_ms:     t.duration_ms  || 0,
    explicit:        t.explicit      || false,
    spotify_url:     t.spotify_url  || '',
    is_charting:     t.id === spotifyId,
    chart_positions: t.id === spotifyId ? chartPositions : [],
    preview_url:     '',
    popularity:      t.popularity   || 0,
  }))

  return {
    track_name:   song.title,
    track_id:     song.spotify_id,
    artist:       primaryArtist,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    artists:      artistCredits.map((c: any) => ({ name: c.name, id: c.spotify_id })),
    album:        album.name        || '',
    album_id:     album.spotify_id  || '',
    album_url:    album.spotify_url || '',
    album_image:  album.image_url   || '',
    release_date: song.release_date || '',
    duration_ms:  song.duration_ms  || 0,
    explicit:     song.explicit      || false,
    popularity:   song.popularity    || 0,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    genres:       ((song.song_genres as any[]) || []).map((g: any) => g.genres?.genre_name).filter(Boolean).sort(),
    spotify_url:  song.spotify_url   || '',
    preview_url:  song.preview_url   || '',
    chart_positions: chartPositions,
    best_position:   chartPositions.length ? Math.min(...chartPositions.map(p => p.position)) : 0,
    charts_count:    new Set(chartPositions.map(p => p.playlist)).size,
    _all_tracks_for_album: processedAllTracks,
  }
}

async function fetchAlbumProfile(spotifyId: string): Promise<AlbumProfile | null> {
  const ctx = await getScrapeId()
  if (!ctx) return null
  const { db, scrapeId } = ctx

  const { data: album, error: e1 } = await db
    .from('albums')
    .select('album_id, spotify_id, name, image_url, spotify_url, album_type, total_tracks, all_tracks, release_date')
    .eq('spotify_id', spotifyId)
    .single()
  if (e1 || !album) return null

  const { data: albumSongs } = await db
    .from('songs')
    .select('song_id, spotify_id')
    .eq('album_id', album.album_id)
  const albumSongIds = ((albumSongs || []) as { song_id: number; spotify_id: string }[]).map(s => s.song_id)

  let chartSongs: unknown[] = []
  if (albumSongIds.length > 0) {
    const { data: cs } = await db
      .from('playlist_songs')
      .select('song_id, position, playlists(name), songs(spotify_id, title, popularity, explicit, preview_url, spotify_url)')
      .in('song_id', albumSongIds)
      .eq('scrape_id', scrapeId)
    chartSongs = cs || []
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const chartingByTrackId: Record<string, { playlist: string; position: number }[]> = {}
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  ;(chartSongs as any[]).forEach(cs => {
    const tid = cs.songs?.spotify_id
    if (!tid) return
    if (!chartingByTrackId[tid]) chartingByTrackId[tid] = []
    chartingByTrackId[tid].push({ playlist: cs.playlists?.name || '', position: cs.position })
  })
  const chartingTrackIds = new Set(Object.keys(chartingByTrackId))

  const rawAllTracks = (album as { all_tracks?: unknown[] }).all_tracks || []
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const allTracksInfo = (rawAllTracks as any[])
    .map(t => ({
      track_name:      t.name         || '',
      track_id:        t.id            || '',
      track_number:    t.track_number  || 0,
      duration_ms:     t.duration_ms   || 0,
      popularity:      t.popularity    || 0,
      explicit:        t.explicit       || false,
      spotify_url:     t.spotify_url   || '',
      is_charting:     chartingTrackIds.has(t.id || ''),
      chart_positions: chartingByTrackId[t.id] || [],
      preview_url:     '',
    }))
    .sort((a, b) => a.track_number - b.track_number)

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const chartingTrackList = (chartSongs as any[]).map(cs => ({
    track_name:  cs.songs?.title       || '',
    track_id:    cs.songs?.spotify_id  || '',
    playlist:    cs.playlists?.name    || '',
    position:    cs.position            || 0,
    popularity:  cs.songs?.popularity  || 0,
    explicit:    cs.songs?.explicit     || false,
    spotify_url: cs.songs?.spotify_url || '',
    preview_url: cs.songs?.preview_url || '',
  })).sort((a, b) =>
    (a.playlist > b.playlist ? 1 : a.playlist < b.playlist ? -1 : 0) || a.position - b.position
  )

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const playlists = [...new Set((chartSongs as any[]).map(cs => cs.playlists?.name).filter(Boolean))]

  const tracksForAvg = rawAllTracks.length > 0 ? rawAllTracks : chartingTrackList
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const pops = (tracksForAvg as any[]).map(t => t.popularity).filter((v: number) => v > 0)
  const avgPopularity = pops.length ? pops.reduce((a: number, b: number) => a + b, 0) / pops.length : 0

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const primaryArtist = (rawAllTracks as any[])[0]?.artist || ''

  const seenIds = new Set<string>()
  const uniqueCharting = chartingTrackList.filter(t => {
    const k = t.track_id || t.track_name
    if (seenIds.has(k)) return false
    seenIds.add(k); return true
  })

  return {
    album:               album.name         || '',
    album_id:            album.spotify_id   || '',
    album_url:           album.spotify_url  || '',
    album_image:         album.image_url    || '',
    artist:              primaryArtist,
    release_date:        album.release_date || '',
    album_type:          album.album_type   || '',
    total_tracks:        album.total_tracks  || 0,
    charting_tracks:     chartingTrackList,
    charting_track_count: uniqueCharting.length,
    playlists_reached:   (playlists as string[]).sort(),
    avg_popularity:      avgPopularity,
    all_tracks:          allTracksInfo,
  }
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function formatNumber(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000)     return (n / 1_000).toFixed(1) + 'K'
  return String(n)
}

function formatDuration(ms: number): string {
  const s = Math.floor(ms / 1000)
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
}

// ── Sub-components ───────────────────────────────────────────────────────────

function ChartBadge({ playlist, position, playlistUrls }: {
  playlist: string; position: number; playlistUrls: Record<string, string>
}) {
  const url = playlistUrls[playlist]
  const label = `#${position} ${playlist}`
  return url
    ? <a href={url} target="_blank" rel="noreferrer" className={styles.chartBadge}>{label}</a>
    : <span className={styles.chartBadge}>{label}</span>
}

function MiniBarChart({ tracks }: { tracks: { track_name: string; popularity: number }[] }) {
  return (
    <div className={styles.miniBarChartWrapper}>
      <div className={styles.miniBarLabel}>Track Popularity Distribution</div>
      <div className={styles.miniBarChart}>
        {tracks.map((t, i) => {
          const pop = Number(t.popularity) || 0
          const height = Math.max(4, pop * 0.6)
          return (
            <div
              key={i}
              className={styles.miniBar}
              style={{ height: `${height}px` }}
              title={`${t.track_name}\nPopularity: ${pop}`}
            />
          )
        })}
      </div>
    </div>
  )
}

function PopBar({ pop }: { pop: number }) {
  return (
    <div className={styles.popContainer}>
      <span className={styles.popValue}>{pop}</span>
      <span className={styles.popBarBg}>
        <span className={styles.popBar} style={{ width: `${Math.min(100, pop)}%` }} />
      </span>
    </div>
  )
}

// ── Artist modal body ─────────────────────────────────────────────────────────

function ArtistBody({ artist, playlistUrls }: { artist: ArtistProfile; playlistUrls: Record<string, string> }) {
  const chartsDropdown = artist.playlist_names.map(pl => {
    const url = playlistUrls[pl]
    return url ? `<li><a href="${url}" target="_blank">${pl}</a></li>` : `<li>${pl}</li>`
  }).join('') || '<li>No charts</li>'

  // Group tracks by name
  const trackMap: Record<string, { url: string; positions: { playlist: string; position: number }[] }> = {}
  artist.tracks.forEach(t => {
    if (!trackMap[t.track_name]) trackMap[t.track_name] = { url: t.spotify_url, positions: [] }
    if (t.playlist && t.position) trackMap[t.track_name].positions.push({ playlist: t.playlist, position: t.position })
  })

  return (
    <>
      {/* Stats grid */}
      <div className={styles.statsGrid}>
        <StatCard label="Charts" value={artist.chart_count}>
          <ul className={styles.statDropdownList} dangerouslySetInnerHTML={{ __html: chartsDropdown }} />
        </StatCard>
        <StatCard label="Appearances" value={artist.track_appearances}>
          <ul className={styles.statDropdownList}>
            {Object.entries(trackMap).map(([name, data]) => (
              <li key={name}>
                {data.url ? <a href={data.url} target="_blank" rel="noreferrer">{name}</a> : name}
                {data.positions.length > 0 && (
                  <div className={styles.trackChartPositions}>
                    {data.positions.map((p, i) => (
                      <span key={i} className={styles.chartPositionPill}>#{p.position} {p.playlist}</span>
                    ))}
                  </div>
                )}
              </li>
            ))}
          </ul>
        </StatCard>
      </div>

      {/* Charting tracks list */}
      {artist.tracks.length > 0 && (
        <div className={styles.modalSection}>
          <div className={styles.modalSectionTitle}>Charting Tracks ({artist.tracks.length})</div>
          <ul className={styles.modalTrackList}>
            {artist.tracks.map((t, i) => (
              <li key={i} className={`${styles.modalTrackItem} ${styles.charting}`}>
                {t.album_image && (
                  <div className={styles.trackImgWrapper}>
                    <img src={t.album_image} alt="" />
                    {t.preview_url && (
                      <a href={t.preview_url} target="_blank" rel="noreferrer" className={styles.trackThumbPlay} title="Play preview" />
                    )}
                  </div>
                )}
                <div className={styles.modalTrackInfo}>
                  <div className={styles.modalTrackName}>
                    {t.spotify_url
                      ? <a href={t.spotify_url} target="_blank" rel="noreferrer">{t.track_name}</a>
                      : t.track_name}
                    {t.explicit && <span className={styles.explicitBadge}>E</span>}
                  </div>
                  {t.album && (
                    <div className={styles.modalTrackMeta}>
                      {t.album_url
                        ? <a href={t.album_url} target="_blank" rel="noreferrer" className={styles.albumLink}>{t.album}</a>
                        : t.album}
                    </div>
                  )}
                  <div className={styles.chartBadges}>
                    <ChartBadge playlist={t.playlist} position={t.position} playlistUrls={playlistUrls} />
                  </div>
                </div>
                {t.popularity > 0 && <div className={styles.albumTrackPop}><PopBar pop={t.popularity} /></div>}
              </li>
            ))}
          </ul>
        </div>
      )}
    </>
  )
}

// ── Track modal body ──────────────────────────────────────────────────────────

function TrackBody({ track, playlistUrls }: { track: TrackProfile; playlistUrls: Record<string, string> }) {
  const releaseYear = track.release_date ? track.release_date.split('-')[0] : 'N/A'
  const allTracks = track._all_tracks_for_album

  return (
    <>
      <div className={styles.statsGrid}>
        <StatCard label="Best Position" value={`#${track.best_position}`}>
          <ul className={styles.statDropdownList}>
            {track.chart_positions
              .filter(cp => cp.position === track.best_position)
              .map((cp, i) => {
                const url = playlistUrls[cp.playlist]
                return (
                  <li key={i}>
                    {url ? <a href={url} target="_blank" rel="noreferrer">{cp.playlist}</a> : cp.playlist}
                  </li>
                )
              })}
          </ul>
        </StatCard>
        <StatCard label="Charts" value={track.charts_count}>
          <ul className={styles.statDropdownList}>
            {track.chart_positions.map((cp, i) => {
              const url = playlistUrls[cp.playlist]
              const label = `#${cp.position} ${cp.playlist}`
              return <li key={i}>{url ? <a href={url} target="_blank" rel="noreferrer">{label}</a> : label}</li>
            })}
          </ul>
        </StatCard>
        <StatCard label="Released" value={releaseYear} noDropdown />
        <StatCard label="Popularity" value={track.popularity} noDropdown>
          <div className={styles.modalStatPopBar}>
            <div className={styles.modalStatPopFill} style={{ width: `${track.popularity}%` }} />
          </div>
        </StatCard>
      </div>

      {/* Album tracklist */}
      {track.album && (
        <AlbumSection
          albumName={track.album}
          albumUrl={track.album_url}
          allTracks={allTracks}
          playlistUrls={playlistUrls}
        />
      )}

      {/* Chart positions badge cloud */}
      {track.chart_positions.length > 0 && (
        <div className={styles.modalSection}>
          <div className={styles.modalSectionTitle}>Chart Positions</div>
          <div className={styles.chartBadgeCloud}>
            {track.chart_positions.map((cp, i) => (
              <ChartBadge key={i} playlist={cp.playlist} position={cp.position} playlistUrls={playlistUrls} />
            ))}
          </div>
        </div>
      )}

    </>
  )
}

function AlbumSection({ albumName, albumUrl, allTracks, playlistUrls }: {
  albumName: string
  albumUrl: string
  allTracks: AlbumTrackInfo[]
  playlistUrls: Record<string, string>
}) {
  return (
    <div className={styles.modalSection}>
      <div className={styles.modalSectionTitle}>Album</div>
      <details className={styles.trackAlbumDropdown}>
        <summary className={styles.trackAlbumHeader}>
          {albumUrl
            ? <a href={albumUrl} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()}>{albumName}</a>
            : albumName}
          {allTracks.length > 0 && <span className={styles.trackAlbumChevron}>▾</span>}
        </summary>
        {allTracks.length > 0 && (
          <ul className={styles.trackAlbumTracklist}>
            {allTracks.map((t, i) => {
              const dur = t.duration_ms ? formatDuration(t.duration_ms) : ''
              return (
                <li key={i} className={`${styles.trackAlbumItem} ${t.is_charting ? styles.isCharting : ''}`}>
                  <span className={styles.trackAlbumNum}>{t.track_number}</span>
                  <span className={styles.trackAlbumName}>
                    {t.spotify_url
                      ? <a href={t.spotify_url} target="_blank" rel="noreferrer">{t.track_name}</a>
                      : t.track_name}
                    {t.explicit && <span className={styles.explicitBadge}>E</span>}
                    {t.is_charting && t.chart_positions.length > 0 && (
                      <span className={styles.trackAlbumBadges}>
                        {t.chart_positions.map((cp, ci) => (
                          <ChartBadge key={ci} playlist={cp.playlist} position={cp.position} playlistUrls={playlistUrls} />
                        ))}
                      </span>
                    )}
                  </span>
                  {dur && <span className={styles.trackAlbumDur}>{dur}</span>}
                </li>
              )
            })}
          </ul>
        )}
      </details>
    </div>
  )
}

// ── Album modal body ──────────────────────────────────────────────────────────

function AlbumBody({ album, playlistUrls }: { album: AlbumProfile; playlistUrls: Record<string, string> }) {
  const seenForChart = new Set<string>()
  const uniqueChartingList = album.charting_tracks.filter(t => {
    const k = t.track_id || t.track_name
    if (seenForChart.has(k)) return false
    seenForChart.add(k); return true
  })

  const chartsReachedDropdown = album.playlists_reached.map(pl => {
    const url = playlistUrls[pl]
    return url
      ? `<li><a href="${url}" target="_blank" rel="noreferrer">${pl}</a></li>`
      : `<li>${pl}</li>`
  }).join('') || '<li>No charts</li>'

  const chartingTracksDropdown = uniqueChartingList.map(t =>
    t.spotify_url
      ? `<li><a href="${t.spotify_url}" target="_blank" rel="noreferrer">${t.track_name}</a></li>`
      : `<li>${t.track_name}</li>`
  ).join('') || '<li>No charting tracks</li>'

  const allTracks = album.all_tracks

  return (
    <>
      <div className={styles.statsGrid}>
        <StatCard label="Charting Tracks" value={album.charting_track_count}>
          <ul className={styles.statDropdownList} dangerouslySetInnerHTML={{ __html: chartingTracksDropdown }} />
        </StatCard>
        <StatCard label="Total Tracks" value={album.total_tracks || '?'} noDropdown />
        <StatCard label="Charts Reached" value={album.playlists_reached.length}>
          <ul className={styles.statDropdownList} dangerouslySetInnerHTML={{ __html: chartsReachedDropdown }} />
        </StatCard>
        <StatCard label="Avg Popularity" value={Math.round(album.avg_popularity)}>
          <MiniBarChart tracks={allTracks.length > 0 ? allTracks : uniqueChartingList} />
        </StatCard>
      </div>

      {/* Full tracklist */}
      {allTracks.length > 0 && (
        <div className={`${styles.modalSection} ${styles.albumModalTracks}`}>
          <div className={styles.modalSectionTitle}>All Tracks ({allTracks.length})</div>
          <div className={styles.albumTrackHeaders}>
            <span className={styles.colNum}>#</span>
            <span className={styles.colTitle}>TITLE</span>
            <span className={styles.colDuration}>◷</span>
            <span className={styles.colPop}>POPULARITY</span>
          </div>
          <ul className={styles.modalTrackList}>
            {allTracks.map((t, i) => {
              const pop = Number(t.popularity) || 0
              const dur = t.duration_ms ? formatDuration(t.duration_ms) : ''
              const chartBadges = t.is_charting && t.chart_positions.length > 0
                ? t.chart_positions
                : []

              return (
                <li key={i} className={`${styles.modalTrackItem} ${t.is_charting ? styles.charting : ''}`}>
                  <div className={styles.trackNumberWrapper}>
                    <span className={styles.modalTrackNumber}>{t.track_number}</span>
                  </div>
                  <div className={styles.modalTrackInfo}>
                    <div className={styles.modalTrackNameLine}>
                      <div className={styles.modalTrackName}>
                        {t.spotify_url
                          ? <a href={t.spotify_url} target="_blank" rel="noreferrer">{t.track_name}</a>
                          : t.track_name}
                        {t.explicit && <span className={styles.explicitBadge}>E</span>}
                      </div>
                    </div>
                    {chartBadges.length > 0 && (
                      <div className={styles.chartBadges}>
                        {chartBadges.map((cp, ci) => (
                          <ChartBadge key={ci} playlist={cp.playlist} position={cp.position} playlistUrls={playlistUrls} />
                        ))}
                      </div>
                    )}
                  </div>
                  {dur && <span className={styles.modalTrackDuration}>{dur}</span>}
                  <div className={styles.albumTrackPop}>
                    {pop > 0 && <PopBar pop={pop} />}
                  </div>
                </li>
              )
            })}
          </ul>
        </div>
      )}

    </>
  )
}

// ── StatCard (re-used across all three modal types) ───────────────────────────

function StatCard({ label, value, children, noDropdown }: {
  label: string
  value: string | number
  children?: React.ReactNode
  noDropdown?: boolean
}) {
  return (
    <div className={`${styles.modalStat} ${noDropdown ? styles.noClick : ''}`}>
      <div className={styles.modalStatValue}>{value}</div>
      <div className={styles.modalStatLabel}>{label}</div>
      {!noDropdown && children && (
        <div className={styles.modalStatDropdown}>{children}</div>
      )}
      {noDropdown && children}
    </div>
  )
}

// ── Main ProfileModal ─────────────────────────────────────────────────────────

export default function ProfileModal() {
  const { modal, closeModal } = useModal()
  const overlayRef = useRef<HTMLDivElement>(null)

  // Re-use the runData query cached by ChartsView (zero extra network cost)
  const { data: runData } = useQuery<RunData>({
    queryKey: ['runData'],
    queryFn: fetchDashboardData,
    staleTime: 1000 * 60 * 60,
  })
  const playlistUrls: Record<string, string> = runData?.playlist_urls ?? {}

  // In-memory cache lives outside of React query to avoid refetch on re-open
  const artistCache = useRef<Map<string, ArtistProfile>>(new Map())
  const trackCache  = useRef<Map<string, TrackProfile>>(new Map())
  const albumCache  = useRef<Map<string, AlbumProfile>>(new Map())

  const { type, id } = modal
  const isOpen = Boolean(type && id)

  // Fetch the right profile based on type
  const { data: artistData, isLoading: artistLoading } = useQuery<ArtistProfile | null>({
    queryKey: ['artistProfile', id],
    queryFn: async () => {
      if (artistCache.current.has(id!)) return artistCache.current.get(id!)!
      const p = await fetchArtistProfile(id!)
      if (p) artistCache.current.set(id!, p)
      return p
    },
    enabled: isOpen && type === 'artist',
    staleTime: Infinity,
  })

  const { data: trackData, isLoading: trackLoading } = useQuery<TrackProfile | null>({
    queryKey: ['trackProfile', id],
    queryFn: async () => {
      if (trackCache.current.has(id!)) return trackCache.current.get(id!)!
      const p = await fetchTrackProfile(id!)
      if (p) trackCache.current.set(id!, p)
      return p
    },
    enabled: isOpen && type === 'track',
    staleTime: Infinity,
  })

  const { data: albumData, isLoading: albumLoading } = useQuery<AlbumProfile | null>({
    queryKey: ['albumProfile', id],
    queryFn: async () => {
      if (albumCache.current.has(id!)) return albumCache.current.get(id!)!
      const p = await fetchAlbumProfile(id!)
      if (p) albumCache.current.set(id!, p)
      return p
    },
    enabled: isOpen && type === 'album',
    staleTime: Infinity,
  })

  // Escape key + overlay click to close
  useEffect(() => {
    function onKey(e: KeyboardEvent) { if (e.key === 'Escape') closeModal() }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [closeModal])

  // Lock body scroll when open
  useEffect(() => {
    document.body.style.overflow = isOpen ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [isOpen])

  const handleOverlayClick = useCallback((e: React.MouseEvent) => {
    if (e.target === overlayRef.current) closeModal()
  }, [closeModal])

  if (!isOpen) return null

  // Resolve current profile
  const isLoading = artistLoading || trackLoading || albumLoading
  const profile = type === 'artist' ? artistData : type === 'track' ? trackData : albumData

  // Build header content
  let headerImage: React.ReactNode = null
  let title = ''
  let subtitle = ''
  let genreTags: string[] = []
  let previewUrl = ''

  if (!isLoading && profile) {
    if (type === 'artist') {
      const a = profile as ArtistProfile
      title = a.name
      genreTags = a.genres
      previewUrl = ''
      subtitle = [
        a.followers > 0 ? `${formatNumber(a.followers)} followers` : '',
        a.url ? `<a href="${a.url}" target="_blank">Open in Spotify ↗</a>` : '',
      ].filter(Boolean).join(' · ')
      headerImage = a.image
        ? <img src={a.image} className={`${styles.modalImage} ${styles.artist}`} alt="" />
        : <div className={`${styles.modalImagePlaceholder} ${styles.artist}`}>♪</div>
    } else if (type === 'track') {
      const t = profile as TrackProfile
      title = t.track_name
      genreTags = t.genres
      previewUrl = t.preview_url
      subtitle = `by ${t.artist}${t.spotify_url ? ` · <a href="${t.spotify_url}" target="_blank">Open in Spotify ↗</a>` : ''}`
      headerImage = t.album_image
        ? (previewUrl
            ? <div className={styles.modalImageWrapper}>
                <img src={t.album_image} className={`${styles.modalImage} ${styles.album}`} alt="" />
                <a href={previewUrl} target="_blank" rel="noreferrer" className={styles.playOverlay} title="Play preview">
                  <span className={styles.playIcon} />
                </a>
              </div>
            : <img src={t.album_image} className={`${styles.modalImage} ${styles.album}`} alt="" />)
        : <div className={`${styles.modalImagePlaceholder} ${styles.album}`}>♪</div>
    } else {
      const al = profile as AlbumProfile
      title = al.album
      subtitle = `by ${al.artist}${al.album_url ? ` · <a href="${al.album_url}" target="_blank">Open in Spotify ↗</a>` : ''}`
      const ctPrev = al.charting_tracks.find(t => t.preview_url)?.preview_url || ''
      previewUrl = ctPrev
      headerImage = al.album_image
        ? (previewUrl
            ? <div className={styles.modalImageWrapper}>
                <img src={al.album_image} className={`${styles.modalImage} ${styles.album}`} alt="" />
                <a href={previewUrl} target="_blank" rel="noreferrer" className={styles.playOverlay} title="Play preview">
                  <span className={styles.playIcon} />
                </a>
              </div>
            : <img src={al.album_image} className={`${styles.modalImage} ${styles.album}`} alt="" />)
        : <div className={`${styles.modalImagePlaceholder} ${styles.album}`}>♪</div>
    }
  }

  return (
    <div
      ref={overlayRef}
      className={`${styles.overlay} ${isOpen ? styles.open : ''}`}
      onClick={handleOverlayClick}
    >
      <div className={styles.content}>
        {/* Header */}
        <div className={styles.modalHeader}>
          <div className={styles.modalImageContainer}>{headerImage}</div>
          <div className={styles.modalTitleSection}>
            <h2 className={styles.modalTitle}>
              {isLoading ? 'Loading…' : title || 'Unavailable'}
              {!isLoading && type === 'track' && (profile as TrackProfile)?.explicit && (
                <span className={`${styles.explicitBadge} ${styles.titleExplicit}`}>E</span>
              )}
            </h2>
            <div
              className={styles.modalSubtitle}
              dangerouslySetInnerHTML={{ __html: subtitle }}
            />
            {genreTags.length > 0 && (
              <div className={styles.headerGenres}>
                {genreTags.map(g => (
                  <span key={g} className={styles.headerGenreTag}>{g}</span>
                ))}
              </div>
            )}
          </div>
          <button className={styles.closeBtn} onClick={closeModal} aria-label="Close">&times;</button>
        </div>

        {/* Body */}
        <div className={styles.modalBody}>
          {isLoading && (
            <div className={styles.statsGrid}>
              <div className={styles.skeletonCard} />
              <div className={styles.skeletonCard} />
              <div className={styles.skeletonCard} />
              <div className={styles.skeletonCard} />
            </div>
          )}
          {!isLoading && !profile && (
            <div className={styles.errorMsg}>Profile not found or Supabase not configured.</div>
          )}
          {!isLoading && profile && type === 'artist' && (
            <ArtistBody artist={profile as ArtistProfile} playlistUrls={playlistUrls} />
          )}
          {!isLoading && profile && type === 'track' && (
            <TrackBody track={profile as TrackProfile} playlistUrls={playlistUrls} />
          )}
          {!isLoading && profile && type === 'album' && (
            <AlbumBody album={profile as AlbumProfile} playlistUrls={playlistUrls} />
          )}
        </div>

        {/* Footer — rendered outside the scroll container so it never covers content */}
        {!isLoading && profile && type === 'track' && (profile as TrackProfile).release_date && (
          <div className={styles.modalFooter}>
            {(profile as TrackProfile).explicit && <span>Explicit · </span>}
            {(profile as TrackProfile).release_date}
          </div>
        )}
        {!isLoading && profile && type === 'album' && (
          <div className={styles.modalFooter}>
            {(profile as AlbumProfile).album_type && (
              <span style={{ textTransform: 'capitalize' }}>
                {(profile as AlbumProfile).album_type} ·{' '}
              </span>
            )}
            {(profile as AlbumProfile).release_date || 'Unknown release date'}
          </div>
        )}
      </div>
    </div>
  )
}
