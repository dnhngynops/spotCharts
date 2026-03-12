import { useState } from 'react'
import type { GenreStat } from '../../lib/types'
import styles from './CollapsibleList.module.css'

interface Props {
  genres: GenreStat[]
  title?: string
}

export default function GenresList({ genres, title = 'Top Genres (All Charts)' }: Props) {
  const [openIdx, setOpenIdx] = useState<number | null>(null)

  if (!genres.length) return null

  return (
    <div className={styles.section}>
      <h2 className={styles.sectionTitle}>{title}</h2>
      <ul className={styles.list}>
        {genres.slice(0, 20).map((genre, i) => {
          const isOpen = openIdx === i
          return (
            <li key={genre.name} className={styles.listItem}>
              <div className={styles.itemRow}>
                <span className={styles.rank}>{i + 1}</span>
                <span className={styles.name}>{genre.name}</span>
                <span className={styles.stats}>
                  <span className={styles.chartCount}>{genre.playlists} charts</span>
                  <button
                    className={`${styles.badge} ${isOpen ? styles.badgeOpen : ''}`}
                    onClick={() => setOpenIdx(isOpen ? null : i)}
                    aria-expanded={isOpen}
                  >
                    {genre.count} tracks
                  </button>
                </span>
              </div>
              <ul className={`${styles.dropdown} ${isOpen ? styles.dropdownOpen : ''}`}>
                {genre.tracks.map((t, ti) => (
                  <li key={ti} className={styles.dropdownItem}>
                    <span className={styles.dropdownTrackName}>
                      {t.spotify_url
                        ? <a href={t.spotify_url} target="_blank" rel="noreferrer">{t.track_name}</a>
                        : t.track_name}
                    </span>
                    <span className={styles.dropdownMeta}> — {t.artist}</span>
                    {t.playlist && (
                      <span className={styles.dropdownMeta}>, {t.playlist.replace(/ - /g, ' ')}</span>
                    )}
                  </li>
                ))}
              </ul>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
