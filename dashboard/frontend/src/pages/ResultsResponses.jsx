import { useEffect, useState } from 'react'
import { api } from '../api.js'

export default function ResultsResponses({ rows, methodMeta, modelMeta, evaluation = 'original' }) {
  const semantic = evaluation !== 'original'
  const normalize = (data) => semantic ? data.probes.map((p) => ({
    ...p, prompt: p.question, continuation: p.answer, sampling_version: 2,
  })) : data
  const [run, setRun] = useState(null)
  const [steps, setSteps] = useState([])
  const [step, setStep] = useState(null)
  const [sample, setSample] = useState(null)
  // Step 0 runs before any edit is applied, for every method family, so it is
  // the natural "before" to read every later step against. Fetched once per
  // run rather than per step, since it never changes within a run.
  const [baseline, setBaseline] = useState(null)

  useEffect(() => {
    if (!rows.length) {
      setRun(null)
      return
    }
    if (!run || !rows.some((r) => r.run === run)) setRun(rows[0].run)
  }, [rows, run])

  useEffect(() => {
    if (!run) return
    let cancelled = false;
    setSample(null)
    setSteps([])
    setStep(null)
    const load = () => (semantic ? api.evaluations(run) : api.samples(run)).then((ss) => {
      if (cancelled) return
      setSteps(ss)
      setStep((previous) => previous != null && ss.includes(previous) ? previous : ss[ss.length - 1] ?? null)
    }).catch(() => { if (!cancelled) setSteps([]) })
    load()
    const timer = setInterval(load, 15000)
    return () => { cancelled = true; clearInterval(timer) }
  }, [run, evaluation])

  useEffect(() => {
    if (!run || step == null) return
    let cancelled = false;
    setSample(null)
    const load = () => (semantic ? api.evaluation(run, step) : api.sample(run, step))
      .then((s) => { if (!cancelled) setSample(normalize(s)) })
      .catch(() => { if (!cancelled) setSample(null) })
    load()
    const timer = setInterval(load, 15000)
    return () => { cancelled = true; clearInterval(timer) }
  }, [run, step, evaluation])

  useEffect(() => {
    if (!run) {
      setBaseline(null)
      return
    }
    let cancelled = false;
    (semantic ? api.evaluation(run, 0) : api.sample(run, 0))
      .then((s) => { if (!cancelled) setBaseline(normalize(s)) })
      .catch(() => { if (!cancelled) setBaseline(null) })
    return () => { cancelled = true }
  }, [run, evaluation])

  if (!rows.length) return <p className="dataset-missing">No results for this dataset yet.</p>

  // Model and method get a row each rather than one row of combined runs.
  // Combined reads fine at one model, but the row is a cross product: every
  // model added multiplies it, while two rows only grow by one tab each.
  const current = rows.find((r) => r.run === run) || rows[0]
  const models = [...new Set(rows.map((r) => r.model))]
  const methods = [...new Set(rows.map((r) => r.method))]
  const runsFor = (model, method) => rows.filter((r) => r.model === model && r.method === method)

  // Not every pair has been run. Switching model keeps the current method
  // where that pair exists and otherwise falls back to the model's first
  // available method, so the selection is never left pointing at nothing.
  function chooseModel(model) {
    const matches = runsFor(model, current.method)
    const fallback = rows.filter((r) => r.model === model)
    setRun((matches.length ? matches : fallback)[0].run)
  }

  // A method with no run for this model stays visible but disabled, rather
  // than vanishing: which combinations are missing is worth seeing on a
  // results page, and a row that reshuffles on every model switch is harder
  // to use than one that holds still.
  function chooseMethod(method) {
    const matches = runsFor(current.model, method)
    if (matches.length) setRun(matches[0].run)
  }

  // Only when one model/method pair holds several runs, e.g. a learning-rate
  // sweep. Usually absent.
  const isBaseline = step === 0
  const variants = runsFor(current.model, current.method)
  const variantLabel = (r) => (r.lr != null ? `lr ${r.lr.toExponential(0)}` : r.run)

  return (
    <div>
      {semantic && <p className="metric-note">Scored / total probes: {Object.entries(current.evaluations?.[evaluation]?.coverage || {}).map(([metric, counts]) => `${metric}: ${counts.scored}/${counts.total}`).join(' · ')}</p>}
      <div className="axis-controls">
        <div className="axis-selector">
          <span className="axis-selector-label">Model</span>
          <div className="axis-tabs" role="group" aria-label="Model">
            {models.map((m) => (
              <button
                key={m}
                type="button"
                className={`subnav-tab${current.model === m ? ' active' : ''}`}
                aria-pressed={current.model === m}
                onClick={() => chooseModel(m)}
              >
                {modelMeta[m]?.label || m}
              </button>
            ))}
          </div>
        </div>

        <div className="axis-selector">
          <span className="axis-selector-label">Method</span>
          <div className="axis-tabs" role="group" aria-label="Method">
            {methods.map((m) => {
              const available = runsFor(current.model, m).length > 0
              return (
                <button
                  key={m}
                  type="button"
                  disabled={!available}
                  title={available ? undefined : `No ${methodMeta[m]?.label || m} run on ${modelMeta[current.model]?.label || current.model} for this dataset`}
                  className={`subnav-tab${current.method === m ? ' active' : ''}${available ? '' : ' is-unavailable'}`}
                  aria-pressed={current.method === m}
                  onClick={() => chooseMethod(m)}
                >
                  {methodMeta[m]?.label || m}
                </button>
              )
            })}
          </div>
        </div>

        {variants.length > 1 && (
          <div className="axis-selector">
            <span className="axis-selector-label">Variant</span>
            <div className="axis-tabs" role="group" aria-label="Run variant">
              {variants.map((r) => (
                <button
                  key={r.run}
                  type="button"
                  title={r.run}
                  className={`subnav-tab${run === r.run ? ' active' : ''}`}
                  aria-pressed={run === r.run}
                  onClick={() => setRun(r.run)}
                >
                  {variantLabel(r)}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="axis-selector">
          <span className="axis-selector-label">Step</span>
          <div className="axis-tabs" role="group" aria-label="Checkpoint step">
            {steps.map((s) => (
              <button
                key={s}
                type="button"
                className={`subnav-tab${step === s ? ' active' : ''}`}
                aria-pressed={step === s}
                onClick={() => setStep(s)}
              >
                {s.toLocaleString()}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="samples-list">
        {Array.isArray(sample) &&
          sample.map((s, i) => {
            // The same three prompts are generated at every step, greedily, so
            // matching on the prompt pairs them reliably even if their order
            // ever changes.
            const before = Array.isArray(baseline)
              ? baseline.find((b) => semantic ? b.id === s.id : b.prompt === s.prompt)?.continuation
              : null
            const unchanged = before != null && before === s.continuation
            return (
              <div key={i} className="sample-card">
                <div className="sample-prompt">{s.prompt ?? JSON.stringify(s)}</div>
                {semantic && <div className="metric-note">
                  <strong>{s.metric} · {s.category}</strong>
                  <p>Reference: {s.reference_answers?.join(' / ') || 'Unavailable'}</p>
                  <p>{evaluation === 'bertscore' ? 'BERTScore F1' : evaluation === 'exact_match' ? 'Exact Match' : 'Judge score'}: {s.scores?.[evaluation] == null ? 'Unavailable' : Number(s.scores[evaluation]).toFixed(3)}</p>
                  {evaluation === 'llm_judge' && s.judgment && <p>{s.judgment.verdict}: {s.judgment.reason}</p>}
                </div>}
                <div className="sample-compare">
                  <div className="sample-side">
                    <span className="sample-side-label">Before · no edits</span>
                    <div className="sample-generation">
                      {before == null ? <em className="sample-missing">No baseline sample for this run.</em>
                        : before.trim() ? before : <em className="sample-missing">Empty response (no visible text generated).</em>}
                    </div>
                  </div>
                  {!isBaseline && (
                    <div className="sample-side">
                      <span className="sample-side-label">
                        After · step {step?.toLocaleString()}
                        {unchanged && (!['ike', 'scr'].includes(current.method) || s.sampling_version === 2)
                          && <span className="sample-unchanged">identical</span>}
                      </span>
                      <div className="sample-generation">
                        {['ike', 'scr'].includes(current.method) && s.sampling_version !== 2
                          ? <em className="sample-missing">This legacy sample omitted the method’s context. A corrected response needs to be generated.</em>
                          : s.continuation?.trim() ? s.continuation
                            : <em className="sample-missing">Empty response (no visible text generated).</em>}
                      </div>
                      {s.recovered_at && <p className="dataset-note">Regenerated from the saved run configuration.</p>}
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        {sample && !Array.isArray(sample) && <pre className="sample-raw">{JSON.stringify(sample, null, 2)}</pre>}
      </div>

      {isBaseline && steps.length > 1 && (
        <p className="dataset-note">Showing the pre-edit baseline itself. Pick a later step to see it beside the edited output.</p>
      )}
      {isBaseline && steps.length === 1 && (
        <p className="dataset-note">
          This run only sampled at step 0, so there is no post-edit output to compare against. Runs launched from now on
          always sample at their final step as well.
        </p>
      )}
    </div>
  )
}
