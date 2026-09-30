import { Suspense, lazy } from 'react'
import { Routes, Route, NavLink, Navigate, useLocation } from 'react-router-dom'
import Home from './pages/Home.jsx'
import Experiments from './pages/Experiments.jsx'
import CausalTracing from './pages/CausalTracing.jsx'
import Hyperparameters from './pages/Hyperparameters.jsx'
import HyperparameterInvestigation from './pages/HyperparameterInvestigation.jsx'
import Datasets from './pages/Datasets.jsx'
import Models from './pages/Models.jsx'
import Methods from './pages/Methods.jsx'
import Downloads from './pages/Downloads.jsx'
import ThemeSwitcher from './components/ThemeSwitcher.jsx'

// Separate pages, loaded only when opened: choosing Main never fetches sweep
// data, and choosing Hyperparameters never fetches the main results.
const MainResults = lazy(() => import('./pages/Results.jsx'))
const HyperparameterResults = lazy(() => import('./pages/HyperparameterResults.jsx'))

const linkClass = ({ isActive }) => (isActive ? 'active' : '')

// One accent hue per page - purely a wayfinding cue, the base theme
// (colors, glass, everything else) stays the same everywhere. Home ("/")
// gets no entry here, so it always shows each theme's own signature
// accent unshifted - it's the "base" the other pages rotate away from.
const PAGE_ACCENT_CLASS = {
  '/datasets': 'accent-datasets',
  '/models': 'accent-models',
  '/methods': 'accent-methods',
  '/experiments': 'accent-experiments',
  '/results': 'accent-results',
  '/hyperparameters': 'accent-tracing',
  '/downloads': 'accent-models',
}

export default function App() {
  const location = useLocation()
  const section = '/' + (location.pathname.split('/')[1] || '')
  const accentClass = PAGE_ACCENT_CLASS[location.pathname] || PAGE_ACCENT_CLASS[section] || ''

  return (
    <div className="app">
      <nav className="topnav">
        <NavLink to="/" end className="brand brand-link">Knowledge-Editing Dashboard</NavLink>
        <div className="navlinks">
          <NavLink to="/datasets" className={linkClass}>Datasets</NavLink>
          <NavLink to="/models" className={linkClass}>Models</NavLink>
          <NavLink to="/methods" className={linkClass}>Methods</NavLink>
          <NavLink to="/experiments" className={linkClass}>Experiments</NavLink>
          <NavLink to="/hyperparameters" className={linkClass}>Hyperparameters</NavLink>
          <NavLink to="/results" className={linkClass}>Results</NavLink>
          <NavLink to="/downloads" className={linkClass}>Downloads</NavLink>
        </div>
        <ThemeSwitcher />
      </nav>
      <main className={`content ${accentClass}`}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/datasets" element={<Datasets />} />
          <Route path="/models" element={<Models />} />
          <Route path="/methods" element={<Methods />} />
          <Route path="/experiments" element={<Experiments />} />
          <Route path="/hyperparameters" element={<Hyperparameters />} />
          <Route path="/hyperparameters/edit_layers/causal-tracing" element={<CausalTracing />} />
          <Route path="/hyperparameters/:investigationId" element={<HyperparameterInvestigation />} />
          <Route path="/causal-tracing" element={<Navigate to="/hyperparameters/edit_layers/causal-tracing" replace />} />
          <Route path="/results" element={<Navigate to="/results/main" replace />} />
          <Route path="/results/main" element={<Suspense fallback={<p className="empty">Loading…</p>}><MainResults /></Suspense>} />
          <Route path="/results/hyperparameters" element={<Suspense fallback={<p className="empty">Loading…</p>}><HyperparameterResults /></Suspense>} />
          <Route path="/downloads" element={<Downloads />} />
        </Routes>
      </main>
    </div>
  )
}
