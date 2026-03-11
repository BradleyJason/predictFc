import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useTheme } from '../context/ThemeContext'

const NAV_LINKS = [
  { to: '/',             label: 'MATCHS'       },
  { to: '/smart-ticket', label: 'SMART TICKET' },
  { to: '/guide',        label: 'GUIDE'        },
]

export default function Navbar() {
  const { pathname }      = useLocation()
  const { theme, toggle } = useTheme()
  const isDark            = theme === 'dark'
  const [menuOpen, setMenuOpen] = useState(false)

  const closeMenu = () => setMenuOpen(false)

  return (
    <>
      <nav style={{
        position: 'fixed', top: 0, left: 0, right: 0, height: '60px',
        background: isDark ? 'rgba(6,6,14,0.96)' : 'rgba(240,242,248,0.96)',
        backdropFilter: 'blur(12px)',
        borderBottom: '1px solid var(--border)',
        display: 'flex', alignItems: 'center',
        padding: '0 20px', zIndex: 1000,
        justifyContent: 'space-between',
      }}>
        {/* Logo */}
        <Link to="/" onClick={closeMenu} style={{ textDecoration: 'none', flexShrink: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '28px', height: '28px', borderRadius: '50%',
              border: '2px solid var(--accent-green)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
            }}>
              <div style={{
                width: '8px', height: '8px', borderRadius: '50%',
                background: 'var(--accent-green)', boxShadow: '0 0 8px var(--accent-green)',
                animation: 'scannerPulse 2s ease-out infinite',
              }} />
            </div>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: '22px', letterSpacing: '0.05em', color: 'var(--text-primary)', lineHeight: 1 }}>
              PREDICT<span style={{ color: 'var(--accent-green)' }}>///</span>FC
            </span>
          </div>
        </Link>

        {/* Desktop : liens + toggle thème */}
        <div className="nav-desktop" style={{ gap: '8px', alignItems: 'center' }}>
          {NAV_LINKS.map(({ to, label }) => (
            <Link key={to} to={to} className={`nav-link ${pathname === to ? 'active' : ''}`}>
              {label}
            </Link>
          ))}
          <ThemeToggle isDark={isDark} toggle={toggle} />
        </div>

        {/* Mobile : toggle thème + hamburger */}
        <div className="nav-mobile" style={{ gap: '8px', alignItems: 'center' }}>
          <ThemeToggle isDark={isDark} toggle={toggle} />
          <button
            onClick={() => setMenuOpen((o) => !o)}
            aria-label="Menu"
            style={{
              width: '36px', height: '36px', borderRadius: '3px',
              background: menuOpen ? 'var(--accent-green-d)' : 'transparent',
              border: `1px solid ${menuOpen ? 'var(--accent-green)' : 'var(--border)'}`,
              color: menuOpen ? 'var(--accent-green)' : 'var(--text-secondary)',
              fontSize: '18px', cursor: 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              transition: 'all 0.15s ease',
            }}
          >
            {menuOpen ? '✕' : '☰'}
          </button>
        </div>
      </nav>

      {/* Menu déroulant mobile — conditionnel + classe CSS */}
      {menuOpen && (
        <div
          className="nav-dropdown"
          style={{
            position: 'fixed', top: '60px', left: 0, right: 0,
            background: isDark ? 'rgba(6,6,14,0.98)' : 'rgba(240,242,248,0.98)',
            backdropFilter: 'blur(12px)',
            borderBottom: '1px solid var(--border)',
            zIndex: 999,
            padding: '12px 20px 20px',
            gap: '8px',
          }}
        >
          {NAV_LINKS.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              onClick={closeMenu}
              className={`nav-link ${pathname === to ? 'active' : ''}`}
              style={{ textAlign: 'center', padding: '12px' }}
            >
              {label}
            </Link>
          ))}
        </div>
      )}
    </>
  )
}

function ThemeToggle({ isDark, toggle }) {
  return (
    <button
      onClick={toggle}
      title={isDark ? 'Mode clair' : 'Mode sombre'}
      style={{
        width: '36px', height: '36px', borderRadius: '3px', cursor: 'pointer',
        background: 'transparent', border: '1px solid var(--border)',
        color: 'var(--text-secondary)', fontSize: '16px',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        transition: 'all 0.15s ease', flexShrink: 0,
      }}
      onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'var(--border-bright)'; e.currentTarget.style.color = 'var(--text-primary)' }}
      onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--text-secondary)' }}
    >
      {isDark ? '☀' : '◑'}
    </button>
  )
}
