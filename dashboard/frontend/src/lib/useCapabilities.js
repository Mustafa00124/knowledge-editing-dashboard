import { useEffect, useState } from 'react'
import { api } from '../api.js'

// What this machine can run (see backend/environment.py). On gaivi every
// type can launch; on a fresh clone without SLURM, a GPU or the experiment
// environment, launching is greyed out and the reasons are shown instead.
// Null until loaded, and a failed load blocks nothing: the backend still
// refuses a launch it cannot run, with the same reasons.
export default function useCapabilities() {
  const [capabilities, setCapabilities] = useState(null)
  useEffect(() => {
    let live = true
    api.capabilities().then((next) => { if (live) setCapabilities(next) }).catch(() => {})
    return () => { live = false }
  }, [])
  return capabilities
}

export function launchBlockers(capabilities, experimentType) {
  if (!capabilities || !experimentType) return []
  return capabilities.blockers?.[experimentType] || []
}
