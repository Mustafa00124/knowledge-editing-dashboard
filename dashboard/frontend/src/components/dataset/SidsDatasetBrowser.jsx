import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api.js'
import AuditDetailModal from './AuditDetailModal.jsx'
import DerivationModal from './DerivationModal.jsx'
import DatasetSummary from './DatasetSummary.jsx'
import SidsCriteriaModal from './SidsCriteriaModal.jsx'
import { RecordReview, ReviewDots, ReviewLegend } from './SidsReviewDots.jsx'
import { BOXES, EDIT_OPERATIONS, FICTIONAL, TOPICS } from '../../lib/sidsDatasetTaxonomy.js'
import RecordCard, { TabRow, matches, modelLabel } from './SidsRecordCard.jsx'

// Browses the records under the categorization: topic, then belief revision
// operation (expansion, revision, contraction), then knowledge form (box). Each tab shows how many records it
// holds given the layers above it, and the records at the selected coordinate
// are listed below with every query. Tab rows and record cards: SidsRecordCard.jsx.

const STATUS_TEXT = {
  green: 'green (gave the expected pre-edit answer)',
  red: 'red (did not give it)',
  yellow: 'not audited (or stale since the record changed, or the judge could not label it)',
}

// One dot per model in the fixed order; a model the audit never asks this
// query of (no pre-edit answer) gets an empty ring. Each dot is a button that
// opens AuditDetailModal (what the model answered, and why it failed).
function AuditDots({ statuses, models, onOpen }) {
  if (!models?.length) return null
  return (
    <span className="sids-audit-dots">
      {models.map((m) => {
        const s = statuses?.[m] || 'na'
        const text = s === 'na' ? 'not asked (no pre-edit answer to check)' : STATUS_TEXT[s] || s
        const label = `${modelLabel(m)}: ${text}`
        if (!onOpen) return <span key={m} className={`sids-audit-dot is-${s}`} title={label} />
        return (
          <button key={m} type="button" className={`sids-audit-dot is-${s} is-button`} title={`${label}. Click for details.`}
            aria-label={`${label}. Show details`} onClick={(ev) => { ev.stopPropagation(); onOpen(m) }} />
        )
      })}
    </span>
  )
}

// Review (CRITERIA.md manual rules): who is reviewing in this browser and
// whether review mode is on (both remembered per browser).
const REVIEWER_KEY = 'sids-dataset-reviewer'
const readStored = (key) => { try { return localStorage.getItem(key) || '' } catch { return '' } }
const store = (key, v) => { try { localStorage.setItem(key, v) } catch { /* private window */ } }
// Queries a record carries (10 for ABox/TBox, 7 for RBox), counted rather
// than assumed so a malformed record shows up in the total.
function queryCount(rec) {
  return Object.values(rec.queries || {}).reduce((n, q) => n + (Array.isArray(q) ? q.length : q ? 1 : 0), 0)
}

// The whole-dataset block other benchmarks show, built from the records:
// totals, then records per belief revision operation (expansion split by what is fictional).
function sidsBreakdown(records) {
  const categories = EDIT_OPERATIONS.map(({ key, label }) => {
    const rs = records.filter((r) => r.edit_operation === key)
    const parts = FICTIONAL.map((f) => [f, rs.filter((r) => r.fictional === f.key).length]).filter(([, n]) => n)
    return {
      name: label,
      records: rs.length,
      note: parts.length ? `made up: ${parts.map(([f, n]) => `${f.label.toLowerCase()} ${n}`).join(', ')}` : '',
    }
  })
  return {
    records: records.length,
    unit: `records across ${EDIT_OPERATIONS.length} belief revision operations`,
    extra: [{ value: records.reduce((n, r) => n + queryCount(r), 0), label: 'queries' }],
    categories,
  }
}

export default function SidsDatasetBrowser() {
  const [records, setRecords] = useState(null)
  const [relations, setRelations] = useState({})
  const [relationChecks, setRelationChecks] = useState({})
  const [audit, setAudit] = useState(null)
  // Pre-edit status dots: the four main instruct models, or every audited model.
  const [status, setStatus] = useState(null)
  const [allModels, setAllModels] = useState(false)
  const [chain, setChain] = useState(null)
  // The audit dot whose detail modal is open: { record, model, key }.
  const [auditDot, setAuditDot] = useState(null)
  const [showCriteria, setShowCriteria] = useState(false)
  const [reviews, setReviews] = useState(null)
  const [reviewError, setReviewError] = useState(null)
  const [me, setMe] = useState(() => readStored(REVIEWER_KEY))
  const [error, setError] = useState(null)
  const [coordinate, setCoordinate] = useState({
    // The first tab of each level: Geography, Revision, ABox.
    topic: TOPICS[0].key,
    edit_operation: EDIT_OPERATIONS[0].key,
    box: BOXES[0].key,
  })
  const [formal, setFormal] = useState(null)
  useEffect(() => {
    api.sidsDatasetFormalStatus().then(setFormal).catch(() => setFormal(null))
  }, [])
  useEffect(() => {
    api.sidsDatasetRecords().then((d) => {
      setRecords(d.records)
      setRelations(d.relations || {})
      setRelationChecks(d.relation_checks || {})
    }).catch((err) => setError(String(err.message || err)))
  }, [])
  useEffect(() => {
    api.sidsDatasetReviews().then(setReviews).catch((err) => setReviewError(String(err.message || err)))
  }, [])
  // Only reviewers this token may mark as (people for the user's token); others are forgotten.
  const meValid = reviews?.can_mark_as?.includes(me) ? me : ''
  const pickMe = (id) => { setMe(id); store(REVIEWER_KEY, id) }
  // Picking a name is review mode: that reviewer's own dots become clickable. Read only: none are.
  const reviewMode = !!meValid
  // A mark on one record's rule or query; the reply carries the record's marks.
  const mark = (rid, item, state) => api.sidsDatasetMark(rid, item, meValid, state)
    .then((d) => setReviews((s) => {
      const marks = { ...s.marks }
      if (Object.keys(d.marks || {}).length) marks[rid] = d.marks
      else delete marks[rid]
      return { ...s, marks }
    }))
  // From the checklist (or "Next unreviewed"): show a record's tab and scroll to its card.
  const jumpTo = (rid) => {
    const rec = (records || []).find((r) => r.id === rid)
    if (!rec) return
    setShowCriteria(false)
    setCoordinate({ topic: rec.topic, edit_operation: rec.edit_operation, box: rec.box })
    setTimeout(() => document.getElementById(`sids-rec-${rid}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' }), 50)
  }
  useEffect(() => {
    api.sidsDatasetAuditStatus(allModels ? 'all' : 'main').then(setStatus).catch(() => setStatus(null))
  }, [allModels])
  const statusModels = status?.models || []
  const set = (layer) => (value) => setCoordinate((c) => ({ ...c, [layer]: value }))
  // Audit results load once, the first time a chain is opened.
  const openChain = (rec, target) => {
    setChain({ rec, target })
    if (audit == null) api.sidsDatasetAuditChecks().then((d) => setAudit(d.models)).catch(() => setAudit([]))
  }

  const pool = records || []
  // Records per tab value, given the layers above that row.
  const counts = (layer) => {
    if (!records) return null
    const out = {}
    for (const r of pool) if (matches(r, coordinate, layer)) out[r[layer]] = (out[r[layer]] || 0) + 1
    return out
  }
  const shown = pool.filter((r) => matches(r, coordinate))

  return (
    <div className="sids-browser">
      {records && <DatasetSummary benchmark="SidsDataset" breakdown={sidsBreakdown(records)} />}
      <div className="sids-criteria-bar">
        <button type="button" className="btn-plain-small" onClick={() => setShowCriteria(true)}
          title="Which CRITERIA.md checks the records pass (datasets/SidsDataset/criteria.py)">
          Criteria checklist
        </button>
      </div>
      {showCriteria && <SidsCriteriaModal onClose={() => setShowCriteria(false)} onJump={jumpTo} />}
      {reviews && (
        <div className="sids-rv-bar">
          <span className="sids-rv-seg" role="radiogroup" aria-label="Reviewing as">
            <span className="sids-rv-seg-label">Reviewing as</span>
            <button type="button" role="radio" aria-checked={!meValid}
              className={`sids-rv-seg-btn${!meValid ? ' active' : ''}`}
              title="Dots are read-only" onClick={() => pickMe('')}>Read only</button>
            {reviews.reviewers.filter((r) => reviews.can_mark_as?.includes(r.id)).map((r) => (
              <button key={r.id} type="button" role="radio" aria-checked={meValid === r.id}
                className={`sids-rv-seg-btn${meValid === r.id ? ' active' : ''}`}
                title={`Your own dots become clickable: yellow, then green, then red, then yellow`}
                onClick={() => pickMe(r.id)}>{r.name}</button>
            ))}
          </span>
          <ReviewLegend />
        </div>
      )}
      {reviewError && <p className="archive-line archive-line-warn">Review marks: {reviewError}</p>}
      <p className="sids-group-label">Topic <span>{records ? `${records.length} records in all` : ''}</span></p>
      <TabRow label="Topic" values={TOPICS} selected={coordinate.topic} onSelect={set('topic')} counts={counts('topic')} />

      <p className="sids-group-label">Belief revision operation</p>
      <TabRow label="Belief revision operation" values={EDIT_OPERATIONS} selected={coordinate.edit_operation} onSelect={set('edit_operation')} counts={counts('edit_operation')} />

      <p className="sids-group-label">Knowledge form (DL box)</p>
      <TabRow label="DL box" values={BOXES} selected={coordinate.box} onSelect={set('box')} counts={counts('box')} />


      {error && <p className="archive-line archive-line-warn">{error}</p>}
      {!records && !error && <p className="empty">Loading records…</p>}
      {records && !shown.length && (
        <p className="empty">
          No records at this coordinate yet. Use the <strong>?</strong> beside the dataset name for the full scheme, the
          derivation types and how each query is scored.
        </p>
      )}
      {shown.length > 0 && (
        <>
          <p className="sids-group-label">Records <span>{shown.length}</span></p>
          {shown.map((rec) => (
            <div key={rec.id} id={`sids-rec-${rec.id}`}>
            <RecordCard rec={rec} relations={relations} onChain={openChain} formal={formal?.records?.[rec.id]}
              review={reviews && <RecordReview rid={rec.id} state={reviews} me={meValid} reviewMode={reviewMode} onMark={mark} />}
              dots={(key) => {
                // 'fact': direct and paraphrase (RBox: direct and the instance questions) held before the edit.
                const audit = status?.records?.[rec.id]
                const dots = <AuditDots statuses={key === 'fact' ? audit?.fact : audit?.queries?.[key]} models={statusModels}
                  onOpen={(m) => setAuditDot({ record: rec.id, model: m, key })} />
                if (key === 'fact' || !reviews) return dots
                // Each query also gets one review dot per reviewer.
                return (
                  <span className="sids-dot-groups">
                    {statusModels.length > 0 && <span className="sids-dot-group"><span className="sids-dot-group-label">Models</span>{dots}</span>}
                    <span className="sids-dot-group"><span className="sids-dot-group-label">Reviews</span>
                      <ReviewDots rid={rec.id} item={key} state={reviews} me={meValid} reviewMode={reviewMode} onMark={mark} /></span>
                  </span>
                )
              }}
              footer={statusModels.length > 0 && (
                <p className="sids-audit-link">
                  Responses: <Link to={`/model-audit?record=${encodeURIComponent(rec.id)}`}>Model audit page</Link>
                </p>
              )} />
            </div>
          ))}
        </>
      )}
      {chain && (
        <DerivationModal rec={chain.rec} target={chain.target} relations={relations} relationChecks={relationChecks}
          audit={audit} onClose={() => setChain(null)} />
      )}
      {auditDot && (
        <AuditDetailModal record={auditDot.record} model={auditDot.model} queryKey={auditDot.key}
          modelLabel={modelLabel(auditDot.model)} onClose={() => setAuditDot(null)} />
      )}
    </div>
  )
}
