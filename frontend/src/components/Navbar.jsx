import { Link, useLocation } from 'react-router-dom'

export default function Navbar() {
  const { pathname } = useLocation()

  return (
    <nav
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        height: '60px',
        background: 'rgba(6, 6, 14, 0.96)',
        backdropFilter: 'blur(12px)',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        padding: '0 24px',
        zIndex: 100,
        justifyContent: 'space-between',
      }}
    >
      {/* Logo */}
      <Link to="/" style={{ textDecoration: 'none' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {/* Target icon */}
          <div
            style={{
              width: '28px',
              height: '28px',
              borderRadius: '50%',
              border: '2px solid var(--accent-green)',
              position: 'relative',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <div
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: 'var(--accent-green)',
                boxShadow: '0 0 8px var(--accent-green)',
                animation: 'scannerPulse 2s ease-out infinite',
              }}
            />
          </div>
          <span
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: '22px',
              letterSpacing: '0.05em',
              color: 'var(--text-primary)',
              lineHeight: 1,
            }}
          >
            PREDICT
            <span style={{ color: 'var(--accent-green)' }}>///</span>
            FC
          </span>
        </div>
      </Link>

      {/* Nav links */}
      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
        <Link
          to="/"
          className={`nav-link ${pathname === '/' ? 'active' : ''}`}
        >
          MATCHS
        </Link>
        <Link
          to="/smart-ticket"
          className={`nav-link ${pathname === '/smart-ticket' ? 'active' : ''}`}
        >
          SMART TICKET
        </Link>
      </div>
    </nav>
  )
}
