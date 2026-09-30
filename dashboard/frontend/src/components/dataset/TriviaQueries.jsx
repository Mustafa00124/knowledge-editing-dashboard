import { useMemo } from 'react'
import { useDatasetPage } from '../../lib/useDatasetPage.js'
import { QueryCard } from './RecordCard.jsx'

export default function TriviaQueries({ benchmark, subset, pageSize }) {
  const pool = useMemo(() => ({ ...subset, key: `${subset.key}/locality`, editKey: subset.queryKey }), [subset])
  const { data, loading, error, page, setPage, totalPages } = useDatasetPage(benchmark, pool, 'edit', pageSize)
  return (
    <section className="record-card">
      <h2>Shared locality queries</h2>
      <p>These check retained knowledge across the edit set. They are not paired with individual edits.</p>
      {loading && !data && <p>Loading…</p>}
      {error && <p role="alert">{error}</p>}
      {data?.records.map((record, i) => <QueryCard key={data.offset + i} query={{ purpose: 'Locality', prompt: record.question || record.prompt, answer: record.ground_truth }} />)}
      {data && <div className="pager">
        <button type="button" disabled={page === 0} onClick={() => setPage(p => p - 1)}>‹ Prev queries</button>
        <span>Page {page + 1} of {totalPages} ({data.total} queries)</span>
        <button type="button" disabled={page + 1 >= totalPages} onClick={() => setPage(p => p + 1)}>Next queries ›</button>
      </div>}
    </section>
  )
}
