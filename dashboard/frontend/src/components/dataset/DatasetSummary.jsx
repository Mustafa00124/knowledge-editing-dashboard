import { useEffect, useState } from 'react'
import { api } from '../../api.js'
import { datasetCategory } from '../../lib/normalizeDatasetRecord.js'

function formatBytes(bytes) {
  if (bytes == null) return '…'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let n = bytes
  let i = 0
  while (n >= 1024 && i < units.length - 1) {
    n /= 1024
    i++
  }
  return `${n.toFixed(i === 0 || n >= 10 ? 0 : 1)} ${units[i]}`
}

const formatCount = (n) => n.toLocaleString()

// Whole-benchmark stats shown right after picking a benchmark, before
// narrowing down to an edit type / subset - disk size comes from the
// files endpoint (cheap, just stat()s each file), record counts come
// from each subset's own `recordCount` in datasetCatalog.js (baked in
// rather than parsed live - UniEdit alone is ~774MB, ~80s to fully parse
// for a count, not something to redo on every page visit). A benchmark
// without subsets (Sid's Dataset) passes its own `breakdown` instead:
// { records, unit, extra: [{ value, label }], categories: [{ name, records, note }] }.
export default function DatasetSummary({ benchmark, subsets = [], breakdown }) {
  const [sizeBytes, setSizeBytes] = useState(null)

  useEffect(() => {
    setSizeBytes(null)
    api
      .datasetFiles(benchmark)
      .then((files) => setSizeBytes(files.reduce((sum, f) => sum + f.size_bytes, 0)))
      .catch(() => setSizeBytes(undefined))
  }, [benchmark])

  const totalRecords = breakdown ? breakdown.records : subsets.reduce((sum, s) => sum + (s.recordCount || 0), 0)

  const byCategory = new Map()
  for (const s of subsets) {
    const cat = datasetCategory(s)
    const entry = byCategory.get(cat) || { subsets: 0, records: 0 }
    entry.subsets += 1
    entry.records += s.recordCount || 0
    byCategory.set(cat, entry)
  }
  const categories = breakdown
    ? breakdown.categories
    : [...byCategory.entries()].map(([name, { subsets: n, records }]) => ({
        name, records, note: `${n} subset${n === 1 ? '' : 's'}`,
      }))

  return (
    <div className="dataset-summary">
      <div className="dataset-summary-stats">
        <div className="dataset-summary-stat">
          <span className="dataset-summary-value">{sizeBytes === undefined ? '—' : formatBytes(sizeBytes)}</span>
          <span className="dataset-summary-label">on disk</span>
        </div>
        <div className="dataset-summary-stat">
          <span className="dataset-summary-value">{formatCount(totalRecords)}</span>
          <span className="dataset-summary-label">
            {breakdown ? breakdown.unit : `records across ${subsets.length} subset${subsets.length === 1 ? '' : 's'}`}
          </span>
        </div>
        {(breakdown?.extra || []).map((x) => (
          <div key={x.label} className="dataset-summary-stat">
            <span className="dataset-summary-value">{formatCount(x.value)}</span>
            <span className="dataset-summary-label">{x.label}</span>
          </div>
        ))}
      </div>
      <div className="dataset-summary-categories">
        {categories.map(({ name, records, note }) => (
          <span key={name} className="dataset-summary-category">
            <strong>{name}</strong>: {formatCount(records)}{note ? ` (${note})` : ''}
          </span>
        ))}
      </div>
    </div>
  )
}
