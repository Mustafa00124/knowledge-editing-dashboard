import { Suspense, lazy } from 'react'
import { Routes, Route, NavLink, Navigate, useLocation, useParams } from 'react-router-dom'
import Home from './pages/Home.jsx'
import Experiments from './pages/Experiments.jsx'
import CausalTracing from './pages/CausalTracing.jsx'
import TracingFormats from './pages/TracingFormats.jsx'
import NeuronTracing from './pages/NeuronTracing.jsx'
import CircuitTracing from './pages/CircuitTracing.jsx'
import Investigations from './pages/Investigations.jsx'
import SweepInvestigation from './pages/SweepInvestigation.jsx'
import Datasets from './pages/Datasets.jsx'
import Models from './pages/Models.jsx'
import Methods from './pages/Methods.jsx'
import Downloads from './pages/Downloads.jsx'
import ThemeSwitcher from './components/ThemeSwitcher.jsx'

// Separate pages, loaded only when opened: choosing Main never fetches sweep
// data, and choosing Investigations never fetches the main results.
const MainResults = lazy(() => import('./pages/Results.jsx'))
const InvestigationResults = lazy(() => import('./pages/InvestigationResults.jsx'))

// Old /hyperparameters links (bookmarks, notes) land on the same page under
// its new address, query string and investigation id included.
function Moved({ to }) {
  const { search } = useLocation()
  const { investigationId } = useParams()
  return <Navigate to={to.replace(':investigationId', investigationId || '') + search} replace />
}

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
          <Route path="/experiments/investigations" element={<Investigations />} />
          <Route path="/experiments/investigations/causal_tracing" element={<CausalTracing />} />
          <Route path="/experiments/investigations/tracing_formats" element={<TracingFormats />} />
          <Route path="/experiments/investigations/neuron_tracing" element={<NeuronTracing />} />
          <Route path="/experiments/investigations/circuit_tracing" element={<CircuitTracing />} />
          <Route path="/experiments/investigations/:investigationId" element={<SweepInvestigation />} />
          <Route path="/hyperparameters" element={<Moved to="/experiments/investigations" />} />
          <Route path="/hyperparameters/edit_layers/causal-tracing" element={<Moved to="/experiments/investigations/causal_tracing" />} />
          <Route path="/hyperparameters/:investigationId" element={<Moved to="/experiments/investigations/:investigationId" />} />
          <Route path="/causal-tracing" element={<Moved to="/experiments/investigations/causal_tracing" />} />
          <Route path="/results" element={<Navigate to="/results/main" replace />} />
          <Route path="/results/main" element={<Suspense fallback={<p className="empty">Loading…</p>}><MainResults /></Suspense>} />
          <Route path="/results/investigations" element={<Suspense fallback={<p className="empty">Loading…</p>}><InvestigationResults /></Suspense>} />
          <Route path="/results/hyperparameters" element={<Moved to="/results/investigations" />} />
          <Route path="/downloads" element={<Downloads />} />
        </Routes>
      </main>
    </div>
  )
}
