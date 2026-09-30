import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api.js'
import useDownloads, { formatBytes, isActive } from '../lib/useDownloads.js'
import useCapabilities from '../lib/useCapabilities.js'
import { BENCHMARK_LABELS } from '../lib/datasetCatalog.js'
import { PUBLISHED_BENCHMARKS } from '../lib/publishedBenchmarks.js'

// Everything the git repo leaves out, chosen piece by piece. Nothing is
// fetched until Download is pressed; each item becomes one background task
// running scripts/setup.py for just that item (see backend/downloads.py),
// so the command line and this page always agree.

const key = (item) => `${item.kind}:${item.name}`
const TUNING = { raw: 'Base', chat: 'Instruct', reasoning: 'Reasoning' }

// Bytes still to fetch for an item plus whichever optional parts are ticked.
function pendingBytes(item, parts) {
  let bytes = item.installed ? 0 : Math.max((item.bytes || 0) - (item.present_bytes || 0), 0)
  for (const part of parts || []) {
    const info = item.parts?.[part]
    if (info && !info.installed) bytes += info.bytes
  }
  return bytes
}

function StatusCell({ item }) {
  const task = item.task
  if (task?.state === 'queued') return <span className="dl-status is-queued">Queued</span>
  if (task?.state === 'downloading') {
    const verb = item.kind === 'component' ? 'Installing' : 'Downloading'
    return (
      <span className="dl-status is-running">
        {verb}{task.progress != null ? ` ${Math.round(task.progress * 100)}%` : '…'}
      </span>
    )
  }
  if (item.installed) return <span className="dl-status is-done">{item.kind === 'component' ? 'Installed' : 'Downloaded'}</span>
  if (item.partial && item.kind === 'component') return <span className="dl-status is-partial" title="An earlier install did not finish; installing again completes it">Unfinished install</span>
  if (item.partial) return <span className="dl-status is-partial" title="Some files are here already; downloading resumes from them">Partly downloaded</span>
  return <span className="dl-status is-missing">Not downloaded</span>
}

function Section({ title, intro, items, selected, onToggle, onToggleAll, columns, renderRow }) {
  const selectable = items.filter((item) => item.selectable)
  const allOn = selectable.length > 0 && selectable.every((item) => selected[key(item)])
  return (
    <section className="dl-section">
      <div className="dl-section-head">
        <h2 className="section-heading">{title}</h2>
        {selectable.length > 1 && (
          <button type="button" className="btn-plain-small" onClick={() => onToggleAll(selectable, !allOn)}>
            {allOn ? 'Select none' : `Select all ${selectable.length} not downloaded`}
          </button>
        )}
      </div>
      {intro && <p className="dl-section-intro">{intro}</p>}
      <div className="table-wrap">
        <table className="dl-table">
          <thead>
            <tr>
              <th aria-label="Select" />
              {columns.map((c) => <th key={c}>{c}</th>)}
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={key(item)} className={item.selectable ? '' : 'is-unselectable'}>
                <td>
                  <input
                    type="checkbox"
                    aria-label={`Select ${item.label}`}
                    checked={Boolean(selected[key(item)])}
                    disabled={!item.selectable}
                    onChange={() => onToggle(item)}
                  />
                </td>
                {renderRow(item)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

function TaskList({ tasks, onCancel, onClear }) {
  const [openLog, setOpenLog] = useState(null)
  const [logText, setLogText] = useState('')
  // Finished tasks fold away so the queue shows what is happening now; a
  // failure stays visible until looked at, since it needs action.
  const [showFinished, setShowFinished] = useState(false)

  async function toggleLog(id) {
    if (openLog === id) { setOpenLog(null); return }
    setOpenLog(id)
    setLogText('Loading…')
    try {
      setLogText((await api.downloadLog(id)).log || '(no output yet)')
    } catch (e) {
      setLogText(e.message)
    }
  }

  if (!tasks.length) return null
  const finished = tasks.filter((t) => !isActive(t)).length
  // A failure stays up until something newer for the same item replaces it.
  const superseded = (t) => tasks.some((o) => o.kind === t.kind && o.name === t.name && o.submitted > t.submitted)
  const shown = showFinished ? tasks : tasks.filter((t) => isActive(t) || (t.state === 'failed' && !superseded(t)))
  return (
    <section className="dl-section">
      <div className="dl-section-head">
        <h2 className="section-heading">Download queue</h2>
        <span className="dl-task-controls">
          {finished > 0 && (
            <button type="button" className="btn-plain-small" onClick={() => setShowFinished((v) => !v)}>
              {showFinished ? 'Hide finished' : `Show ${finished} finished`}
            </button>
          )}
          {finished > 0 && <button type="button" className="btn-plain-small" onClick={onClear}>Clear finished</button>}
        </span>
      </div>
      <p className="dl-section-intro">One item downloads at a time; the rest wait in order. Downloads keep going if you leave this page, and a cancelled or failed one resumes from what it already fetched when you start it again.</p>
      {!shown.length && <p className="dl-dim">Nothing downloading right now.</p>}
      <ul className="dl-tasks">
        {shown.map((task) => (
          <li key={task.id} className={`dl-task is-${task.state}`}>
            <div className="dl-task-top">
              <span className="dl-task-label">
                {task.label}{task.parts?.length ? ` + ${task.parts.join(', ')}` : ''}
                {task.bytes ? <span className="dl-dim"> · {formatBytes(task.bytes)}</span> : null}
              </span>
              <span className={`badge dl-badge-${task.state}`}>{task.state}</span>
            </div>
            {isActive(task) && (
              <div className={`progress-track${task.progress == null ? ' is-indeterminate' : ''}`}>
                <div className="progress-fill" style={{ width: task.progress == null ? '35%' : `${Math.max(task.progress * 100, 2)}%` }} />
              </div>
            )}
            {task.last_line && <div className="dl-task-line" title={task.last_line}>{task.last_line}</div>}
            <div className="dl-task-actions">
              {task.elapsed && task.state !== 'queued' && <span className="dl-dim">{task.elapsed}</span>}
              <button type="button" className="btn-plain-small" onClick={() => toggleLog(task.id)}>
                {openLog === task.id ? 'Hide log' : 'Show log'}
              </button>
              {isActive(task) && (
                <button type="button" className="btn-danger-small" onClick={() => onCancel(task.id)}>Cancel</button>
              )}
            </div>
            {openLog === task.id && <pre className="dl-log">{logText}</pre>}
          </li>
        ))}
      </ul>
    </section>
  )
}

export default function Downloads() {
  const { overview, error, start, cancel, refresh } = useDownloads({ onFinished: () => refresh() })
  const capabilities = useCapabilities()
  const [selected, setSelected] = useState({})
  const [parts, setParts] = useState({})
  const [modelScope, setModelScope] = useState('main')
  const [submitting, setSubmitting] = useState(false)
  const [message, setMessage] = useState(null)

  const items = useMemo(() => (overview?.items || []).map((item) => {
    const partsMissing = Object.values(item.parts || {}).some((p) => !p.installed)
    return { ...item, selectable: !item.task && (!item.installed || partsMissing) }
  }), [overview])

  const byKind = (kind) => items.filter((item) => item.kind === kind)
  const components = byKind('component')
  const datasets = byKind('dataset')
  const allModels = byKind('model')
  const models = modelScope === 'main' ? allModels.filter((m) => m.main) : allModels

  const chosen = items.filter((item) => selected[key(item)] && item.selectable)
  const totalBytes = chosen.reduce((sum, item) => sum + pendingBytes(item, parts[item.name]), 0)
  const free = overview?.disk_free_bytes
  const tooBig = free != null && totalBytes > free
  const gatedChosen = chosen.filter((item) => item.gated)
  const noGpu = capabilities && capabilities.scheduler === 'local' && !capabilities.gpus?.length

  function setOn(list, on) {
    setSelected((previous) => {
      const next = { ...previous }
      for (const item of list) {
        if (on) next[key(item)] = true
        else delete next[key(item)]
        // The experiment environment installs EasyEdit's requirements, so
        // it cannot come before EasyEdit.
        if (on && item.name === 'experiment-env') {
          const easyedit = items.find((i) => i.name === 'easyedit')
          if (easyedit?.selectable) next[key(easyedit)] = true
        }
      }
      return next
    })
    setMessage(null)
  }

  const toggle = (item) => setOn([item], !selected[key(item)])

  function preset(name) {
    const pick = {
      browse: datasets.filter((d) => d.selectable),
      first: [...components, ...datasets.filter((d) => d.name === 'KnowEdit'), ...allModels.filter((m) => m.name === 'Qwen3-4B')]
        .filter((i) => i.selectable),
      main: [...components, ...datasets, ...allModels.filter((m) => m.main)].filter((i) => i.selectable),
    }[name]
    setSelected({})
    setOn(pick, true)
  }

  function togglePart(dataset, part) {
    setParts((previous) => {
      const current = new Set(previous[dataset] || [])
      if (current.has(part)) current.delete(part)
      else current.add(part)
      return { ...previous, [dataset]: [...current] }
    })
  }

  async function download() {
    setSubmitting(true)
    setMessage(null)
    try {
      // Components first: the environment needs EasyEdit, and both are
      // needed before a model is any use for an experiment.
      const order = { component: 0, dataset: 1, model: 2 }
      const request = [...chosen]
        .sort((a, b) => order[a.kind] - order[b.kind] || (a.name === 'easyedit' ? -1 : b.name === 'easyedit' ? 1 : 0))
        .map((item) => ({ kind: item.kind, name: item.name, parts: parts[item.name] || [] }))
      const tasks = await start(request)
      setSelected({})
      setMessage({ ok: true, text: tasks.length ? `Queued ${tasks.length} download${tasks.length === 1 ? '' : 's'}. Progress is shown below.` : 'Everything selected is already downloaded.' })
    } catch (e) {
      setMessage({ ok: false, text: e.message.replace(/^\d+ [^:]*: /, '').replace(/^\{"detail":"(.*)"\}$/, '$1') })
    } finally {
      setSubmitting(false)
    }
  }

  async function clearFinished() {
    await api.clearDownloads()
    refresh()
  }

  if (error && !overview) return <div><div className="page-header"><h1>Downloads</h1></div><p className="empty">{error}</p></div>
  if (!overview) return <div><div className="page-header"><h1>Downloads</h1></div><p className="empty">Checking what is on disk…</p></div>

  return (
    <div className="downloads-page">
      <div className="page-header">
        <h1>Downloads</h1>
        <span className="dl-dim">{formatBytes(free)} free on this disk</span>
      </div>

      <div className="dl-intro">
        <p>
          Choose what to download. Nothing is fetched until you press <strong>Download selected</strong>, and everything
          can be added later.
        </p>
        <ul>
          <li><strong>To browse benchmarks</strong> on the <Link to="/datasets">Datasets</Link> page, download the datasets you want. That is all it needs.</li>
          <li><strong>To run experiments</strong>, you also need EasyEdit, the experiment Python environment, at least one model, and an NVIDIA GPU (or a SLURM cluster).</li>
        </ul>
        {noGpu && (
          <p className="dl-warning">
            This machine has no NVIDIA GPU, so experiments cannot run here. Datasets are still fully browsable; models and
            the experiment environment are only worth downloading on a machine that has a GPU.
          </p>
        )}
      </div>

      <div className="dl-presets" role="group" aria-label="Quick selections">
        <span className="dl-dim">Quick picks:</span>
        <button type="button" className="pill" onClick={() => preset('browse')}>Every dataset</button>
        <button type="button" className="pill" onClick={() => preset('first')}>A first experiment (EasyEdit, environment, KnowEdit, Qwen3-4B)</button>
        <button type="button" className="pill" onClick={() => preset('main')}>Everything for the main experiments</button>
        {chosen.length > 0 && <button type="button" className="btn-plain-small" onClick={() => setSelected({})}>Clear selection</button>}
      </div>

      <TaskList tasks={overview.tasks} onCancel={cancel} onClear={clearFinished} />

      <Section
        title="Experiment setup"
        intro="Only needed to launch experiments. Browsing results and datasets works without either."
        items={components}
        selected={selected}
        onToggle={toggle}
        onToggleAll={setOn}
        columns={['Component', 'Size', 'Status']}
        renderRow={(item) => (
          <>
            <td className="dl-name-cell">
              <div className="dl-name">{item.label}</div>
              <div className="dl-desc">{item.description}</div>
            </td>
            <td>{item.kind === 'component' && item.name === 'experiment-env' ? `about ${formatBytes(item.bytes)}` : formatBytes(item.bytes)}</td>
            <td><StatusCell item={item} /></td>
          </>
        )}
      />

      <Section
        title="Datasets"
        intro="Each benchmark is fetched from its original source at a pinned version and checked against recorded checksums."
        items={datasets}
        selected={selected}
        onToggle={toggle}
        onToggleAll={setOn}
        columns={['Benchmark', 'Size', 'Status']}
        renderRow={(item) => (
          <>
            <td className="dl-name-cell">
              <div className="dl-name">
                {BENCHMARK_LABELS[item.name] || item.name}
                {item.repository && <a className="dl-source" href={item.repository} target="_blank" rel="noreferrer">source</a>}
              </div>
              {PUBLISHED_BENCHMARKS[item.name]?.title && <div className="dl-desc">{PUBLISHED_BENCHMARKS[item.name].title}</div>}
              {Object.entries(item.parts || {}).map(([part, info]) => (
                <label key={part} className={`dl-part${info.installed ? ' is-installed' : ''}`}>
                  <input
                    type="checkbox"
                    checked={info.installed || (parts[item.name] || []).includes(part)}
                    disabled={info.installed || !item.selectable}
                    onChange={() => { togglePart(item.name, part); if (!selected[key(item)]) setOn([item], true) }}
                  />
                  Also the {info.label.toLowerCase()} · {formatBytes(info.bytes)}{info.installed ? ' · downloaded' : ''}
                </label>
              ))}
            </td>
            <td>{formatBytes(item.bytes)}</td>
            <td><StatusCell item={item} /></td>
          </>
        )}
      />

      <Section
        title="Models"
        intro={
          <>
            Weights come from Hugging Face. The main set is what the current experiments compare: every tuning stage of
            Qwen3-4B and Olmo-3-7B, plus GPT-J-6B.{' '}
            <span className="dl-filter" role="group" aria-label="Which models to list">
              {[['main', 'Main experiments'], ['all', `All ${allModels.length} models`]].map(([value, label]) => (
                <button key={value} type="button" className={`pill${modelScope === value ? ' selected' : ''}`}
                  aria-pressed={modelScope === value} onClick={() => setModelScope(value)}>{label}</button>
              ))}
            </span>
          </>
        }
        items={models}
        selected={selected}
        onToggle={toggle}
        onToggleAll={setOn}
        columns={['Model', 'Type', 'Parameters', 'Size', 'Status']}
        renderRow={(item) => (
          <>
            <td className="dl-name-cell">
              <div className="dl-name">
                {item.name}
                <a className="dl-source" href={item.repository} target="_blank" rel="noreferrer">source</a>
                {item.gated && <span className="badge badge-gated" title="Accept the model's license on huggingface.co, then run `hf auth login` on this machine">needs Hugging Face login</span>}
              </div>
              <div className="dl-desc">{item.family === 'Other' ? 'Not part of a tuning-stage family' : `${item.family} family`}</div>
            </td>
            <td>{TUNING[item.model_type] || item.model_type}</td>
            <td>{item.parameters_b}B</td>
            <td>{formatBytes(item.bytes)}</td>
            <td><StatusCell item={item} /></td>
          </>
        )}
      />

      <div className={`dl-bar${chosen.length ? ' has-selection' : ''}`}>
        <div className="dl-bar-summary">
          {chosen.length
            ? <><strong>{chosen.length}</strong> selected · <strong>{formatBytes(totalBytes)}</strong> to download · {formatBytes(free)} free</>
            : 'Tick the items you want, or use a quick pick above.'}
          {tooBig && <div className="dl-bar-warning">That is more than the free space on this disk. Deselect something first.</div>}
          {gatedChosen.length > 0 && (
            <div className="dl-bar-warning">
              {gatedChosen.map((m) => m.name).join(', ')} {gatedChosen.length === 1 ? 'is' : 'are'} gated: accept the license on
              huggingface.co and run <code>hf auth login</code> on this machine first, or the download will fail.
            </div>
          )}
          {message && <div className={message.ok ? 'dl-bar-ok' : 'dl-bar-warning'} role="status">{message.text}</div>}
        </div>
        <button type="button" className="btn-primary" disabled={!chosen.length || tooBig || submitting} onClick={download}>
          {submitting ? 'Queueing…' : 'Download selected'}
        </button>
      </div>
    </div>
  )
}
