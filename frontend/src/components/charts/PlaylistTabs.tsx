import styles from './PlaylistTabs.module.css'

interface Props {
  playlistNames: string[]
  activeTab: string
  onTabChange: (tab: string) => void
}

/** Convert a playlist name to the tab slug used as the active tab key. */
export function toTabSlug(name: string): string {
  return name.replace(/[ /]/g, '-')
}

/** Strip "Top " / " - " for a shorter button label, matching the Jinja2 template. */
function toTabLabel(name: string): string {
  return name.replace(/^Top /, '').replace(/ - /g, ' ')
}

export default function PlaylistTabs({ playlistNames, activeTab, onTabChange }: Props) {
  return (
    <div className={styles.tabButtons}>
      <button
        className={`${styles.tabButton} ${activeTab === 'all-tracks' ? styles.active : ''}`}
        onClick={() => onTabChange('all-tracks')}
      >
        All Tracks
      </button>
      {playlistNames.map(name => (
        <button
          key={name}
          className={`${styles.tabButton} ${activeTab === toTabSlug(name) ? styles.active : ''}`}
          onClick={() => onTabChange(toTabSlug(name))}
        >
          {toTabLabel(name)}
        </button>
      ))}
    </div>
  )
}
