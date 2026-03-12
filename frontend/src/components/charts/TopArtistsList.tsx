import type { TopArtist } from '../../lib/types'
import { useModal } from '../../contexts/ModalContext'
import styles from './CollapsibleList.module.css'

interface Props {
  artists: TopArtist[]
  title?: string
  followerMap?: Map<string, number>
}

function followerTierLabel(followers: number): string {
  if (followers < 1_000_000) return '<1M'
  if (followers < 5_000_000) return '1M–5M'
  return '5M+'
}

export default function TopArtistsList({ artists, title = 'Top Artists (All Charts)', followerMap }: Props) {
  const { openModal } = useModal()

  if (!artists.length) return null

  return (
    <div className={styles.section}>
      <h2 className={styles.sectionTitle}>{title}</h2>
      <ul className={styles.list}>
        {artists.slice(0, 20).map((artist, i) => {
          const followers = followerMap?.get(artist.profile_key)
          const tier = followers != null ? followerTierLabel(followers) : null
          return (
            <li key={artist.profile_key || artist.name} className={styles.listItem}>
              <div className={styles.itemRow}>
                <span className={styles.rank}>{i + 1}</span>
                <span className={styles.name}>
                  <span
                    className={styles.nameLink}
                    onClick={() => openModal('artist', artist.profile_key)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={e => e.key === 'Enter' && openModal('artist', artist.profile_key)}
                  >
                    {artist.name}
                  </span>
                </span>
                <span className={styles.stats}>
                  <span className={styles.chartCount}>{artist.playlists} charts</span>
                  {tier && <span className={styles.followerTier}>{tier}</span>}
                  <span className={styles.badge}>{artist.count} tracks</span>
                </span>
              </div>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
