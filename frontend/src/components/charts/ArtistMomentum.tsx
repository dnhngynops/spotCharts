import { useMemo } from 'react'
import styles from './ArtistMomentum.module.css'
import type { Track } from '../../lib/types'
import type { TrendInfo } from '../../lib/types'

interface Props {
  allTracks: Track[]
  trendData: Map<string, TrendInfo>
  isLoading: boolean
}

interface ArtistMoment {
  profileKey: string
  name: string
  trackCount: number
  delta: number | null   // null = no trend data
  allNew: boolean
  followerTier: string | null
}

export function ArtistMomentum({ allTracks, trendData, isLoading }: Props) {
  const momentum = useMemo((): ArtistMoment[] => {
    const artistMap = new Map<string, { name: string; trackIds: string[]; followers?: number }>()
    allTracks.forEach(track => {
      const a = track.artists?.[0]
      if (!a) return
      const key = a.id
      if (!key) return
      if (!artistMap.has(key)) artistMap.set(key, { name: a.name, trackIds: [], followers: track.artist_followers })
      artistMap.get(key)!.trackIds.push(track.track_id ?? '')
    })

    const results: ArtistMoment[] = []
    artistMap.forEach((data, key) => {
      let deltaSum = 0
      let allNew = true
      let hasAnyTrend = false

      data.trackIds.forEach(tid => {
        if (!tid) return
        const t = trendData.get(tid)
        if (!t) return
        hasAnyTrend = true
        if (t.badge === 'new') {
          deltaSum += 1
        } else {
          allNew = false
          deltaSum += t.badge === 'up' ? (t.delta ?? 0) : -(t.delta ?? 0)
        }
      })

      const followers = data.followers
      const tier = followers == null ? null
        : followers < 1_000_000 ? '<1M'
        : followers < 5_000_000 ? '1M–5M'
        : '5M+'

      results.push({
        profileKey: key,
        name: data.name,
        trackCount: data.trackIds.length,
        delta: hasAnyTrend ? deltaSum : null,
        allNew: hasAnyTrend && allNew,
        followerTier: tier,
      })
    })

    return results.sort((a, b) => b.trackCount - a.trackCount).slice(0, 10)
  }, [allTracks, trendData])

  const hasTrend = trendData.size > 0

  return (
    <div className={styles.container}>
      <h3 className={styles.title}>Artist Momentum</h3>
      {isLoading && <p className={styles.empty}>Loading momentum…</p>}
      {!isLoading && !hasTrend && (
        <p className={styles.empty}>Connect Supabase for trend data</p>
      )}
      <ul className={styles.list}>
        {momentum.map((a, i) => (
          <li key={a.profileKey} className={styles.item}>
            <span className={styles.rank}>{i + 1}</span>
            <span className={styles.name}>{a.name}</span>
            {a.followerTier && <span className={styles.tier}>{a.followerTier}</span>}
            <span className={styles.tracks}>{a.trackCount} tracks</span>
            {hasTrend && a.delta !== null && (
              <span className={a.allNew ? styles.badgeNew : a.delta > 0 ? styles.badgeUp : a.delta < 0 ? styles.badgeDown : styles.badgeFlat}>
                {a.allNew ? 'NEW' : a.delta > 0 ? `▲${a.delta}` : a.delta < 0 ? `▼${Math.abs(a.delta)}` : '◆'}
              </span>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
