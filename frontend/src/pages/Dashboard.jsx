import { useEffect, useState } from 'react'
import { getMatches } from '../services/api'
import MatchCard from '../components/MatchCard'

const LEAGUES = [
  { code: null, label: 'TOUT' },
  { code: 'FL1',  label: 'FL1'  },
  { code: 'PL',   label: 'PL'   },
  { code: 'PD',   label: 'PD'   },
  { code: 'BL1',  label: 'BL1'  },
  { code: 'SA',   label: 'SA'   },
  { code: 'CL',   label: 'CL'   },
]

export default function Dashboard() {
  const [matches, setMatches] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)
  const [league, setLeague]   = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    getMatches({ limit: 60 })
      .then((res) => {
        setMatches(res.data.matches || [])
        setLoading(false)
      })
      .catch(() => {
        setError('Impossible de charger les matchs. Le backend est-il démarré ?')
        setLoading(false)
      })
  }, [])

  const filtered = league
    ? matches.filter((m) => m.competition?.code === league)
    : matches

  return (
    <div style={{ maxWidth: '1240px', margin: '0 auto', padding: '36px 24px' }}>
      {/* Page heading */}
      <div style={{ marginBottom: '32px' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'baseline',
            gap: '14px',
            marginBottom: '8px',
          }}
        >
          <h1
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: 'clamp(36px, 6vw, 56px)',
              letterSpacing: '0.04em',
              color: 'var(--text-primary)',
              lineHeight: 1,
              margin: 0,
            }}
          >
            MATCHS
          </h1>
          {!loading && (
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '11px',
                color: 'var(--text-muted)',
                letterSpacing: '0.1em',
              }}
            >
              {filtered.length} RÉSULTATS
            </span>
          )}
        </div>
        {/* Accent underline */}
        <div
          style={{
            width: '44px',
            height: '2px',
            background: 'var(--accent-green)',
            boxShadow: '0 0 10px var(--accent-green)',
          }}
        />
      </div>

      {/* League filter tabs */}
      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '32px' }}>
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

      {/* States */}
      {loading && <LoadingState />}
      {!loading && error && <ErrorState message={error} />}
      {!loading && !error && filtered.length === 0 && <EmptyState />}

      {/* Match grid */}
      {!loading && !error && filtered.length > 0 && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
            gap: '14px',
          }}
        >
          {filtered.map((match, i) => (
            <MatchCard key={match.id} match={match} animationDelay={i * 55} />
          ))}
        </div>
      )}
    </div>
  )
}

/* ── Sub-components ── */

function LoadingState() {
  return (
    <div
      style={{
        textAlign: 'center',
        padding: '100px 0',
        fontFamily: 'var(--font-mono)',
        fontSize: '12px',
        color: 'var(--text-muted)',
        letterSpacing: '0.12em',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '14px',
      }}
    >
      <span
        style={{
          color: 'var(--accent-green)',
          fontSize: '22px',
          animation: 'pulseGlow 1.4s ease-in-out infinite',
        }}
      >
        ■ ■ ■
      </span>
      RÉCUPÉRATION DES DONNÉES...
    </div>
  )
}

function ErrorState({ message }) {
  return (
    <div
      style={{
        border: '1px solid rgba(255, 68, 85, 0.3)',
        background: 'rgba(255, 68, 85, 0.05)',
        borderRadius: '4px',
        padding: '20px 24px',
        fontFamily: 'var(--font-mono)',
        color: '#ff5566',
        fontSize: '12px',
        letterSpacing: '0.06em',
        lineHeight: 1.6,
      }}
    >
      <div style={{ marginBottom: '6px', fontSize: '10px', color: '#ff5566aa', letterSpacing: '0.14em' }}>
        ERREUR RÉSEAU
      </div>
      ⚠ {message}
    </div>
  )
}

function EmptyState() {
  return (
    <div
      style={{
        textAlign: 'center',
        padding: '100px 0',
        fontFamily: 'var(--font-mono)',
        color: 'var(--text-muted)',
        fontSize: '12px',
        letterSpacing: '0.12em',
        border: '1px dashed var(--border)',
        borderRadius: '4px',
      }}
    >
      AUCUN MATCH DISPONIBLE POUR CETTE SÉLECTION
    </div>
  )
}
