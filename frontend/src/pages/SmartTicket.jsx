import { useEffect, useState } from 'react'
import { generateSmartTicket, getMatches } from '../services/api'

const LEAGUE_NAMES = {
  FL1: 'Ligue 1', PL: 'Premier League', PD: 'La Liga',
  BL1: 'Bundesliga', SA: 'Serie A', CL: 'Champions League',
}

const MODES = [
  {
    key: 'combined',
    label: 'SMART TICKET',
    sublabel: 'Combiné safe',
    desc: 'Plusieurs paris indépendants · Anti-corrélation · Proba ≥ 60%',
    color: 'var(--accent-green)',
    bg: 'rgba(0,255,136,0.08)',
  },
  {
    key: 'simple',
    label: 'SIMPLE',
    sublabel: 'Pari unique safe',
    desc: 'Meilleur pari unique par match · Proba ≥ 60%',
    color: 'var(--accent-cyan)',
    bg: 'rgba(0,204,255,0.08)',
  },
  {
    key: 'hot',
    label: '🔥 DANGER ZONE',
    sublabel: 'Paris risqués',
    desc: 'Paris à haute valeur · Proba 35–59% · Cotes élevées',
    color: '#ff6b35',
    bg: 'rgba(255,107,53,0.08)',
  },
]

function fmtShortDate(str) {
  if (!str) return '—'
  const d = new Date(str)
  return d.toLocaleDateString('fr-FR', { weekday: 'short', day: '2-digit', month: 'short' })
}

function probaColor(value, isHot = false) {
  if (isHot) {
    if (value >= 0.52) return '#ffcc00'
    if (value >= 0.42) return '#ff6b35'
    return '#ff4455'
  }
  if (value >= 0.75) return '#00ff88'
  if (value >= 0.60) return '#00ccff'
  return '#ffcc00'
}

function getDateWindow() {
  const now = new Date()
  const to = new Date(now)
  to.setDate(now.getDate() + 7)
  return {
    date_from: now.toISOString().split('T')[0],
    date_to: to.toISOString().split('T')[0],
  }
}

export default function SmartTicket() {
  const [matches,      setMatches]      = useState([])
  const [matchLoad,    setMatchLoad]    = useState(true)
  const [selected,     setSelected]     = useState([])
  const [mode,         setMode]         = useState('combined')
  const [ticket,       setTicket]       = useState(null)
  const [ticketLoad,   setTicketLoad]   = useState(false)
  const [error,        setError]        = useState(null)
  const [leagueFilter, setLeagueFilter] = useState(null)

  useEffect(() => {
    const { date_from, date_to } = getDateWindow()
    getMatches({ limit: 200, date_from, date_to })
      .then((r) => {
        const upcoming = (r.data.matches || []).filter((m) => m.status !== 'FINISHED')
        setMatches(upcoming)
        setMatchLoad(false)
      })
      .catch(() => setMatchLoad(false))
  }, [])

  const toggleSelect = (id) => {
    setSelected((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id])
    setTicket(null)
  }

  const handleGenerate = () => {
    if (selected.length === 0) return
    setTicketLoad(true)
    setError(null)
    generateSmartTicket(selected, mode)
      .then((r) => { setTicket(r.data); setTicketLoad(false) })
      .catch((e) => {
        setError(e?.response?.data?.detail || 'Impossible de générer le ticket.')
        setTicketLoad(false)
      })
  }

  const LEAGUES = [...new Set(matches.map((m) => m.competition?.code).filter(Boolean))]
  const displayedMatches = leagueFilter
    ? matches.filter((m) => m.competition?.code === leagueFilter)
    : matches
  const isHot = mode === 'hot'

  return (
    <div style={{ maxWidth: '1060px', margin: '0 auto', padding: '36px 24px' }}>
      <div style={{ marginBottom: '36px' }}>
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(36px, 6vw, 56px)', letterSpacing: '0.04em', color: 'var(--text-primary)', lineHeight: 1, margin: 0, marginBottom: '8px' }}>
          SMART TICKET
        </h1>
        <div style={{ width: '44px', height: '2px', background: 'var(--accent-green)', boxShadow: '0 0 10px var(--accent-green)', marginBottom: '12px' }} />
        <p style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)', letterSpacing: '0.1em' }}>
          SÉLECTIONNEZ DES MATCHS · GÉNÉREZ LE COMBINÉ OPTIMAL
        </p>
      </div>

      <div className="ticket-layout">
        {/* ── Gauche : liste ── */}
        <div>
          {/* Filtre compétition */}
          {LEAGUES.length > 1 && (
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '20px' }}>
              <button onClick={() => setLeagueFilter(null)} className={`league-tab ${leagueFilter === null ? 'active' : ''}`} style={{ fontSize: '10px', padding: '4px 12px' }}>TOUT</button>
              {LEAGUES.map((code) => (
                <button key={code} onClick={() => setLeagueFilter(code)} className={`league-tab ${leagueFilter === code ? 'active' : ''}`} style={{ fontSize: '10px', padding: '4px 12px' }}>
                  {LEAGUE_NAMES[code] || code}
                </button>
              ))}
            </div>
          )}

          {/* Header liste */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <span style={{ color: 'var(--accent-green)', fontSize: '7px' }}>◆</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', fontWeight: 600, letterSpacing: '0.16em', color: 'var(--text-muted)' }}>
              MATCHS DISPONIBLES
            </span>
            {selected.length > 0 && (
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', fontWeight: 700, background: 'var(--accent-green)', color: '#06060e', borderRadius: '10px', padding: '1px 9px' }}>
                {selected.length} SÉLECTIONNÉ{selected.length > 1 ? 'S' : ''}
              </span>
            )}
          </div>

          {matchLoad ? (
            <div style={{ textAlign: 'center', padding: '48px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', fontSize: '12px' }}>
              <span style={{ animation: 'pulseGlow 1.4s infinite', color: 'var(--accent-green)' }}>■ ■ ■</span>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
              {displayedMatches.map((match) => (
                <SelectableMatch
                  key={match.id}
                  match={match}
                  selected={selected.includes(match.id)}
                  onToggle={() => toggleSelect(match.id)}
                />
              ))}
              {displayedMatches.length === 0 && (
                <div style={{ textAlign: 'center', padding: '40px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', fontSize: '12px', border: '1px dashed var(--border)', borderRadius: '4px' }}>
                  AUCUN MATCH DISPONIBLE CETTE SEMAINE
                </div>
              )}
            </div>
          )}
        </div>

        {/* ── Droite : panneau ── */}
        <div className="ticket-sticky" style={{ position: 'sticky', top: '76px' }}>
          <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: '4px', padding: '16px', marginBottom: '12px' }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', letterSpacing: '0.18em', color: 'var(--text-muted)', marginBottom: '10px' }}>
              TYPE DE TICKET
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {MODES.map((m) => (
                <button key={m.key} onClick={() => { setMode(m.key); setTicket(null) }}
                  style={{ padding: '10px 12px', textAlign: 'left', background: mode === m.key ? m.bg : 'transparent', border: `1px solid ${mode === m.key ? m.color : 'var(--border)'}`, borderRadius: '3px', cursor: 'pointer', transition: 'all 0.15s ease' }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '3px' }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', fontWeight: 700, letterSpacing: '0.1em', color: mode === m.key ? m.color : 'var(--text-secondary)' }}>{m.label}</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '8px', color: mode === m.key ? m.color : 'var(--text-muted)', letterSpacing: '0.06em' }}>{m.sublabel}</span>
                  </div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '8px', color: 'var(--text-muted)', letterSpacing: '0.04em', lineHeight: 1.5 }}>{m.desc}</div>
                </button>
              ))}
            </div>
          </div>

          <button onClick={handleGenerate} disabled={selected.length === 0 || ticketLoad}
            className={`generate-btn ${selected.length > 0 && !ticketLoad ? 'ready' : ''}`}
            style={isHot && selected.length > 0 ? { borderColor: '#ff6b35', color: '#ff6b35' } : {}}
          >
            {ticketLoad
              ? <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}><span style={{ color: 'var(--accent-green)', animation: 'pulseGlow 1s infinite' }}>■</span> CALCUL EN COURS...</span>
              : selected.length === 0 ? 'SÉLECTIONNER DES MATCHS'
              : `GÉNÉRER LE TICKET (${selected.length})`}
          </button>

          {error && (
            <div style={{ marginTop: '10px', padding: '10px 14px', border: '1px solid rgba(255,68,85,0.3)', background: 'rgba(255,68,85,0.05)', borderRadius: '3px', fontFamily: 'var(--font-mono)', fontSize: '11px', color: '#ff5566' }}>
              ⚠ {error}
            </div>
          )}

          {ticket && <TicketResult ticket={ticket} allMatches={matches} />}
        </div>
      </div>
    </div>
  )
}

/* ── Match row ── */
function SelectableMatch({ match, selected, onToggle }) {
  const home = match.home_team?.short_name || match.home_team?.name || '—'
  const away = match.away_team?.short_name || match.away_team?.name || '—'
  const compName = LEAGUE_NAMES[match.competition?.code] || match.competition?.code || '—'

  return (
    <div onClick={onToggle} className={`selectable-match ${selected ? 'selected' : ''}`}
      style={{ padding: '12px 14px', display: 'grid', gridTemplateColumns: 'auto 1fr auto', alignItems: 'center', gap: '14px', cursor: 'pointer' }}
    >
      {/* Checkbox */}
      <div style={{ width: '16px', height: '16px', border: `1.5px solid ${selected ? 'var(--accent-green)' : 'var(--border-bright)'}`, borderRadius: '2px', background: selected ? 'var(--accent-green)' : 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, transition: 'all 0.15s ease' }}>
        {selected && <span style={{ color: '#06060e', fontSize: '10px', fontWeight: 900 }}>✓</span>}
      </div>

      {/* Centre : compétition + équipes */}
      <div>
        {/* Ligne compétition */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', marginBottom: '5px' }}>
          {match.competition?.crest_url && (
            <img src={match.competition.crest_url} alt="" width={12} height={12}
              style={{ objectFit: 'contain', opacity: 0.7 }}
              onError={(e) => { e.target.style.display = 'none' }}
            />
          )}
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', color: 'var(--text-muted)', letterSpacing: '0.08em' }}>
            {compName}
          </span>
        </div>
        {/* Ligne équipes */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {match.home_team?.crest_url && (
            <img src={match.home_team.crest_url} alt="" width={18} height={18}
              style={{ objectFit: 'contain' }}
              onError={(e) => { e.target.style.display = 'none' }}
            />
          )}
          <span style={{ fontFamily: 'var(--font-display)', fontSize: '16px', color: 'var(--text-primary)', letterSpacing: '0.03em' }}>
            {home}
          </span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-muted)' }}>VS</span>
          <span style={{ fontFamily: 'var(--font-display)', fontSize: '16px', color: 'var(--text-primary)', letterSpacing: '0.03em' }}>
            {away}
          </span>
          {match.away_team?.crest_url && (
            <img src={match.away_team.crest_url} alt="" width={18} height={18}
              style={{ objectFit: 'contain' }}
              onError={(e) => { e.target.style.display = 'none' }}
            />
          )}
        </div>
      </div>

      {/* Date */}
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-muted)', textAlign: 'right', letterSpacing: '0.04em' }}>
        {fmtShortDate(match.match_date)}
      </span>
    </div>
  )
}

/* ── Ticket result ── */
function TicketResult({ ticket, allMatches }) {
  const isSimple = ticket.mode === 'simple'
  const isHot = ticket.mode === 'hot'
  const accentColor = isHot ? '#ff6b35' : 'var(--accent-green)'

  const byMatch = ticket.selections?.reduce((acc, sel) => {
    if (!acc[sel.match_id]) acc[sel.match_id] = []
    acc[sel.match_id].push(sel)
    return acc
  }, {})

  return (
    <div className="animate-fade-up" style={{ marginTop: '14px', background: 'var(--bg-surface)', border: `1px solid ${isHot ? 'rgba(255,107,53,0.3)' : 'var(--border)'}`, borderRadius: '4px', overflow: 'hidden' }}>
      <div style={{ padding: '10px 16px', borderBottom: '1px solid var(--border)', background: isHot ? 'rgba(255,107,53,0.06)' : 'var(--bg-elevated)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', letterSpacing: '0.18em', color: 'var(--text-muted)' }}>TICKET GÉNÉRÉ</span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', letterSpacing: '0.14em', color: accentColor, fontWeight: 700 }}>
          {isHot ? '🔥 DANGER ZONE' : isSimple ? 'SIMPLE' : 'SMART TICKET'}
        </span>
      </div>

      <div style={{ padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {Object.entries(byMatch || {}).map(([matchId, sels]) => {
          const match = allMatches.find((m) => m.id === parseInt(matchId))
          const home = match?.home_team?.short_name || match?.home_team?.name || '?'
          const away = match?.away_team?.short_name || match?.away_team?.name || '?'
          return (
            <div key={matchId} style={{ background: 'var(--bg-elevated)', borderRadius: '3px', overflow: 'hidden' }}>
              <div style={{ padding: '8px 12px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                {match?.home_team?.crest_url && <img src={match.home_team.crest_url} alt="" width={14} height={14} style={{ objectFit: 'contain' }} onError={(e) => { e.target.style.display = 'none' }} />}
                <span style={{ fontFamily: 'var(--font-display)', fontSize: '12px', color: 'var(--text-secondary)', letterSpacing: '0.03em' }}>{home}</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', color: 'var(--text-muted)' }}>—</span>
                <span style={{ fontFamily: 'var(--font-display)', fontSize: '12px', color: 'var(--text-secondary)', letterSpacing: '0.03em' }}>{away}</span>
                {match?.away_team?.crest_url && <img src={match.away_team.crest_url} alt="" width={14} height={14} style={{ objectFit: 'contain' }} onError={(e) => { e.target.style.display = 'none' }} />}
              </div>
              {sels.map((sel, i) => {
                const pct = Math.round(sel.probability * 100)
                const color = probaColor(sel.probability, isHot)
                return (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', borderLeft: `3px solid ${color}`, borderBottom: i < sels.length - 1 ? '1px solid var(--border)' : 'none' }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '0.07em' }}>{sel.label}</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '16px', fontWeight: 700, color, textShadow: `0 0 8px ${color}55` }}>{pct}%</span>
                  </div>
                )
              })}
            </div>
          )
        })}
      </div>

      {ticket.correlated_warning && (
        <div style={{ margin: '0 16px 12px', padding: '8px 12px', background: 'rgba(255,204,0,0.07)', border: '1px solid rgba(255,204,0,0.25)', borderRadius: '3px', fontFamily: 'var(--font-mono)', fontSize: '9px', color: 'var(--accent-amber)', lineHeight: 1.6 }}>
          ⚠ {ticket.correlated_warning}
        </div>
      )}

      <div style={{ padding: '14px 16px', borderTop: '1px solid var(--border)', display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {!isSimple && (
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', letterSpacing: '0.14em', color: 'var(--text-muted)' }}>
              {isHot ? 'PROBABILITÉ GLOBALE' : 'PROBABILITÉ COMBINÉE'}
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '24px', fontWeight: 700, color: accentColor, textShadow: `0 0 12px ${accentColor}66` }}>
              {Math.round((ticket.combined_proba ?? 0) * 100)}%
            </span>
          </div>
        )}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', letterSpacing: '0.14em', color: 'var(--text-muted)' }}>INDICE DE CONFIANCE</span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '18px', fontWeight: 600, color: 'var(--accent-cyan)' }}>{ticket.confidence_score}/100</span>
        </div>
        {isHot && (
          <div style={{ padding: '8px 10px', background: 'rgba(255,107,53,0.08)', border: '1px solid rgba(255,107,53,0.2)', borderRadius: '3px', fontFamily: 'var(--font-mono)', fontSize: '9px', color: '#ff6b35', lineHeight: 1.6 }}>
            🔥 PARIS À HAUTE VALEUR — Risque élevé · Potentiel de gain fort · Jouez responsablement
          </div>
        )}
      </div>

      {ticket.disclaimer && (
        <div style={{ padding: '10px 16px', borderTop: '1px solid var(--border)', fontFamily: 'var(--font-mono)', fontSize: '9px', color: 'var(--text-muted)', lineHeight: 1.7 }}>
          ⚠ {ticket.disclaimer}
        </div>
      )}
    </div>
  )
}
