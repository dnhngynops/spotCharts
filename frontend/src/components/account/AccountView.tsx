import styles from './AccountView.module.css'

export default function AccountView() {
  return (
    <div className={styles.container}>
      <div className={styles.content}>
        <svg className={styles.icon} width="48" height="48" viewBox="0 0 18 18" fill="currentColor">
          <circle cx="9" cy="6" r="4"/>
          <path d="M1 17c0-4.4 3.6-8 8-8s8 3.6 8 8H1z"/>
        </svg>
        <h2>Account</h2>
        <p>Account settings — coming soon.</p>
      </div>
    </div>
  )
}
