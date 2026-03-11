import { useEffect, useState } from 'react'
import { generateSmartTicket, getMatches } from '../services/api'

const LEAGUE_NAMES = {
  FL1: 'Ligue 1', PL: 'Premier League', PD: 'La Liga',
  BL1: 'Bundesliga', SA: 'Serie A', CL: 'Champions League',
}

/* ─── Modes disponibles ─── */
const MODES = [
  {
    key: 'combined',
    label: 'SMART TICKET',
    sublabel: 'Combiné safe',
    desc: 'Plusieurs paris · Anti-corrélation · Proba ≥ 60%',
    color: 'var(--accent-green)',
    bg: 'rgba(0,255,136,0.08)',
    minMatches: 2,
    maxMatches: null,
    hint: 'Sélectionnez au moins 2 matchs',
  },
  {
    key: 'simple',
    label: 'SIMPLE',
    sublabel: 'Pari unique safe',
    desc: 'Meilleur pari unique par match · Proba ≥ 60%',
    color: 'var(--accent-cyan)',
    bg: 'rgba(0,204,255,0.08)',
    minMatches: 1,
    maxMatches: 1,
    hint: 'Sélectionnez exactement 1 match',
  },
  {
    key: 'hot_simple',
    label: '🔥 DANGER SIMPLE',
    sublabel: 'Pari risqué unique',
    desc: 'Paris à haute valeur · Proba 35–59% · 1 match',
    color: '#ff6b35',
    bg: 'rgba(255,107,53,0.08)',
    minMatches: 1,
    maxMatches: 1,
    hint: 'Sélectionnez exactement 1 match',
  },
  {
    key: 'hot_combined',
    label: '🔥 DANGER COMBINÉ',
    sublabel: 'Paris risqués combinés',
    desc: 'Paris à haute valeur · Proba 35–59% · Multi-matchs',
    color: '#ff4422',
    bg: 'rgba(255,68,34,0.08)',
    minMatches: 2,
    maxMatches: null,
    hint: 'Sélectionnez au moins 2 matchs',
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
  const to  = new Date(now)
  to.setDate(now.getDate() + 7)
  return {
    date_from: now.toISOString().split('T')[0],
    date_to:   to.toISOString().split('T')[0],
  }
}

/* ══════════════════════════════════════════
   PAGE PRINCIPALE
══════════════════════════════════════════ */
export default function SmartTicket() {
  const [matches,      setMatches]      = useState([])
  const [matchLoad,    setMatchLoad]    = useState(true)
  const [selected,     setSelected]     = useState([])
  const [mode,         setMode]         = useState('combined')
  const [ticket,       setTicket]       = useState(null)
  const [ticketLoad,   setTicketLoad]   = useState(false)
  const [error,        setError]        = useState(null)
  const [leagueFilter, setLeagueFilter] = useState(null)
  const [showModal,    setShowModal]    = useState(false)

  const currentMode = MODES.find(m => m.key === mode)

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

  // Quand on change de mode, on vide la sélection si elle dépasse le max
  const handleModeChange = (newMode) => {
    const m = MODES.find(x => x.key === newMode)
    setMode(newMode)
    setTicket(null)
    setError(null)
    if (m.maxMatches && selected.length > m.maxMatches) {
      setSelected(selected.slice(0, m.maxMatches))
    }
  }

  const toggleSelect = (id) => {
    setSelected((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id)
      if (currentMode.maxMatches && prev.length >= currentMode.maxMatches) {
        // Mode 1 match max : on remplace la sélection
        return [id]
      }
      return [...prev, id]
    })
    setTicket(null)
    setError(null)
  }

  // Validation avant génération
  const canGenerate = () => {
    if (selected.length < currentMode.minMatches) return false
    if (currentMode.maxMatches && selected.length > currentMode.maxMatches) return false
    return true
  }

  const getButtonLabel = () => {
    if (ticketLoad) return null
    if (selected.length === 0) return currentMode.hint
    if (selected.length < currentMode.minMatches)
      return `${currentMode.hint} (${selected.length}/${currentMode.minMatches} min)`
    if (currentMode.maxMatches && selected.length > currentMode.maxMatches)
      return `Maximum ${currentMode.maxMatches} match`
    return `GÉNÉRER LE TICKET (${selected.length} match${selected.length > 1 ? 's' : ''})`
  }

  const handleGenerate = () => {
    if (!canGenerate()) return
    setTicketLoad(true)
    setError(null)
    // On mappe les modes danger vers 'hot' pour l'API
    const apiMode = mode.startsWith('hot') ? 'hot' : mode
    generateSmartTicket(selected, apiMode)
      .then((r) => {
        setTicket(r.data)
        setTicketLoad(false)
        setShowModal(true)
      })
      .catch((e) => {
        setError(e?.response?.data?.detail || 'Impossible de générer le ticket.')
        setTicketLoad(false)
      })
  }

  const LEAGUES = [...new Set(matches.map((m) => m.competition?.code).filter(Boolean))]
  const displayedMatches = leagueFilter
    ? matches.filter((m) => m.competition?.code === leagueFilter)
    : matches
  const isHot = mode.startsWith('hot')
  const accentColor = isHot
    ? (mode === 'hot_combined' ? '#ff4422' : '#ff6b35')
    : currentMode.color

  return (
    <div className="page-container" style={{
      maxWidth: '1060px', margin: '0 auto',
      padding: '36px 24px', boxSizing: 'border-box', width: '100%',
    }}>

      {/* ── Titre ── */}
      <div style={{ marginBottom: '36px' }}>
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(36px, 6vw, 56px)', letterSpacing: '0.04em', color: 'var(--text-primary)', lineHeight: 1, margin: 0, marginBottom: '8px' }}>
          SMART TICKET
        </h1>
        <div style={{ width: '44px', height: '2px', background: 'var(--accent-green)', boxShadow: '0 0 10px var(--accent-green)', marginBottom: '12px' }} />
        <p style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)', letterSpacing: '0.1em' }}>
          SÉLECTIONNEZ DES MATCHS · GÉNÉREZ LE COMBINÉ OPTIMAL
        </p>
      </div>

      {/* ── Layout : liste + panneau ── */}
      <div className="ticket-layout">

        {/* ── Gauche : liste matchs ── */}
        <div style={{ minWidth: 0 }}>

          {/* Filtres ligues */}
          {LEAGUES.length > 1 && (
            <div className="league-filters" style={{ display: 'flex', gap: '6px', marginBottom: '20px' }}>
              <button onClick={() => setLeagueFilter(null)} className={`league-tab ${leagueFilter === null ? 'active' : ''}`}>TOUT</button>
              {LEAGUES.map((code) => (
                <button key={code} onClick={() => setLeagueFilter(code)} className={`league-tab ${leagueFilter === code ? 'active' : ''}`}>
                  {LEAGUE_NAMES[code] || code}
                </button>
              ))}
            </div>
          )}

          {/* Header section */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px', flexWrap: 'wrap' }}>
            <span style={{ color: 'var(--accent-green)', fontSize: '7px' }}>◆</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', fontWeight: 600, letterSpacing: '0.16em', color: 'var(--text-muted)' }}>
              MATCHS DISPONIBLES
            </span>
            {selected.length > 0 && (
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', fontWeight: 700, background: accentColor, color: '#06060e', borderRadius: '10px', padding: '1px 9px' }}>
                {selected.length} SÉLECTIONNÉ{selected.length > 1 ? 'S' : ''}
              </span>
            )}
          </div>

          {/* Hint mode */}
          <div style={{ marginBottom: '12px', padding: '8px 12px', background: `${accentColor}10`, border: `1px solid ${accentColor}30`, borderRadius: '3px', fontFamily: 'var(--font-mono)', fontSize: '9px', color: accentColor, letterSpacing: '0.06em' }}>
            {currentMode.hint}
            {currentMode.maxMatches === 1 && selected.length === 1 && ' · ✓ 1 match sélectionné'}
            {!currentMode.maxMatches && selected.length >= currentMode.minMatches && ` · ✓ ${selected.length} matchs sélectionnés`}
          </div>

          {/* Liste matchs */}
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
                  accentColor={accentColor}
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

        {/* ── Droite : panneau config ── */}
        <div className="ticket-sticky" style={{ position: 'sticky', top: '76px', minWidth: 0 }}>

          {/* Choix mode */}
          <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: '4px', padding: '16px', marginBottom: '12px' }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', letterSpacing: '0.18em', color: 'var(--text-muted)', marginBottom: '10px' }}>
              TYPE DE TICKET
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {MODES.map((m) => (
                <button
                  key={m.key}
                  onClick={() => handleModeChange(m.key)}
                  style={{
                    width: '100%', padding: '10px 12px', textAlign: 'left',
                    background: mode === m.key ? m.bg : 'transparent',
                    border: `1px solid ${mode === m.key ? m.color : 'var(--border)'}`,
                    borderRadius: '3px', cursor: 'pointer', transition: 'all 0.15s ease',
                    boxSizing: 'border-box',
                  }}
                >
                  {/* Ligne titre */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '3px', gap: '8px' }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', fontWeight: 700, letterSpacing: '0.1em', color: mode === m.key ? m.color : 'var(--text-secondary)', flexShrink: 0 }}>
                      {m.label}
                    </span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '8px', color: mode === m.key ? m.color : 'var(--text-muted)', letterSpacing: '0.06em', textAlign: 'right' }}>
                      {m.sublabel}
                    </span>
                  </div>
                  {/* Description */}
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '8px', color: 'var(--text-muted)', letterSpacing: '0.03em', lineHeight: 1.5 }}>
                    {m.desc}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Bouton générer */}
          <button
            onClick={handleGenerate}
            disabled={!canGenerate() || ticketLoad}
            style={{
              width: '100%', padding: '14px', borderRadius: '4px',
              background: canGenerate() && !ticketLoad ? accentColor : 'var(--bg-elevated)',
              border: `2px solid ${canGenerate() && !ticketLoad ? accentColor : 'var(--border)'}`,
              color: canGenerate() && !ticketLoad ? '#06060e' : 'var(--text-muted)',
              fontFamily: 'var(--font-ui)', fontSize: '12px', fontWeight: 700,
              letterSpacing: '0.12em', textTransform: 'uppercase',
              cursor: canGenerate() && !ticketLoad ? 'pointer' : 'not-allowed',
              transition: 'all 0.2s ease', boxSizing: 'border-box',
              boxShadow: canGenerate() && !ticketLoad ? `0 0 20px ${accentColor}40` : 'none',
            }}
          >
            {ticketLoad
              ? <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                  <span style={{ color: accentColor, animation: 'pulseGlow 1s infinite' }}>■</span>
                  CALCUL EN COURS...
                </span>
              : getButtonLabel()
            }
          </button>

          {/* Bouton "Voir le dernier ticket" si ticket dispo */}
          {ticket && !showModal && (
            <button
              onClick={() => setShowModal(true)}
              style={{
                width: '100%', padding: '10px', marginTop: '8px', borderRadius: '4px',
                background: 'transparent',
                border: `1px solid ${accentColor}`,
                color: accentColor,
                fontFamily: 'var(--font-mono)', fontSize: '10px', fontWeight: 700,
                letterSpacing: '0.1em', textTransform: 'uppercase',
                cursor: 'pointer', transition: 'all 0.15s ease', boxSizing: 'border-box',
              }}
            >
              VOIR LE DERNIER TICKET →
            </button>
          )}

          {error && (
            <div style={{ marginTop: '10px', padding: '10px 14px', border: '1px solid rgba(255,68,85,0.3)', background: 'rgba(255,68,85,0.05)', borderRadius: '3px', fontFamily: 'var(--font-mono)', fontSize: '11px', color: '#ff5566' }}>
              ⚠ {error}
            </div>
          )}
        </div>
      </div>

      {/* ── Modal résultat ticket ── */}
      {showModal && ticket && (
        <TicketModal
          ticket={ticket}
          allMatches={matches}
          isHot={isHot}
          accentColor={accentColor}
          onClose={() => setShowModal(false)}
          onRegenerate={() => { setShowModal(false); handleGenerate() }}
        />
      )}
    </div>
  )
}

/* ══════════════════════════════════════════
   SELECTABLE MATCH ROW
══════════════════════════════════════════ */
function SelectableMatch({ match, selected, onToggle, accentColor }) {
  const home     = match.home_team?.short_name || match.home_team?.name || '—'
  const away     = match.away_team?.short_name || match.away_team?.name || '—'
  const compName = LEAGUE_NAMES[match.competition?.code] || match.competition?.code || '—'

  return (
    <div
      onClick={onToggle}
      className={`selectable-match ${selected ? 'selected' : ''}`}
      style={{
        padding: '10px 14px', cursor: 'pointer',
        borderColor: selected ? `${accentColor}55` : undefined,
        background: selected ? `${accentColor}08` : undefined,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>

        {/* Checkbox */}
        <div style={{
          width: '16px', height: '16px', flexShrink: 0,
          border: `1.5px solid ${selected ? accentColor : 'var(--border-bright)'}`,
          borderRadius: '2px',
          background: selected ? accentColor : 'transparent',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          transition: 'all 0.15s ease',
        }}>
          {selected && <span style={{ color: '#06060e', fontSize: '10px', fontWeight: 900, lineHeight: 1 }}>✓</span>}
        </div>

        {/* Contenu central */}
        <div style={{ flex: 1, minWidth: 0 }}>
          {/* Compétition */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px', marginBottom: '5px' }}>
            {match.competition?.crest_url && (
              <img src={match.competition.crest_url} alt="" width={11} height={11}
                style={{ objectFit: 'contain', opacity: 0.7, flexShrink: 0 }}
                onError={(e) => { e.target.style.display = 'none' }}
              />
            )}
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', color: 'var(--text-muted)', letterSpacing: '0.06em' }}>
              {compName}
            </span>
          </div>
          {/* Équipes */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
            <TeamRow team={match.home_team} name={home} size={15} color="var(--text-primary)" />
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '8px', color: 'var(--text-muted)', flexShrink: 0 }}>vs</span>
              <TeamRow team={match.away_team} name={away} size={15} color="var(--text-secondary)" />
            </div>
          </div>
        </div>

        {/* Date */}
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', color: 'var(--text-muted)', flexShrink: 0, whiteSpace: 'nowrap' }}>
          {fmtShortDate(match.match_date)}
        </span>
      </div>
    </div>
  )
}

function TeamRow({ team, name, size, color }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', overflow: 'hidden' }}>
      {team?.crest_url && (
        <img src={team.crest_url} alt="" width={size} height={size}
          style={{ objectFit: 'contain', flexShrink: 0 }}
          onError={(e) => { e.target.style.display = 'none' }}
        />
      )}
      <span style={{ fontFamily: 'var(--font-display)', fontSize: '14px', color, letterSpacing: '0.03em', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {name}
      </span>
    </div>
  )
}

/* ══════════════════════════════════════════
   MODAL RÉSULTAT TICKET
══════════════════════════════════════════ */
function TicketModal({ ticket, allMatches, isHot, accentColor, onClose, onRegenerate }) {
  const isSimple = ticket.mode === 'simple'

  const byMatch = ticket.selections?.reduce((acc, sel) => {
    if (!acc[sel.match_id]) acc[sel.match_id] = []
    acc[sel.match_id].push(sel)
    return acc
  }, {})

  return (
    /* Overlay */
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, zIndex: 2000,
        background: 'rgba(6,6,14,0.88)',
        backdropFilter: 'blur(6px)',
        display: 'flex', alignItems: 'flex-end', justifyContent: 'center',
        animation: 'fadeIn 0.2s ease-out',
      }}
    >
      {/* Panel — stoppe la propagation du clic */}
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: '100%', maxWidth: '560px',
          maxHeight: '90vh', overflowY: 'auto',
          background: 'var(--bg-surface)',
          border: `1px solid ${accentColor}44`,
          borderBottom: 'none',
          borderRadius: '12px 12px 0 0',
          animation: 'fadeInUp 0.3s ease-out',
          boxShadow: `0 -8px 40px ${accentColor}20`,
        }}
      >
        {/* Handle de drag */}
        <div style={{ display: 'flex', justifyContent: 'center', padding: '12px 0 4px' }}>
          <div style={{ width: '40px', height: '4px', borderRadius: '2px', background: 'var(--border-bright)' }} />
        </div>

        {/* Header modal */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 20px 16px' }}>
          <div>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: '22px', color: accentColor, letterSpacing: '0.05em' }}>
              {isHot ? '🔥 DANGER ZONE' : isSimple ? 'SIMPLE' : 'SMART TICKET'}
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', color: 'var(--text-muted)', letterSpacing: '0.1em', marginTop: '2px' }}>
              TICKET GÉNÉRÉ
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              width: '32px', height: '32px', borderRadius: '50%',
              background: 'var(--bg-elevated)', border: '1px solid var(--border)',
              color: 'var(--text-secondary)', fontSize: '16px', cursor: 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >✕</button>
        </div>

        {/* Contenu ticket */}
        <div style={{ padding: '0 20px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {Object.entries(byMatch || {}).map(([matchId, sels]) => {
            const match = allMatches.find((m) => m.id === parseInt(matchId))
            const home  = match?.home_team?.short_name || match?.home_team?.name || '?'
            const away  = match?.away_team?.short_name || match?.away_team?.name || '?'
            return (
              <div key={matchId} style={{ background: 'var(--bg-elevated)', borderRadius: '6px', overflow: 'hidden', border: '1px solid var(--border)' }}>
                {/* Header match */}
                <div style={{ padding: '10px 14px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                  {match?.home_team?.crest_url && <img src={match.home_team.crest_url} alt="" width={16} height={16} style={{ objectFit: 'contain' }} onError={(e) => { e.target.style.display = 'none' }} />}
                  <span style={{ fontFamily: 'var(--font-display)', fontSize: '13px', color: 'var(--text-primary)', letterSpacing: '0.03em' }}>{home}</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', color: 'var(--text-muted)' }}>vs</span>
                  <span style={{ fontFamily: 'var(--font-display)', fontSize: '13px', color: 'var(--text-secondary)', letterSpacing: '0.03em' }}>{away}</span>
                  {match?.away_team?.crest_url && <img src={match.away_team.crest_url} alt="" width={16} height={16} style={{ objectFit: 'contain' }} onError={(e) => { e.target.style.display = 'none' }} />}
                </div>
                {/* Paris */}
                {sels.map((sel, i) => {
                  const pct   = Math.round(sel.probability * 100)
                  const color = probaColor(sel.probability, isHot)
                  return (
                    <div key={i} style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                      padding: '12px 14px', gap: '12px',
                      borderLeft: `3px solid ${color}`,
                      borderBottom: i < sels.length - 1 ? '1px solid var(--border)' : 'none',
                    }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)', letterSpacing: '0.06em', flex: 1 }}>
                        {sel.label}
                      </span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '20px', fontWeight: 700, color, textShadow: `0 0 10px ${color}55`, flexShrink: 0 }}>
                        {pct}%
                      </span>
                    </div>
                  )
                })}
              </div>
            )
          })}
        </div>

        {/* Warning corrélation */}
        {ticket.correlated_warning && (
          <div style={{ margin: '12px 20px 0', padding: '10px 14px', background: 'rgba(255,204,0,0.07)', border: '1px solid rgba(255,204,0,0.25)', borderRadius: '6px', fontFamily: 'var(--font-mono)', fontSize: '9px', color: 'var(--accent-amber)', lineHeight: 1.6 }}>
            ⚠ {ticket.correlated_warning}
          </div>
        )}

        {/* Stats ticket */}
        <div style={{ margin: '16px 20px', padding: '16px', background: 'var(--bg-elevated)', borderRadius: '8px', border: `1px solid ${accentColor}22`, display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {!isSimple && (
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '0.1em' }}>
                {isHot ? 'PROBABILITÉ GLOBALE' : 'PROBABILITÉ COMBINÉE'}
              </span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '28px', fontWeight: 700, color: accentColor, textShadow: `0 0 14px ${accentColor}66` }}>
                {Math.round((ticket.combined_proba ?? 0) * 100)}%
              </span>
            </div>
          )}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '0.1em' }}>INDICE DE CONFIANCE</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '22px', fontWeight: 600, color: 'var(--accent-cyan)' }}>
              {ticket.confidence_score}/100
            </span>
          </div>
        </div>

        {/* Avertissement danger zone */}
        {isHot && (
          <div style={{ margin: '0 20px', padding: '12px 14px', background: 'rgba(255,107,53,0.08)', border: '1px solid rgba(255,107,53,0.2)', borderRadius: '6px', fontFamily: 'var(--font-mono)', fontSize: '9px', color: '#ff6b35', lineHeight: 1.7 }}>
            🔥 PARIS À HAUTE VALEUR — Risque élevé · Potentiel de gain fort · Jouez responsablement
          </div>
        )}

        {/* Disclaimer */}
        {ticket.disclaimer && (
          <div style={{ margin: '12px 20px 0', padding: '10px 14px', fontFamily: 'var(--font-mono)', fontSize: '9px', color: 'var(--text-muted)', lineHeight: 1.7, borderTop: '1px solid var(--border)' }}>
            ⚠ {ticket.disclaimer}
          </div>
        )}

        {/* Actions */}
        <div style={{ padding: '16px 20px 28px', display: 'flex', gap: '10px' }}>
          <button
            onClick={onRegenerate}
            style={{
              flex: 1, padding: '12px',
              background: `${accentColor}15`,
              border: `1px solid ${accentColor}`,
              borderRadius: '6px',
              color: accentColor,
              fontFamily: 'var(--font-mono)', fontSize: '10px', fontWeight: 700,
              letterSpacing: '0.1em', cursor: 'pointer', transition: 'all 0.15s ease',
            }}
          >
            ↻ RÉGÉNÉRER
          </button>
          <button
            onClick={onClose}
            style={{
              flex: 1, padding: '12px',
              background: 'transparent',
              border: '1px solid var(--border)',
              borderRadius: '6px',
              color: 'var(--text-secondary)',
              fontFamily: 'var(--font-mono)', fontSize: '10px', fontWeight: 700,
              letterSpacing: '0.1em', cursor: 'pointer', transition: 'all 0.15s ease',
            }}
          >
            FERMER
          </button>
        </div>
      </div>
    </div>
  )
}
