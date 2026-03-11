import { useEffect, useState } from 'react'
import { getMatches } from '../services/api'
import MatchCard from '../components/MatchCard'

const LEAGUES = [
  { code: null,  label: 'TOUT'             },
  { code: 'FL1', label: 'Ligue 1'          },
  { code: 'PL',  label: 'Premier League'   },
  { code: 'PD',  label: 'La Liga'          },
  { code: 'BL1', label: 'Bundesliga'       },
  { code: 'SA',  label: 'Serie A'          },
  { code: 'CL',  label: 'Champions League' },
]

const TABS = [
  { key: 'upcoming', label: 'À VENIR'   },
  { key: 'live',     label: 'EN COURS'  },
  { key: 'results',  label: 'RÉSULTATS' },
]

function getDateWindow(tab) {
  const now = new Date()
  if (tab === 'results') {
    const from = new Date(now)
    from.setDate(now.getDate() - 3)
    const to = new Date(now)
    to.setDate(now.getDate() - 1)
    return {
      date_from: from.toISOString().split('T')[0],
      date_to:   to.toISOString().split('T')[0],
      status:    'FINISHED',
    }
  }
  const from = new Date(now)
  const to   = new Date(now)
  to.setDate(now.getDate() + 7)
  return {
    date_from: from.toISOString().split('T')[0],
    date_to:   to.toISOString().split('T')[0],
  }
}

export default function Dashboard() {
  const [allMatches, setAllMatches] = useState([])
  const [loading, setLoading]       = useState(true)
  const [error, setError]           = useState(null)
  const [league, setLeague]         = useState(null)
  const [tab, setTab]               = useState('upcoming')

  useEffect(() => {
    setLoading(true)
    setError(null)
    const { date_from, date_to, status } = getDateWindow(tab)
    const params = { limit: 200, date_from, date_to, ...(status ? { status } : {}) }
    getMatches(params)
      .then((res) => {
        setAllMatches(res.data.matches || [])
        setLoading(false)
      })
      .catch(() => {
        setError('Impossible de charger les matchs. Le backend est-il démarré ?')
        setLoading(false)
      })
  }, [tab])

  const byLeague = league
    ? allMatches.filter((m) => m.competition?.code === league)
    : allMatches

  const filtered = byLeague.filter((m) => {
    if (tab === 'live')    return m.status === 'IN_PLAY'
    if (tab === 'results') return m.status === 'FINISHED'
    return m.status !== 'FINISHED' && m.status !== 'IN_PLAY'
  })

  const liveCount = allMatches.filter((m) => m.status === 'IN_PLAY').length

  return (
    <div className="page-container" style={{ maxWidth: '1240px', margin: '0 auto', padding: '36px 24px' }}>
      <div style={{ marginBottom: '32px' }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '14px', marginBottom: '8px' }}>
          <h1 style={{
            fontFamily: 'var(--font-display)',
            fontSize: 'clamp(36px, 6vw, 56px)',
            letterSpacing: '0.04em',
            color: 'var(--text-primary)',
            lineHeight: 1,
            margin: 0,
          }}>
            MATCHS
          </h1>
          {!loading && (
            <span style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '11px',
              color: 'var(--text-muted)',
              letterSpacing: '0.1em',
            }}>
              {filtered.length} RÉSULTATS
            </span>
          )}
        </div>
        <div style={{ width: '44px', height: '2px', background: 'var(--accent-green)', boxShadow: '0 0 10px var(--accent-green)' }} />
      </div>

      {/* Onglets — scroll horizontal sur mobile */}
      <div className="tabs-row" style={{ display: 'flex', gap: '4px', marginBottom: '20px' }}>
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '11px',
              letterSpacing: '0.1em',
              padding: '8px 18px',
              borderRadius: '2px',
              border: tab === t.key ? '1px solid var(--accent-green)' : '1px solid var(--border)',
              background: tab === t.key ? 'rgba(0,255,136,0.08)' : 'transparent',
              color: tab === t.key ? 'var(--accent-green)' : 'var(--text-muted)',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            {t.label}
            {t.key === 'live' && liveCount > 0 && (
              <span style={{
                background: 'var(--accent-green)',
                color: '#06060e',
                fontSize: '9px',
                fontWeight: 700,
                padding: '1px 5px',
                borderRadius: '10px',
              }}>
                {liveCount}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Filtres ligues — scroll horizontal sur mobile */}
      <div className="league-filters" style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '32px' }}>
        {LEAGUES.map((l) => (
          <button
            key={l.label}
            onClick={() => setLeague(l.code)}
            className={`league-tab ${league === l.code ? 'active' : ''}`}
          >
            {l.label}
          </button>
        ))}
      </div>

      {loading && <LoadingState />}
      {!loading && error && <ErrorState message={error} />}
      {!loading && !error && filtered.length === 0 && <EmptyState tab={tab} />}

      {!loading && !error && filtered.length > 0 && (
        <div className="matches-grid" style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
          gap: '14px',
        }}>
          {filtered.map((match, i) => (
            <MatchCard
              key={match.id}
              match={match}
              animationDelay={i * 55}
              showAnalyze={match.status !== 'FINISHED'}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function LoadingState() {
  return (
    <div style={{
      textAlign: 'center', padding: '100px 0',
      fontFamily: 'var(--font-mono)', fontSize: '12px',
      color: 'var(--text-muted)', letterSpacing: '0.12em',
      display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '14px',
    }}>
      <span style={{ color: 'var(--accent-green)', fontSize: '22px', animation: 'pulseGlow 1.4s ease-in-out infinite' }}>
        ■ ■ ■
      </span>
      RÉCUPÉRATION DES DONNÉES...
    </div>
  )
}

function ErrorState({ message }) {
  return (
    <div style={{
      border: '1px solid rgba(255, 68, 85, 0.3)',
      background: 'rgba(255, 68, 85, 0.05)',
      borderRadius: '4px', padding: '20px 24px',
      fontFamily: 'var(--font-mono)', color: '#ff5566',
      fontSize: '12px', letterSpacing: '0.06em', lineHeight: 1.6,
    }}>
      <div style={{ marginBottom: '6px', fontSize: '10px', color: '#ff5566aa', letterSpacing: '0.14em' }}>
        ERREUR RÉSEAU
      </div>
      ⚠ {message}
    </div>
  )
}

function EmptyState({ tab }) {
  const messages = {
    live:     'AUCUN MATCH EN COURS ACTUELLEMENT',
    upcoming: 'AUCUN MATCH À VENIR CETTE SEMAINE',
    results:  'AUCUN RÉSULTAT SUR LES 3 DERNIERS JOURS',
  }
  return (
    <div style={{
      textAlign: 'center', padding: '100px 0',
      fontFamily: 'var(--font-mono)', color: 'var(--text-muted)',
      fontSize: '12px', letterSpacing: '0.12em',
      border: '1px dashed var(--border)', borderRadius: '4px',
    }}>
      {messages[tab] || 'AUCUN MATCH DISPONIBLE'}
    </div>
  )
}
