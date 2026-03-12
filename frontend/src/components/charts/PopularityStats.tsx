import type { Analytics } from '../../lib/types'
import styles from './PopularityStats.module.css'

interface Props {
  popularityStats: Analytics['popularity_stats']
  playlistUrls?: Record<string, string>
}

export default function PopularityStats({ popularityStats, playlistUrls }: Props) {
  const entries = Object.entries(popularityStats.by_playlist)
  if (!entries.length) return null

  return (
    <div className={styles.section}>
      <h2 className={styles.sectionTitle}>Popularity by Playlist</h2>
      <div className={styles.grid}>
        {entries.map(([playlist, stats]) => {
          const fillLeft = `${stats.min}%`
          const fillWidth = `${Math.max(0, stats.max - stats.min)}%`
          const markerLeft = `${stats.avg}%`
          const url = playlistUrls?.[playlist]
          return (
            <div key={playlist} className={styles.card}>
              {url
                ? <a href={url} target="_blank" rel="noopener" className={styles.playlistLink}>{playlist}</a>
                : <div className={styles.playlistName}>{playlist}</div>
              }
              <div className={styles.avgValue}>{stats.avg.toFixed(1)}</div>
              <div className={styles.rangeBarWrapper}>
                <div className={styles.rangeBarFill} style={{ left: fillLeft, width: fillWidth }} />
                <div className={styles.rangeBarMarker} style={{ left: markerLeft }} />
              </div>
              <div className={styles.range}>{stats.min} – {stats.max}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
