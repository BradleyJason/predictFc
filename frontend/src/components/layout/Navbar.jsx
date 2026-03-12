import { Link } from 'react-router-dom'
import { useTheme } from '../../context/ThemeContext'

export default function Navbar({ onMenuToggle }) {
  const { theme, toggle, setSystemTheme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <nav style={{
      position: 'fixed', top: 0, right: 0, height: '60px',
      background: isDark ? 'rgba(6,6,14,0.96)' : 'rgba(240,242,248,0.96)',
      backdropFilter: 'blur(12px)',
      borderBottom: '1px solid var(--border)',
      display: 'flex', alignItems: 'center',
      padding: '0 20px', zIndex: 100,
      justifyContent: 'space-between',
      gap: '12px',
    }}
    className="top-navbar"
    >
      {/* Hamburger mobile */}
      <button
        onClick={onMenuToggle}
        className="hamburger-btn"
        aria-label="Menu"
        style={{
          width: '36px', height: '36px', borderRadius: '3px',
          background: 'transparent',
          border: '1px solid var(--border)',
          color: 'var(--text-secondary)',
          fontSize: '18px', cursor: 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}
      >☰</button>

      {/* Logo mobile */}
      <Link to="/" className="navbar-logo-mobile" style={{ textDecoration: 'none' }}>
        <span style={{
          fontFamily: 'var(--font-display)', fontSize: '18px',
          letterSpacing: '0.05em', color: 'var(--text-primary)',
        }}>
          PREDICT<span style={{ color: 'var(--accent-green)' }}>///</span>FC
        </span>
      </Link>

      {/* Theme toggle */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
        <button
          onClick={toggle}
          title={isDark ? 'Mode clair' : 'Mode sombre'}
          style={{
            width: '36px', height: '36px', borderRadius: '3px',
            background: 'transparent', border: '1px solid var(--border)',
            color: 'var(--text-secondary)', fontSize: '16px',
            cursor: 'pointer', display: 'flex',
            alignItems: 'center', justifyContent: 'center',
            transition: 'all 0.15s ease',
          }}
        >
          {isDark ? '☀' : '◑'}
        </button>
        <button
          onClick={setSystemTheme}
          title="Thème système"
          style={{
            width: '36px', height: '36px', borderRadius: '3px',
            background: 'transparent', border: '1px solid var(--border)',
            color: 'var(--text-muted)', fontSize: '13px',
            cursor: 'pointer', display: 'flex',
            alignItems: 'center', justifyContent: 'center',
            transition: 'all 0.15s ease',
          }}
        >
          ⊙
        </button>
      </div>
    </nav>
  )
}
