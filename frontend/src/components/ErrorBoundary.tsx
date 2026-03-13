import { Component, ReactNode, ErrorInfo } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('App error boundary caught:', error, info)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          background: '#131C25',
          color: '#C8D0D8',
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: 'Roboto, sans-serif',
          gap: '16px',
          padding: '40px',
          textAlign: 'center',
        }}>
          <h1 style={{ color: '#58C69D', fontSize: '1.5em', fontWeight: 600, margin: 0 }}>
            Dashboard Unavailable
          </h1>
          <p style={{ color: '#8C96A1', maxWidth: '480px', margin: 0, lineHeight: 1.6 }}>
            {this.state.error?.message || 'An unexpected error occurred.'}
          </p>
          <button
            onClick={() => window.location.reload()}
            style={{
              background: 'rgba(88,198,157,0.15)',
              border: '1px solid #58C69D',
              color: '#58C69D',
              padding: '8px 20px',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
              marginTop: '8px',
            }}
          >
            Reload
          </button>
        </div>
      )
    }

    return this.props.children
  }
}
