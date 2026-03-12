import type { Track } from '../../lib/types'
import styles from './PlaylistPopularityStats.module.css'

interface Props {
  tracks: Track[]
}

interface Bucket {
  label: string
  count: number
  heightPct: number
}

function buildHistogram(pops: number[], numBuckets = 5): Bucket[] {
  if (!pops.length) return []
  const lo = Math.min(...pops)
  const hi = Math.max(...pops)
  if (lo === hi) return [{ label: String(lo), count: pops.length, heightPct: 100 }]
  const step = (hi - lo) / numBuckets
  const buckets: Bucket[] = Array.from({ length: numBuckets }, (_, i) => ({
    label: `${Math.round(lo + i * step)}–${Math.round(lo + (i + 1) * step)}`,
    count: 0,
    heightPct: 0,
  }))
  pops.forEach(p => {
    let idx = Math.floor((p - lo) / step)
    if (idx >= numBuckets) idx = numBuckets - 1
    buckets[idx].count++
  })
  const maxCount = Math.max(...buckets.map(b => b.count)) || 1
  buckets.forEach(b => { b.heightPct = Math.round((b.count / maxCount) * 100) })
  return buckets
}

export default function PlaylistPopularityStats({ tracks }: Props) {
  const pops = tracks.map(t => t.popularity).filter(p => p > 0)
  if (!pops.length) return null

  const min = Math.min(...pops)
  const max = Math.max(...pops)
  const avg = Math.round((pops.reduce((a, b) => a + b, 0) / pops.length) * 10) / 10
  const avgPct = min === max ? 50 : ((avg - min) / (max - min)) * 100
  const buckets = buildHistogram(pops)

  return (
    <div className={styles.section}>
      <h2 className={styles.sectionTitle}>Popularity Stats</h2>

      <div className={styles.avgArea}>
        <div className={styles.avgValue}>{avg.toFixed(1)}</div>
        <div className={styles.avgLabel}>Average Popularity</div>
      </div>

      <div className={styles.rangeSection}>
        <div className={styles.rangeBar}>
          <div className={styles.rangeBarFill} />
          <div className={styles.rangeBarAvg} style={{ left: `${avgPct.toFixed(1)}%` }} />
        </div>
        <div className={styles.rangeLabels}>
          <span>{min}</span>
          <span>Range: {min} – {max}</span>
          <span>{max}</span>
        </div>
      </div>

      <div className={styles.histogramWrapper}>
        <div className={styles.yLabel}>Tracks</div>
        <div className={styles.histogramArea}>
          <div className={styles.histogram}>
            {buckets.map(b => (
              <div key={b.label} className={styles.histCol}>
                <div className={styles.histCount}>{b.count}</div>
                <div className={styles.histBarWrap}>
                  <div className={styles.histBar} style={{ height: `${b.heightPct}%` }} />
                </div>
                <div className={styles.histLabel}>{b.label}</div>
              </div>
            ))}
          </div>
          <div className={styles.xLabel}>Popularity Score</div>
        </div>
      </div>
    </div>
  )
}
