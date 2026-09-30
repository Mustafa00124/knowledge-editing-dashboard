// Display names and units for the numeric keys in manifest.json /
// checkpoints.jsonl. Anything not listed here still renders (the label
// falls back to a humanized key, the value to plain decimals), so a new
// metric added by the runner shows up without a frontend change.
const LABELS = {
  bertscore_edit_succ: 'Edit success BERTScore',
  bertscore_portability: 'Generalizability BERTScore',
  bertscore_locality: 'Locality BERTScore',
  edit_succ: 'Edit success',
  portability: 'Generalizability',
  locality: 'Locality',
  fluency: 'Fluency',
  loss: 'Loss',
  total_sec: 'Time',
  elapsed_sec: 'Time',
  gpu_mem_alloc_mb: 'GPU memory',
  gpu_mem_peak_mb: 'GPU memory (peak)',
  host_rss_mb: 'Host memory',
}

// Rolled up as 100 * mean(accuracy) by aggregate_metrics(), so already
// 0-100 and just needs the sign. Fluency goes through that same scaling
// but is an n-gram entropy (~500), not a percentage, so it is not here.
const PERCENT_METRICS = new Set(['edit_succ', 'portability', 'locality'])

const EMPTY = '—'

export function metricLabel(metricKey) {
  if (LABELS[metricKey]) return LABELS[metricKey]
  const words = metricKey.replace(/_(mb|sec)$/, '').split('_').join(' ')
  return words.charAt(0).toUpperCase() + words.slice(1)
}

export function formatDuration(seconds) {
  if (!Number.isFinite(seconds)) return EMPTY
  const tenths = Math.round(seconds * 10)
  if (tenths < 600) return `${(tenths / 10).toFixed(1)}s`

  const wholeSeconds = Math.round(seconds)
  if (wholeSeconds < 3600) {
    const minutes = Math.floor(wholeSeconds / 60)
    return `${minutes}m ${String(wholeSeconds % 60).padStart(2, '0')}s`
  }
  if (wholeSeconds < 86400) {
    const hours = Math.floor(wholeSeconds / 3600)
    return `${hours}h ${String(Math.floor((wholeSeconds % 3600) / 60)).padStart(2, '0')}m`
  }
  const days = Math.floor(wholeSeconds / 86400)
  return `${days}d ${String(Math.floor((wholeSeconds % 86400) / 3600)).padStart(2, '0')}h`
}

// memory_snapshot() and gpu_mem_total_mb both divide bytes by 1e6, so the
// stored numbers are decimal MB. Displaying those as "GB" by dividing by
// 1000 made a 96 GB card read as 102 GB. NVIDIA's spec sheet, nvidia-smi and
// every other GPU tool use binary units, so convert rather than relabel.
export function toGibibytes(mb) {
  return (mb * 1e6) / 1024 ** 3
}

function formatMegabytes(mb) {
  const gib = toGibibytes(mb)
  return gib >= 1 ? `${gib.toFixed(2)} GiB` : `${((mb * 1e6) / 1024 ** 2).toFixed(0)} MiB`
}

function formatLoss(value) {
  return value !== 0 && Math.abs(value) < 1e-3 ? value.toExponential(2) : value.toFixed(4)
}

export function formatMetricValue(metricKey, value) {
  if (!Number.isFinite(value)) return EMPTY
  if (metricKey === 'total_sec' || metricKey === 'elapsed_sec') return formatDuration(value)
  if (metricKey === 'loss') return formatLoss(value)
  if (metricKey.endsWith('_mb')) return formatMegabytes(value)
  if (PERCENT_METRICS.has(metricKey)) return `${value.toFixed(1)}%`
  if (metricKey === 'fluency') return value.toFixed(1)
  return Math.abs(value) >= 1000 ? value.toFixed(1) : value.toFixed(4)
}
