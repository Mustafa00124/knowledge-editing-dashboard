import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine, ResponsiveContainer } from 'recharts'
import ExperimentsSubnav from '../components/ExperimentsSubnav.jsx'
import InvestigationProgress from '../components/InvestigationProgress.jsx'
import MechanisticLaunch from '../components/MechanisticLaunch.jsx'
import { api } from '../api.js'
import { SERIES } from '../lib/vizColors.js'
import '../mechanistic.css'

const EXPERIMENT = 'neuron_tracing'
const CONTROLS = ['fact_set', 'format', 'data_path', 'split', 'n_prompts', 'ig_steps', 'threshold', 'max_neurons']
const THIN = 50

const VERDICT_HELP = {
  causal: 'suppressing the selected neurons removes clearly more of the answer than as many random neurons (95% intervals apart), at least a third of it, and other facts lose under half as much',
  partial: 'suppression beats random neurons, but removes little, or hits other facts nearly as hard',
  not_causal: 'suppressing the selected neurons does no more than suppressing random ones',
}

function pct(v) {
  return v == null ? '—' : `${Math.round(v * 100)}%`
}

function ci(pair) {
  return pair ? ` [${pct(pair[0])}–${pct(pair[1])}]` : ''
}

export default function NeuronTracing() {
  const [overview, setOverview] = useState(null)
  const [openRun, setOpenRun] = useState(null)
  const [detail, setDetail] = useState({})
  const [error, setError] = useState(null)

  const load = useCallback(() => {
    api.mechanistic(EXPERIMENT).then(setOverview).catch((e) => setError(String(e.message || e)))
  }, [])
  useEffect(() => { load() }, [load])

  function open(run) {
    const next = openRun === run ? null : run
    setOpenRun(next)
    if (next && detail[next] === undefined) {
      setDetail((previous) => ({ ...previous, [next]: null }))
      api.mechanisticRun(EXPERIMENT, next)
        .then((data) => setDetail((previous) => ({ ...previous, [next]: data })))
        .catch(() => setDetail((previous) => ({ ...previous, [next]: false })))
    }
  }

  const runs = overview?.runs || []
  const summary = runs.find((row) => row.run === openRun)
  const facts = detail[openRun]?.facts

  const layerData = useMemo(() => {
    if (!summary?.layer_share) return []
    return summary.layer_share.map((share, layer) => ({ layer, share, mass: summary.layer_mass?.[layer] }))
  }, [summary])

  return (
    <div>
      <ExperimentsSubnav />
      <div className="hp-breadcrumb">
        <Link to="/experiments/investigations">Investigations</Link> / Neuron attribution
      </div>
      <div className="page-header"><h1>Neuron attribution</h1></div>
      <p className="dataset-note trace-intro">
        Which single MLP neurons carry a fact the model knows: the unit Knowledge Neurons, FiNE and NMKE edit. For each
        fact, every neuron's activation at the last prompt token is scaled from zero to its real value and the gradient
        of the answer's probability integrated along the way (Dai et al.'s integrated gradients). Neurons above a share
        of the fact's largest attribution are its knowledge neurons. Then the claim is tested: switch them off and
        compare with switching off as many random neurons in the same layers, and see how much another fact suffers.
        Same facts and formats as <Link to="/experiments/investigations/causal_tracing">Knowledge localisation</Link>,
        whose traced peak is shown beside the neurons' own. Attribution of this kind tends to favour late layers,
        so a peak far later than the traced one is a known pattern, not a bug.
      </p>
      {error && <p className="archive-line archive-line-warn">{error}</p>}

      <InvestigationProgress investigation="neuron_tracing" />

      <h2 className="archive-section-title">Attribute a model</h2>
      <MechanisticLaunch
        experiment={EXPERIMENT}
        overview={overview}
        controls={CONTROLS}
        verb="Attribute"
        onFinished={load}
        costNote="One SLURM job per model. 100 facts take about 10 to 20 minutes for a 4B to 8B model; the cost grows with integration steps and layers."
        progress={(m) => (m?.peak_layer != null ? `peak layer ${m.peak_layer}, ${m.neurons_per_fact} neurons per fact` : null)}
      />

      <h2 className="archive-section-title">All runs</h2>
      <p className="dataset-note">
        Peak: the layer holding most of the facts' attribution, with causal tracing's peak for the same model in
        brackets. Band: the share of selected neurons in the early-to-mid layers (first half by default), with what an
        even spread would give. Suppression: the share of the answer's probability lost with the fact's neurons off,
        against as many random neurons off; other fact: what the same neurons cost an unrelated fact. Brackets are 95%
        intervals over facts. Click a model for its layers, shared neurons and facts.
      </p>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Model</th><th>Format</th><th>Facts</th><th>Neurons per fact</th><th>Peak (traced)</th>
              <th>In band (even)</th><th>Last quarter</th><th>Top-10 share</th><th>Suppression vs random</th>
              <th>Other fact</th><th>Verdict</th><th>Fact set</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((row) => {
              const a = row.ablation || {}
              return (
                <tr key={row.run} className={row.run === openRun ? 'is-selected' : undefined}>
                  <td><button type="button" className="archive-run-toggle" onClick={() => open(row.run)}>{row.model}</button></td>
                  <td>{row.format || 'completion'}</td>
                  <td>
                    {row.n_prompts}
                    {row.n_prompts < THIN && <span className="trace-thin" title="below the 50-fact minimum"> thin</span>}
                  </td>
                  <td>{row.neurons_per_fact ?? '—'}</td>
                  <td>{row.peak_layer ?? '—'} ({row.traced_peak_layer ?? '—'})</td>
                  <td>{pct(row.share_in_band)} ({pct(row.baseline)})</td>
                  <td>{pct(row.share_last_quarter)}</td>
                  <td>{pct(row.top10_share)}</td>
                  <td>{a.suppress_drop != null ? `${pct(a.suppress_drop)}${ci(a.suppress_drop_ci)} vs ${pct(a.control_drop)}` : '—'}</td>
                  <td>{pct(a.other_fact_drop)}</td>
                  <td title={VERDICT_HELP[a.verdict] || undefined}>{a.verdict?.replace('_', ' ') || '—'}</td>
                  <td>{row.fact_set_name || '—'}</td>
                </tr>
              )
            })}
            {!runs.length && <tr><td colSpan={12} className="empty">No runs yet.</td></tr>}
          </tbody>
        </table>
      </div>

      {summary && (
        <>
          <h2 className="archive-section-title">{summary.model} ({summary.format || 'completion'}): where the neurons are</h2>
          <p className="dataset-note">
            Per layer: the share of all selected neurons, and the facts' mean share of positive attribution. The dashed line
            is causal tracing's peak for this model{summary.traced_peak_layer == null ? ' (not traced yet)' : ''}.
            {' '}{summary.facts_without_neurons ? `${summary.facts_without_neurons} facts had no positive attribution. ` : ''}
            Enhancing (doubling) the neurons changed the answer's probability by {pct(summary.ablation?.enhance_gain)}.
          </p>
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={layerData}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                <XAxis dataKey="layer" label={{ value: 'layer', position: 'insideBottom', offset: -4 }} />
                <YAxis width={60} tickFormatter={(v) => `${Math.round(v * 100)}%`} />
                <Tooltip formatter={(v) => (typeof v === 'number' ? `${(v * 100).toFixed(1)}%` : v)} labelFormatter={(l) => `layer ${l}`} />
                <Legend />
                {summary.traced_peak_layer != null && (
                  <ReferenceLine x={summary.traced_peak_layer} stroke="var(--text-dim)" strokeDasharray="4 4"
                    label={{ value: `traced peak ${summary.traced_peak_layer}`, position: 'top', fill: 'var(--text-dim)', fontSize: 11 }} />
                )}
                <Line type="monotone" dataKey="share" name="Selected neurons" stroke={SERIES[0]} strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="mass" name="Attribution mass" stroke={SERIES[1]} strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <h2 className="archive-section-title">Neurons shared across facts</h2>
          <p className="dataset-note">
            Mean overlap (Jaccard) of two facts' neuron sets: {pct(summary.overlap?.same_relation)} for facts of the same
            relation ({summary.overlap?.n_same ?? 0} pairs), {pct(summary.overlap?.other_relation)} across relations
            ({summary.overlap?.n_other ?? 0} pairs). Neurons selected for three facts or more are listed: a neuron that
            many facts share is more likely about the relation or the answer format than any one fact, and editing it
            reaches all of them.
          </p>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Layer</th><th>Neuron</th><th>Facts</th><th>Relations</th></tr></thead>
              <tbody>
                {(summary.hubs || []).map((hub) => (
                  <tr key={`${hub.layer}.${hub.neuron}`}>
                    <td>{hub.layer}</td><td>{hub.neuron}</td><td>{hub.facts}</td><td>{hub.relations.join(', ') || '—'}</td>
                  </tr>
                ))}
                {!(summary.hubs || []).length && <tr><td colSpan={4} className="empty">No neuron was selected for three facts.</td></tr>}
              </tbody>
            </table>
          </div>

          <h2 className="archive-section-title">Facts</h2>
          {facts === null && <p className="dataset-note">Loading…</p>}
          {facts === false && <p className="dataset-note">This run's neurons.json is missing.</p>}
          {facts && (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr><th>Prompt</th><th>Answer</th><th>P</th><th>Neurons</th><th>Top neurons (layer.index)</th>
                    <th>Off</th><th>Random off</th><th>Doubled</th></tr>
                </thead>
                <tbody>
                  {facts.map((fact) => (
                    <tr key={fact.id}>
                      <td title={fact.prompt}>{fact.prompt.length > 70 ? `…${fact.prompt.slice(-70)}` : fact.prompt}</td>
                      <td>{fact.answer}</td>
                      <td>{fact.p_clean.toFixed(2)}</td>
                      <td>{fact.neurons.length}</td>
                      <td>{fact.neurons.slice(0, 4).map(([L, i]) => `${L}.${i}`).join(' ')}</td>
                      <td>{fact.p_suppress != null ? fact.p_suppress.toFixed(2) : '—'}</td>
                      <td>{fact.p_control != null ? fact.p_control.toFixed(2) : '—'}</td>
                      <td>{fact.p_enhance != null ? fact.p_enhance.toFixed(2) : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  )
}
