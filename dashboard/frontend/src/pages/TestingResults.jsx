import { useEffect, useState } from 'react'
import EvaluationFilter from '../components/EvaluationFilter.jsx'
import BERTScoreNote from '../components/BERTScoreNote.jsx'
import { evaluationRow } from '../lib/evaluationModes.js'
import { api } from '../api.js'

export default function TestingResults() {
  const [evaluation, setEvaluation] = useState('original')
  const [groups, setGroups] = useState([])
  const [selected, setSelected] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    const load = () => api.testingResults().then(setGroups).catch((e) => setError(e.message))
    load()
    const timer = setInterval(load, 5000)
    return () => clearInterval(timer)
  }, [])

  const group = groups.find((g) => g.id === selected)

  return (
    <div className="testing-results">
      <EvaluationFilter value={evaluation} onChange={setEvaluation} />
      {evaluation === 'bertscore' && <BERTScoreNote />}
      {error && <div className="form-error">{error}</div>}
      {groups.length === 0 && <p className="empty">No trial runs yet. Turn off “Save to main Results” when staging an experiment.</p>}
      <div className="testing-layout">
        <div className="testing-list" aria-label="Trial runs, newest first">
          {groups.map((g) => (
            <button key={g.id} type="button" className={`testing-list-item${selected === g.id ? ' active' : ''}`} onClick={() => setSelected(g.id)}>
              <strong>{new Date(g.submitted_at).toLocaleString()}</strong>
              <span>{g.jobs.length} job{g.jobs.length === 1 ? '' : 's'} · {g.jobs.map((j) => j.status.state).join(', ')}</span>
            </button>
          ))}
        </div>
        {group && <div className="testing-detail">
          <h2>{new Date(group.submitted_at).toLocaleString()}</h2>
          <p className="drawer-desc">Folder: Trial Runs/{group.id}</p>
          {group.jobs.map((job) => (
            <article className="testing-job" key={job.job_id}>
              <h3>{job.run_name}</h3>
              <p><strong>Status:</strong> {job.status.state} · <strong>Job:</strong> {job.job_id} · <strong>Elapsed:</strong> {job.status.elapsed || '—'}</p>
              <p><strong>Checkpoints:</strong> {job.checkpoint_count} {job.latest_checkpoint?.step != null && `· Latest step: ${job.latest_checkpoint.step}`}</p>
              <p><strong>Sample steps:</strong> {job.sample_steps.length ? job.sample_steps.join(', ') : 'None yet'}</p>
              <details><summary>Settings</summary><pre>{JSON.stringify(job.params, null, 2)}</pre></details>
              {job.latest_checkpoint && <details open><summary>Latest metrics</summary><pre>{JSON.stringify(evaluationRow(job.latest_checkpoint, evaluation), null, 2)}</pre></details>}
              {job.summary && <details open><summary>Final summary</summary><pre>{JSON.stringify(evaluationRow(job.summary, evaluation), null, 2)}</pre></details>}
              {job.latest_sample && <details><summary>Latest generated responses</summary><pre>{JSON.stringify(job.latest_sample, null, 2)}</pre></details>}
              {job.err_tail && <details><summary>Error log</summary><pre>{job.err_tail}</pre></details>}
              {job.log_tail && <details><summary>Output log</summary><pre>{job.log_tail}</pre></details>}
            </article>
          ))}
        </div>}
      </div>
    </div>
  )
}
