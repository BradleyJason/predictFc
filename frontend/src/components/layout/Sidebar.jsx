import { useState, useEffect, useRef } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'
import { getLiveMatches, getCompetitions, searchTeams } from '../../services/api'

const NAV = [
  { to: '/',             icon: '⬡', label: 'ACCUEIL'      },
  { to: '/matches',      icon: '◈', label: 'MATCHS'       },
  { to: '/value-bets',   icon: '◆', label: 'VALUE BETS'   },
  { to: '/smart-ticket', icon: '▲', label: 'SMART TICKET' },
  { to: '/guide',        icon: '◉', label: 'GUIDE'        },
]

export default function Sidebar({ open, onClose }) {
  const { pathname } = useLocation()
  const navigate     = useNavigate()
  const logout       = useAuthStore((s) => s.logout)
  const [search,       setSearch]       = useState('')
  const [searchRes,    setSearchRes]    = useState([])
  const [searchOpen,   setSearchOpen]   = useState(false)
  const [liveList,     setLiveList]     = useState([])
  const [competitions, setCompetitions] = useState([])
  const [compLimit,    setCompLimit]    = useState(8)
  const searchRef = useRef(null)

  // Charger compétitions
  useEffect(() => {
    getCompetitions()
      .then((r) => setCompetitions(r.data || []))
      .catch(() => {})
  }, [])

  // Poll live toutes les 60s
  useEffect(() => {
    const fetch = () => {
      getLiveMatches().then((r) => setLiveList(r.data || [])).catch(() => {})
    }
    fetch()
    const id = setInterval(fetch, 60000)
    return () => clearInterval(id)
  }, [])

  // Recherche équipe avec debounce
  useEffect(() => {
    if (search.trim().length < 2) { setSearchRes([]); setSearchOpen(false); return }
    const t = setTimeout(() => {
      searchTeams(search.trim())
        .then((r) => { setSearchRes(r.data || []); setSearchOpen(true) })
        .catch(() => {})
    }, 300)
    return () => clearTimeout(t)
  }, [search])

  // Fermer dropdown si clic extérieur
  useEffect(() => {
    const handler = (e) => {
      if (searchRef.current && !searchRef.current.contains(e.target)) {
        setSearchOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleNav = () => onClose?.()

  const handleTeamSelect = (team) => {
    setSearch('')
    setSearchOpen(false)
    navigate(`/search?team_id=${team.id}&name=${encodeURIComponent(team.name)}`)
    onClose?.()
  }

  // Filtrer compétitions : ligues en premier, puis coupes
  const leagues = competitions.filter(c => c.type === 'LEAGUE')
  const cups    = competitions.filter(c => c.type !== 'LEAGUE')
  const allSorted = [...leagues, ...cups]
  const displayed = allSorted.slice(0, compLimit)

  return (
    <>
      {open && (
        <div onClick={onClose} style={{
          position: 'fixed', inset: 0, zIndex: 199,
          background: 'rgba(6,6,14,0.7)', backdropFilter: 'blur(4px)',
        }} />
      )}

      <aside className="sidebar" style={{
        position: 'fixed', top: 0, left: 0, bottom: 0, width: '240px',
        background: 'var(--bg-surface)',
        borderRight: '1px solid var(--border)',
        zIndex: 200, display: 'flex', flexDirection: 'column',
        transition: 'transform 0.25s ease', overflowY: 'auto',
      }}>
        {/* Logo */}
        <div style={{ padding: '18px 18px 14px', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
          <Link to="/" onClick={handleNav} style={{ textDecoration: 'none' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{
                width: '26px', height: '26px', borderRadius: '50%',
                border: '2px solid var(--accent-green)',
                display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
              }}>
                <div style={{
                  width: '7px', height: '7px', borderRadius: '50%',
                  background: 'var(--accent-green)', boxShadow: '0 0 8px var(--accent-green)',
                  animation: 'scannerPulse 2s ease-out infinite',
                }} />
              </div>
              <span style={{ fontFamily: 'var(--font-display)', fontSize: '19px', letterSpacing: '0.05em', color: 'var(--text-primary)' }}>
                PREDICT<span style={{ color: 'var(--accent-green)' }}>///</span>FC
              </span>
            </div>
          </Link>
        </div>

        {/* Search */}
        <div style={{ padding: '12px 12px 8px', flexShrink: 0 }} ref={searchRef}>
          <div style={{ position: 'relative' }}>
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Rechercher une équipe..."
              style={{
                width: '100%', padding: '8px 32px 8px 10px',
                background: 'var(--bg-elevated)', border: '1px solid var(--border)',
                borderRadius: '4px', color: 'var(--text-primary)',
                fontFamily: 'var(--font-mono)', fontSize: '10px',
                outline: 'none', boxSizing: 'border-box', transition: 'border-color 0.2s',
              }}
              onFocus={(e) => e.target.style.borderColor = 'var(--accent-green)'}
              onBlur={(e)  => e.target.style.borderColor = 'var(--border)'}
            />
            <span style={{
              position: 'absolute', right: '8px', top: '50%',
              transform: 'translateY(-50%)', color: 'var(--text-muted)', fontSize: '13px',
            }}>⌕</span>

            {/* Dropdown résultats */}
            {searchOpen && searchRes.length > 0 && (
              <div style={{
                position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 300,
                background: 'var(--bg-surface)', border: '1px solid var(--border)',
                borderRadius: '4px', marginTop: '4px',
                boxShadow: '0 8px 24px rgba(0,0,0,0.4)', overflow: 'hidden',
              }}>
                {searchRes.map((team) => (
                  <div
                    key={team.id}
                    onClick={() => handleTeamSelect(team)}
                    style={{
                      display: 'flex', alignItems: 'center', gap: '8px',
                      padding: '9px 12px', cursor: 'pointer',
                      borderBottom: '1px solid var(--border)',
                      transition: 'background 0.1s',
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-elevated)'}
                    onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                  >
                    {team.crest_url
                      ? <img src={team.crest_url} alt="" width={18} height={18} style={{ objectFit: 'contain', flexShrink: 0 }} onError={(e) => e.target.style.display = 'none'} />
                      : <div style={{ width: 18, height: 18, borderRadius: '50%', background: 'var(--bg-elevated)', flexShrink: 0 }} />
                    }
                    <span style={{ fontFamily: 'var(--font-display)', fontSize: '12px', color: 'var(--text-primary)' }}>
                      {team.name}
                    </span>
                  </div>
                ))}
              </div>
            )}
            {searchOpen && searchRes.length === 0 && search.length >= 2 && (
              <div style={{
                position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 300,
                background: 'var(--bg-surface)', border: '1px solid var(--border)',
                borderRadius: '4px', marginTop: '4px', padding: '10px 12px',
                fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-muted)',
              }}>
                Aucune équipe trouvée
              </div>
            )}
          </div>
        </div>

        {/* Nav */}
        <nav style={{ padding: '0 8px', flex: 1, overflowY: 'auto' }}>
          <SidebarLabel>NAVIGATION</SidebarLabel>
          {NAV.map(({ to, icon, label }) => {
            const active = pathname === to
            return (
              <Link key={to} to={to} onClick={handleNav} style={{
                display: 'flex', alignItems: 'center', gap: '10px',
                padding: '8px 10px', borderRadius: '4px',
                textDecoration: 'none', marginBottom: '1px',
                background: active ? 'rgba(0,255,136,0.08)' : 'transparent',
                border: active ? '1px solid rgba(0,255,136,0.2)' : '1px solid transparent',
                transition: 'all 0.15s ease',
              }}
              onMouseEnter={(e) => { if (!active) e.currentTarget.style.background = 'var(--bg-elevated)' }}
              onMouseLeave={(e) => { if (!active) e.currentTarget.style.background = 'transparent' }}
              >
                <span style={{ fontSize: '10px', color: active ? 'var(--accent-green)' : 'var(--text-muted)', flexShrink: 0 }}>{icon}</span>
                <span style={{
                  fontFamily: 'var(--font-mono)', fontSize: '10px', fontWeight: 600,
                  letterSpacing: '0.1em', color: active ? 'var(--accent-green)' : 'var(--text-secondary)',
                }}>{label}</span>
              </Link>
            )
          })}

          {/* Live */}
          {liveList.length > 0 && (
            <>
              <SidebarLabel style={{ marginTop: '12px' }}>
                LIVE
                <span style={{
                  marginLeft: '6px', background: 'var(--accent-green)', color: '#06060e',
                  fontSize: '7px', fontWeight: 700, padding: '1px 5px', borderRadius: '10px',
                  animation: 'pulseGlow 1.4s infinite',
                }}>{liveList.length}</span>
              </SidebarLabel>
              {liveList.slice(0, 3).map((m) => (
                <Link key={m.id} to={`/match/${m.id}`} onClick={handleNav} style={{
                  display: 'flex', alignItems: 'center', gap: '6px',
                  padding: '6px 10px', borderRadius: '4px', textDecoration: 'none',
                  marginBottom: '1px', background: 'rgba(0,255,136,0.04)',
                  border: '1px solid rgba(0,255,136,0.1)', transition: 'all 0.15s',
                }}>
                  <span style={{ width: '5px', height: '5px', borderRadius: '50%', background: 'var(--accent-green)', animation: 'pulseGlow 1.4s infinite', flexShrink: 0 }} />
                  <span style={{ fontFamily: 'var(--font-display)', fontSize: '10px', color: 'var(--text-primary)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {m.home_team?.short_name || m.home_team?.name} {m.home_score}—{m.away_score} {m.away_team?.short_name || m.away_team?.name}
                  </span>
                </Link>
              ))}
            </>
          )}

          {/* Compétitions dynamiques */}
          <SidebarLabel style={{ marginTop: '12px' }}>COMPÉTITIONS</SidebarLabel>
          {displayed.map((c) => (
            <Link key={c.id} to={`/matches?competition=${c.code || c.id}`} onClick={handleNav} style={{
              display: 'flex', alignItems: 'center', gap: '8px',
              padding: '6px 10px', borderRadius: '4px', textDecoration: 'none',
              marginBottom: '1px', transition: 'all 0.15s',
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-elevated)'}
            onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
            >
              {c.crest_url
                ? <img src={c.crest_url} alt="" width={14} height={14} style={{ objectFit: 'contain', flexShrink: 0 }} onError={(e) => e.target.style.display = 'none'} />
                : <span style={{ width: 14, height: 14, borderRadius: '50%', background: 'var(--border)', display: 'inline-block', flexShrink: 0 }} />
              }
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-secondary)', letterSpacing: '0.03em', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {c.name}
              </span>
            </Link>
          ))}
          {allSorted.length > compLimit && (
            <button onClick={() => setCompLimit(l => l + 10)} style={{
              width: '100%', padding: '6px', marginTop: '4px',
              background: 'transparent', border: '1px dashed var(--border)',
              borderRadius: '4px', color: 'var(--text-muted)',
              fontFamily: 'var(--font-mono)', fontSize: '9px',
              letterSpacing: '0.1em', cursor: 'pointer',
            }}>
              + VOIR PLUS ({allSorted.length - compLimit})
            </button>
          )}
        </nav>

        {/* Footer */}
        <div style={{ padding: '10px 12px', borderTop: '1px solid var(--border)', flexShrink: 0 }}>
          <Link to="/profile" onClick={handleNav} style={{
            display: 'flex', alignItems: 'center', gap: '8px',
            padding: '7px 8px', borderRadius: '4px', textDecoration: 'none',
            marginBottom: '6px', transition: 'all 0.15s',
          }}
          onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-elevated)'}
          onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
          >
            <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>◎</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-secondary)', letterSpacing: '0.08em' }}>PROFIL ADMIN</span>
          </Link>
          <button onClick={() => { logout(); navigate('/login') }} style={{
            width: '100%', padding: '7px 8px', background: 'transparent',
            border: '1px solid rgba(255,68,85,0.2)', borderRadius: '4px',
            color: '#ff5566', cursor: 'pointer', fontFamily: 'var(--font-mono)',
            fontSize: '10px', letterSpacing: '0.1em', textAlign: 'left',
            transition: 'all 0.15s',
          }}
          onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,68,85,0.06)'}
          onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
          >
            ⊗ DÉCONNEXION
          </button>
        </div>
      </aside>
    </>
  )
}

function SidebarLabel({ children, style }) {
  return (
    <div style={{
      fontFamily: 'var(--font-mono)', fontSize: '8px', letterSpacing: '0.2em',
      color: 'var(--text-muted)', padding: '6px 10px 3px',
      display: 'flex', alignItems: 'center', ...style,
    }}>
      {children}
    </div>
  )
}
