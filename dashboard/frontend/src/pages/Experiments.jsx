import { useMemo, useState } from 'react'
import ExperimentsSubnav from '../components/ExperimentsSubnav.jsx'
import ExperimentDrawer from '../components/ExperimentDrawer.jsx'
import GpuQueue from '../components/GpuQueue.jsx'
import InvestigationProgress from '../components/InvestigationProgress.jsx'
import useQueue from '../lib/useQueue.js'

export default function Experiments() {
  const q = useQueue()
  const [drawerOpen, setDrawerOpen] = useState(false)
  // An experiment type with its own page ("queue": false in dashboard.json:
  // in context, the tracing types) is launched from that page's drawer.
  // Memoised: a new array each render would reset the drawer's form.
  const types = useMemo(() => q.experimentTypes.filter((t) => t.queue !== false), [q.experimentTypes])

  return (
    <div>
      <ExperimentsSubnav />
      <div className="page-header">
        <h1>Main experiments</h1>
        <button className="btn-primary" onClick={() => setDrawerOpen(true)}>
          + New Experiment
        </button>
      </div>

      <GpuQueue q={q} />

      <InvestigationProgress investigation="main" />

      <ExperimentDrawer
        open={drawerOpen}
        onToggle={() => setDrawerOpen((o) => !o)}
        onClose={() => setDrawerOpen(false)}
        experimentTypes={types}
        queue={q.queue}
        onSubmit={q.stage}
      />
    </div>
  )
}
