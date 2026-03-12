import type { Analytics } from '../../lib/types'
import styles from './ExplicitStats.module.css'

interface Props {
  explicitStats: Analytics['explicit_stats']
  playlistUrls?: Record<string, string>
}

export default function ExplicitStats({ explicitStats }: Props) {
  const entries = Object.entries(explicitStats.by_playlist)
  if (!entries.length) return null

  const totalExplicit = explicitStats.total_explicit ?? 0
  const totalTracks = explicitStats.total_tracks ?? entries.reduce((s, [, v]) => s + v.total, 0)
  const overallPct = totalTracks > 0 ? (totalExplicit / totalTracks) * 100 : (explicitStats.percentage ?? 0)

  return (
    <div className={styles.section}>
      <h2 className={styles.sectionTitle}>Explicit Content</h2>
      <div className={styles.summaryRow}>
        <span className={styles.overallPct}>{Math.round(overallPct)}%</span>
        <span className={styles.overallLabel}>explicit overall</span>
      </div>
      <div className={styles.breakdownRow}>
        {entries.map(([playlist, stats], i) => (
          <span key={playlist} className={styles.breakdownItem}>
            {i > 0 && <span className={styles.breakdownSep}> · </span>}
            <span className={styles.breakdownName}>{playlist}</span>
            <span className={styles.breakdownPct}> {Math.round(stats.percentage ?? 0)}%</span>
          </span>
        ))}
      </div>
    </div>
  )
}
