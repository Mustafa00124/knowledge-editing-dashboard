import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api.js'
import ExperimentsSubnav from '../components/ExperimentsSubnav.jsx'
import { GROUP_HELP, GROUP_LABEL, GROUP_ORDER, TUNING_KINDS } from '../lib/hparams.js'

// Launch summary keys for the two kinds of main experiment, not investigations.
const NOT_INVESTIGATIONS = ['main', 'in_context']

// Hyperparameter tuning: one card per method family, tuned in two kinds of
// sweep (a Latin hypercube screen, then stage-wise), and below them the
// supporting investigations (where models keep knowledge, prompt formats)
// that inform the settings. Each card opens its own page; a planned one is
// listed but not built yet.
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

  const sweepCount = (id, kind) => sweeps.filter((s) => s.investigation === id && (kind ? s.kind === kind : s.kind !== 'setup')).length

  function card(inv) {
    const planned = inv.status === 'planned'
    const body = (
      <>
        <div className="card-header">
          <span className="card-title">{inv.label}</span>
          {planned && <span className="badge">planned</span>}
          {running[inv.id] && <span className="badge badge-running">{running[inv.id].running} running{running[inv.id].waiting ? `, ${running[inv.id].waiting} waiting` : ''}</span>}
          {!planned && inv.group === 'sweep'
            ? TUNING_KINDS.filter((k) => sweepCount(inv.id, k.key)).map((k) => (
              <span key={k.key} className="badge">{sweepCount(inv.id, k.key)} {k.label.toLowerCase()}</span>))
            : !planned && sweepCount(inv.id) > 0 && <span className="badge">{sweepCount(inv.id)} sweep{sweepCount(inv.id) === 1 ? '' : 's'}</span>}
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
        <h1>Hyperparameter tuning</h1>
        <Link to="/results/investigations" className="btn-plain-small">Tuning results →</Link>
      </div>
      <p className="hp-intro">
        Picks each method’s settings for the main experiments. Sweeps edit <strong>dev records only</strong>, which
        main experiments never use. A setting is chosen by edit success on the direct question (rewrite) among runs that
        keep at least 85% of the unedited model’s fluency; paraphrase, generalization and locality are recorded beside it.
      </p>
      <ol className="tuning-kinds">
        {TUNING_KINDS.map((k) => (
          <li key={k.key} className="card tuning-kind">
            <div className="card-title">{k.label} <span className="dl-dim">· {k.short}</span></div>
            <div className="card-sub">{k.help}</div>
          </li>
        ))}
      </ol>
      {error && <p className="form-error">{error}</p>}
      {investigations && Object.keys(running).some((id) => !NOT_INVESTIGATIONS.includes(id)) && (
        <section className="dl-section inv-running-now">
          <h2 className="section-heading">Running now</h2>
          <ul className="inv-running-list">
            {Object.entries(running).filter(([id]) => !NOT_INVESTIGATIONS.includes(id)).map(([id, r]) => {
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
      {investigations && GROUP_ORDER.filter((g) => investigations.some((i) => i.group === g)).map((group, index) => (
        <section key={group} className="hp-category">
          {index === 1 && (
            <p className="hp-supporting">
              <strong>Supporting investigations.</strong> Not tuning sweeps: they measure where each model keeps
              knowledge and how prompt format changes a result, which the tuning uses (layer suggestions, prompt format).
            </p>
          )}
          <h2 className="section-heading">
            {GROUP_LABEL[group]} <span className="hp-category-help">{GROUP_HELP[group]}</span>
          </h2>
          <div className="card-grid">
            {investigations.filter((i) => i.group === group && !i.legacy).map(card)}
          </div>
          {investigations.some((i) => i.group === group && i.legacy) && (
            <details className="inv-legacy">
              <summary>Earlier sweeps, by kind of setting</summary>
              <p className="dl-dim">
                Sweeps from before the investigations were organised by method family. Their results stay readable
                here and on Results · Hyperparameter tuning; new sweeps start from the family above.
              </p>
              <div className="card-grid">
                {investigations.filter((i) => i.group === group && i.legacy).map(card)}
              </div>
            </details>
          )}
        </section>
      ))}
    </div>
  )
}
