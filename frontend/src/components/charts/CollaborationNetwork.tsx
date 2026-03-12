import type { Analytics } from '../../lib/types'
import styles from './CollaborationNetwork.module.css'

interface Props {
  collaborationNetwork: Analytics['collaboration_network']
}

export default function CollaborationNetwork({ collaborationNetwork }: Props) {
  if (!collaborationNetwork || collaborationNetwork.length === 0) return null

  return (
    <div className={styles.section}>
      <h2 className={styles.sectionTitle}>Artist Collaboration Network</h2>
      <div className={styles.grid}>
        {collaborationNetwork.slice(0, 12).map((pair, i) => (
          <div key={i} className={styles.card}>
            <div className={styles.artists}>
              <div className={styles.artist}>{pair.artist1}</div>
              <div className={styles.separator}>×</div>
              <div className={styles.artist}>{pair.artist2}</div>
            </div>
            <div className={styles.stats}>
              <div className={styles.statItem}>
                <span className={styles.statValue}>{pair.track_count}</span>
                <span className={styles.statLabel}>
                  {pair.track_count === 1 ? 'Track' : 'Tracks'}
                </span>
              </div>
              <div className={styles.statItem}>
                <span className={styles.statValue}>{pair.avg_popularity.toFixed(1)}</span>
                <span className={styles.statLabel}>Avg Pop</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
