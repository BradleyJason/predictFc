import { useState, useEffect } from 'react'
import { getMatches, generateSmartTicket } from '../services/api'
import { fmtDateShort } from '../utils'

const MODES = [
  { key: 'combined',       icon: '🎯', label: 'Combiné safe',    desc: 'Anti-corrélation · Proba ≥ 60%',  risk: 'safe'   },
  { key: 'single',         icon: '✅', label: 'Simple safe',     desc: 'Meilleur pari unique · Proba ≥ 60%', risk: 'safe' },
  { key: 'danger_single',  icon: '🔥', label: 'Danger simple',   desc: 'Haute valeur · Proba 35–57%',     risk: 'danger' },
  { key: 'danger_combined',icon: '💣', label: 'Danger combiné',  desc: 'Multi-match risqué · Proba 35–57%', risk: 'danger'},
]

const RISK_COLOR = { safe: 'var(--accent-green)', danger: '#ff6b35' }

export default function SmartTicket() {
  const [matches,   setMatches]   = useState([])
  const [grouped,   setGrouped]   = useState({})
  const [selected,  setSelected]  = useState(new Set())
  const [mode,      setMode]      = useState('combined')
  const [result,    setResult]    = useState(null)
  const [loading,   setLoading]   = useState(false)
  const [fetching,  setFetching]  = useState(true)
  const [compFilter,setCompFilter]= useState('ALL')
  const [comps,     setComps]     = useState([])

  useEffect(() => {
    const now  = new Date()
    const to   = new Date(now); to.setDate(now.getDate() + 7)
    getMatches({
      limit:     60,
      date_from: now.toISOString().split('T')[0],
      date_to:   to.toISOString().split('T')[0],
    }).then(r => {
      const list = (r.data?.matches || []).filter(m =>
        m.status === 'SCHEDULED' || m.status === 'TIMED'
      )
      setMatches(list)

      // Grouper par date
      const grp = {}
      list.forEach(m => {
        const d = m.match_date ? m.match_date.split('T')[0] : 'Inconnu'
        if (!grp[d]) grp[d] = []
        grp[d].push(m)
      })
      setGrouped(grp)

      // Compétitions présentes
      const seen = new Map()
      list.forEach(m => {
        if (m.competition && !seen.has(m.competition.id)) {
          seen.set(m.competition.id, m.competition)
        }
      })
      setComps([...seen.values()])
      setFetching(false)
    }).catch(() => setFetching(false))
  }, [])

  const toggle = (id) => {
    setSelected(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
    setResult(null)
  }

  const selectAll = () => {
    const visible = filteredMatches().map(m => m.id)
    setSelected(prev => {
      const next = new Set(prev)
      visible.forEach(id => next.add(id))
      return next
    })
  }

  const clearAll = () => { setSelected(new Set()); setResult(null) }

  const filteredMatches = () =>
    compFilter === 'ALL' ? matches
      : matches.filter(m => m.competition?.id === compFilter)

  const filteredGrouped = () => {
    const fm = filteredMatches()
    const grp = {}
    fm.forEach(m => {
      const d = m.match_date ? m.match_date.split('T')[0] : 'Inconnu'
      if (!grp[d]) grp[d] = []
      grp[d].push(m)
    })
    return grp
  }

  const generate = async () => {
    if (selected.size < 1) return
    setLoading(true); setResult(null)
    try {
      const r = await generateSmartTicket([...selected], mode)
      setResult(r.data)
    } catch {
      setResult({ error: 'Erreur lors de la génération.' })
    }
    setLoading(false)
  }

  const selMode  = MODES.find(m => m.key === mode)
  const selMatches = matches.filter(m => selected.has(m.id))
  const canGen   = selected.size >= (mode.includes('combined') ? 2 : 1)

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '32px 24px' }}>

      {/* Header */}
      <div style={{ marginBottom: '28px' }}>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', letterSpacing: '0.3em', color: 'var(--accent-green)', marginBottom: '8px' }}>◆ GÉNÉRATEUR</div>
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(36px, 6vw, 64px)', color: 'var(--text-primary)', margin: '0 0 6px', letterSpacing: '0.04em', lineHeight: 1 }}>
          SMART TICKET
        </h1>
        <p style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)', margin: 0 }}>
          Sélectionne des matchs · On génère le combiné optimal pour toi
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '20px', alignItems: 'start' }}>

        {/* ── Colonne gauche : matchs ── */}
        <div>
          {/* Filtres compétitions */}
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '14px' }}>
            <CompChip label="TOUS" active={compFilter === 'ALL'} onClick={() => setCompFilter('ALL')} />
            {comps.slice(0, 6).map(c => (
              <CompChip key={c.id} label={c.name} logo={c.crest_url} active={compFilter === c.id} onClick={() => setCompFilter(c.id)} />
            ))}
          </div>

          {/* Barre actions */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', color: 'var(--text-muted)', letterSpacing: '0.1em' }}>
              {filteredMatches().length} MATCHS DISPONIBLES
            </span>
            <div style={{ display: 'flex', gap: '8px' }}>
              <ActionBtn onClick={selectAll}>TOUT SÉLECT.</ActionBtn>
              {selected.size > 0 && <ActionBtn onClick={clearAll} danger>EFFACER ({selected.size})</ActionBtn>}
            </div>
          </div>

          {/* Liste matchs groupés par date */}
          {fetching ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
              {Array.from({ length: 8 }, (_, i) => (
                <div key={i} style={{ height: '44px', background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: '4px', animation: 'shimmer 1.4s infinite', opacity: 1 - i * 0.08 }} />
              ))}
            </div>
          ) : (
            Object.entries(filteredGrouped()).sort(([a], [b]) => a.localeCompare(b)).map(([date, dayMatches]) => (
              <div key={date} style={{ marginBottom: '14px' }}>
                {/* Séparateur date */}
                <div style={{
                  display: 'flex', alignItems: 'center', gap: '10px',
                  marginBottom: '6px',
                }}>
                  <div style={{ height: '1px', flex: 1, background: 'var(--border)' }} />
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', color: 'var(--text-muted)', letterSpacing: '0.1em', whiteSpace: 'nowrap' }}>
                    {formatDateLabel(date)}
                  </span>
                  <div style={{ height: '1px', flex: 1, background: 'var(--border)' }} />
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                  {dayMatches.map(m => {
                    const sel = selected.has(m.id)
                    const home = m.home_team?.short_name || m.home_team?.name || '—'
                    const away = m.away_team?.short_name || m.away_team?.name || '—'
                    return (
                      <div key={m.id} onClick={() => toggle(m.id)} style={{
                        display: 'grid', gridTemplateColumns: '28px 1fr auto 1fr auto',
                        alignItems: 'center', gap: '10px',
                        padding: '10px 14px',
                        background: sel ? 'rgba(0,255,136,0.06)' : 'var(--bg-surface)',
                        border: `1px solid ${sel ? 'rgba(0,255,136,0.35)' : 'var(--border)'}`,
                        borderRadius: '4px', cursor: 'pointer',
                        transition: 'all 0.15s ease',
                      }}
                      onMouseEnter={(e) => { if (!sel) e.currentTarget.style.background = 'var(--bg-elevated)' }}
                      onMouseLeave={(e) => { if (!sel) e.currentTarget.style.background = 'var(--bg-surface)' }}
                      >
                        {/* Checkbox */}
                        <div style={{
                          width: '18px', height: '18px', borderRadius: '4px', flexShrink: 0,
                          border: `2px solid ${sel ? 'var(--accent-green)' : 'var(--border)'}`,
                          background: sel ? 'var(--accent-green)' : 'transparent',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          transition: 'all 0.15s',
                        }}>
                          {sel && <span style={{ fontSize: '10px', color: '#06060e', fontWeight: 700 }}>✓</span>}
                        </div>

                        {/* Équipe domicile */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '7px', minWidth: 0, justifyContent: 'flex-end' }}>
                          <span style={{ fontFamily: 'var(--font-display)', fontSize: '13px', color: sel ? 'var(--text-primary)' : 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {home}
                          </span>
                          {m.home_team?.crest_url && <img src={m.home_team.crest_url} alt="" width={20} height={20} style={{ objectFit: 'contain', flexShrink: 0 }} onError={e => e.target.style.display = 'none'} />}
                        </div>

                        {/* VS + heure */}
                        <div style={{ textAlign: 'center', flexShrink: 0 }}>
                          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', color: 'var(--text-muted)', letterSpacing: '0.1em' }}>VS</div>
                          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '8px', color: 'var(--text-muted)' }}>
                            {m.match_date ? new Date(m.match_date).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) : '—'}
                          </div>
                        </div>

                        {/* Équipe extérieur */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '7px', minWidth: 0 }}>
                          {m.away_team?.crest_url && <img src={m.away_team.crest_url} alt="" width={20} height={20} style={{ objectFit: 'contain', flexShrink: 0 }} onError={e => e.target.style.display = 'none'} />}
                          <span style={{ fontFamily: 'var(--font-display)', fontSize: '13px', color: sel ? 'var(--text-primary)' : 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {away}
                          </span>
                        </div>

                        {/* Compétition */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', flexShrink: 0 }}>
                          {m.competition?.crest_url && <img src={m.competition.crest_url} alt="" width={12} height={12} style={{ objectFit: 'contain' }} onError={e => e.target.style.display = 'none'} />}
                          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '8px', color: 'var(--text-muted)', maxWidth: '70px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {m.competition?.name || ''}
                          </span>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            ))
          )}
        </div>

        {/* ── Colonne droite : panneau ticket ── */}
        <div style={{ position: 'sticky', top: '80px', display: 'flex', flexDirection: 'column', gap: '12px' }}>

          {/* Mode de ticket */}
          <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: '6px', padding: '16px' }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '8px', letterSpacing: '0.18em', color: 'var(--text-muted)', marginBottom: '10px' }}>TYPE DE TICKET</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {MODES.map(m => {
                const active = mode === m.key
                const color  = RISK_COLOR[m.risk]
                return (
                  <div key={m.key} onClick={() => setMode(m.key)} style={{
                    padding: '10px 12px', borderRadius: '4px', cursor: 'pointer',
                    background: active ? `${color}10` : 'transparent',
                    border: `1px solid ${active ? color + '50' : 'var(--border)'}`,
                    transition: 'all 0.15s',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
                        <span style={{ fontSize: '13px' }}>{m.icon}</span>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', fontWeight: 600, color: active ? color : 'var(--text-secondary)', letterSpacing: '0.06em' }}>
                          {m.label}
                        </span>
                      </div>
                      {active && <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: color, display: 'inline-block' }} />}
                    </div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '8px', color: 'var(--text-muted)', marginTop: '3px', paddingLeft: '20px' }}>
                      {m.desc}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Sélection en cours */}
          <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: '6px', padding: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '8px', letterSpacing: '0.18em', color: 'var(--text-muted)' }}>
                SÉLECTION
              </div>
              <span style={{
                fontFamily: 'var(--font-mono)', fontSize: '9px', fontWeight: 700,
                background: selected.size > 0 ? 'rgba(0,255,136,0.12)' : 'var(--bg-elevated)',
                color: selected.size > 0 ? 'var(--accent-green)' : 'var(--text-muted)',
                padding: '2px 8px', borderRadius: '10px',
                border: `1px solid ${selected.size > 0 ? 'rgba(0,255,136,0.3)' : 'var(--border)'}`,
              }}>
                {selected.size} match{selected.size > 1 ? 's' : ''}
              </span>
            </div>

            {selMatches.length === 0 ? (
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-muted)', textAlign: 'center', padding: '16px 0', lineHeight: 1.6 }}>
                Clique sur les matchs<br />pour les ajouter
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '5px', maxHeight: '200px', overflowY: 'auto' }}>
                {selMatches.map(m => (
                  <div key={m.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 8px', background: 'var(--bg-elevated)', borderRadius: '3px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', minWidth: 0 }}>
                      {m.home_team?.crest_url && <img src={m.home_team.crest_url} alt="" width={14} height={14} style={{ objectFit: 'contain', flexShrink: 0 }} onError={e => e.target.style.display = 'none'} />}
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {m.home_team?.short_name || '?'} vs {m.away_team?.short_name || '?'}
                      </span>
                    </div>
                    <button onClick={(e) => { e.stopPropagation(); toggle(m.id) }} style={{
                      background: 'transparent', border: 'none', color: 'var(--text-muted)',
                      cursor: 'pointer', fontSize: '12px', padding: '0 2px', flexShrink: 0,
                    }}>✕</button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Résultat */}
          {result && !result.error && (
            <div style={{ background: 'rgba(0,255,136,0.06)', border: '1px solid rgba(0,255,136,0.25)', borderRadius: '6px', padding: '16px' }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '8px', letterSpacing: '0.18em', color: 'var(--accent-green)', marginBottom: '12px' }}>
                ✓ TICKET GÉNÉRÉ
              </div>
              {(result.bets || result.selections || []).map((bet, i) => (
                <div key={i} style={{ marginBottom: '8px', padding: '8px', background: 'var(--bg-surface)', borderRadius: '4px', border: '1px solid var(--border)' }}>
                  <div style={{ fontFamily: 'var(--font-display)', fontSize: '11px', color: 'var(--text-primary)', marginBottom: '3px' }}>
                    {bet.match || bet.label || `Pari ${i + 1}`}
                  </div>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    {bet.prediction && <Tag color="var(--accent-green)">{bet.prediction}</Tag>}
                    {bet.probability && <Tag color="var(--accent-cyan)">{Math.round(bet.probability * 100)}%</Tag>}
                    {bet.odd && <Tag color="var(--accent-amber)">Cote {bet.odd}</Tag>}
                  </div>
                </div>
              ))}
              {result.total_odd && (
                <div style={{ marginTop: '10px', padding: '10px', background: 'rgba(0,255,136,0.08)', borderRadius: '4px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', color: 'var(--text-muted)', letterSpacing: '0.1em' }}>COTE TOTALE</span>
                  <span style={{ fontFamily: 'var(--font-display)', fontSize: '20px', color: 'var(--accent-green)' }}>{result.total_odd?.toFixed(2)}</span>
                </div>
              )}
            </div>
          )}

          {result?.error && (
            <div style={{ background: 'rgba(255,68,85,0.08)', border: '1px solid rgba(255,68,85,0.2)', borderRadius: '6px', padding: '12px 16px', fontFamily: 'var(--font-mono)', fontSize: '10px', color: '#ff5566' }}>
              {result.error}
            </div>
          )}

          {/* Bouton générer */}
          <button onClick={generate} disabled={!canGen || loading} style={{
            width: '100%', padding: '14px',
            background: canGen ? 'var(--accent-green)' : 'var(--bg-elevated)',
            border: `1px solid ${canGen ? 'var(--accent-green)' : 'var(--border)'}`,
            borderRadius: '6px',
            color: canGen ? '#06060e' : 'var(--text-muted)',
            fontFamily: 'var(--font-mono)', fontSize: '11px',
            fontWeight: 700, letterSpacing: '0.14em',
            cursor: canGen ? 'pointer' : 'not-allowed',
            transition: 'all 0.2s',
            boxShadow: canGen ? '0 0 20px rgba(0,255,136,0.2)' : 'none',
          }}>
            {loading ? '⏳ GÉNÉRATION...' : canGen ? `⚡ GÉNÉRER LE TICKET` : `SÉLECTIONNE ${mode.includes('combined') ? '2+' : '1+'} MATCH${mode.includes('combined') ? 'S' : ''}`}
          </button>

          {canGen && (
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '8px', color: 'var(--text-muted)', textAlign: 'center', letterSpacing: '0.06em', lineHeight: 1.5 }}>
              Mode : {selMode?.icon} {selMode?.label}
            </div>
          )}
        </div>
      </div>
    </div>
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
      {logo && <img src={logo} alt="" width={12} height={12} style={{ objectFit: 'contain' }} onError={e => e.target.style.display = 'none'} />}
      {label}
    </button>
  )
}

function ActionBtn({ children, onClick, danger }) {
  return (
    <button onClick={onClick} style={{
      padding: '4px 10px', background: 'transparent', cursor: 'pointer',
      border: `1px solid ${danger ? 'rgba(255,68,85,0.3)' : 'var(--border)'}`,
      borderRadius: '4px',
      color: danger ? '#ff5566' : 'var(--text-muted)',
      fontFamily: 'var(--font-mono)', fontSize: '9px', letterSpacing: '0.08em',
      transition: 'all 0.15s',
    }}>
      {children}
    </button>
  )
}

function Tag({ children, color }) {
  return (
    <span style={{
      fontFamily: 'var(--font-mono)', fontSize: '8px', fontWeight: 600,
      padding: '2px 6px', borderRadius: '3px',
      background: color + '18', color, border: `1px solid ${color}30`,
      letterSpacing: '0.06em',
    }}>
      {children}
    </span>
  )
}

function formatDateLabel(dateStr) {
  const today    = new Date(); today.setHours(0,0,0,0)
  const tomorrow = new Date(today); tomorrow.setDate(today.getDate() + 1)
  const d        = new Date(dateStr)
  if (d.toDateString() === today.toDateString())    return 'AUJOURD\'HUI'
  if (d.toDateString() === tomorrow.toDateString()) return 'DEMAIN'
  return d.toLocaleDateString('fr-FR', { weekday: 'short', day: 'numeric', month: 'short' }).toUpperCase()
}
