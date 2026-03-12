import type { Analytics } from '../../lib/types'
import styles from './AlbumDominance.module.css'

interface Props {
  albumDominance: Analytics['album_dominance']
}

export default function AlbumDominance({ albumDominance }: Props) {
  if (!albumDominance || albumDominance.length === 0) return null

  return (
    <div className={styles.section}>
      <h2 className={styles.sectionTitle}>Album Dominance</h2>
      <div className={styles.grid}>
        {albumDominance.slice(0, 8).map((album, i) => (
          <div key={i} className={styles.card}>
            {album.album_image && (
              <img src={album.album_image} alt={album.album} className={styles.albumCover} />
            )}
            <div className={styles.info}>
              <div className={styles.albumName}>
                {album.album_url ? (
                  <a href={album.album_url} target="_blank" rel="noreferrer">{album.album}</a>
                ) : (
                  album.album
                )}
              </div>
              <div className={styles.artist}>{album.artist}</div>
              <div className={styles.stats}>
                <div className={styles.statItem}>
                  <span className={styles.statValue}>{album.track_count}</span>
                  <span className={styles.statLabel}>Tracks</span>
                </div>
                <div className={styles.statItem}>
                  <span className={styles.statValue}>{album.playlist_count}</span>
                  <span className={styles.statLabel}>Playlists</span>
                </div>
                <div className={styles.statItem}>
                  <span className={styles.statValue}>{album.avg_popularity.toFixed(1)}</span>
                  <span className={styles.statLabel}>Avg Pop</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
