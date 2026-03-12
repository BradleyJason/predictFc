import { useState, useEffect, useCallback } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { getMatches, getCompetitions } from '../services/api'
import { fmtDateShort, STATUS_META } from '../utils'

const TABS = [
  { key: 'upcoming', label: 'À VENIR'   },
  { key: 'today',    label: "AUJOURD'HUI" },
  { key: 'finished', label: 'TERMINÉS'  },
]

const STATUS_BY_TAB = {
  upcoming: ['SCHEDULED', 'TIMED'],
  today:    ['SCHEDULED', 'TIMED', 'IN_PLAY', 'PAUSED', 'HALFTIME'],
  finished: ['FINISHED'],
}

export default function Matches() {
  const [searchParams, setSearchParams] = useSearchParams()
  const tabParam  = searchParams.get('tab')  || 'upcoming'
  const compParam = searchParams.get('competition') || ''

  const [tab,          setTab]          = useState(tabParam)
  const [competitions, setCompetitions] = useState([])
  const [selComp,      setSelComp]      = useState(compParam)
  const [matches,      setMatches]      = useState([])
  const [loading,      setLoading]      = useState(true)
  const [page,         setPage]         = useState(1)
  const [total,        setTotal]        = useState(0)
  const LIMIT = 20

  // Charger compétitions
  useEffect(() => {
    getCompetitions().then(r => setCompetitions(r.data || [])).catch(() => {})
  }, [])

  // Charger matchs
  const fetchMatches = useCallback(() => {
    setLoading(true)
    const now   = new Date()
    const today = now.toISOString().split('T')[0]

    const params = {
      limit:  LIMIT,
      offset: (page - 1) * LIMIT,
    }

    if (tab === 'today') {
      params.date_from = today
      params.date_to   = today
    } else if (tab === 'upcoming') {
      params.date_from = today
      const future = new Date(now); future.setDate(now.getDate() + 14)
      params.date_to = future.toISOString().split('T')[0]
    } else if (tab === 'finished') {
      const past = new Date(now); past.setDate(now.getDate() - 30)
      params.date_from = past.toISOString().split('T')[0]
      params.date_to   = today
    }

    if (selComp) params.competition = selComp

    getMatches(params)
      .then(r => {
        const data = r.data
        setMatches(data.matches || [])
        setTotal(data.total   || 0)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [tab, selComp, page])

  useEffect(() => { fetchMatches() }, [fetchMatches])

  const changeTab = (t) => {
    setTab(t); setPage(1)
    const p = new URLSearchParams(searchParams)
    p.set('tab', t)
    setSearchParams(p)
  }

  const changeComp = (code) => {
    setSelComp(code); setPage(1)
    const p = new URLSearchParams(searchParams)
    if (code) p.set('competition', code); else p.delete('competition')
    setSearchParams(p)
  }

  const totalPages = Math.ceil(total / LIMIT)

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '32px 24px' }}>

      {/* Header */}
      <div style={{ marginBottom: '28px' }}>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', letterSpacing: '0.3em', color: 'var(--accent-green)', marginBottom: '8px' }}>
          ◆ CALENDRIER
        </div>
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(36px, 6vw, 64px)', color: 'var(--text-primary)', margin: 0, letterSpacing: '0.04em', lineHeight: 1 }}>
          MATCHS
        </h1>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '4px', marginBottom: '20px', borderBottom: '1px solid var(--border)', paddingBottom: '0' }}>
        {TABS.map(({ key, label }) => (
          <button key={key} onClick={() => changeTab(key)} style={{
            padding: '8px 18px', background: 'transparent', border: 'none',
            borderBottom: tab === key ? '2px solid var(--accent-green)' : '2px solid transparent',
            color: tab === key ? 'var(--accent-green)' : 'var(--text-muted)',
            fontFamily: 'var(--font-mono)', fontSize: '10px', fontWeight: 600,
            letterSpacing: '0.12em', cursor: 'pointer', marginBottom: '-1px',
            transition: 'all 0.15s',
          }}>
            {label}
          </button>
        ))}
      </div>

      {/* Filtre compétitions */}
      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '20px' }}>
        <CompChip label="TOUTES" active={!selComp} onClick={() => changeComp('')} />
        {competitions.filter(c => c.type === 'LEAGUE').slice(0, 8).map(c => (
          <CompChip
            key={c.id}
            label={c.code || c.name}
            logo={c.crest_url}
            active={selComp === c.code || selComp === String(c.id)}
            onClick={() => changeComp(c.code || String(c.id))}
          />
        ))}
      </div>

      {/* Résultats */}
      {loading ? (
        <LoadingGrid />
      ) : matches.length === 0 ? (
        <EmptyState tab={tab} />
      ) : (
        <>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', color: 'var(--text-muted)', letterSpacing: '0.1em', marginBottom: '12px' }}>
            {total} MATCH{total > 1 ? 'S' : ''} · PAGE {page}/{totalPages || 1}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {matches.map(m => <MatchRow key={m.id} match={m} />)}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div style={{ display: 'flex', justifyContent: 'center', gap: '6px', marginTop: '24px' }}>
              <PageBtn disabled={page <= 1}            onClick={() => setPage(p => p - 1)}>← PRÉC</PageBtn>
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                const n = Math.max(1, Math.min(page - 2, totalPages - 4)) + i
                return (
                  <PageBtn key={n} active={n === page} onClick={() => setPage(n)}>{n}</PageBtn>
                )
              })}
              <PageBtn disabled={page >= totalPages}   onClick={() => setPage(p => p + 1)}>SUIV →</PageBtn>
            </div>
          )}
        </>
      )}
    </div>
  )
}

function MatchRow({ match: m }) {
  const meta   = STATUS_META[m.status] || STATUS_META.DEFAULT
  const isLive = m.status === 'IN_PLAY' || m.status === 'PAUSED' || m.status === 'HALFTIME'
  const isDone = m.status === 'FINISHED'
  const home   = m.home_team?.short_name || m.home_team?.name || '—'
  const away   = m.away_team?.short_name || m.away_team?.name || '—'

  return (
    <Link to={`/match/${m.id}`} style={{
      display: 'grid',
      gridTemplateColumns: '140px 1fr auto 1fr 90px',
      alignItems: 'center', gap: '12px',
      padding: '12px 16px',
      background: 'var(--bg-surface)',
      border: `1px solid ${isLive ? 'rgba(0,255,136,0.2)' : 'var(--border)'}`,
      borderRadius: '4px', textDecoration: 'none',
      transition: 'all 0.15s ease',
    }}
    onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'rgba(0,255,136,0.35)'; e.currentTarget.style.transform = 'translateX(2px)' }}
    onMouseLeave={(e) => { e.currentTarget.style.borderColor = isLive ? 'rgba(0,255,136,0.2)' : 'var(--border)'; e.currentTarget.style.transform = 'none' }}
    >
      {/* Compétition + date */}
      <div style={{ minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', marginBottom: '3px' }}>
          {m.competition?.crest_url && (
            <img src={m.competition.crest_url} alt="" width={12} height={12}
              style={{ objectFit: 'contain', flexShrink: 0 }}
              onError={(e) => e.target.style.display = 'none'} />
          )}
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '8px', color: 'var(--text-muted)', letterSpacing: '0.06em', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {m.competition?.name || '—'}
          </span>
        </div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', color: 'var(--text-muted)' }}>
          {fmtDateShort(m.match_date)}
        </div>
      </div>

      {/* Équipe domicile */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', justifyContent: 'flex-end', minWidth: 0 }}>
        <span style={{ fontFamily: 'var(--font-display)', fontSize: '14px', color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {home}
        </span>
        {m.home_team?.crest_url && (
          <img src={m.home_team.crest_url} alt="" width={22} height={22}
            style={{ objectFit: 'contain', flexShrink: 0 }}
            onError={(e) => e.target.style.display = 'none'} />
        )}
      </div>

      {/* Score ou VS */}
      <div style={{ textAlign: 'center', flexShrink: 0, minWidth: '60px' }}>
        {isDone || isLive ? (
          <div style={{
            fontFamily: 'var(--font-mono)', fontSize: '16px', fontWeight: 700,
            color: isLive ? 'var(--accent-green)' : 'var(--text-primary)',
            letterSpacing: '0.05em',
          }}>
            {m.home_score ?? 0}
            <span style={{ color: 'var(--text-muted)', margin: '0 3px' }}>—</span>
            {m.away_score ?? 0}
          </div>
        ) : (
          <div style={{
            fontFamily: 'var(--font-mono)', fontSize: '9px', color: 'var(--text-muted)',
            letterSpacing: '0.15em', border: '1px solid var(--border)',
            borderRadius: '3px', padding: '3px 8px', display: 'inline-block',
          }}>VS</div>
        )}
        {isLive && (
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '7px', color: 'var(--accent-green)', letterSpacing: '0.1em', marginTop: '2px', animation: 'pulseGlow 1.4s infinite' }}>
            ● LIVE
          </div>
        )}
      </div>

      {/* Équipe extérieur */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0 }}>
        {m.away_team?.crest_url && (
          <img src={m.away_team.crest_url} alt="" width={22} height={22}
            style={{ objectFit: 'contain', flexShrink: 0 }}
            onError={(e) => e.target.style.display = 'none'} />
        )}
        <span style={{ fontFamily: 'var(--font-display)', fontSize: '14px', color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {away}
        </span>
      </div>

      {/* Badge statut */}
      <div style={{ textAlign: 'right' }}>
        <span style={{
          fontFamily: 'var(--font-mono)', fontSize: '8px', fontWeight: 600,
          letterSpacing: '0.08em', padding: '3px 8px', borderRadius: '3px',
          background: `${meta.color}18`, color: meta.color,
          border: `1px solid ${meta.color}30`,
        }}>
          {meta.label}
        </span>
      </div>
    </Link>
  )
}

function CompChip({ label, logo, active, onClick }) {
  return (
    <button onClick={onClick} style={{
      display: 'flex', alignItems: 'center', gap: '5px',
      padding: '4px 10px', borderRadius: '20px', cursor: 'pointer',
      background: active ? 'rgba(0,255,136,0.12)' : 'var(--bg-surface)',
      border: active ? '1px solid rgba(0,255,136,0.4)' : '1px solid var(--border)',
      color: active ? 'var(--accent-green)' : 'var(--text-muted)',
      fontFamily: 'var(--font-mono)', fontSize: '9px',
      fontWeight: active ? 700 : 400, letterSpacing: '0.08em',
      transition: 'all 0.15s', whiteSpace: 'nowrap',
    }}>
      {logo && <img src={logo} alt="" width={12} height={12} style={{ objectFit: 'contain' }} onError={(e) => e.target.style.display = 'none'} />}
      {label}
    </button>
  )
}

function PageBtn({ children, active, disabled, onClick }) {
  return (
    <button onClick={onClick} disabled={disabled} style={{
      padding: '6px 12px', background: active ? 'rgba(0,255,136,0.12)' : 'transparent',
      border: active ? '1px solid rgba(0,255,136,0.4)' : '1px solid var(--border)',
      borderRadius: '4px', color: active ? 'var(--accent-green)' : 'var(--text-muted)',
      fontFamily: 'var(--font-mono)', fontSize: '9px', letterSpacing: '0.1em',
      cursor: disabled ? 'not-allowed' : 'pointer', opacity: disabled ? 0.4 : 1,
      transition: 'all 0.15s',
    }}>
      {children}
    </button>
  )
}

function LoadingGrid() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
      {Array.from({ length: 8 }, (_, i) => (
        <div key={i} style={{
          height: '58px', background: 'var(--bg-surface)',
          border: '1px solid var(--border)', borderRadius: '4px',
          animation: 'shimmer 1.4s infinite',
          opacity: 1 - i * 0.08,
        }} />
      ))}
    </div>
  )
}

function EmptyState({ tab }) {
  const msgs = {
    upcoming: 'Aucun match à venir dans les 14 prochains jours.',
    today:    "Aucun match aujourd'hui.",
    finished: 'Aucun match terminé dans les 30 derniers jours.',
  }
  return (
    <div style={{ textAlign: 'center', padding: '64px 24px' }}>
      <div style={{ fontFamily: 'var(--font-display)', fontSize: '48px', color: 'var(--border)', marginBottom: '12px' }}>◈</div>
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)', letterSpacing: '0.1em' }}>
        {msgs[tab] || 'Aucun résultat.'}
      </div>
    </div>
  )
}
