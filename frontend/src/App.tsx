import { Outlet } from 'react-router-dom'
import Sidebar from './components/layout/Sidebar'
import ProfileModal from './components/shared/ProfileModal'
import { ModalProvider } from './contexts/ModalContext'
import styles from './App.module.css'

export default function App() {
  return (
    <ModalProvider>
      <div className={styles.layout}>
        <Sidebar />
        <main className={styles.mainContent}>
          <Outlet />
        </main>
      </div>
      {/* ProfileModal mounted once at root — triggered by openModal() from any child */}
      <ProfileModal />
    </ModalProvider>
  )
}
