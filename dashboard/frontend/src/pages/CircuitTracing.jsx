import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine, ResponsiveContainer } from 'recharts'
import ExperimentsSubnav from '../components/ExperimentsSubnav.jsx'
import InvestigationProgress from '../components/InvestigationProgress.jsx'
import GpuQueue from '../components/GpuQueue.jsx'
import MechanisticDrawer from '../components/MechanisticDrawer.jsx'
import useQueue from '../lib/useQueue.js'
import { api } from '../api.js'
import { SERIES } from '../lib/vizColors.js'
import '../mechanistic.css'

const EXPERIMENT = 'circuit_tracing'
const CONTROLS = ['fact_set', 'format', 'data_path', 'split', 'n_prompts', 'n_noise_samples', 'verify_k']
const THIN = 50
const POSITION_LABELS = { subject: 'Subject tokens', last: 'Last token', other: 'Other tokens' }

const VERDICT_HELP = {
  compact: 'at most 20 components, patched clean together, give back 80% of what the corruption took, on facts the circuit was not chosen from',
  distributed: 'only a circuit larger than 20 components gives back 80% on held-out facts',
  not_found: 'no tested circuit size gives back 80% on held-out facts',
}

function pct(v) {
  return v == null ? '—' : `${Math.round(v * 100)}%`
}

function verdictCell(verdict, k80) {
  if (!verdict) return '—'
  return <span title={VERDICT_HELP[verdict]}>{verdict.replace('_', ' ')}{k80 ? ` (K=${k80})` : ''}</span>
}

function PositionChart({ title, rows, positions, nLayers, tracedPeak }) {
  const data = Array.from({ length: nLayers }, (_, layer) => ({
    layer, ...Object.fromEntries(positions.map((p, i) => [p, rows?.[i]?.[layer]])),
  }))
  return (
    <>
      <h3 className="trace-heatmap-title">{title}</h3>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
            <XAxis dataKey="layer" label={{ value: 'layer', position: 'insideBottom', offset: -4 }} />
            <YAxis width={60} tickFormatter={(v) => v.toFixed(2)} />
            <Tooltip formatter={(v) => (typeof v === 'number' ? v.toFixed(3) : v)} labelFormatter={(l) => `layer ${l}`} />
            <Legend />
            {tracedPeak != null && (
              <ReferenceLine x={tracedPeak} stroke="var(--text-dim)" strokeDasharray="4 4"
                label={{ value: `traced peak ${tracedPeak}`, position: 'top', fill: 'var(--text-dim)', fontSize: 11 }} />
            )}
            {positions.map((p, i) => (
              <Line key={p} type="monotone" dataKey={p} name={POSITION_LABELS[p]} stroke={SERIES[i]} strokeWidth={2} dot={false} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </>
  )
}

function FaithfulnessChart({ title, rows }) {
  if (!rows?.length) return <p className="dataset-note">{title}: not tested (too few held-out facts).</p>
  const data = rows.map((r) => ({ k: String(r.k), recovery: r.recovery, random: r.random, necessity: r.necessity }))
  return (
    <div className="mech-half">
      <h3 className="trace-heatmap-title">{title}</h3>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
            <XAxis dataKey="k" label={{ value: 'components (K)', position: 'insideBottom', offset: -4 }} />
            <YAxis width={50} domain={[0, 'auto']} tickFormatter={(v) => `${Math.round(v * 100)}%`} />
            <Tooltip formatter={(v) => (typeof v === 'number' ? `${(v * 100).toFixed(1)}%` : v)} labelFormatter={(l) => `K = ${l}`} />
            <Legend />
            <ReferenceLine y={0.8} stroke="var(--text-dim)" strokeDasharray="4 4" />
            <Line type="monotone" dataKey="recovery" name="Circuit restored" stroke={SERIES[0]} strokeWidth={2} dot={{ r: 4 }} />
            <Line type="monotone" dataKey="random" name="Random, same mix" stroke={SERIES[1]} strokeWidth={2} strokeDasharray="5 4" dot={{ r: 4 }} />
            <Line type="monotone" dataKey="necessity" name="Circuit knocked out" stroke={SERIES[2]} strokeWidth={2} dot={{ r: 4 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

// Heads as a layer x head grid; positive scores in blue, negative in orange,
// both fading to nothing at zero.
function HeadGrid({ grid }) {
  if (!grid) return null
  const peak = Math.max(...grid.flat().map(Math.abs), 1e-6)
  return (
    <div className="table-wrap">
      <table className="heatmap-table">
        <thead>
          <tr><th>layer</th>{grid[0].map((_, h) => <th key={h}>{h}</th>)}</tr>
        </thead>
        <tbody>
          {grid.map((row, layer) => (
            <tr key={layer}>
              <td className="heatmap-label">{layer}</td>
              {row.map((v, h) => (
                <td key={h} title={`L${layer}.H${h}: ${v.toFixed(4)}`}
                  style={{ background: `color-mix(in srgb, ${v >= 0 ? SERIES[0] : SERIES[1]} ${Math.round(Math.min(1, Math.abs(v) / peak) * 100)}%, transparent)` }} />
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// The strongest residual paths, block to block: x is the layer, rows are
// embedding/attention/MLP/unembedding. Width follows the score.
function PathDiagram({ edges, nLayers }) {
  if (!edges?.length) return null
  const W = 900
  const H = 190
  const pad = 40
  const x = (layer) => pad + ((layer + 1) / (nLayers + 1)) * (W - 2 * pad)
  const rowY = { emb: H / 2, a: 50, b: H / 2, m: H - 50, logits: H / 2 }
  const point = (name) => {
    if (name === 'emb') return [x(-1), rowY.emb]
    if (name === 'logits') return [x(nLayers), rowY.logits]
    return [x(Number(name.slice(1))), rowY[name[0]]]
  }
  const peak = Math.max(...edges.map((e) => Math.abs(e.score)), 1e-6)
  const used = [...new Set(edges.flatMap((e) => [e.from, e.to]))]
  return (
    <div className="mech-paths">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Strongest residual-stream paths between blocks">
        <text x={8} y={rowY.a + 4} className="mech-axis">attn</text>
        <text x={8} y={rowY.m + 4} className="mech-axis">MLP</text>
        {edges.map((e, i) => {
          const [x1, y1] = point(e.from)
          const [x2, y2] = point(e.to)
          const bend = Math.max(20, (x2 - x1) / 3)
          return (
            <path key={i} d={`M${x1},${y1} C${x1 + bend},${y1} ${x2 - bend},${y2} ${x2},${y2}`} fill="none"
              stroke={e.score >= 0 ? SERIES[0] : SERIES[1]} strokeOpacity={0.75}
              strokeWidth={1 + 5 * Math.abs(e.score) / peak}>
              <title>{`${e.from} → ${e.to}: ${e.score.toFixed(3)}`}</title>
            </path>
          )
        })}
        {used.map((name) => {
          const [cx, cy] = point(name)
          return (
            <g key={name}>
              <circle cx={cx} cy={cy} r={5} className="mech-node" />
              <text x={cx} y={cy - 9} textAnchor="middle" className="mech-label">{name}</text>
            </g>
          )
        })}
      </svg>
    </div>
  )
}

export default function CircuitTracing() {
  const [overview, setOverview] = useState(null)
  const [openRun, setOpenRun] = useState(null)
  const [detail, setDetail] = useState({})
  const [error, setError] = useState(null)

  const q = useQueue()
  const [drawerOpen, setDrawerOpen] = useState(false)

  const load = useCallback(() => {
    api.mechanistic(EXPERIMENT).then(setOverview).catch((e) => setError(String(e.message || e)))
  }, [])
  // Polled, so a run finishing on a GPU queue card shows up here.
  useEffect(() => {
    load()
    const timer = setInterval(load, 20000)
    return () => clearInterval(timer)
  }, [load])

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
  const full = detail[openRun]
  const headGrid = useMemo(() => {
    const byPos = full?.heads_by_position
    if (!byPos) return null
    return byPos[0].map((row, layer) => row.map((_, h) => byPos.reduce((sum, grid) => sum + grid[layer][h], 0)))
  }, [full])

  return (
    <div>
      <ExperimentsSubnav />
      <div className="hp-breadcrumb">
        <Link to="/experiments/investigations">Investigations</Link> / Circuit tracing
      </div>
      <div className="page-header">
        <h1>Circuit tracing</h1>
        <button className="btn-primary" onClick={() => setDrawerOpen(true)}>+ New Trace</button>
      </div>
      <p className="dataset-note trace-intro">
        Which attention heads and MLPs, and which paths between them, carry a fact from the subject to the answer. The
        corruption is <Link to="/experiments/investigations/causal_tracing">Knowledge localisation</Link>'s (noise on
        the subject), but instead of restoring one layer at a time, every head and MLP is scored at once by attribution
        patching (a first-order estimate of restoring it), split by where it acts: on the subject tokens, at the last
        token, elsewhere. Paths between blocks are scored the same way. The estimates are checked by really patching each
        fact's top components, and the circuit is chosen on half the facts and tested on the other half: restored alone
        into the corrupted run (does it suffice?) and knocked out of the clean run (is it needed?).
      </p>
      {error && <p className="archive-line archive-line-warn">{error}</p>}

      <GpuQueue q={q} />

      <InvestigationProgress investigation="circuit_tracing" />

      <h2 className="archive-section-title">All runs</h2>
      <p className="dataset-note">
        MLP peak: the layer whose MLP, at the subject tokens, does the most to restore the answer, with causal tracing's
        peak in brackets. Subject share: how much of the MLPs' effect is on the subject tokens; last-token share: the same
        for heads. Circuit: the smallest K that gives back 80% on held-out facts, over all components and over heads
        alone. Check: median rank correlation between estimated and really patched effects per fact.
      </p>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Model</th><th>Format</th><th>Facts</th><th>MLP peak (traced)</th><th>MLP at subject</th>
              <th>Heads at last token</th><th>Top head</th><th>Circuit</th><th>Heads only</th><th>Check</th><th>Fact set</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((row) => {
              const top = row.top_heads?.[0]
              return (
                <tr key={row.run}>
                  <td><button type="button" className="archive-run-toggle" onClick={() => open(row.run)}>{row.model}</button></td>
                  <td>{row.format || 'completion'}</td>
                  <td>
                    {row.n_prompts}
                    {row.n_prompts < THIN && <span className="trace-thin" title="below the 50-fact minimum"> thin</span>}
                  </td>
                  <td>{row.peak_layer ?? '—'} ({row.traced_peak_layer ?? '—'})</td>
                  <td>{pct(row.mlp_subject_share)}</td>
                  <td>{pct(row.heads_last_share)}</td>
                  <td>{top ? `L${top.layer}.H${top.head} (${top.position})` : '—'}</td>
                  <td>{verdictCell(row.verdict, row.k80)}</td>
                  <td>{verdictCell(row.verdict_heads, row.k80_heads)}</td>
                  <td>{row.attribution_check?.spearman_median != null ? row.attribution_check.spearman_median.toFixed(2) : '—'}</td>
                  <td>{row.fact_set_name || '—'}</td>
                </tr>
              )
            })}
            {!runs.length && <tr><td colSpan={11} className="empty">No runs yet.</td></tr>}
          </tbody>
        </table>
      </div>

      {summary && (
        <>
          <h2 className="archive-section-title">{summary.model} ({summary.format || 'completion'}): which components restore the answer</h2>
          <p className="dataset-note">
            Estimated share of the lost log-probability each block gives back when restored, averaged over{' '}
            {summary.n_prompts} facts (clean {summary.p_clean?.toFixed(3)}, corrupted {summary.p_corrupt?.toFixed(3)}).
            Geva et al. find MLPs working on the subject tokens and attention moving the answer to the last token; the
            split shows whether this model does the same.
          </p>
          <PositionChart title="MLPs" rows={summary.mlp_by_position} positions={summary.positions} nLayers={summary.n_layers}
            tracedPeak={summary.traced_peak_layer} />
          <PositionChart title="Attention (all heads of a layer)" rows={summary.attn_by_position} positions={summary.positions}
            nLayers={summary.n_layers} />

          <h2 className="archive-section-title">The circuit on held-out facts</h2>
          <p className="dataset-note">
            Components ranked on half the facts, tested on the other half. Restored: the top K patched clean into the
            corrupted run, as a share of what the corruption took (dashed: K random components of the same mix).
            Knocked out: the clean run with the top K held at their corrupted values, as a share of the same. The
            dotted line is 80%. Top components overall: {(summary.circuit || []).slice(0, 10).join(', ')}.
          </p>
          <div className="mech-pair">
            <FaithfulnessChart title="All components" rows={summary.faithfulness} />
            <FaithfulnessChart title="Heads only" rows={summary.faithfulness_heads} />
          </div>

          <h2 className="archive-section-title">Strongest paths</h2>
          <p className="dataset-note">
            Edge attribution between blocks (a = attention, m = MLP, b = a GPT-J block): what restoring one block's
            output, as seen by one later block only, gives back. Blue gives back, orange takes away; width is size.
          </p>
          <PathDiagram edges={(summary.top_edges || []).slice(0, 25)} nLayers={summary.n_layers} />

          <h2 className="archive-section-title">Heads</h2>
          {full === null && <p className="dataset-note">Loading…</p>}
          {full === false && <p className="dataset-note">This run's circuit.json is missing.</p>}
          <HeadGrid grid={headGrid} />
          <div className="table-wrap">
            <table>
              <thead><tr><th>Head</th><th>Score</th><th>Acts mostly at</th><th>Subject / last / other</th></tr></thead>
              <tbody>
                {(summary.top_heads || []).map((h) => (
                  <tr key={`${h.layer}.${h.head}`}>
                    <td>L{h.layer}.H{h.head}</td><td>{h.score.toFixed(3)}</td><td>{POSITION_LABELS[h.position]}</td>
                    <td>{h.by_position.map((v) => v.toFixed(3)).join(' / ')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {full?.facts && (
            <>
              <h2 className="archive-section-title">Facts</h2>
              <div className="table-wrap">
                <table>
                  <thead><tr><th>Prompt</th><th>Answer</th><th>Clean</th><th>Corrupted</th><th>Top components</th><th>Estimate vs patched (top 3)</th></tr></thead>
                  <tbody>
                    {full.facts.map((f) => (
                      <tr key={f.id}>
                        <td title={f.prompt}>{f.prompt.length > 70 ? `…${f.prompt.slice(-70)}` : f.prompt}</td>
                        <td>{f.answer}</td>
                        <td>{f.p_clean.toFixed(2)}</td>
                        <td>{f.p_corrupt.toFixed(3)}</td>
                        <td>{f.top.slice(0, 5).map(([name]) => name).join(' ')}</td>
                        <td>{f.check ? f.check.nodes.slice(0, 3).map((n, i) => `${n} ${f.check.estimate[i].toFixed(2)}/${f.check.actual[i].toFixed(2)}`).join(', ') : '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </>
      )}
      <MechanisticDrawer
        open={drawerOpen}
        onToggle={() => setDrawerOpen((o) => !o)}
        onClose={() => setDrawerOpen(false)}
        title="New Trace"
        queue={q.queue}
        onStage={q.stage}
        expType={q.experimentTypes.find((t) => t.name === EXPERIMENT)}
        models={(overview?.models || []).map((m) => ({ ...m, tag: m.runs ? `${m.runs} run${m.runs === 1 ? '' : 's'}` : 'not run' }))}
        controls={CONTROLS}
        factSets={overview?.fact_sets}
        costNote="One SLURM job per model. One gradient pass per fact plus the checks; 100 facts take a few minutes on these GPUs."
      />
    </div>
  )
}
