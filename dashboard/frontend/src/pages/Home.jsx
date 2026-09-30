import { Link } from 'react-router-dom'

// Every other page is built for clarity first; this one gets to be a
// little more decorative since it's not somewhere data actually lives -
// each card reuses that destination's own accent-* class, so the color
// preview here always matches what you'll actually land on.
const SECTIONS = [
  {
    to: '/datasets',
    accentClass: 'accent-datasets',
    label: 'Datasets',
    blurb: 'Every benchmark wired into this project: record-level detail, edit-type breakdowns, and per-benchmark size/count stats.',
  },
  {
    to: '/models',
    accentClass: 'accent-models',
    label: 'Models',
    blurb: 'Which base models are downloaded and ready to edit.',
  },
  {
    to: '/methods',
    accentClass: 'accent-methods',
    label: 'Methods',
    blurb: 'Every knowledge-editing method this project can run, organized by family. Press one to see how it actually works.',
  },
  {
    to: '/experiments',
    accentClass: 'accent-experiments',
    label: 'Experiments',
    blurb: 'Stage and launch SLURM runs: pick a method, model, dataset, and hyperparameter sweep across 8 queue slots.',
  },
  {
    to: '/results',
    accentClass: 'accent-results',
    label: 'Results',
    blurb: 'Compare finished runs: a table averaged across any two config axes, per-method training curves, and raw generated responses.',
  },
]

export default function Home() {
  return (
    <div className="home">
      <section className="home-hero">
        <h1>Welcome to the Knowledge-Editing Dashboard</h1>
        <p className="home-byline">by Sid</p>
        <p className="home-intro">
          A dashboard for running and tracking knowledge-editing research: finetuning, locate-and-edit, and
          in-context methods, evaluated across a growing set of datasets and models, launched as SLURM jobs and
          tracked here as they run.
        </p>
      </section>

      <div className="home-grid">
        {SECTIONS.map((s) => (
          <Link key={s.to} to={s.to} className={`home-card ${s.accentClass}`}>
            <h2>{s.label}</h2>
            <p>{s.blurb}</p>
            <span className="home-card-arrow" aria-hidden="true">→</span>
          </Link>
        ))}
      </div>
    </div>
  )
}
