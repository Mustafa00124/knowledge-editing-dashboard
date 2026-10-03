import { NavLink } from 'react-router-dom'

// The two results areas are separate pages, not tabs: each loads only its
// own data when opened (App.jsx lazy-loads both).
export default function ResultsSubnav() {
  const cls = ({ isActive }) => `results-subnav-link${isActive ? ' active' : ''}`
  return (
    <nav className="results-subnav" aria-label="Results area">
      <NavLink to="/results/main" className={cls}>Main experiments</NavLink>
      <NavLink to="/results/investigations" className={cls}>Investigations</NavLink>
    </nav>
  )
}
