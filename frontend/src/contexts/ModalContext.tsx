import { createContext, useContext, useState, useCallback, type ReactNode } from 'react'

export type ModalType = 'artist' | 'track' | 'album'

interface ModalState {
  type: ModalType | null
  id: string | null
}

interface ModalContextValue {
  modal: ModalState
  openModal: (type: ModalType, id: string) => void
  closeModal: () => void
}

const ModalContext = createContext<ModalContextValue | null>(null)

export function ModalProvider({ children }: { children: ReactNode }) {
  const [modal, setModal] = useState<ModalState>({ type: null, id: null })

  const openModal = useCallback((type: ModalType, id: string) => {
    setModal({ type, id })
  }, [])

  const closeModal = useCallback(() => {
    setModal({ type: null, id: null })
  }, [])

  return (
    <ModalContext.Provider value={{ modal, openModal, closeModal }}>
      {children}
    </ModalContext.Provider>
  )
}

export function useModal(): ModalContextValue {
  const ctx = useContext(ModalContext)
  if (!ctx) throw new Error('useModal must be used inside ModalProvider')
  return ctx
}
