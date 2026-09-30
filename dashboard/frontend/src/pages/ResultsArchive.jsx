import { useCallback, useEffect, useState } from 'react'
import ArchiveConfirm from '../components/ArchiveConfirm.jsx'
import { api } from '../api.js'
import { formatMetricValue, metricLabel } from '../lib/formatMetric.js'
import { toggleGroup } from '../lib/groupSelect.js'
import { useArchiveMove } from '../lib/useArchiveMove.js'

const SHOWN_METRICS = ['edit_succ', 'portability', 'locality']

function describe(facts = {}, summary) {
  const source = summary || facts
  const config = [source.method, source.model].filter(Boolean).join(' · ')
  const dataset = [source.dataset_benchmark, source.dataset_subset].filter(Boolean).join(' / ')
  return { config: config || '—', dataset: dataset || '—' }
}

function shortTime(iso) {
  if (!iso) return '—'
  return iso.replace('T', ' ').slice(0, 16)
}

// The Results page's Archive tab: what has been retired out of runs/, and
// what is sitting in runs/ unable to appear on any of the other tabs.
export default function ResultsArchive({ onChanged }) {
  const [archived, setArchived] = useState([])
  const [incomplete, setIncomplete] = useState([])
  const [selected, setSelected] = useState([])
  const [openRun, setOpenRun] = useState(null)
  const [peek, setPeek] = useState({})
  const [error, setError] = useState(null)

  const load = useCallback(() => {
    setError(null)
    Promise.all([api.archivedRuns(), api.incompleteRuns()])
      .then(([a, i]) => { setArchived(a); setIncomplete(i) })
      .catch((e) => setError(String(e.message || e)))
  }, [])

  useEffect(() => { load() }, [load])

  const move = useArchiveMove(() => {
    load()
    setSelected([])
    // The other tabs read the manifest this move just rewrote.
    if (onChanged) onChanged()
  })

  // An archived run's checkpoints are still readable in place, which is the
  // only evidence of what happened for a run that died before writing a
  // summary - exactly the ones you are deciding whether to restore.
  useEffect(() => {
    if (!openRun || peek[openRun] !== undefined) return
    setPeek((previous) => ({ ...previous, [openRun]: null }))  // in flight
    api.checkpoints(openRun, undefined, true)
      .then((rows) => setPeek((previous) => ({ ...previous, [openRun]: rows })))
      .catch(() => setPeek((previous) => ({ ...previous, [openRun]: [] })))
  }, [openRun, peek])

  const incompleteNames = incomplete.map((row) => row.run)

  return (
    <div>
      <p className="dataset-note archive-intro">
        Archiving moves a run's directory from <code>runs/</code> to <code>archive/runs/</code> inside the same results
        folder. The manifest is rebuilt from whatever is in <code>runs/</code>, so an archived run leaves the Results page
        and stays gone across later jobs. Nothing is ever deleted, and Restore is the same move backwards.
      </p>

      {error && <p className="archive-line archive-line-warn">{error}</p>}

      <h2 className="archive-section-title">Archived runs ({archived.length})</h2>
      {archived.length === 0 ? (
        <p className="dataset-missing">Nothing archived yet. Use “Select runs” on the Table tab to retire them.</p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Run</th>
                <th>Method · model</th>
                <th>Dataset</th>
                {SHOWN_METRICS.map((key) => <th key={key}>{metricLabel(key)}</th>)}
                <th>Archived</th>
                <th>Reason</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {archived.map((row) => {
                const { config, dataset } = describe(row.facts, row.summary)
                const checkpoints = peek[row.run]
                const last = checkpoints?.length ? checkpoints[checkpoints.length - 1] : null
                return (
                  <tr key={row.run} className="archive-row">
                    <td>
                      <button
                        type="button"
                        className="archive-run-toggle"
                        aria-expanded={openRun === row.run}
                        onClick={() => setOpenRun(openRun === row.run ? null : row.run)}
                      >
                        <code>{row.run}</code>
                      </button>
                      {openRun === row.run && (
                        <div className="archive-peek">
                          {checkpoints == null && 'Reading checkpoints…'}
                          {checkpoints && !last && 'No checkpoints were written.'}
                          {last && (
                            <>
                              {checkpoints.length} checkpoint{checkpoints.length === 1 ? '' : 's'}, last at step {last.step}:{' '}
                              {SHOWN_METRICS.filter((key) => typeof last[key] === 'number')
                                .map((key) => `${metricLabel(key)} ${formatMetricValue(key, last[key])}`)
                                .join(', ') || 'no metrics recorded'}
                            </>
                          )}
                        </div>
                      )}
                    </td>
                    <td>{config}</td>
                    <td>{dataset}</td>
                    {SHOWN_METRICS.map((key) => (
                      <td key={key}>
                        {typeof row.summary?.[key] === 'number' ? formatMetricValue(key, row.summary[key]) : '—'}
                      </td>
                    ))}
                    <td>{shortTime(row.archived_at)}</td>
                    <td className="archive-reason-cell">{row.reason || '—'}</td>
                    <td>
                      <button type="button" className="btn-plain-small" onClick={() => move.begin('restore', [row.run])}>
                        Restore
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      <h2 className="archive-section-title">Incomplete runs ({incomplete.length})</h2>
      <p className="dataset-note">
        Live run directories with no <code>summary.json</code>: they died before finishing, so the manifest skips them and
        the Results page can never show them however long they sit there. Anything listed under <em>superseded by</em> is a
        later rerun of the same configuration that did finish.
      </p>
      {incomplete.length === 0 ? (
        <p className="dataset-missing">Every run in the live tree finished.</p>
      ) : (
        <>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th className="archive-check-col">
                    <input
                      type="checkbox"
                      aria-label="Select every incomplete run"
                      checked={selected.length === incompleteNames.length && incompleteNames.length > 0}
                      onChange={() => setSelected((previous) => toggleGroup(incompleteNames, previous))}
                    />
                  </th>
                  <th>Run</th>
                  <th>Method · model</th>
                  <th>Dataset</th>
                  <th>Checkpoints</th>
                  <th>Last written</th>
                  <th>Superseded by</th>
                </tr>
              </thead>
              <tbody>
                {incomplete.map((row) => {
                  const { config, dataset } = describe(row.facts)
                  return (
                    <tr key={row.run}>
                      <td className="archive-check-col">
                        <input
                          type="checkbox"
                          aria-label={`Select ${row.run}`}
                          checked={selected.includes(row.run)}
                          onChange={() => setSelected((previous) => toggleGroup([row.run], previous))}
                        />
                      </td>
                      <td><code>{row.run}</code></td>
                      <td>{config}</td>
                      <td>{dataset}</td>
                      <td>{row.checkpoints}</td>
                      <td>{shortTime(row.modified_at)}</td>
                      <td>
                        {row.superseded_by.length
                          ? row.superseded_by.map((name) => <code key={name} className="archive-superseded">{name}</code>)
                          : '—'}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          <div className="archive-section-actions">
            <button
              type="button"
              className="btn-primary"
              disabled={!selected.length}
              onClick={() => move.begin('archive', selected)}
            >
              Archive {selected.length} run{selected.length === 1 ? '' : 's'}
            </button>
          </div>
        </>
      )}

      {move.open && (
        <ArchiveConfirm
          direction={move.direction}
          plan={move.plan}
          reason={move.reason}
          onReason={move.setReason}
          result={move.result}
          pending={move.pending}
          error={move.error}
          onConfirm={move.confirm}
          onClose={move.close}
        />
      )}
    </div>
  )
}
