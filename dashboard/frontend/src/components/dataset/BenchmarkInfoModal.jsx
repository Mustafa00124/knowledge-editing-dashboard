import { useEffect } from 'react'
import { CITATION_CAVEAT, PUBLISHED_BENCHMARKS, citationInfo } from '../../lib/publishedBenchmarks.js'

// "7B" -> 7, "1.5B" -> 1.5, "400M" -> 0.4. Only used for the min/max of the
// size range, so an unparseable or absent size drops out rather than
// counting as zero and dragging the floor down.
function billions(params) {
  if (!params) return null
  const match = /^([\d.]+)\s*([BM])$/.exec(params.trim())
  if (!match) return null
  const value = Number(match[1])
  return match[2] === 'M' ? value / 1000 : value
}

function formatB(value) {
  if (value == null) return null
  return value < 1 ? `${Math.round(value * 1000)}M` : `${value}B`
}

// The four facts worth reading before the table itself: how many, how big,
// base or instruct, and how old. This is the whole reason the table is here,
// so it is computed rather than written by hand and cannot disagree with the
// rows below it.
function summarise(models) {
  if (!models?.length) return []
  const sizes = models.map((m) => billions(m.params)).filter((n) => n != null)
  const years = models.map((m) => m.year).filter((y) => y != null)
  const base = models.filter((m) => m.type === 'base').length
  const instruct = models.length - base
  const out = [[`${models.length}`, models.length === 1 ? 'model' : 'models']]
  if (sizes.length) {
    const low = formatB(Math.min(...sizes))
    const high = formatB(Math.max(...sizes))
    out.push([low === high ? low : `${low}–${high}`,
              sizes.length === models.length ? 'size' : `size, ${sizes.length} of ${models.length}`])
  }
  out.push([base && instruct ? `${base} / ${instruct}` : base ? 'base' : 'instruct',
            base && instruct ? 'base / instruct' : 'all models'])
  if (years.length) {
    const low = Math.min(...years)
    const high = Math.max(...years)
    out.push([low === high ? `${low}` : `${low}–${high}`, 'released'])
  }
  return out
}

// Deliberately small: for a published benchmark the useful facts are what it
// tests, where it appeared, and how well cited it is. The long-form panel is
// only for our own dataset, whose categorization we actually have to explain.
export default function BenchmarkInfoModal({ benchmarkKey, label, onClose }) {
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const info = PUBLISHED_BENCHMARKS[benchmarkKey]
  const citation = citationInfo(benchmarkKey)

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal benchmark-info-modal"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label={`About ${label}`}
      >
        <div className="modal-header">
          <div className="modal-title-group">
            <h2>{label}</h2>
          </div>
          <button type="button" className="btn-plain" onClick={onClose} aria-label="Close">✕</button>
        </div>

        <div className="modal-body benchmark-info-body">
          {!info ? (
            <p className="empty">No reference details recorded for this benchmark yet.</p>
          ) : (
            <>
              <p className="benchmark-info-title">{info.title}</p>
              <p className="benchmark-info-byline">{info.authors}</p>

              <div className="benchmark-info-facts">
                <div>
                  <span className="benchmark-info-value">{info.venue}</span>
                  <span className="benchmark-info-label">Published in</span>
                </div>
                <div>
                  <span className="benchmark-info-value">{info.year}</span>
                  <span className="benchmark-info-label">Year</span>
                </div>
                <div>
                  <span className="benchmark-info-value">
                    {citation ? citation.count.toLocaleString() : 'n/a'}
                  </span>
                  <span className="benchmark-info-label">
                    {citation ? `Citations · ${citation.source}` : 'Citations'}
                  </span>
                </div>
              </div>

              <p>{info.overview}</p>
              {info.note && <p className="dataset-note">{info.note}</p>}

              <div className="benchmark-models">
                <h3>Models evaluated</h3>
                {info.models?.length > 0 && (
                  <>
                    <div className="benchmark-model-summary">
                      {summarise(info.models).map(([value, label]) => (
                        <div key={label}>
                          <span className="benchmark-info-value">{value}</span>
                          <span className="benchmark-info-label">{label}</span>
                        </div>
                      ))}
                    </div>
                    <table className="benchmark-model-table">
                      <thead>
                        <tr><th>Model</th><th>Size</th><th>Type</th><th>Released</th></tr>
                      </thead>
                      <tbody>
                        {info.models.map((model) => (
                          <tr key={model.name}>
                            <td>{model.name}</td>
                            <td className="text-dim">{model.params || '—'}</td>
                            <td><span className={`qf-tag qf-tag-model-${model.type}`}>{model.type}</span></td>
                            <td className="text-dim">{model.year ?? '—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </>
                )}
                {info.modelsNote && <p className="dataset-note">{info.modelsNote}</p>}
              </div>

              <div className="benchmark-info-footer">
                <a href={info.url} target="_blank" rel="noreferrer noopener">Paper ↗</a>
                {citation && <span title={CITATION_CAVEAT}>Counts as of {citation.fetched}, lower bound</span>}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
