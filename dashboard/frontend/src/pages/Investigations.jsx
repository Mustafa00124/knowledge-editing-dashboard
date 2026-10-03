import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api.js'
import ExperimentsSubnav from '../components/ExperimentsSubnav.jsx'
import { GROUP_HELP, GROUP_LABEL, GROUP_ORDER } from '../lib/hparams.js'

// The investigations, grouped by what kind of experiment they are. Each card
// opens its own page; a planned one is listed but not built yet.
export default function Investigations() {
  const [investigations, setInvestigations] = useState(null)
  const [sweeps, setSweeps] = useState([])
  const [running, setRunning] = useState({})
  const [error, setError] = useState(null)

  useEffect(() => {
    api.investigations().then(setInvestigations).catch((e) => setError(e.message))
    api.sweeps().then(setSweeps).catch(() => {})
    // What is running now, per investigation, whoever launched it.
    const loadRunning = () => api.launchSummary().then(setRunning).catch(() => {})
    loadRunning()
    const timer = setInterval(loadRunning, 8000)
    return () => clearInterval(timer)
  }, [])

  const sweepCount = (id) => sweeps.filter((s) => s.investigation === id).length

  function card(inv) {
    const planned = inv.status === 'planned'
    const body = (
      <>
        <div className="card-header">
          <span className="card-title">{inv.label}</span>
          {planned && <span className="badge">planned</span>}
          {running[inv.id] && <span className="badge badge-running">{running[inv.id].running} running{running[inv.id].waiting ? `, ${running[inv.id].waiting} waiting` : ''}</span>}
          {!planned && sweepCount(inv.id) > 0 && <span className="badge">{sweepCount(inv.id)} sweep{sweepCount(inv.id) === 1 ? '' : 's'}</span>}
        </div>
        <div className="card-sub">{inv.question}</div>
        {inv.scope === 'model' ? (
          <div className="hp-tool-note">Per model: no editing method involved</div>
        ) : (
          <div className="hp-method-chips">
            {inv.methods.map((m) => (
              <span key={m.method} className={`chip-pill${m.available ? '' : ' is-off'}`}>{m.label}</span>
            ))}
          </div>
        )}
      </>
    )
    return planned
      ? <div key={inv.id} className="card hp-card is-planned" aria-disabled="true">{body}</div>
      : <Link key={inv.id} to={`/experiments/investigations/${inv.id}`} className="card hp-card">{body}</Link>
  }

  return (
    <div>
      <ExperimentsSubnav />
      <div className="page-header">
        <h1>Investigations</h1>
        <Link to="/results/investigations" className="btn-plain-small">Sweep results →</Link>
      </div>
      <p className="hp-intro">
        Experiments that set up the main experiments' configuration, each with its own goal: measure where a model keeps
        knowledge, pick each method's settings, or check how prompt format changes a measurement. Sweeps edit{' '}
        <strong>dev records only</strong>, which main experiments never use, and are scored on reliability,
        generalizability, locality and fluency so a setting cannot win by giving one up.
      </p>
      {error && <p className="form-error">{error}</p>}
      {investigations && Object.keys(running).some((id) => id !== 'main') && (
        <section className="dl-section inv-running-now">
          <h2 className="section-heading">Running now</h2>
          <ul className="inv-running-list">
            {Object.entries(running).filter(([id]) => id !== 'main').map(([id, r]) => {
              const inv = investigations.find((i) => i.id === id)
              return (
                <li key={id}>
                  <Link to={`/experiments/investigations/${id}`}>{inv?.label || id}</Link>
                  <span className="dl-dim">
                    {' '}{r.launches} launch{r.launches === 1 ? '' : 'es'}: {r.running} running, {r.waiting} waiting
                    {r.by_agent ? ` · ${r.by_agent} by an agent` : ''}
                  </span>
                </li>
              )
            })}
          </ul>
        </section>
      )}
      {!investigations && !error && <p className="empty">Loading…</p>}
      {investigations && GROUP_ORDER.filter((g) => investigations.some((i) => i.group === g)).map((group) => (
        <section key={group} className="hp-category">
          <h2 className="section-heading">
            {GROUP_LABEL[group]} <span className="hp-category-help">{GROUP_HELP[group]}</span>
          </h2>
          <div className="card-grid">
            {investigations.filter((i) => i.group === group).map(card)}
          </div>
        </section>
      ))}
    </div>
  )
}
