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
// for a count, not something to redo on every page visit).
export default function DatasetSummary({ benchmark, subsets }) {
  const [sizeBytes, setSizeBytes] = useState(null)

  useEffect(() => {
    setSizeBytes(null)
    api
      .datasetFiles(benchmark)
      .then((files) => setSizeBytes(files.reduce((sum, f) => sum + f.size_bytes, 0)))
      .catch(() => setSizeBytes(undefined))
  }, [benchmark])

  const totalRecords = subsets.reduce((sum, s) => sum + (s.recordCount || 0), 0)

  const byCategory = new Map()
  for (const s of subsets) {
    const cat = datasetCategory(s)
    const entry = byCategory.get(cat) || { subsets: 0, records: 0 }
    entry.subsets += 1
    entry.records += s.recordCount || 0
    byCategory.set(cat, entry)
  }

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
            records across {subsets.length} subset{subsets.length === 1 ? '' : 's'}
          </span>
        </div>
      </div>
      <div className="dataset-summary-categories">
        {[...byCategory.entries()].map(([cat, { subsets: n, records }]) => (
          <span key={cat} className="dataset-summary-category">
            <strong>{cat}</strong>: {formatCount(records)} ({n} subset{n === 1 ? '' : 's'})
          </span>
        ))}
      </div>
    </div>
  )
}
