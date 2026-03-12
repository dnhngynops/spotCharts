import type { Analytics } from '../../lib/types'
import styles from './DurationAnalysis.module.css'

interface Props {
  durationAnalysis: Analytics['duration_analysis']
}

export default function DurationAnalysis({ durationAnalysis }: Props) {
  if (!durationAnalysis || durationAnalysis.length === 0) return null

  const maxCount = Math.max(...durationAnalysis.map(b => b.track_count))

  return (
    <div className={styles.section}>
      <h2 className={styles.sectionTitle}>Duration vs Popularity Analysis</h2>
      <div className={styles.grid}>
        {durationAnalysis.map((bucket, i) => {
          const barHeight = maxCount > 0 ? (bucket.track_count / maxCount) * 100 : 0
          return (
            <div key={i} className={styles.bucket}>
              <div className={styles.label}>{bucket.label}</div>
              <div className={styles.barContainer}>
                <div className={styles.bar} style={{ height: `${barHeight}%` }}>
                  <span className={styles.barLabel}>{bucket.track_count}</span>
                </div>
              </div>
              <div className={styles.stats}>
                <div className={styles.statItem}>
                  <span className={styles.statLabel}>Avg Popularity</span>
                  <span className={styles.statValue}>{bucket.avg_popularity.toFixed(1)}</span>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
