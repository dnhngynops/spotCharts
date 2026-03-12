import { useState } from 'react'
import type { Analytics, OverlapTrack, MultiChartTrack } from '../../lib/types'
import styles from './ChartOverlap.module.css'

interface Props {
  chartOverlap: Analytics['chart_overlap']
  playlistUrls: Record<string, string>
}

type ExpandedSection = 'usa' | 'both' | 'global' | null

function OverlapTrackList({ tracks }: { tracks: OverlapTrack[] }) {
  if (!tracks.length) return <li className={styles.emptyMsg}>No tracks</li>
  return (
    <>
      {tracks.map((t, i) => (
        <li key={i} className={styles.dropdownItem}>
          <span className={styles.dropdownTrackName}>
            {t.spotify_url
              ? <a href={t.spotify_url} target="_blank" rel="noreferrer">{t.track_name}</a>
              : t.track_name}
          </span>
          <span className={styles.dropdownMeta}> — {t.artist}</span>
        </li>
      ))}
    </>
  )
}

function MultiChartTrackCard({ track, playlistUrls }: { track: MultiChartTrack; playlistUrls: Record<string, string> }) {
  return (
    <div className={styles.overlapTrack}>
      {track.album_image && (
        <img src={track.album_image} alt="" className={styles.overlapThumb} />
      )}
      <div className={styles.overlapInfo}>
        <div className={styles.overlapTrackName}>
          {track.spotify_url
            ? <a href={track.spotify_url} target="_blank" rel="noreferrer">{track.track_name}</a>
            : track.track_name}
        </div>
        <div className={styles.overlapArtist}>{track.artist}</div>
        <div className={styles.chartTags}>
          {track.appearances.map((app, i) => {
            const url = playlistUrls[app.playlist]
            const label = `#${app.position} ${app.playlist.replace(/ - /g, ' ')}`
            return url
              ? <a key={i} href={url} target="_blank" rel="noreferrer" className={styles.chartTag}>{label}</a>
              : <span key={i} className={styles.chartTag}>{label}</span>
          })}
        </div>
      </div>
    </div>
  )
}

export default function ChartOverlap({ chartOverlap, playlistUrls }: Props) {
  const [expanded, setExpanded] = useState<ExpandedSection>(null)

  const { usa_global_comparison: cmp, multi_chart_tracks } = chartOverlap

  function toggle(section: ExpandedSection) {
    setExpanded(prev => prev === section ? null : section)
  }

  return (
    <div className={styles.section}>
      <h2 className={styles.sectionTitle}>USA vs Global</h2>

      <div className={styles.overlapStats}>
        {/* USA Only */}
        <div
          className={`${styles.overlapStat} ${expanded === 'usa' ? styles.open : ''}`}
          onClick={() => toggle('usa')}
          role="button"
          tabIndex={0}
          onKeyDown={e => e.key === 'Enter' && toggle('usa')}
        >
          <div className={styles.number}>{cmp.usa_only}</div>
          <div className={styles.statLabel}>USA Only</div>
          <ul className={styles.statDropdown}>
            <OverlapTrackList tracks={cmp.usa_only_tracks} />
          </ul>
        </div>

        {/* Both */}
        <div
          className={`${styles.overlapStat} ${expanded === 'both' ? styles.open : ''}`}
          onClick={() => toggle('both')}
          role="button"
          tabIndex={0}
          onKeyDown={e => e.key === 'Enter' && toggle('both')}
        >
          <div className={styles.number}>{cmp.both}</div>
          <div className={styles.statLabel}>Both Charts</div>
          <ul className={styles.statDropdown}>
            <OverlapTrackList tracks={cmp.both_tracks} />
          </ul>
        </div>

        {/* Global Only */}
        <div
          className={`${styles.overlapStat} ${expanded === 'global' ? styles.open : ''}`}
          onClick={() => toggle('global')}
          role="button"
          tabIndex={0}
          onKeyDown={e => e.key === 'Enter' && toggle('global')}
        >
          <div className={styles.number}>{cmp.global_only}</div>
          <div className={styles.statLabel}>Global Only</div>
          <ul className={styles.statDropdown}>
            <OverlapTrackList tracks={cmp.global_only_tracks} />
          </ul>
        </div>
      </div>

      {multi_chart_tracks.length > 0 && (
        <>
          <h3 className={styles.multiChartHeading}>Tracks on Multiple Charts</h3>
          <div className={styles.multiChartList}>
            {multi_chart_tracks.slice(0, 8).map((track, i) => (
              <MultiChartTrackCard key={i} track={track} playlistUrls={playlistUrls} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}
