import React, { useState, useMemo, useCallback } from 'react'
import type { Track, TrendInfo } from '../../lib/types'
import { useModal } from '../../contexts/ModalContext'
import styles from './TracksTable.module.css'

interface Props {
  tracks: Track[]
  playlistNames: string[]
  trendData: Map<string, TrendInfo>
  showPlaylistFilter?: boolean
  title?: string
}

type SortKey = 'position' | 'track' | 'album' | 'duration' | 'popularity'
type SortDir = 'asc' | 'desc'

const PRIMARY_CREDIT_ROLES = new Set(['Producer', 'Songwriter'])

function TrackCreditSubtext({ artists }: { artists: { name: string; role?: string }[] }) {
  const [expanded, setExpanded] = useState(false)

  const creditsByRole: Record<string, string[]> = {}
  artists.forEach(a => {
    if (a.role && a.role !== 'Artist') {
      if (!creditsByRole[a.role]) creditsByRole[a.role] = []
      creditsByRole[a.role].push(a.name)
    }
  })

  const primaryParts = Object.entries(creditsByRole)
    .filter(([role]) => PRIMARY_CREDIT_ROLES.has(role))
    .map(([role, names]) => `${role}: ${names.join(', ')}`)

  const secondaryParts = Object.entries(creditsByRole)
    .filter(([role]) => !PRIMARY_CREDIT_ROLES.has(role))
    .map(([role, names]) => `${role}: ${names.join(', ')}`)

  if (primaryParts.length === 0 && secondaryParts.length === 0) return null

  return (
    <small className={styles.creditSubtext}>
      {primaryParts.join(' · ')}
      {secondaryParts.length > 0 && (
        <>
          {expanded ? (
            <>
              {primaryParts.length > 0 ? ' · ' : ''}{secondaryParts.join(' · ')}{' '}
              <button className={styles.showCreditsLink} onClick={() => setExpanded(false)}>less</button>
            </>
          ) : (
            <button className={styles.showCreditsLink} onClick={() => setExpanded(true)}>
              {primaryParts.length > 0 ? ' ' : ''}+{secondaryParts.length} more
            </button>
          )}
        </>
      )}
    </small>
  )
}

function formatDuration(ms: number): string {
  const totalSec = Math.floor(ms / 1000)
  const m = Math.floor(totalSec / 60)
  const s = String(totalSec % 60).padStart(2, '0')
  return `${m}:${s}`
}

function TrendBadge({ info }: { info: TrendInfo | undefined }) {
  if (!info) return null
  const { badge, delta, weeksOnChart, peakPos } = info
  const title = `${weeksOnChart} week${weeksOnChart !== 1 ? 's' : ''} on chart · Peak: #${peakPos}`
  if (badge === 'new') return <span className={`${styles.trendBadge} ${styles.trendNew}`} title={title}>NEW</span>
  if (badge === 'up') return <span className={`${styles.trendBadge} ${styles.trendUp}`} title={title}>▲{delta}</span>
  if (badge === 'down') return <span className={`${styles.trendBadge} ${styles.trendDown}`} title={title}>▼{delta}</span>
  return <span className={`${styles.trendBadge} ${styles.trendSame}`} title={title}>◆</span>
}

export default function TracksTable({
  tracks,
  playlistNames,
  trendData,
  showPlaylistFilter = true,
  title = 'All Tracks',
}: Props) {
  const { openModal } = useModal()

  // ── Filter state ──────────────────────────────────────────────────────────
  const [search, setSearch] = useState('')
  const [playlist, setPlaylist] = useState('')
  const [genre, setGenre] = useState('')
  const [explicit, setExplicit] = useState<'' | 'yes' | 'no'>('')

  // ── Sort state ────────────────────────────────────────────────────────────
  const [sortKey, setSortKey] = useState<SortKey>('position')
  const [sortDir, setSortDir] = useState<SortDir>('asc')

  // ── Derived genre list ────────────────────────────────────────────────────
  const allGenres = useMemo(() => {
    const s = new Set<string>()
    tracks.forEach(t => t.genres?.forEach(g => { if (g) s.add(g) }))
    return Array.from(s).sort()
  }, [tracks])

  // ── Apply filters + sort ──────────────────────────────────────────────────
  const visible = useMemo(() => {
    let rows = tracks

    if (search) {
      const q = search.toLowerCase()
      rows = rows.filter(t =>
        t.track_name.toLowerCase().includes(q) || t.artist.toLowerCase().includes(q)
      )
    }
    if (playlist) {
      rows = rows.filter(t => {
        // all_tracks rows may have comma-separated playlists baked via the Python pipeline;
        // individual playlist tabs have a single playlist string.
        const playlists = t.playlist.split(',').map(p => p.trim())
        return playlists.includes(playlist)
      })
    }
    if (genre) {
      rows = rows.filter(t => t.genres?.includes(genre))
    }
    if (explicit === 'yes') rows = rows.filter(t => t.explicit)
    if (explicit === 'no') rows = rows.filter(t => !t.explicit)

    // Sort
    const dir = sortDir === 'asc' ? 1 : -1
    rows = [...rows].sort((a, b) => {
      if (sortKey === 'position') {
        const pa = a.position || 999
        const pb = b.position || 999
        return (pa - pb) * dir
      }
      if (sortKey === 'track') return a.track_name.localeCompare(b.track_name) * dir
      if (sortKey === 'album') return a.album.localeCompare(b.album) * dir
      if (sortKey === 'duration') {
        return ((a.duration_ms ?? 0) - (b.duration_ms ?? 0)) * dir
      }
      if (sortKey === 'popularity') return ((a.popularity ?? 0) - (b.popularity ?? 0)) * dir
      return 0
    })

    return rows
  }, [tracks, search, playlist, genre, explicit, sortKey, sortDir])

  const handleSort = useCallback((key: SortKey) => {
    setSortKey(prev => {
      if (prev === key) {
        setSortDir(d => d === 'asc' ? 'desc' : 'asc')
        return key
      }
      setSortDir('asc')
      return key
    })
  }, [])

  function resetFilters() {
    setSearch('')
    setPlaylist('')
    setGenre('')
    setExplicit('')
    setSortKey('position')
    setSortDir('asc')
  }

  function SortIndicator({ col }: { col: SortKey }) {
    if (sortKey !== col) return null
    return <span className={styles.sortIndicator}>{sortDir === 'asc' ? ' ▲' : ' ▼'}</span>
  }

  return (
    <div className={styles.section}>
      <div className={styles.tableHeader}>
        <h2 className={styles.tableTitle}>{title}</h2>
        <span className={styles.tableMeta}>{tracks.length} tracks</span>
      </div>

      {/* Filter bar */}
      <div className={styles.filterBar}>
        <div className={styles.filterRow}>
          <div className={styles.filterGroup}>
            <label className={styles.filterLabel}>Search</label>
            <input
              type="text"
              className={styles.filterInput}
              placeholder="Track or artist name…"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>

          {showPlaylistFilter && (
            <div className={styles.filterGroup}>
              <label className={styles.filterLabel}>Playlist</label>
              <select
                className={styles.filterSelect}
                value={playlist}
                onChange={e => setPlaylist(e.target.value)}
              >
                <option value="">All Playlists</option>
                {playlistNames.map(n => (
                  <option key={n} value={n}>{n}</option>
                ))}
              </select>
            </div>
          )}

          <div className={styles.filterGroup}>
            <label className={styles.filterLabel}>Genre</label>
            <select
              className={styles.filterSelect}
              value={genre}
              onChange={e => setGenre(e.target.value)}
            >
              <option value="">All Genres</option>
              {allGenres.map(g => (
                <option key={g} value={g}>{g}</option>
              ))}
            </select>
          </div>

          <div className={styles.filterGroup}>
            <label className={styles.filterLabel}>Explicit</label>
            <div className={styles.toggleButtons}>
              <button
                className={`${styles.toggleBtn} ${explicit === '' ? styles.toggleActive : ''}`}
                onClick={() => setExplicit('')}
              >
                All
              </button>
              <button
                className={`${styles.toggleBtn} ${explicit === 'yes' ? styles.toggleActive : ''}`}
                onClick={() => setExplicit('yes')}
              >
                Yes
              </button>
              <button
                className={`${styles.toggleBtn} ${explicit === 'no' ? styles.toggleActive : ''}`}
                onClick={() => setExplicit('no')}
              >
                No
              </button>
            </div>
          </div>

          <div className={styles.filterGroup}>
            <button className={styles.resetBtn} onClick={resetFilters}>Reset</button>
          </div>
        </div>

        <div className={styles.filterResults}>
          <span className={styles.filterCount}>{visible.length}</span> of {tracks.length} tracks
        </div>
      </div>

      {/* Table */}
      <div className={styles.tableWrapper}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th
                className={`${styles.th} ${styles.sortable} ${sortKey === 'position' ? styles.sortActive : ''}`}
                onClick={() => handleSort('position')}
                aria-sort={sortKey === 'position' ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}
              >
                #<SortIndicator col="position" />
              </th>
              <th
                className={`${styles.th} ${styles.sortable} ${sortKey === 'track' ? styles.sortActive : ''}`}
                onClick={() => handleSort('track')}
                aria-sort={sortKey === 'track' ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}
              >
                Track<SortIndicator col="track" />
              </th>
              <th
                className={`${styles.th} ${styles.sortable} ${sortKey === 'album' ? styles.sortActive : ''}`}
                onClick={() => handleSort('album')}
                aria-sort={sortKey === 'album' ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}
              >
                Album<SortIndicator col="album" />
              </th>
              <th
                className={`${styles.th} ${styles.sortable} ${sortKey === 'duration' ? styles.sortActive : ''}`}
                onClick={() => handleSort('duration')}
                aria-sort={sortKey === 'duration' ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}
              >
                ◷<SortIndicator col="duration" />
              </th>
              <th
                className={`${styles.th} ${styles.sortable} ${sortKey === 'popularity' ? styles.sortActive : ''}`}
                onClick={() => handleSort('popularity')}
                aria-sort={sortKey === 'popularity' ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}
              >
                Popularity<SortIndicator col="popularity" />
              </th>
            </tr>
          </thead>
          <tbody>
            {visible.length === 0 && (
              <tr>
                <td colSpan={5} className={styles.noResults}>No tracks match the current filters</td>
              </tr>
            )}
            {visible.map((track, i) => {
              const trackId = track.track_id ?? ''
              const trend = trendData.get(trackId)
              const pop = track.popularity ?? 0
              const rank = track.rank ?? track.position
              const releaseYear = track.release_date?.slice(0, 4)

              const followerTier = track.artist_followers == null ? null
                : track.artist_followers < 1_000_000 ? '<1M'
                : track.artist_followers < 5_000_000 ? '1M–5M'
                : '5M+'

              const isHiddenGem = track.rank != null
                ? (track.best_position != null && track.best_position <= 20 && (track.popularity ?? 0) < 50)
                : (track.position != null && track.position <= 20 && (track.popularity ?? 0) < 50)

              return (
                <tr
                  key={`${trackId}-${i}`}
                  className={`${styles.row}${isHiddenGem ? ` ${styles.hiddenGem}` : ''}`}
                  title={isHiddenGem ? 'High chart position, low mainstream popularity — early signal' : undefined}
                >
                  {/* Position + trend */}
                  <td className={styles.posCell}>
                    <div className={styles.posWrapper}>
                      <span className={styles.posNum}>{rank || '—'}</span>
                      <TrendBadge info={trend} />
                    </div>
                  </td>

                  {/* Track + artists */}
                  <td className={styles.trackCell}>
                    <div className={styles.trackInner}>
                      {track.album_image_url && (
                        <img
                          src={track.album_image_url}
                          alt=""
                          className={styles.albumThumb}
                          loading="lazy"
                        />
                      )}
                      <div className={styles.trackMeta}>
                        <div className={styles.trackName}>
                          {trackId
                            ? (
                              <a
                                href={track.spotify_url ?? '#'}
                                target="_blank"
                                rel="noopener"
                                className={styles.profileLink}
                                onClick={e => { if (!e.ctrlKey && !e.metaKey) { e.preventDefault(); openModal('track', trackId) } }}
                              >
                                {track.track_name}
                              </a>
                            )
                            : track.track_name}
                          {track.explicit && <span className={styles.explicit}>E</span>}
                        </div>
                        <div className={styles.artistList}>
                          {(track.artists || []).filter(a => a.role === 'Artist' || !a.role).map((a, ai) => (
                            <span key={ai}>
                              {ai > 0 && <span className={styles.artistSep}>, </span>}
                              {a.id
                                ? (
                                  <a
                                    href={a.url ?? '#'}
                                    target="_blank"
                                    rel="noopener"
                                    className={styles.profileLink}
                                    onClick={e => { if (!e.ctrlKey && !e.metaKey) { e.preventDefault(); openModal('artist', a.id!) } }}
                                  >
                                    {a.name}
                                  </a>
                                )
                                : <span>{a.name}</span>}
                            </span>
                          ))}
                          {followerTier && <span className={styles.followerBadge}>{followerTier}</span>}
                        </div>
                        <TrackCreditSubtext artists={track.artists || []} />
                      </div>
                    </div>
                  </td>

                  {/* Album */}
                  <td className={styles.albumCell}>
                    {track.album_id
                      ? (
                        <a
                          href={track.album_url ?? '#'}
                          target="_blank"
                          rel="noopener"
                          className={styles.profileLink}
                          onClick={e => { if (!e.ctrlKey && !e.metaKey) { e.preventDefault(); openModal('album', track.album_id!) } }}
                        >
                          {track.album}
                        </a>
                      )
                      : <span className={styles.albumText}>{track.album}</span>}
                    {releaseYear && <span className={styles.yearBadge}>{releaseYear}</span>}
                  </td>

                  {/* Duration */}
                  <td className={styles.durationCell}>
                    {track.duration_ms ? formatDuration(track.duration_ms) : '—'}
                  </td>

                  {/* Popularity */}
                  <td className={styles.popCell}>
                    <div className={styles.popContainer}>
                      <span className={styles.popValue}>{pop}</span>
                      <span className={styles.popBarBg}>
                        <span
                          className={styles.popBar}
                          style={{ '--bar-width': `${Math.min(100, pop)}%` } as React.CSSProperties}
                        />
                      </span>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
