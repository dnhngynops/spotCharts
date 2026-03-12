import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import styles from './Sidebar.module.css'

function IconHamburger() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="currentColor">
      <rect y="2"  width="18" height="2" rx="1"/>
      <rect y="8"  width="18" height="2" rx="1"/>
      <rect y="14" width="18" height="2" rx="1"/>
    </svg>
  )
}

function IconCharts() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="currentColor">
      <rect x="1"  y="8" width="4" height="9" rx="1"/>
      <rect x="7"  y="4" width="4" height="13" rx="1"/>
      <rect x="13" y="1" width="4" height="16" rx="1"/>
    </svg>
  )
}

function IconDollar() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5">
      <circle cx="9" cy="9" r="7.5"/>
      <text x="9" y="13.5" textAnchor="middle" fontSize="9" fill="currentColor" stroke="none"
            fontFamily="Helvetica Neue, Arial, sans-serif">$</text>
    </svg>
  )
}

function IconPeople() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="currentColor">
      <circle cx="6"  cy="5" r="3"/>
      <circle cx="12" cy="5" r="3"/>
      <path d="M0 16c0-3.3 2.7-6 6-6s6 2.7 6 6H0z"/>
      <path d="M12 10c1.5 0 6 .8 6 3v3h-6v-3c0-1-.4-1.9-1-2.6A5.9 5.9 0 0 1 12 10z"/>
    </svg>
  )
}

function IconPerson() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="currentColor">
      <circle cx="9" cy="6" r="4"/>
      <path d="M1 17c0-4.4 3.6-8 8-8s8 3.6 8 8H1z"/>
    </svg>
  )
}

function navClass({ isActive }: { isActive: boolean }) {
  return `${styles.navItem}${isActive ? ` ${styles.active}` : ''}`
}

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(() => {
    try { return localStorage.getItem('sidebarCollapsed') === 'true' }
    catch { return false }
  })

  function toggle() {
    setCollapsed(prev => {
      const next = !prev
      try { localStorage.setItem('sidebarCollapsed', String(next)) } catch { /* ignore */ }
      return next
    })
  }

  const sidebarClass = `${styles.sidebar}${collapsed ? ` ${styles.collapsed}` : ''}`

  return (
    <aside className={sidebarClass}>
      {/* ── Header ── */}
      <div className={styles.sidebarHeader}>
        <button className={styles.sidebarToggle} onClick={toggle} aria-label="Toggle sidebar">
          <IconHamburger />
        </button>
        <span className={styles.sidebarLogo}>
          <img
            src="https://www.milkhoneyla.com/wp-content/uploads/2024/05/MH-Logo.png"
            alt="Milk &amp; Honey"
          />
        </span>
      </div>

      {/* ── Nav ── */}
      <nav className={styles.sidebarNav}>
        <div className={styles.navSectionLabel}>Analytics</div>
        <NavLink to="/" end className={navClass} data-tooltip="Charts">
          <span className={styles.navIcon}><IconCharts /></span>
          <span className={styles.navLabel}>Charts Dashboard</span>
        </NavLink>

        <div className={styles.navSectionLabel}>Tools</div>
        <NavLink to="/deal-projector" className={navClass} data-tooltip="Deal Projector">
          <span className={styles.navIcon}><IconDollar /></span>
          <span className={styles.navLabel}>Deal Projector</span>
        </NavLink>

        <div className={styles.navSectionLabel}>Management</div>
        <NavLink to="/rosters" className={navClass} data-tooltip="Rosters">
          <span className={styles.navIcon}><IconPeople /></span>
          <span className={styles.navLabel}>Rosters</span>
        </NavLink>
      </nav>

      {/* ── Footer ── */}
      <div className={styles.sidebarFooter}>
        <NavLink to="/account" className={navClass} data-tooltip="Account">
          <span className={styles.navIcon}><IconPerson /></span>
          <span className={styles.navLabel}>Account</span>
        </NavLink>
      </div>
    </aside>
  )
}
