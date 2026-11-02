import { NavLink } from 'react-router-dom'

// The two main experiments, one per study (parameter editing, and in-context
// editing against a knowledge base of distractors), and the investigations:
// side experiments that set up their configuration. Same look as the Results subnav.
export default function ExperimentsSubnav() {
  const cls = ({ isActive }) => `results-subnav-link${isActive ? ' active' : ''}`
  return (
    <nav className="results-subnav" aria-label="Experiments area">
      <NavLink to="/experiments" end className={cls}>Parameter editing experiments</NavLink>
      <NavLink to="/experiments/in-context" className={cls}>In-context experiments</NavLink>
      <NavLink to="/experiments/investigations" className={cls}>Hyperparameter tuning</NavLink>
    </nav>
  )
}
