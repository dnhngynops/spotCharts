import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createHashRouter, RouterProvider } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import './index.css'
import App from './App'
import ChartsView from './components/charts/ChartsView'
import DealProjectorView from './components/deal-projector/DealProjectorView'
import RostersView from './components/rosters/RostersView'
import AccountView from './components/account/AccountView'
import { ErrorBoundary } from './components/ErrorBoundary'

// createHashRouter: URLs look like /#/rosters
// No 404 redirect config needed on GitHub Pages — the hash is handled client-side.
const router = createHashRouter([
  {
    path: '/',
    element: <App />,
    children: [
      { index: true,              element: <ChartsView /> },
      { path: 'deal-projector',   element: <DealProjectorView /> },
      { path: 'rosters',          element: <RostersView /> },
      { path: 'account',          element: <AccountView /> },
    ],
  },
])

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 60,  // 1hr — pipeline runs at most once daily
      retry: 1,
    },
  },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    </ErrorBoundary>
  </StrictMode>,
)
