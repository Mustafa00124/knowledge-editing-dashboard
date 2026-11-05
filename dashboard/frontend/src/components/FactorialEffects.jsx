import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { duration, formatValue } from '../lib/hparams.js'

// Effects of a two-level factorial sweep (step 1): per method, model and
// dataset, each setting's main effect and each pair's interaction on rewrite,
// the fluency gate and edit time, judged against Lenth's noise estimate.

const VERDICT = {
  strong: { text: 'strong', title: 'beyond the simultaneous margin (SME): real even allowing for testing every effect' },
  active: { text: 'real', title: 'beyond the margin of error (ME) from Lenth’s pseudo standard error' },
  noise: { text: '', title: 'within the margin of error: indistinguishable from noise' },
}

function fmt(value, unit) {
  if (value == null) return 'n/a'
  if (unit === 'seconds') return `${value >= 0 ? '+' : '−'}${duration(Math.abs(value))}`
  return `${value >= 0 ? '+' : '−'}${Math.abs(value).toFixed(2)}`
}

function level(value, unit) {
  if (value == null) return 'n/a'
  return unit === 'seconds' ? duration(value) : value.toFixed(2)
}

function Verdict({ verdict }) {
  if (!verdict || verdict === 'noise') return null
  return <span className={`hp-flag ${verdict === 'strong' ? 'is-error' : 'is-warn'}`} title={VERDICT[verdict].title}>{VERDICT[verdict].text}</span>
}

function Noise({ analysis, unit }) {
  if (!analysis.noise || analysis.noise.me == null) return <span className="dl-dim">{analysis.noise_note || 'too few runs to estimate noise'}</span>
  return (
    <span className="dl-dim" title="Lenth's method: pseudo standard error from the smaller effects; ME is the 95% margin for one effect, SME allows for testing them all">
      noise: PSE {level(analysis.noise.pse, unit)}, ME {level(analysis.noise.me, unit)}, SME {level(analysis.noise.sme, unit)}
      {' '}over {analysis.noise.m} contrasts
    </span>
  )
}

function Curvature({ c, unit }) {
  if (!c) return null
  const verdict = c.significant == null ? 'not tested (needs two or more centre runs)' : c.significant ? 'real' : 'within noise'
  return (
    <div className="dl-dim" title="A two-level design only sees straight lines: if the middle beats the corners, the best value may lie between low and high">
      Centre vs corners: {level(c.centre_mean, unit)} vs {level(c.corner_mean, unit)} ({fmt(c.difference, unit)}, {verdict}, {c.centre_runs} centre run{c.centre_runs === 1 ? '' : 's'})
    </div>
  )
}

function ResponseBlock({ response, analysis, design }) {
  const [allPairs, setAllPairs] = useState(false)
  const unit = response.unit
  if (!analysis || !analysis.main?.length) {
    return <div className="hp-effects-response"><h4>{response.label}</h4><p className="dl-dim">Not enough finished runs yet ({analysis?.used ?? 0} of {analysis?.runs ?? 0}).</p></div>
  }
  const pairs = allPairs ? analysis.interactions : analysis.interactions.filter((i, n) => n < 5 || (i.verdict && i.verdict !== 'noise'))
  const main = [...analysis.main].sort((a, b) => Math.abs(b.effect ?? 0) - Math.abs(a.effect ?? 0))
  return (
    <div className="hp-effects-response">
      <h4 title={response.help}>{response.label}</h4>
      <div><Noise analysis={analysis} unit={unit} /></div>
      {!analysis.complete && <div className="dl-bar-warning">Approximate: {analysis.used} of {analysis.runs} corner runs have this response, so the contrasts are not balanced.</div>}
      <div className="table-wrap">
        <table className="hp-table">
          <thead>
            <tr>
              <th>Setting</th><th title="mean at high minus mean at low">Effect</th>
              <th>Mean at low</th><th>Mean at high</th>
              {unit === 'seconds' && <th title="mean time at high over mean time at low">High / low</th>}
              <th />
            </tr>
          </thead>
          <tbody>
            {main.map((m) => (
              <tr key={m.factor}>
                <td><code>{m.factor}</code> <span className="dl-dim">{formatValue(design.levels?.[m.factor]?.low)} → {formatValue(design.levels?.[m.factor]?.high)}</span>
                  {m.aliases?.length ? <div className="dl-dim">aliased with {m.aliases.join(', ')}</div> : null}</td>
                <td><strong>{fmt(m.effect, unit)}</strong></td>
                <td>{level(m.low_mean, unit)}</td>
                <td>{level(m.high_mean, unit)}</td>
                {unit === 'seconds' && <td>{m.ratio == null ? 'n/a' : `${m.ratio.toFixed(2)}x`}</td>}
                <td><Verdict verdict={m.verdict} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="table-wrap">
        <table className="hp-table">
          <thead><tr><th>Pair</th><th title="half of: the first setting's effect at the second's high value minus its effect at the second's low value">Interaction</th><th /></tr></thead>
          <tbody>
            {pairs.map((i) => (
              <tr key={i.factors.join('|')}>
                <td><code>{i.factors[0]}</code> × <code>{i.factors[1]}</code>
                  {i.aliases?.length ? <div className="dl-dim">aliased with {i.aliases.join(', ')}</div> : null}</td>
                <td>{fmt(i.effect, unit)}</td>
                <td><Verdict verdict={i.verdict} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {analysis.interactions.length > pairs.length || allPairs ? (
        <button type="button" className="btn-plain-small" onClick={() => setAllPairs((v) => !v)}>
          {allPairs ? 'Show the largest pairs only' : `Show all ${analysis.interactions.length} pairs`}
        </button>
      ) : null}
      <Curvature c={analysis.curvature} unit={unit} />
    </div>
  )
}

function Group({ group, timeRule }) {
  const d = group.design
  return (
    <div className="card hp-effects-group">
      <div className="card-title">
        {group.method} · {group.model_label} <span className="dl-dim">· {group.dataset}</span>
      </div>
      <div className="card-sub">
        {d.runs} corner runs ({d.p ? `2^(${d.k}-${d.p}), resolution ${d.resolution}, ${d.generators.join(', ')}` : `full 2^${d.k}`})
        {' '}+ {d.centre_points} centre runs; {group.finished} of {group.total} runs scored.
        {d.notes?.length ? ` ${d.notes.join('. ')}.` : ''}
      </div>
      <h4>Suggested level per setting</h4>
      <p className="dl-dim">
        From the main effects: the level with more rewrite when the effect is real, unless it is slower and gains under
        {' '}{timeRule} rewrite; with no real rewrite effect, the level that keeps fluency more often, else the faster one. Hints only.
      </p>
      <div className="table-wrap">
        <table className="hp-table">
          <thead><tr><th>Setting</th><th>Keep</th><th>Why</th></tr></thead>
          <tbody>
            {Object.entries(group.suggestions).map(([factor, s]) => (
              <tr key={factor}>
                <td><code>{factor}</code></td>
                <td>{s.level ? <><strong>{s.level}</strong> <span className="dl-dim">{formatValue(s.value)}</span></> : 'n/a'}</td>
                <td className="dl-dim">{s.text}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="hp-effects-grid">
        {group.responses.map((r) => <ResponseBlock key={r.key} response={r} analysis={group.analyses[r.key]} design={d} />)}
      </div>
    </div>
  )
}

export default function FactorialEffects({ investigation, sweepIds }) {
  const [sweepId, setSweepId] = useState(sweepIds[0] || '')
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  useEffect(() => {
    if (!sweepIds.includes(sweepId)) setSweepId(sweepIds[0] || '')
  }, [sweepIds.join(',')])
  useEffect(() => {
    if (!sweepId) return
    let live = true
    setData(null)
    setError(null)
    api.sweepEffects(investigation, sweepId).then((d) => { if (live) setData(d) }).catch((e) => { if (live) setError(e.message) })
    return () => { live = false }
  }, [investigation, sweepId])
  if (!sweepIds.length) return null
  return (
    <section className="dl-section">
      <h2 className="section-heading">Effects</h2>
      <p className="dl-dim">
        An effect is the mean at a setting’s high value minus the mean at its low value, over every other setting’s values;
        a pair’s interaction is how much one setting’s effect changes with the other. Rewrite and edit time are scored
        per run; the fluency gate is 1 for a run that keeps fluency and grammar and 0 for one that does not, so a failed
        run counts there and never as a rewrite of 0. Runs that crashed or have not finished are left out.
      </p>
      <label className="hp-filter">Sweep{' '}
        <select value={sweepId} onChange={(e) => setSweepId(e.target.value)}>
          {sweepIds.map((id) => <option key={id} value={id}>{id}</option>)}
        </select>
      </label>
      {error && <p className="form-error">{error}</p>}
      {!data && !error && <p className="empty">Loading…</p>}
      {data && data.groups.map((g) => <Group key={`${g.method}|${g.model}|${g.data_path}`} group={g} timeRule={data.time_rule} />)}
    </section>
  )
}
