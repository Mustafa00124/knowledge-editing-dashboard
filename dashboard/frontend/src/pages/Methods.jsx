import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { METHOD_DETAILS, FAMILY_DETAILS } from '../lib/methodDetails.js'

function MethodRow({ method, detail, open, onToggle }) {
  return (
    <div className="method-row">
      <button
        type="button"
        className={`method-row-header${method.available === false ? ' unavailable' : ''}`}
        aria-expanded={open}
        onClick={onToggle}
      >
        <span className="method-row-toggle">{open ? '▾' : '▸'}</span>
        <span className="method-row-label">{method.label}</span>
        {detail?.tagline && <span className="method-row-tagline">{detail.tagline}</span>}
        {method.available === false && <span className="method-row-badge">not wired up yet</span>}
        {method.note && <span className="method-row-note" title={method.note}>ⓘ</span>}
      </button>
      {open && (
        <div className="method-detail">
          {detail?.paper && <p className="method-detail-paper">{detail.paper}</p>}
          {detail?.howItWorks && (
            <div className="method-detail-section">
              <h4>How it works</h4>
              <p>{detail.howItWorks}</p>
            </div>
          )}
          {detail?.stepMeaning && (
            <div className="method-detail-section">
              <h4>What a "step" means here</h4>
              <p>{detail.stepMeaning}</p>
            </div>
          )}
          {detail?.keyHyperparams?.length > 0 && (
            <div className="method-detail-section">
              <h4>Key hyperparameters</h4>
              <dl className="method-hparams">
                {detail.keyHyperparams.map((h) => (
                  <div key={h.name}>
                    <dt>{h.name}</dt>
                    <dd>{h.meaning}</dd>
                  </div>
                ))}
              </dl>
            </div>
          )}
          {detail?.files?.length > 0 && (
            <div className="method-detail-section">
              <h4>Implementation</h4>
              <ul className="method-files">
                {detail.files.map((f) => (
                  <li key={f.path}>
                    <code>{f.path}</code>
                    {f.note && <span>: {f.note}</span>}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {detail?.caveats?.length > 0 && (
            <div className="method-detail-section">
              {detail.caveats.map((c, i) => (
                <p key={i} className="dataset-note">
                  {c}
                </p>
              ))}
            </div>
          )}
          {method.note && <p className="dataset-note">{method.note}</p>}
          {!detail && <p className="dataset-note">No details written up for this method yet.</p>}
        </div>
      )}
    </div>
  )
}

export default function Methods() {
  const [families, setFamilies] = useState(null)
  const [openKeys, setOpenKeys] = useState(new Set())

  useEffect(() => {
    api.experimentTypes().then((types) => {
      const cfg = types.find((t) => t.name === 'run_experiment') || types[0]
      const methodField = cfg?.fields?.find((f) => f.name === 'method')
      setFamilies(methodField?.categories || [])
    })
  }, [])

  function toggle(value) {
    setOpenKeys((prev) => {
      const next = new Set(prev)
      if (next.has(value)) next.delete(value)
      else next.add(value)
      return next
    })
  }

  return (
    <div>
      <div className="page-header">
        <h1>Knowledge Editing Methods</h1>
      </div>
      <p className="dataset-note">
        Every method any experiment can run, organized by family. Press a method to see how it works, what its
        hyperparameters mean, and which file in this project actually implements it.
      </p>

      {!families && <p className="empty">Loading…</p>}

      {families && (
        <div className="method-tree">
          {families.map((family) => (
            <div className="method-family" key={family.label}>
              <h2 className="method-family-label">{family.label}</h2>
              {FAMILY_DETAILS[family.label] && <p className="method-family-desc">{FAMILY_DETAILS[family.label]}</p>}
              <div className="method-family-methods">
                {family.methods.map((method) => (
                  <MethodRow
                    key={method.value}
                    method={method}
                    detail={METHOD_DETAILS[method.value]}
                    open={openKeys.has(method.value)}
                    onToggle={() => toggle(method.value)}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
