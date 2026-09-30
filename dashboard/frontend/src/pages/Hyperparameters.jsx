import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api.js'
import { CATEGORY_HELP, CATEGORY_ORDER } from '../lib/hparams.js'

// The investigations, grouped by what kind of setting they tune. Each card
// opens its own page for launching sweeps; results live under Results.
export default function Hyperparameters() {
  const [investigations, setInvestigations] = useState(null)
  const [sweeps, setSweeps] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    api.investigations().then(setInvestigations).catch((e) => setError(e.message))
    api.sweeps().then(setSweeps).catch(() => {})
  }, [])

  const sweepCount = (id) => sweeps.filter((s) => s.investigation === id).length

  return (
    <div>
      <div className="page-header">
        <h1>Hyperparameters</h1>
        <Link to="/results/hyperparameters" className="btn-plain-small">Sweep results →</Link>
      </div>
      <p className="hp-intro">
        Find settings that work before the main experiments. Each investigation tunes one kind of setting across the
        methods that have it. Sweeps edit <strong>dev records only</strong>, which main experiments never use, and are
        scored on reliability, generalizability, locality and fluency so a setting cannot win by giving one up.
      </p>
      {error && <p className="form-error">{error}</p>}
      {!investigations && !error && <p className="empty">Loading…</p>}
      {investigations && CATEGORY_ORDER.filter((c) => investigations.some((i) => i.category === c)).map((category) => (
        <section key={category} className="hp-category">
          <h2 className="section-heading">
            {category} <span className="hp-category-help">{CATEGORY_HELP[category]}</span>
          </h2>
          <div className="card-grid">
            {investigations.filter((i) => i.category === category).map((inv) => (
              <Link key={inv.id} to={`/hyperparameters/${inv.id}`} className="card hp-card">
                <div className="card-header">
                  <span className="card-title">{inv.label}</span>
                  {sweepCount(inv.id) > 0 && <span className="badge">{sweepCount(inv.id)} sweep{sweepCount(inv.id) === 1 ? '' : 's'}</span>}
                </div>
                <div className="card-sub">{inv.question}</div>
                <div className="hp-method-chips">
                  {inv.methods.map((m) => (
                    <span key={m.method} className={`chip-pill${m.available ? '' : ' is-off'}`}>{m.label}</span>
                  ))}
                </div>
                {inv.tools?.includes('causal_tracing') && <div className="hp-tool-note">Includes causal tracing</div>}
              </Link>
            ))}
          </div>
        </section>
      ))}
    </div>
  )
}
