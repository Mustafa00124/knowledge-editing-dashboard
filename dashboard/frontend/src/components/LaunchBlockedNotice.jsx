import { Link } from 'react-router-dom'

// Explains why Launch is greyed out on this machine. Browsing results and
// datasets still works; only starting experiments needs these.
export default function LaunchBlockedNotice({ blockers }) {
  if (!blockers?.length) return null
  return (
    <div className="launch-blocked" role="status">
      <strong>Experiments can't launch on this machine.</strong> Results and datasets are still browsable.
      <ul>
        {blockers.map((reason) => <li key={reason}>{reason}</li>)}
      </ul>
      <p className="launch-blocked-action">
        Missing downloads can be added on the <Link to="/downloads">Downloads page</Link>.
      </p>
    </div>
  )
}
