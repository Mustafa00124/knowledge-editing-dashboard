import { useEffect, useRef, useState } from 'react'
import { api } from '../api.js'
import { datasetCategory } from '../lib/normalizeDatasetRecord.js'
import { BENCHMARKS, BENCHMARK_GROUPS, BENCHMARK_LABELS, PAGE_SIZES } from '../lib/datasetCatalog.js'
import { useDatasetPage } from '../lib/useDatasetPage.js'
import TriviaQueries from '../components/dataset/TriviaQueries.jsx'
import RecordCard from '../components/dataset/RecordCard.jsx'
import DatasetSummary from '../components/dataset/DatasetSummary.jsx'
import SidsDatasetBrowser from '../components/dataset/SidsDatasetBrowser.jsx'
import SidsDatasetInfoModal from '../components/dataset/SidsDatasetInfoModal.jsx'
import BenchmarkInfoModal from '../components/dataset/BenchmarkInfoModal.jsx'
import QueryFormatsModal from '../components/dataset/QueryFormatsModal.jsx'
import DownloadAction from '../components/DownloadAction.jsx'
import useDownloads from '../lib/useDownloads.js'

// Only kinds of edit belong here. Locality checks aren't one (they're a
// view within a subset - see the Locality toggle below), and there's no
// "Unclassified" bucket: datasetCategory() always returns a real type.
const EDIT_TYPES = [
  ['All types', 'All types'],
  ['Insertion', 'Insert'],
  ['Replacement', 'Replace'],
  ['Forgetting', 'Forget'],
  ['Text/Behavior Modification', 'Text / Behavior'],
]

export default function Datasets() {
  const [benchmark, setBenchmark] = useState('UniEdit')
  const [category, setCategory] = useState('All types')
  const [subsetKey, setSubsetKey] = useState(BENCHMARKS[benchmark][0]?.key)
  const [split, setSplit] = useState('test')
  const [viewMode, setViewMode] = useState('edit_queries')
  const [showLocality, setShowLocality] = useState(false)
  const [pageSize, setPageSize] = useState(5)
  // Which benchmark's reference panel is open, by key, or null.
  const [infoFor, setInfoFor] = useState(null)
  // The cross-benchmark format table, which belongs to the whole published
  // group rather than to any one benchmark in it.
  const [showFormats, setShowFormats] = useState(false)
  const publishedRowRef = useRef(null)
  // Benchmark folders actually on disk, or null until known. The catalog
  // below is static, but a fresh clone has not downloaded UniEdit or DUnE
  // (scripts/setup.py --datasets), so those are marked instead of erroring.
  const [installed, setInstalled] = useState(null)
  const missing = installed !== null && !installed.has(benchmark)
  const benchmarkRef = useRef(benchmark)
  benchmarkRef.current = benchmark
  const pickedRef = useRef(false)
  const hasSubsets = BENCHMARKS[benchmark].length > 0
  const availableTypes = new Set(BENCHMARKS[benchmark].map(datasetCategory))
  const subsets = BENCHMARKS[benchmark].filter(s =>
    (category === 'All types' || datasetCategory(s) === category) &&
    (benchmark !== 'UniEdit' || s.key.startsWith(`${split}/`)))
  const subset = subsets.find(s => s.key === subsetKey) || subsets[0]

  function chooseBenchmark(value) {
    setBenchmark(value)
    setCategory('All types')
    setSubsetKey(BENCHMARKS[value][0]?.key)
    setSplit('test')
    setShowLocality(false)
  }

  function chooseSplit(value) {
    setSplit(value)
    setSubsetKey(`${value}/${subset.key.split('/')[1]}`)
  }

  // Derived, not stored: switching to a subset with no companion locality
  // file silently drops back to its edits rather than showing an empty list.
  const localityActive = showLocality && Boolean(subset?.localityFile)
  const { data, loading, error, page, setPage, totalPages } = useDatasetPage(benchmark, missing ? null : subset, viewMode, pageSize, localityActive)

  // A download started here (or on the Downloads page) makes its benchmark
  // browsable as soon as it finishes, without a reload.
  const [installedVersion, setInstalledVersion] = useState(0)
  const { start: startDownload, find: findDownload } = useDownloads({
    onFinished: () => setInstalledVersion((v) => v + 1),
  })

  useEffect(() => {
    let live = true
    api.datasets().then((list) => {
      if (!live) return
      const names = new Set(list.map((d) => d.name))
      setInstalled(names)
      // Open on something browsable when the default is not downloaded,
      // unless a benchmark was picked while the list was loading.
      if (!names.has(benchmarkRef.current) && !pickedRef.current) {
        const first = BENCHMARK_GROUPS.flatMap((g) => g.benchmarks).find((b) => names.has(b))
        if (first) chooseBenchmark(first)
      }
    }).catch(() => {})
    return () => { live = false }
  }, [installedVersion])
  const effectiveViewMode = subset?.hasQueries ? viewMode : 'edit'

  useEffect(() => {
    const row = publishedRowRef.current
    const selected = row?.querySelector('[aria-pressed="true"]')
    if (!selected) return
    const bounds = row.getBoundingClientRect()
    const pill = selected.getBoundingClientRect()
    if (pill.left < bounds.left || pill.right > bounds.right) {
      row.scrollBy({ left: pill.left - bounds.left - (row.clientWidth - pill.width) / 2, behavior: 'smooth' })
    }
  }, [benchmark])

  return (
    <div>
      <div className="page-header">
        <h1>Datasets</h1>
      </div>

      {BENCHMARK_GROUPS.map(group => (
        <div key={group.label} className="benchmark-group">
          <h2 className="section-heading">
            {group.label}
            {/* Group-level "?", distinct from the per-benchmark ones below:
                this one compares query form, MCQ and answer length across
                all of them, which only reads as a table side by side. */}
            {group.label === 'Published Datasets' && (
              <button
                type="button"
                className="dataset-help-btn section-help-btn"
                onClick={() => setShowFormats(true)}
                aria-label="About query and answer formats across these datasets"
                title="Query form, multiple choice and answer length, compared"
              >
                ?
              </button>
            )}
          </h2>
          <div
            className={`pill-row benchmark-row${group.label === 'Published Datasets' ? ' published-benchmark-row' : ''}`}
            ref={group.label === 'Published Datasets' ? publishedRowRef : undefined}
            aria-label={group.label === 'Published Datasets' ? 'Published datasets, scroll horizontally' : undefined}
            tabIndex={group.label === 'Published Datasets' ? 0 : undefined}
          >
            {/* The "?" is a trailing sibling styled as a superscript rather
                than nested in the pill, since a button inside a button is
                invalid markup. Our own dataset opens the long-form
                categorization panel; a published one opens its paper card. */}
            {group.benchmarks.map((b) => (
              <span className="benchmark-with-help" key={b}>
                <button
                  type="button"
                  className={`pill${b === benchmark ? ' selected' : ''}${installed && !installed.has(b) ? ' not-downloaded' : ''}`}
                  aria-pressed={b === benchmark}
                  onClick={() => { pickedRef.current = true; chooseBenchmark(b) }}
                  title={installed && !installed.has(b) ? 'Not downloaded in this checkout' : undefined}
                >
                  {BENCHMARK_LABELS[b] || b}
                </button>
                <button
                  type="button"
                  className="dataset-help-btn"
                  onClick={() => setInfoFor(b)}
                  aria-label={`About ${BENCHMARK_LABELS[b] || b}`}
                  title={b === 'SidsDataset' ? 'Overview, rubrics and categorization' : 'Paper, venue and citations'}
                >
                  ?
                </button>
              </span>
            ))}
          </div>
        </div>
      ))}

      {showFormats && <QueryFormatsModal onClose={() => setShowFormats(false)} />}

      {infoFor === 'SidsDataset' && <SidsDatasetInfoModal onClose={() => setInfoFor(null)} />}
      {infoFor && infoFor !== 'SidsDataset' && (
        <BenchmarkInfoModal
          benchmarkKey={infoFor}
          label={BENCHMARK_LABELS[infoFor] || infoFor}
          onClose={() => setInfoFor(null)}
        />
      )}

      {missing && (
        <div className="empty">
          <p>{BENCHMARK_LABELS[benchmark] || benchmark} is not downloaded yet.</p>
          <DownloadAction item={findDownload('dataset', benchmark)} onStart={startDownload} />
        </div>
      )}

      {!missing && !hasSubsets && benchmark === 'SidsDataset' && <SidsDatasetBrowser />}

      {!missing && !hasSubsets && benchmark !== 'SidsDataset' && (
        <p className="empty">
          {BENCHMARK_LABELS[benchmark] || benchmark} doesn't have any records yet. Add files under{' '}
          <code>datasets/{benchmark}/</code> and register its subsets in <code>datasetCatalog.js</code> to browse
          them here.
        </p>
      )}

      {!missing && hasSubsets && subset && (
        <>
          <DatasetSummary benchmark={benchmark} subsets={BENCHMARKS[benchmark]} />

          {/* Only the types this benchmark actually contains: a greyed-out
              tab for a type that can never apply here is just noise. A lone
              "All types" tab would be, too, so the row hides entirely when
              the benchmark has only one kind of edit. */}
          {availableTypes.size > 1 && (
            <div className="subnav dataset-type-tabs" aria-label="Edit types">
              {EDIT_TYPES.filter(([type]) => type === 'All types' || availableTypes.has(type)).map(([type, label]) => (
                <button key={type} type="button" aria-pressed={category === type}
                  title={`Show ${label.toLowerCase()}`}
                  className={`subnav-tab${category === type ? ' active' : ''}`}
                  onClick={() => setCategory(type)}>{label}</button>
              ))}
            </div>
          )}

          <p className="dataset-note">
            {benchmark === 'UniEdit'
              ? 'UniEdit does not label edit types per record, but every record is a counterfactual replacement by construction: its pipeline always substitutes a different real value for an existing claim, with no insertion or deletion path. KnowEdit is the one benchmark here carrying all three labeled types.'
              : availableTypes.size > 1
                ? 'Choose an edit type to filter the subsets below.'
                : `Every ${benchmark} subset is the same edit type: ${[...availableTypes][0]}.`}
          </p>

          <div className="subnav dataset-domain-tabs" aria-label="Dataset domains">
            {subsets.map(s => (
              <button key={s.key} type="button" aria-pressed={s.key === subset.key}
                className={`subnav-tab${s.key === subset.key ? ' active' : ''}`}
                onClick={() => setSubsetKey(s.key)}>
                {benchmark === 'UniEdit' ? s.key.split('/')[1] : s.label}
              </button>
            ))}
          </div>

          {benchmark === 'UniEdit' && <div className="subnav" aria-label="Dataset split">
            {['test', 'train'].map(value => (
              <button key={value} type="button" aria-pressed={split === value}
                className={`subnav-tab${split === value ? ' active' : ''}`}
                onClick={() => chooseSplit(value)}>{value === 'test' ? 'Test' : 'Train'}</button>
            ))}
          </div>}

          {subset.description && <p className="dataset-note">{subset.description}</p>}

          <div className="dataset-controls">
            {/* Part of the subset, not a sibling of it: these records are the
                "should not change" half of this same benchmark subset. */}
            {subset.localityFile && (
              <div className="pill-row">
                <button
                  type="button"
                  className={`pill${localityActive ? '' : ' selected'}`}
                  onClick={() => setShowLocality(false)}
                >
                  Edits ({subset.recordCount})
                </button>
                <button
                  type="button"
                  className={`pill${localityActive ? ' selected' : ''}`}
                  onClick={() => setShowLocality(true)}
                  title="Companion records whose answers should stay unchanged after editing"
                >
                  Locality checks ({subset.localityCount})
                </button>
              </div>
            )}

            {subset.hasQueries && (
              <div className="pill-row">
                <button
                  type="button"
                  className={`pill${viewMode === 'edit' ? ' selected' : ''}`}
                  onClick={() => setViewMode('edit')}
                >
                  Edit
                </button>
                <button
                  type="button"
                  className={`pill${viewMode === 'edit_queries' ? ' selected' : ''}`}
                  onClick={() => setViewMode('edit_queries')}
                >
                  Edit + Queries
                </button>
              </div>
            )}

            <div className="pill-row">
              {PAGE_SIZES.map((n) => (
                <button
                  key={n}
                  type="button"
                  className={`pill${n === pageSize ? ' selected' : ''}`}
                  onClick={() => setPageSize(n)}
                >
                  {n} / page
                </button>
              ))}
            </div>
          </div>


          {loading && !data && <p className="empty">Loading…</p>}
          {error && <p role="alert">{error}</p>}

          {data && (
            <>
              <div className="record-list">
                {data.records.map((record, i) => (
                  <RecordCard key={`${benchmark}/${subset.key}/${localityActive ? 'loc' : 'edit'}/${data.offset + i}`} benchmark={benchmark} recordIndex={data.offset + i} record={record} shape={subset.shape} subset={subset} viewMode={effectiveViewMode} isLocality={localityActive} />
                ))}
              </div>

              <div className="pager">
                <button type="button" disabled={page === 0} onClick={() => setPage((p) => p - 1)}>
                  ‹ Prev
                </button>
                <span>
                  Page {page + 1} of {totalPages} ({data.total} total)
                </span>
                <button type="button" disabled={page + 1 >= totalPages} onClick={() => setPage((p) => p + 1)}>
                  Next ›
                </button>
              </div>
            </>
          )}
          {subset.shape === 'flat_qa' && viewMode === 'edit_queries' && (
            <TriviaQueries benchmark={benchmark} subset={subset} pageSize={pageSize} />
          )}
        </>
      )}
    </div>
  )
}
