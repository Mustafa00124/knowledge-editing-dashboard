import { useEffect, useState } from 'react'

const THEMES = [
  { key: 'midnight', label: 'Midnight', swatch: '#6ea8fe' },
  { key: 'crimson', label: 'Crimson', swatch: '#cc2936' },
  { key: 'forest', label: 'Forest', swatch: '#4cbb7d' },
  { key: 'amber', label: 'Amber', swatch: '#e07b1a' },
  { key: 'violet', label: 'Violet', swatch: '#a084e8' },
]

const STORAGE_KEY = 'dashboard_theme'

// Applies data-theme on <html> (index.html also sets this once,
// synchronously before React mounts, to avoid a flash of the wrong theme
// on reload). Persisted to localStorage so it survives across sessions.
export default function ThemeSwitcher() {
  const [theme, setTheme] = useState(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) || 'midnight'
    } catch {
      return 'midnight'
    }
  })
  const [open, setOpen] = useState(false)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    try {
      localStorage.setItem(STORAGE_KEY, theme)
    } catch {
      // localStorage unavailable (private window etc.) - theme still applies for this session
    }
  }, [theme])

  useEffect(() => {
    if (!open) return
    const close = () => setOpen(false)
    window.addEventListener('click', close)
    return () => window.removeEventListener('click', close)
  }, [open])

  const current = THEMES.find((t) => t.key === theme) || THEMES[0]

  return (
    <div className="theme-switcher" onClick={(e) => e.stopPropagation()}>
      <button
        type="button"
        className="theme-switcher-toggle"
        onClick={() => setOpen((o) => !o)}
        title={`Theme: ${current.label}`}
        aria-label="Choose theme"
        aria-expanded={open}
      >
        <span className="theme-swatch" style={{ background: current.swatch }} />
      </button>
      {open && (
        <div className="theme-switcher-menu" role="menu">
          {THEMES.map((t) => (
            <button
              key={t.key}
              type="button"
              role="menuitemradio"
              aria-checked={t.key === theme}
              className={`theme-option${t.key === theme ? ' selected' : ''}`}
              onClick={() => {
                setTheme(t.key)
                setOpen(false)
              }}
            >
              <span className="theme-swatch" style={{ background: t.swatch }} />
              {t.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
