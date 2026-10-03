import { NavLink } from 'react-router-dom'

// Main experiments and the investigations that set up their configuration
// (mechanistic measurements, hyperparameter sweeps, prompt formats). Same
// look as the Results subnav.
export default function ExperimentsSubnav() {
  const cls = ({ isActive }) => `results-subnav-link${isActive ? ' active' : ''}`
  return (
    <nav className="results-subnav" aria-label="Experiments area">
      <NavLink to="/experiments" end className={cls}>Main experiments</NavLink>
      <NavLink to="/experiments/investigations" className={cls}>Investigations</NavLink>
    </nav>
  )
}
