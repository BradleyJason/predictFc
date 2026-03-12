import { createContext, useContext, useEffect, useState } from 'react'

const ThemeContext = createContext()

function getSystemTheme() {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('predictfc-theme')
    if (saved === 'system') return getSystemTheme()
    return saved || 'dark'
  })
  const [mode, setMode] = useState(() =>
    localStorage.getItem('predictfc-theme-mode') || 'dark'
  )

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  // Ecouter changements système
  useEffect(() => {
    if (mode !== 'system') return
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = (e) => setTheme(e.matches ? 'dark' : 'light')
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [mode])

  const toggle = () => {
    const next = theme === 'dark' ? 'light' : 'dark'
    setTheme(next)
    setMode(next)
    localStorage.setItem('predictfc-theme', next)
    localStorage.setItem('predictfc-theme-mode', next)
  }

  const setSystemTheme = () => {
    setMode('system')
    setTheme(getSystemTheme())
    localStorage.setItem('predictfc-theme', 'system')
    localStorage.setItem('predictfc-theme-mode', 'system')
  }

  return (
    <ThemeContext.Provider value={{ theme, mode, toggle, setSystemTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export const useTheme = () => useContext(ThemeContext)
