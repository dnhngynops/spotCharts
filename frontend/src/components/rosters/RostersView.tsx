import styles from './RostersView.module.css'

export default function RostersView() {
  return (
    <div className={styles.container}>
      <div className={styles.content}>
        <svg className={styles.icon} width="48" height="48" viewBox="0 0 18 18" fill="currentColor">
          <circle cx="6"  cy="5" r="3"/>
          <circle cx="12" cy="5" r="3"/>
          <path d="M0 16c0-3.3 2.7-6 6-6s6 2.7 6 6H0z"/>
          <path d="M12 10c1.5 0 6 .8 6 3v3h-6v-3c0-1-.4-1.9-1-2.6A5.9 5.9 0 0 1 12 10z"/>
        </svg>
        <h2>Rosters</h2>
        <p>A&amp;R roster management — coming soon.</p>
      </div>
    </div>
  )
}
