import { useEffect, useState } from 'react'
import { generateSmartTicket, getMatches } from '../services/api'

function fmtShortDate(str) {
  if (!str) return '—'
  return new Date(str).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' })
}

function probaColor(value) {
  if (value >= 0.65) return '#00ff88'
  if (value >= 0.45) return '#00ccff'
  if (value >= 0.30) return '#ffcc00'
  return '#ff5566'
}

/* ═══════════════════════════════════════════
   Page component
═══════════════════════════════════════════ */
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
    getMatches({ limit: 40, status: 'SCHEDULED' })
      .then((r) => { setMatches(r.data.matches || []); setMatchLoad(false) })
      .catch(() => setMatchLoad(false))
  }, [])

  const toggleSelect = (id) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    )
    setTicket(null) // reset ticket on selection change
  }

  const handleGenerate = () => {
    if (selected.length === 0) return
    setTicketLoad(true)
    setError(null)
    generateSmartTicket(selected, mode)
      .then((r) => { setTicket(r.data); setTicketLoad(false) })
      .catch(() => { setError('Impossible de générer le ticket.'); setTicketLoad(false) })
  }

  const LEAGUES = [...new Set(matches.map((m) => m.competition?.code).filter(Boolean))]

  const displayedMatches = leagueFilter
    ? matches.filter((m) => m.competition?.code === leagueFilter)
    : matches

  return (
    <div style={{ maxWidth: '1060px', margin: '0 auto', padding: '36px 24px' }}>
      {/* Heading */}
      <div style={{ marginBottom: '36px' }}>
        <h1
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: 'clamp(36px, 6vw, 56px)',
            letterSpacing: '0.04em',
            color: 'var(--text-primary)',
            lineHeight: 1,
            margin: 0,
            marginBottom: '8px',
          }}
        >
          SMART TICKET
        </h1>
        <div
          style={{
            width: '44px',
            height: '2px',
            background: 'var(--accent-green)',
            boxShadow: '0 0 10px var(--accent-green)',
            marginBottom: '12px',
          }}
        />
        <p
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '11px',
            color: 'var(--text-muted)',
            letterSpacing: '0.1em',
          }}
        >
          SÉLECTIONNEZ DES MATCHS · GÉNÉREZ LE COMBINÉ OPTIMAL
        </p>
      </div>

      {/* 2-col layout */}
      <div className="ticket-layout">
        {/* ── Left: match list ── */}
        <div>
          {/* League filter pills */}
          {LEAGUES.length > 1 && (
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '16px' }}>
              <button
                onClick={() => setLeagueFilter(null)}
                className={`league-tab ${leagueFilter === null ? 'active' : ''}`}
                style={{ fontSize: '10px', padding: '4px 12px' }}
              >
                TOUT
              </button>
              {LEAGUES.map((code) => (
                <button
                  key={code}
                  onClick={() => setLeagueFilter(code)}
                  className={`league-tab ${leagueFilter === code ? 'active' : ''}`}
                  style={{ fontSize: '10px', padding: '4px 12px' }}
                >
                  {code}
                </button>
              ))}
            </div>
          )}

          {/* Section header */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '12px',
            }}
          >
            <span style={{ color: 'var(--accent-green)', fontSize: '7px' }}>◆</span>
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '10px',
                fontWeight: 600,
                letterSpacing: '0.16em',
                color: 'var(--text-muted)',
              }}
            >
              MATCHS DISPONIBLES
            </span>
            {selected.length > 0 && (
              <span
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '10px',
                  fontWeight: 700,
                  background: 'var(--accent-green)',
                  color: '#06060e',
                  borderRadius: '10px',
                  padding: '1px 9px',
                  marginLeft: '4px',
                }}
              >
                {selected.length} SÉLECTIONNÉ{selected.length > 1 ? 'S' : ''}
              </span>
            )}
          </div>

          {/* List */}
          {matchLoad ? (
            <div
              style={{
                textAlign: 'center',
                padding: '48px',
                fontFamily: 'var(--font-mono)',
                color: 'var(--text-muted)',
                fontSize: '12px',
                letterSpacing: '0.1em',
              }}
            >
              <span style={{ animation: 'pulseGlow 1.4s infinite', color: 'var(--accent-green)' }}>
                ■ ■ ■
              </span>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '7px' }}>
              {displayedMatches.map((match) => (
                <SelectableMatch
                  key={match.id}
                  match={match}
                  selected={selected.includes(match.id)}
                  onToggle={() => toggleSelect(match.id)}
                />
              ))}
              {displayedMatches.length === 0 && (
                <div
                  style={{
                    textAlign: 'center',
                    padding: '40px',
                    fontFamily: 'var(--font-mono)',
                    color: 'var(--text-muted)',
                    fontSize: '12px',
                    border: '1px dashed var(--border)',
                    borderRadius: '4px',
                    letterSpacing: '0.1em',
                  }}
                >
                  AUCUN MATCH PROGRAMMÉ
                </div>
              )}
            </div>
          )}
        </div>

        {/* ── Right: ticket panel ── */}
        <div className="ticket-sticky" style={{ position: 'sticky', top: '76px' }}>
          {/* Mode selector */}
          <div
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border)',
              borderRadius: '4px',
              padding: '16px',
              marginBottom: '12px',
            }}
          >
            <div
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '9px',
                letterSpacing: '0.18em',
                color: 'var(--text-muted)',
                marginBottom: '10px',
              }}
            >
              MODE DU TICKET
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              {['combined', 'simple'].map((m) => (
                <button
                  key={m}
                  onClick={() => { setMode(m); setTicket(null) }}
                  style={{
                    flex: 1,
                    padding: '8px',
                    background: mode === m ? 'var(--accent-green)' : 'transparent',
                    border: `1px solid ${mode === m ? 'var(--accent-green)' : 'var(--border)'}`,
                    borderRadius: '3px',
                    color: mode === m ? '#06060e' : 'var(--text-secondary)',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '10px',
                    fontWeight: 700,
                    letterSpacing: '0.1em',
                    cursor: 'pointer',
                    textTransform: 'uppercase',
                    transition: 'all 0.15s ease',
                  }}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>

          {/* Generate button */}
          <button
            onClick={handleGenerate}
            disabled={selected.length === 0 || ticketLoad}
            className={`generate-btn ${selected.length > 0 && !ticketLoad ? 'ready' : ''}`}
          >
            {ticketLoad ? (
              <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                <span style={{ color: 'var(--accent-green)', animation: 'pulseGlow 1s infinite' }}>■</span>
                CALCUL EN COURS...
              </span>
            ) : selected.length === 0 ? (
              'SÉLECTIONNER DES MATCHS'
            ) : (
              `GÉNÉRER LE TICKET (${selected.length})`
            )}
          </button>

          {/* Error */}
          {error && (
            <div
              style={{
                marginTop: '10px',
                padding: '10px 14px',
                border: '1px solid rgba(255,68,85,0.3)',
                background: 'rgba(255,68,85,0.05)',
                borderRadius: '3px',
                fontFamily: 'var(--font-mono)',
                fontSize: '11px',
                color: '#ff5566',
                letterSpacing: '0.05em',
              }}
            >
              ⚠ {error}
            </div>
          )}

          {/* Ticket result */}
          {ticket && <TicketResult ticket={ticket} allMatches={matches} />}
        </div>
      </div>
    </div>
  )
}

/* ═══════════════════════════════════════════
   Sub-components
═══════════════════════════════════════════ */

function SelectableMatch({ match, selected, onToggle }) {
  const home = match.home_team?.short_name || match.home_team?.name || '—'
  const away = match.away_team?.short_name || match.away_team?.name || '—'

  return (
    <div
      onClick={onToggle}
      className={`selectable-match ${selected ? 'selected' : ''}`}
    >
      {/* Checkbox */}
      <div
        style={{
          width: '16px',
          height: '16px',
          border: `1.5px solid ${selected ? 'var(--accent-green)' : 'var(--border-bright)'}`,
          borderRadius: '2px',
          background: selected ? 'var(--accent-green)' : 'transparent',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          transition: 'all 0.15s ease',
        }}
      >
        {selected && (
          <span style={{ color: '#06060e', fontSize: '10px', fontWeight: 900, lineHeight: 1 }}>✓</span>
        )}
      </div>

      {/* Competition badge */}
      <span
        style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '9px',
          fontWeight: 700,
          background: 'var(--bg-elevated)',
          color: 'var(--accent-cyan)',
          padding: '2px 7px',
          borderRadius: '2px',
          letterSpacing: '0.08em',
          flexShrink: 0,
        }}
      >
        {match.competition?.code}
      </span>

      {/* Teams */}
      <span
        style={{
          fontFamily: 'var(--font-display)',
          fontSize: '17px',
          color: 'var(--text-primary)',
          flex: 1,
          letterSpacing: '0.03em',
          lineHeight: 1,
        }}
      >
        {home} — {away}
      </span>

      {/* Date */}
      <span
        style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '10px',
          color: 'var(--text-muted)',
          flexShrink: 0,
          letterSpacing: '0.04em',
        }}
      >
        {fmtShortDate(match.match_date)}
      </span>
    </div>
  )
}

function TicketResult({ ticket, allMatches }) {
  return (
    <div
      className="animate-fade-up"
      style={{
        marginTop: '14px',
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        borderRadius: '4px',
        overflow: 'hidden',
      }}
    >
      {/* Ticket header bar */}
      <div
        style={{
          padding: '10px 16px',
          borderBottom: '1px solid var(--border)',
          background: 'var(--bg-elevated)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '9px',
            letterSpacing: '0.18em',
            color: 'var(--text-muted)',
          }}
        >
          TICKET GÉNÉRÉ
        </span>
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '9px',
            letterSpacing: '0.14em',
            color: 'var(--accent-green)',
          }}
        >
          {ticket.mode?.toUpperCase()}
        </span>
      </div>

      {/* Selections */}
      <div style={{ padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {ticket.selections?.map((sel, i) => {
          const match = allMatches.find((m) => m.id === sel.match_id)
          const pct = Math.round(sel.probability * 100)
          const color = probaColor(sel.probability)
          return (
            <div
              key={i}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '9px 12px',
                background: 'var(--bg-elevated)',
                borderRadius: '3px',
                borderLeft: `3px solid ${color}`,
              }}
            >
              <div style={{ flex: 1, minWidth: 0 }}>
                {match && (
                  <div
                    style={{
                      fontFamily: 'var(--font-display)',
                      fontSize: '14px',
                      color: 'var(--text-primary)',
                      letterSpacing: '0.03em',
                      marginBottom: '3px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {match.home_team?.short_name || match.home_team?.name} — {match.away_team?.short_name || match.away_team?.name}
                  </div>
                )}
                <div
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '9px',
                    color: 'var(--text-muted)',
                    letterSpacing: '0.07em',
                  }}
                >
                  {sel.label}
                </div>
              </div>
              <span
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '17px',
                  fontWeight: 700,
                  color,
                  textShadow: `0 0 8px ${color}55`,
                  flexShrink: 0,
                }}
              >
                {pct}%
              </span>
            </div>
          )
        })}
      </div>

      {/* Correlated warning */}
      {ticket.correlated_warning && (
        <div
          style={{
            margin: '0 16px 12px',
            padding: '8px 12px',
            background: 'rgba(255,204,0,0.07)',
            border: '1px solid rgba(255,204,0,0.25)',
            borderRadius: '3px',
            fontFamily: 'var(--font-mono)',
            fontSize: '9px',
            color: 'var(--accent-amber)',
            letterSpacing: '0.06em',
            lineHeight: 1.6,
          }}
        >
          ⚠ {ticket.correlated_warning}
        </div>
      )}

      {/* Combined proba + confidence */}
      <div
        style={{
          padding: '14px 16px',
          borderTop: '1px solid var(--border)',
          display: 'flex',
          flexDirection: 'column',
          gap: '10px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '9px',
              letterSpacing: '0.14em',
              color: 'var(--text-muted)',
            }}
          >
            PROBABILITÉ COMBINÉE
          </span>
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '24px',
              fontWeight: 700,
              color: 'var(--accent-green)',
              textShadow: '0 0 12px rgba(0,255,136,0.45)',
            }}
          >
            {Math.round((ticket.combined_proba ?? 0) * 100)}%
          </span>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '9px',
              letterSpacing: '0.14em',
              color: 'var(--text-muted)',
            }}
          >
            INDICE DE CONFIANCE
          </span>
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '18px',
              fontWeight: 600,
              color: 'var(--accent-cyan)',
            }}
          >
            {ticket.confidence_score}/100
          </span>
        </div>
      </div>

      {/* Disclaimer */}
      {ticket.disclaimer && (
        <div
          style={{
            padding: '10px 16px',
            borderTop: '1px solid var(--border)',
            fontFamily: 'var(--font-mono)',
            fontSize: '9px',
            color: 'var(--text-muted)',
            lineHeight: 1.7,
            letterSpacing: '0.03em',
          }}
        >
          ⚠ {ticket.disclaimer}
        </div>
      )}
    </div>
  )
}
