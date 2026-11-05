import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api.js'
import { BOXES, EDIT_OPERATIONS, TOPICS } from '../../lib/sidsDatasetTaxonomy.js'
import RecordCard, { LAYERS, TabRow, matches, modelLabel } from './SidsRecordCard.jsx'
import SidResponseModal from './SidResponseModal.jsx'
import { dotClass, dotNotes, dotText } from '../../lib/sidResponseDots.js'

// Sid's Dataset answers AFTER the edit, browsed like the Datasets page's
// record browser: one method at a time, the records its runs edited, and on
// every query one dot per main instruct model. The backend
// (dashboard/backend/sid_responses.py) picks one run per method x model and
// gives each dot its status from the judge's label and the stored score, as
// experiments/run_experiment/sid_evaluation.py scores it.

// One dot per main model in fixed order. A model with no run, or whose run
// did not edit this record, or that was not asked this query, gets an empty
// ring.
function ResponseDots({ dots, models, runs, edited, recordId, onOpen, what }) {
  return (
    <span className="sids-audit-dots">
      {models.map((m) => {
        const dot = dots?.[m]
        let empty = null
        if (!runs?.[m]) empty = 'no run'
        else if (!edited?.[m]?.includes(recordId)) empty = "not edited in this model's run"
        else if (!dot) empty = 'not asked'
        const head = `${modelLabel(m)}${what ? `, ${what}` : ''}`
        if (empty) return <span key={m} className={dotClass(null, true)} title={`${head}: ${empty}`} />
        const label = `${head}: ${dotText(dot)}${dotNotes(dot).map((n) => `; ${n}`).join('')}`
        return (
          <button key={m} type="button" className={`${dotClass(dot)} is-button`} title={`${label}. Click for details.`}
            aria-label={`${label}. Show details`} onClick={(ev) => { ev.stopPropagation(); onOpen(m) }} />
        )
      })}
    </span>
  )
}

function LegendDot({ cls }) {
  return <span className={`sids-audit-dot sids-pe-dot ${cls}`} aria-hidden="true" />
}

// The colour key, per kind of question, following the scoring code.
function Legend({ models }) {
  return (
    <div className="sids-pe-legend">
      <p className="sids-pe-legend-models">
        Dots, left to right: {models.map(modelLabel).join(', ')}. The dots beside a record's title are its direct
        question. Click a dot for the answers before and after the edit.
      </p>
      <dl>
        <div>
          <dt>About the edited fact</dt>
          <dd>
            Direct, paraphrase, cross-lingual, propositional (yes/no) and determinate derived questions:{' '}
            <span><LegendDot cls="is-pass" />new answer (the edit took)</span>
            <span><LegendDot cls="is-original" />original answer (it did not)</span>
            <span><LegendDot cls="is-other" />something else</span>
            <span><LegendDot cls="is-none" />no answer</span>
            <span><LegendDot cls="is-unclear" />unclear or not judged</span>
            For a yes/no question the new answer is the yes or no that follows from the edit.
          </dd>
        </div>
        <div>
          <dt>Deletions</dt>
          <dd>
            A delete record passes when the model abstains or only denies the old answer:{' '}
            <span><LegendDot cls="is-pass" />abstains</span>
            <span><LegendDot cls="is-original" />still gives the original</span>
            <span><LegendDot cls="is-other" />gives something else</span>
          </dd>
        </div>
        <div>
          <dt>Indeterminate derived</dt>
          <dd>
            Several revisions are consistent with the edit (the record's worlds), so{' '}
            <span><LegendDot cls="is-pass" />any world's answer passes</span>
            even when it is the original one;
            <span><LegendDot cls="is-original" />the original answer when no world gives it</span>
            <span><LegendDot cls="is-other" />an answer no world gives</span>
          </dd>
        </div>
        <div>
          <dt>Locality</dt>
          <dd>
            Unrelated questions, compared with the same model's answer before the edit:{' '}
            <span><LegendDot cls="is-kept" />kept it</span>
            <span><LegendDot cls="is-changed" />changed it (the dialog says whether the new answer leaked in)</span>
            <span><LegendDot cls="is-unclear" />unclear</span>
          </dd>
        </div>
        <div>
          <dt>Markers</dt>
          <dd>
            <span><LegendDot cls="is-pass is-malformed" />purple outline: malformed answer (garbled or looping text)</span>
            <span><LegendDot cls="is-pass is-uncounted" />faded: a determinate derived question the model did not
              answer with the original before the edit, which generalizability leaves out</span>
            <span><LegendDot cls="is-empty" />no run, record not edited, or not asked</span>
          </dd>
        </div>
      </dl>
    </div>
  )
}

const DEFAULT_COORDINATE = { topic: TOPICS[0].key, edit_operation: EDIT_OPERATIONS[0].key, box: BOXES[0].key }

export default function SidResponsesBrowser() {
  const [overview, setOverview] = useState(null)
  const [source, setSource] = useState(null)
  const [method, setMethod] = useState(null)
  const [data, setData] = useState(null)
  const [records, setRecords] = useState(null)
  const [relations, setRelations] = useState({})
  const [coordinate, setCoordinate] = useState(DEFAULT_COORDINATE)
  const [openDot, setOpenDot] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.sidsDatasetRecords().then((d) => {
      setRecords(d.records)
      setRelations(d.relations || {})
    }).catch((err) => setError(String(err.message || err)))
  }, [])

  useEffect(() => {
    let cancelled = false
    api.sidResponses(source).then((o) => {
      if (cancelled) return
      setOverview(o)
      if (!source) setSource(o.source)
      setMethod((m) => {
        if (m && o.methods.some((x) => x.key === m)) return m
        return (o.methods.find((x) => x.models.length) || o.methods[0])?.key || null
      })
    }).catch((err) => { if (!cancelled) setError(String(err.message || err)) })
    return () => { cancelled = true }
  }, [source])

  useEffect(() => {
    if (!method || !source) return
    let cancelled = false
    setData(null)
    api.sidResponsesMethod(method, source).then((d) => { if (!cancelled) setData(d) })
      .catch((err) => { if (!cancelled) setError(String(err.message || err)) })
    return () => { cancelled = true }
  }, [method, source])

  const models = overview?.models || []
  const editedIds = useMemo(() => new Set(Object.values(data?.edited || {}).flat()), [data])
  const edited = useMemo(() => (records || []).filter((r) => editedIds.has(r.id)), [records, editedIds])

  // A new method's records may sit elsewhere: open the first one's coordinate.
  const editedKey = [...editedIds].sort().join(',')
  useEffect(() => {
    if (!edited.length || edited.some((r) => matches(r, coordinate))) return
    setCoordinate(Object.fromEntries(LAYERS.map((l) => [l, edited[0][l]])))
  }, [editedKey, edited.length]) // eslint-disable-line react-hooks/exhaustive-deps

  const set = (layer) => (value) => setCoordinate((c) => ({ ...c, [layer]: value }))
  const counts = (layer) => {
    const out = {}
    for (const r of edited) if (matches(r, coordinate, layer)) out[r[layer]] = (out[r[layer]] || 0) + 1
    return out
  }
  const shown = edited.filter((r) => matches(r, coordinate))
  const methodLabel = overview?.methods.find((m) => m.key === method)?.label || method
  const sourceInfo = overview?.sources.find((s) => s.key === source)

  return (
    <div className="sids-browser sids-pe-browser">
      {overview && (
        <div className="sids-pe-source" role="group" aria-label="Runs from">
          <span className="sids-coordinate-label">Runs from</span>
          {overview.sources.map((s) => (
            <button key={s.key} type="button" title={s.description} aria-pressed={source === s.key}
              className={`btn-plain-small${source === s.key ? ' is-on' : ''}`} onClick={() => setSource(s.key)}>
              {s.label}
            </button>
          ))}
          {sourceInfo && <span className="sids-ad-dim">{sourceInfo.description}</span>}
        </div>
      )}

      {overview && (
        <TabRow label="Method" selected={method} onSelect={setMethod}
          values={overview.methods.map((m) => ({ key: m.key, label: m.label }))}
          counts={Object.fromEntries(overview.methods.map((m) => [m.key, `${m.models.length}/${models.length}`]))} />
      )}

      {data && (
        <ul className="sids-pe-runs">
          {models.map((m) => {
            const run = data.runs[m]
            return (
              <li key={m}>
                <span className="sids-pe-runs-model">{modelLabel(m)}</span>
                {run ? (
                  <span title={run.path}>
                    <code>{run.run}</code>
                    <span className="sids-ad-dim">
                      {' '}{data.edited[m]?.length || 0} records edited
                      {run.edit_mode ? `, ${run.edit_mode}${run.reset_every ? ` (reset every ${run.reset_every})` : ''}` : ''}
                      {run.finished_at ? `, finished ${run.finished_at.replace('T', ' ').slice(0, 16)}` : ''}
                    </span>
                  </span>
                ) : <span className="sids-ad-dim">no run</span>}
              </li>
            )
          })}
        </ul>
      )}

      <Legend models={models} />

      {error && <p className="archive-line archive-line-warn">{error}</p>}
      {(!overview || !records || (method && !data)) && !error && <p className="empty">Loading…</p>}
      {data && records && !edited.length && (
        <p className="empty">No {methodLabel} run on Sid's Dataset for the main instruct models in this source yet.</p>
      )}

      {records && editedIds.size > edited.length && (
        <p className="archive-line archive-line-warn">
          {editedIds.size - edited.length} edited record{editedIds.size - edited.length === 1 ? ' is' : 's are'} no
          longer in the dataset and not shown.
        </p>
      )}
      {edited.length > 0 && (
        <>
          <p className="sids-group-label">Topic <span>{edited.length} records edited</span></p>
          <TabRow label="Topic" values={TOPICS} selected={coordinate.topic} onSelect={set('topic')} counts={counts('topic')} />
          <p className="sids-group-label">Belief revision operation</p>
          <TabRow label="Belief revision operation" values={EDIT_OPERATIONS} selected={coordinate.edit_operation}
            onSelect={set('edit_operation')} counts={counts('edit_operation')} />
          <p className="sids-group-label">Knowledge form (DL box)</p>
          <TabRow label="DL box" values={BOXES} selected={coordinate.box} onSelect={set('box')} counts={counts('box')} />
          {!shown.length && <p className="empty">No edited records at this coordinate.</p>}
          {shown.length > 0 && <p className="sids-group-label">Records <span>{shown.length}</span></p>}
          {shown.map((rec) => (
            <RecordCard key={rec.id} rec={rec} relations={relations}
              dots={(key) => {
                // The header shows the direct question, the edit's headline query.
                const q = key === 'fact' ? 'direct' : key
                return (
                  <ResponseDots dots={data.records[rec.id]?.queries?.[q]} models={models} runs={data.runs}
                    edited={data.edited} recordId={rec.id} what={key === 'fact' ? 'direct question' : null}
                    onOpen={(m) => setOpenDot({ record: rec.id, model: m, key: q })} />
                )
              }} />
          ))}
        </>
      )}

      {openDot && (
        <SidResponseModal method={method} methodLabel={methodLabel} source={source} model={openDot.model}
          record={openDot.record} queryKey={openDot.key} onClose={() => setOpenDot(null)} />
      )}
    </div>
  )
}
