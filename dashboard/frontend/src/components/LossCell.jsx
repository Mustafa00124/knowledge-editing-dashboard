// A run's loss over its optimisation steps (mean over facts), as a tiny line
// with first -> last values. Shared by the results page and HpExplorer.
function Sparkline({ values, bad }) {
  if (!values || values.length < 2) return null
  const max = Math.max(...values), min = Math.min(...values)
  const span = max - min || 1
  const points = values.map((v, i) => `${(i / (values.length - 1)) * 60},${18 - ((v - min) / span) * 16 - 1}`).join(' ')
  return (
    <svg width="60" height="18" viewBox="0 0 60 18" className={`hp-spark${bad ? ' is-bad' : ''}`} aria-hidden="true">
      <polyline points={points} fill="none" strokeWidth="1.5" />
    </svg>
  )
}

export default function LossCell({ loss }) {
  if (!loss) return <span className="dl-dim">—</span>
  const label = loss.kind === 'value_vector' ? 'target-vector loss, mean over facts' : 'training loss'
  const fmt = (v) => (v == null ? '?' : v >= 100 ? v.toFixed(0) : v.toFixed(2))
  return (
    <span className="hp-loss" title={`${label}${loss.final_prob != null ? `; new answer's final probability ${loss.final_prob}` : ''}`}>
      <Sparkline values={loss.curve} bad={loss.nan || (loss.last > loss.first * 1.05)} />
      <span className="dl-dim">{loss.nan ? 'NaN' : `${fmt(loss.first)} → ${fmt(loss.last)}`}</span>
    </span>
  )
}
