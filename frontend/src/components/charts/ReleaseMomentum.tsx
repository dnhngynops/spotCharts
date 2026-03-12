import type { Analytics } from '../../lib/types'
import styles from './ReleaseMomentum.module.css'

interface Props {
  releaseMomentum: Analytics['release_momentum']
}

export default function ReleaseMomentum({ releaseMomentum }: Props) {
  if (!releaseMomentum || releaseMomentum.length === 0) return null

  const maxCount = Math.max(...releaseMomentum.map(r => r.track_count))

  return (
    <div className={styles.section}>
      <h2 className={styles.sectionTitle}>Release Momentum by Year</h2>
      <div className={styles.chart}>
        {releaseMomentum.map((year, i) => {
          const barWidth = maxCount > 0 ? (year.track_count / maxCount) * 100 : 0
          return (
            <div key={i} className={styles.row}>
              <div className={styles.yearLabel}>{year.year}</div>
              <div className={styles.barContainer}>
                <div className={styles.bar} style={{ width: `${barWidth}%` }}>
                  <span className={styles.barText}>{year.track_count} tracks</span>
                </div>
              </div>
              <div className={styles.popularity}>{year.avg_popularity.toFixed(1)}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
