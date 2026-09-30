import { useEffect, useRef, useState } from 'react'
import { api } from '../api.js'

// Keep results tied to their source and page, including the render before
// effects run after a dataset switch. Never hand old records to a new schema.
export function useDatasetPage(benchmark, subset, viewMode, pageSize, showLocality = false) {
  const key = subset?.shape === 'flat_qa' ? subset.editKey : undefined
  // Locality checks live in a sibling file (see datasetCatalog.js), so
  // switching to them is just paging a different file for the same subset.
  const file = showLocality && subset?.localityFile ? subset.localityFile : subset?.file
  const source = JSON.stringify([benchmark, subset?.key, file, key, pageSize])
  const [position, setPosition] = useState({ source, page: 0 })
  const page = position.source === source ? position.page : 0
  const request = JSON.stringify([source, page])
  const [result, setResult] = useState(null)
  const [failure, setFailure] = useState(null)
  const cacheRef = useRef({ source, pages: new Map() })

  function setPage(update) {
    setPosition(previous => {
      const current = previous.source === source ? previous.page : 0
      return { source, page: typeof update === 'function' ? update(current) : update }
    })
  }

  useEffect(() => {
    if (!subset) return
    let cancelled = false
    if (cacheRef.current.source !== source) cacheRef.current = { source, pages: new Map() }
    const cache = cacheRef.current.pages
    function load(p) {
      if (!cache.has(p)) {
        const promise = api.datasetPreview(benchmark, file, p * pageSize, pageSize, key)
          .catch(error => { cache.delete(p); throw error })
        cache.set(p, promise)
      }
      return cache.get(p)
    }
    setFailure(null)
    load(page).then(data => {
      if (cancelled) return
      setResult({ request, data })
      if (data.offset + data.records.length < data.total) load(page + 1).catch(() => {})
    }).catch(() => {
      if (!cancelled) setFailure({ request, message: 'Unable to load this dataset. Try selecting it again or refreshing.' })
    })
    return () => { cancelled = true }
  }, [benchmark, subset, file, key, page, pageSize, source, request])

  const data = result?.request === request ? result.data : null
  const error = failure?.request === request ? failure.message : null
  const loading = Boolean(subset) && !data && !error
  const totalPages = data ? Math.max(1, Math.ceil(data.total / pageSize)) : 0
  return { data, loading, error, page, setPage, totalPages }
}
