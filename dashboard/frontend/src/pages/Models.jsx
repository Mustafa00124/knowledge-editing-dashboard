import { useEffect, useMemo, useState } from 'react'
import { api } from '../api.js'
import DownloadAction from '../components/DownloadAction.jsx'
import useDownloads from '../lib/useDownloads.js'

const formatSize = (bytes) => bytes ? `${(bytes / 1024 ** 3).toFixed(1)} GiB` : '—'

// Scope comes first and defaults to the main set, because that is what the
// current experiments run on: one pretrain per family carrying every tuning
// stage, which is what isolating base vs instruct vs reasoning needs. Nothing
// is hidden - the rest is one click away under "All models", just not in the
// way by default.
const SCOPES = [
  { value: 'main', label: 'Main experiments' },
  { value: 'all', label: 'All models' },
]
const TUNING = [
  { value: 'all', label: 'All types' },
  { value: 'raw', label: 'Base' },
  { value: 'chat', label: 'Instruct' },
  { value: 'reasoning', label: 'Reasoning' },
]
const ARCHITECTURES = [
  { value: 'all', label: 'All architectures' },
  { value: 'dense', label: 'DENSE' },
  { value: 'moe', label: 'MOE' },
]
const SIZES = [
  { value: 'all', label: 'All sizes' },
  { value: '1–8B', label: '1–8B' },
  { value: '20–30B', label: '20–30B' },
]

function Filter({ options, value, onChange, label }) {
  return (
    <div className="pill-row" aria-label={label}>
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          className={`pill${value === o.value ? ' selected' : ''}`}
          aria-pressed={value === o.value}
          onClick={() => onChange(o.value)}
        >
          {o.label}
        </button>
      ))}
    </div>
  )
}

export default function Models() {
  const [models, setModels] = useState([])
  const [scope, setScope] = useState('main')
  const [tuning, setTuning] = useState('all')
  const [architecture, setArchitecture] = useState('all')
  const [sizeGroup, setSizeGroup] = useState('all')
  const [error, setError] = useState('')

  const [modelsVersion, setModelsVersion] = useState(0)
  const { start: startDownload, find: findDownload } = useDownloads({
    onFinished: () => setModelsVersion((v) => v + 1),
  })

  useEffect(() => {
    api.models().then(setModels).catch((err) => setError(err.message))
  }, [modelsVersion])

  const visible = useMemo(() => models.filter((model) =>
    (scope === 'all' || model.main) &&
    (tuning === 'all' || model.model_type === tuning) &&
    (architecture === 'all' || model.architecture === architecture) &&
    (sizeGroup === 'all' || model.size_group === sizeGroup)
  ), [models, scope, tuning, architecture, sizeGroup])

  // Families keep their catalog order so variants of one pretrain stay
  // adjacent - the comparison they exist for is within a family, not across.
  const grouped = useMemo(() => {
    const out = []
    for (const model of visible) {
      const last = out[out.length - 1]
      if (last && last.family === model.family) last.models.push(model)
      else out.push({ family: model.family, models: [model] })
    }
    return out
  }, [visible])

  return (
    <div>
      <div className="page-header"><h1>Models</h1></div>
      <div className="model-filters">
        <Filter options={SCOPES} value={scope} onChange={setScope} label="Scope" />
        <Filter options={TUNING} value={tuning} onChange={setTuning} label="Tuning stage" />
        <Filter options={ARCHITECTURES} value={architecture} onChange={setArchitecture} label="Architecture" />
        <Filter options={SIZES} value={sizeGroup} onChange={setSizeGroup} label="Size" />
      </div>
      {error && <p className="empty">{error}</p>}
      {!error && !visible.length && <p className="empty">No models match these filters.</p>}
      {grouped.map((group) => (
        <section key={group.family} className="model-family">
          <h2 className="model-family-label">{group.family}</h2>
          <div className="card-grid">
            {group.models.map((model) => (
              <div className="card" key={model.name}>
                <div className="card-header">
                  <span className="card-title">{model.name}</span>
                  <span className={`badge badge-${model.status.replace(' ', '-')}`}>{model.status}</span>
                </div>
                <div className="model-tags">
                  <span className={`badge model-type-${model.model_type}`}>
                    {TUNING.find((t) => t.value === model.model_type)?.label || model.model_type}
                  </span>
                  <span className="badge">{model.architecture.toUpperCase()}</span>
                  <span className="badge">{model.size_group}</span>
                </div>
                <div className="card-sub">{model.repo_id}</div>
                <div className="model-facts">
                  <span>{model.parameters_b}B total{model.active_parameters_b ? ` · ${model.active_parameters_b}B active` : ''}</span>
                  <span>{model.status === 'installed' ? `${formatSize(model.size_bytes)} on disk` : ''}</span>
                </div>
                <DownloadAction item={findDownload('model', model.name)} onStart={startDownload} compact />
              </div>
            ))}
          </div>
        </section>
      ))}
    </div>
  )
}
