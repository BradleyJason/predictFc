import React, { useState, useEffect } from 'react'
import { getMatches, generateSmartTicket, getPrediction } from '../services/api'
import { fmtDateShort } from '../utils'

const MODES = [
  { key: 'combined',       icon: '🎰', label: 'Combiné safe',    desc: 'Anti-corrélation · Proba ≥ 60%',  risk: 'safe'   },
  { key: 'single',         icon: '🎯', label: 'Simple safe',     desc: 'Meilleur pari unique · Proba ≥ 60%', risk: 'safe' },
  { key: 'danger_single',  icon: '⚡', label: 'Danger simple',   desc: 'Haute valeur · Proba 35–57%',     risk: 'danger' },
  { key: 'danger_combined',icon: '🔴', label: 'Danger combiné',  desc: 'Multi-match risqué · Proba 35–57%', risk: 'danger'},
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
  const [showModal,  setShowModal]  = useState(false)
  const [ticketCache, setTicketCache] = useState({})
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

  const MODE_MAP = {
    combined:        'combined',
    single:          'simple',
    danger_single:   'hot',
    danger_combined: 'hot',
  }

  const getCacheKey = (ids, m) => [...ids].map(Number).sort((a,b) => a-b).join(',') + '_' + m

  const generate = async () => {
    if (selected.size < 1) return
    const cacheKey = getCacheKey(selected, mode)
    // Réouverture si déjà généré
    if (ticketCache[cacheKey]) {
      setResult(ticketCache[cacheKey])
      setShowModal(true)
      return
    }
    setLoading(true); setResult(null)
    try {
      const backendMode = MODE_MAP[mode] || 'combined'
      const r = await generateSmartTicket([...selected], backendMode)
      if (r.data && !r.data.error) {
        setTicketCache(prev => ({ ...prev, [cacheKey]: r.data }))
        setResult(r.data)
        setShowModal(true)
      } else {
        setResult(r.data)
      }
    } catch (err) {
      const detail = err?.response?.data?.detail
      setResult({ error: detail || 'Erreur lors de la génération.' })
    }
    setLoading(false)
  }

  const selMode  = MODES.find(m => m.key === mode)
  const selMatches = matches.filter(m => selected.has(m.id))
  const canGen   = selected.size >= (mode.includes('combined') ? 2 : 1)

  return (
    <>
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
                const active    = mode === m.key
                const color     = RISK_COLOR[m.risk]
                const isSimple  = m.key === 'single' || m.key === 'danger_single'
                const isCombined = m.key === 'combined' || m.key === 'danger_combined'
                const disabled  = (isSimple && selected.size >= 2) || (isCombined && selected.size < 2)
                return (
                  <div key={m.key} onClick={() => !disabled && setMode(m.key)} style={{
                    padding: '10px 12px', borderRadius: '4px',
                    cursor: disabled ? 'not-allowed' : 'pointer',
                    background: active ? `${color}10` : 'transparent',
                    border: `1px solid ${active ? color + '50' : 'var(--border)'}`,
                    opacity: disabled ? 0.35 : 1,
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

          {/* Résultat — bouton reconsulter */}
          {result && !result.error && (
            <button onClick={() => setShowModal(true)} style={{
              width: '100%', padding: '10px',
              background: 'rgba(0,255,136,0.06)',
              border: '1px solid rgba(0,255,136,0.25)',
              borderRadius: '6px', cursor: 'pointer',
              fontFamily: 'var(--font-mono)', fontSize: '10px',
              color: 'var(--accent-green)', letterSpacing: '0.1em',
            }}>
              ✓ TICKET GÉNÉRÉ — Voir le détail
            </button>
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
            {loading ? 'GÉNÉRATION...' : canGen ? `⚡ GÉNÉRER LE TICKET` : `SÉLECTIONNE ${mode.includes('combined') ? '2+' : '1+'} MATCH${mode.includes('combined') ? 'S' : ''}`}
          </button>

          {canGen && (
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '8px', color: 'var(--text-muted)', textAlign: 'center', letterSpacing: '0.06em', lineHeight: 1.5 }}>
              Mode : {selMode?.icon} {selMode?.label}
            </div>
          )}
        </div>
      </div>
    </div>

    {showModal && result && !result.error && (
      <TicketModal
        result={result}
        matches={matches}
        mode={mode}
        onClose={() => setShowModal(false)}
        onRegenerate={null}
      />
    )}
    </>
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

const MODES_META = {
  combined:        { icon: '🎰', label: 'Combiné safe',   color: 'var(--accent-green)' },
  single:          { icon: '🎯', label: 'Simple safe',    color: 'var(--accent-green)' },
  danger_single:   { icon: '⚡', label: 'Danger simple',  color: '#ff6b35' },
  danger_combined: { icon: '🔴', label: 'Danger combiné', color: '#ff6b35' },
}

const SEUILS     = { combined: 0.60, single: 0.60, danger_single: 0.35, danger_combined: 0.35 }
const SEUILS_MAX = { combined: 1.0,  single: 1.0,  danger_single: 0.60, danger_combined: 0.60 }

function TicketModal({ result, matches, mode, onClose }) {
  const meta   = MODES_META[mode] || MODES_META.combined
  const seuil     = SEUILS[mode]     || 0.60
  const seuilMax  = SEUILS_MAX[mode] || 1.0
  const [preds, setPreds] = React.useState({})

  React.useEffect(() => {
    const ids = [...new Set((result.selections || []).map(s => s.match_id))]
    ids.forEach(id => {
      getPrediction(id).then(r => {
        setPreds(prev => ({ ...prev, [id]: r.data }))
      }).catch(() => {})
    })
  }, [])

  const byMatch = {}
  ;(result.selections || []).forEach(s => {
    if (!byMatch[s.match_id]) byMatch[s.match_id] = []
    byMatch[s.match_id].push(s)
  })

  const getMatch = (id) => matches.find(m => m.id === id)

  return (
    <div onClick={onClose} style={{
      position: 'fixed', inset: 0, zIndex: 1000,
      background: 'rgba(6,6,14,0.88)', backdropFilter: 'blur(8px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: '20px',
    }}>
      <div onClick={e => e.stopPropagation()} style={{
        background: 'var(--bg-surface)', border: '1px solid var(--border)',
        borderRadius: '10px', width: '100%', maxWidth: '620px',
        maxHeight: '88vh', overflowY: 'auto',
        boxShadow: `0 0 60px ${meta.color}22`,
      }}>

        {/* Header sticky */}
        <div style={{
          padding: '18px 24px 14px', borderBottom: '1px solid var(--border)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          position: 'sticky', top: 0, background: 'var(--bg-surface)', zIndex: 2,
        }}>
          <div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '8px', letterSpacing: '0.2em', color: 'var(--text-muted)', marginBottom: '4px' }}>TICKET GÉNÉRÉ</div>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: '18px', color: meta.color, letterSpacing: '0.06em' }}>{meta.icon} {meta.label}</span>
          </div>
          <button onClick={onClose} style={{
            background: 'transparent', border: '1px solid var(--border)',
            borderRadius: '4px', color: 'var(--text-muted)',
            cursor: 'pointer', padding: '4px 10px', fontSize: '14px',
          }}>✕</button>
        </div>

        {/* Métriques globales */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', padding: '14px 24px', borderBottom: '1px solid var(--border)' }}>
          {result.combined_proba != null && (
            <div style={{ background: 'var(--bg-elevated)', borderRadius: '6px', padding: '12px', textAlign: 'center' }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '8px', color: 'var(--text-muted)', letterSpacing: '0.1em', marginBottom: '6px' }}>PROBABILITÉ GLOBALE</div>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: '26px', color: meta.color, lineHeight: 1 }}>
                {Math.round(result.combined_proba * 100)}%
              </div>
            </div>
          )}
          {result.confidence_score != null && (
            <div style={{ background: 'var(--bg-elevated)', borderRadius: '6px', padding: '12px', textAlign: 'center' }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '8px', color: 'var(--text-muted)', letterSpacing: '0.1em', marginBottom: '6px' }}>INDICE DE CONFIANCE</div>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: '26px', lineHeight: 1,
                color: result.confidence_score >= 60 ? 'var(--accent-green)' : result.confidence_score >= 40 ? 'var(--accent-amber)' : '#ff6b35'
              }}>
                {result.confidence_score}<span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>/100</span>
              </div>
            </div>
          )}
        </div>

        {/* Un bloc par match */}
        <div style={{ padding: '16px 24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {Object.entries(byMatch).map(([matchId, sels]) => {
            const mid  = Number(matchId)
            const m    = getMatch(mid)
            const pred = preds[mid]
            const home = m?.home_team?.name || '?'
            const away = m?.away_team?.name || '?'
            const time = m?.match_date ? new Date(m.match_date).toLocaleDateString('fr-FR', {
              weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'
            }) : ''

            // Toutes les probas au-dessus du seuil depuis la prédiction complète
            const allMarkets = pred ? [
              { label: 'Victoire domicile',     proba: pred.home_win_proba },
              { label: 'Match nul',             proba: pred.draw_proba },
              { label: 'Victoire extérieur',    proba: pred.away_win_proba },
              { label: 'Chance double 1X',      proba: pred.home_draw_proba },
              { label: 'Chance double X2',      proba: pred.away_draw_proba },
              { label: 'Chance double 12',      proba: pred.home_away_proba },
              { label: 'Les deux marquent',     proba: pred.btts_proba },
              { label: 'Les deux ne marquent pas', proba: pred.btts_proba != null ? 1 - pred.btts_proba : null },
              { label: 'Plus de 0.5 buts',      proba: pred.over_05_proba },
              { label: 'Plus de 1.5 buts',      proba: pred.over_15_proba },
              { label: 'Plus de 2.5 buts',      proba: pred.over_25_proba },
              { label: 'Plus de 3.5 buts',      proba: pred.over_35_proba },
              { label: 'Moins de 2.5 buts',     proba: pred.over_25_proba != null ? 1 - pred.over_25_proba : null },
              { label: 'Moins de 3.5 buts',     proba: pred.over_35_proba != null ? 1 - pred.over_35_proba : null },
            ].filter(mk => mk.proba != null && mk.proba >= seuil && mk.proba <= seuilMax)
              .sort((a, b) => b.proba - a.proba) : []

            const topScore = pred?.top_scores?.[0]
            const altScores = pred?.top_scores?.slice(1, 4) || []

            return (
              <div key={matchId} style={{ background: 'var(--bg-elevated)', borderRadius: '8px', overflow: 'hidden' }}>

                {/* Header match */}
                <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'rgba(255,255,255,0.02)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {m?.home_team?.crest_url && <img src={m.home_team.crest_url} alt="" width={24} height={24} style={{ objectFit: 'contain' }} onError={e => e.target.style.display='none'} />}
                    <span style={{ fontFamily: 'var(--font-display)', fontSize: '14px', color: 'var(--text-primary)' }}>{home}</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', color: 'var(--text-muted)' }}>vs</span>
                    {m?.away_team?.crest_url && <img src={m.away_team.crest_url} alt="" width={24} height={24} style={{ objectFit: 'contain' }} onError={e => e.target.style.display='none'} />}
                    <span style={{ fontFamily: 'var(--font-display)', fontSize: '14px', color: 'var(--text-primary)' }}>{away}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    {m?.competition?.crest_url && <img src={m.competition.crest_url} alt="" width={14} height={14} style={{ objectFit: 'contain' }} onError={e => e.target.style.display='none'} />}
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '8px', color: 'var(--text-muted)' }}>{time}</span>
                  </div>
                </div>

                <div style={{ padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>

                  {/* Score prédit */}
                  {topScore && (
                    <div>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '8px', letterSpacing: '0.15em', color: 'var(--text-muted)', marginBottom: '8px' }}>SCORE PRÉDIT</div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{ fontFamily: 'var(--font-display)', fontSize: '28px', color: meta.color, letterSpacing: '0.04em' }}>
                            {topScore.home} — {topScore.away}
                          </span>
                          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-muted)', background: 'var(--bg-surface)', padding: '2px 8px', borderRadius: '4px' }}>
                            {Math.round(topScore.probability * 100)}%
                          </span>
                        </div>
                        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                          {altScores.map((s, i) => (
                            <span key={i} style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', color: 'var(--text-muted)', background: 'var(--bg-surface)', padding: '3px 8px', borderRadius: '4px', border: '1px solid var(--border)' }}>
                              {s.home}-{s.away} <span style={{ color: 'var(--text-secondary)' }}>{Math.round(s.probability * 100)}%</span>
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Marchés retenus */}
                  {allMarkets.length > 0 && (
                    <div>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '8px', letterSpacing: '0.15em', color: 'var(--text-muted)', marginBottom: '8px' }}>
                        MARCHÉS {seuilMax < 1 ? `${Math.round(seuil * 100)}% — ${Math.round(seuilMax * 100)}%` : `AU-DESSUS DE ${Math.round(seuil * 100)}%`}
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '7px' }}>
                        {allMarkets.map((mk, i) => {
                          const pct = Math.round(mk.proba * 100)
                          const barColor = pct >= 75 ? 'var(--accent-green)' : pct >= 60 ? 'var(--accent-cyan)' : 'var(--accent-amber)'
                          const isRetenu = sels.some(s => s.label === mk.label)
                          return (
                            <div key={i}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '3px' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                  {isRetenu && <span style={{ width: '5px', height: '5px', borderRadius: '50%', background: meta.color, display: 'inline-block', flexShrink: 0 }} />}
                                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: isRetenu ? 'var(--text-primary)' : 'var(--text-secondary)', fontWeight: isRetenu ? 600 : 400 }}>
                                    {mk.label}
                                  </span>
                                  {isRetenu && <span style={{ fontFamily: 'var(--font-mono)', fontSize: '7px', color: meta.color, letterSpacing: '0.1em' }}>RETENU</span>}
                                </div>
                                <span style={{ fontFamily: 'var(--font-display)', fontSize: '13px', color: barColor, fontWeight: 700 }}>{pct}%</span>
                              </div>
                              <div style={{ height: '2px', background: 'var(--border)', borderRadius: '2px' }}>
                                <div style={{ height: '100%', width: `${pct}%`, background: barColor, borderRadius: '2px' }} />
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  )}

                  {/* Loader si pred pas encore chargée */}
                  {!pred && (
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', color: 'var(--text-muted)', textAlign: 'center', padding: '12px 0' }}>
                      Chargement des données...
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>

        {/* Warning corrélation */}
        {result.correlated_warning && (
          <div style={{ margin: '0 24px 16px', padding: '10px 14px', background: 'rgba(255,170,0,0.08)', border: '1px solid rgba(255,170,0,0.2)', borderRadius: '6px', fontFamily: 'var(--font-mono)', fontSize: '9px', color: 'var(--accent-amber)' }}>
            ⚠ {result.correlated_warning}
          </div>
        )}

        {/* Recommandation */}
        <TicketRecommendation byMatch={byMatch} preds={preds} meta={meta} getMatch={getMatch} seuil={seuil} seuilMax={seuilMax} />

        {/* Disclaimer */}
        <div style={{ margin: '0 24px 16px', padding: '10px 14px', background: 'var(--bg-elevated)', borderRadius: '6px', fontFamily: 'var(--font-mono)', fontSize: '8px', color: 'var(--text-muted)', lineHeight: 1.6 }}>
          {result.disclaimer}
        </div>

        {/* Bouton fermer */}
        <div style={{ padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
          <button onClick={onClose} style={{
            width: '100%', padding: '12px', background: 'transparent',
            border: `1px solid ${meta.color}50`, borderRadius: '6px',
            color: meta.color, fontFamily: 'var(--font-mono)',
            fontSize: '11px', letterSpacing: '0.1em', cursor: 'pointer',
          }}>FERMER</button>
        </div>

      </div>
    </div>
  )
}

// Paires de marchés incompatibles — jamais recommander ensemble
const INCOMPATIBLE = [
  ['Victoire domicile', 'Match nul'],
  ['Victoire domicile', 'Victoire extérieur'],
  ['Match nul', 'Victoire extérieur'],
  ['Les deux marquent', 'Les deux ne marquent pas'],
  ['Plus de 2.5 buts', 'Moins de 2.5 buts'],
  ['Plus de 3.5 buts', 'Moins de 3.5 buts'],
  ['Plus de 3.5 buts', 'Plus de 2.5 buts'],
]

function buildRecommendation(preds, seuil, seuilMax, mode) {
  if (!preds) return null
  const isDanger = seuilMax < 1

  const ALL_MARKETS = [
    { label: 'Victoire domicile',        proba: preds.home_win_proba,                                   group: '1x2'  },
    { label: 'Match nul',                proba: preds.draw_proba,                                       group: '1x2'  },
    { label: 'Victoire extérieur',       proba: preds.away_win_proba,                                   group: '1x2'  },
    { label: 'Chance double 1X',         proba: preds.home_draw_proba,                                  group: 'dc'   },
    { label: 'Chance double X2',         proba: preds.away_draw_proba,                                  group: 'dc'   },
    { label: 'Chance double 12',         proba: preds.home_away_proba,                                  group: 'dc'   },
    { label: 'Les deux marquent',        proba: preds.btts_proba,                                       group: 'btts' },
    { label: 'Les deux ne marquent pas', proba: preds.btts_proba != null ? 1 - preds.btts_proba : null, group: 'btts' },
    { label: 'Plus de 0.5 buts',         proba: preds.over_05_proba,                                    group: 'over' },
    { label: 'Plus de 1.5 buts',         proba: preds.over_15_proba,                                    group: 'over' },
    { label: 'Plus de 2.5 buts',         proba: preds.over_25_proba,                                    group: 'over' },
    { label: 'Plus de 3.5 buts',         proba: preds.over_35_proba,                                    group: 'over' },
    { label: 'Moins de 2.5 buts',        proba: preds.over_25_proba != null ? 1 - preds.over_25_proba : null, group: 'under' },
    { label: 'Moins de 3.5 buts',        proba: preds.over_35_proba != null ? 1 - preds.over_35_proba : null, group: 'under' },
  ].filter(m => m.proba != null && m.proba >= seuil && m.proba <= seuilMax)
   .sort((a, b) => b.proba - a.proba)

  if (ALL_MARKETS.length === 0) return null

  // Pari principal = meilleure proba
  const main = ALL_MARKETS[0]
  const selected = [main]

  // Ajouter marchés complémentaires si proba > seuil + 5% et pas incompatibles
  const complementThreshold = isDanger ? seuil + 0.03 : seuil + 0.05
  for (const mk of ALL_MARKETS.slice(1)) {
    if (selected.length >= 3) break
    if (mk.group === main.group) continue // même groupe = redondant
    const isIncompat = INCOMPATIBLE.some(pair =>
      (pair[0] === main.label && pair[1] === mk.label) ||
      (pair[1] === main.label && pair[0] === mk.label) ||
      selected.some(s => (pair[0] === s.label && pair[1] === mk.label) || (pair[1] === s.label && pair[0] === mk.label))
    )
    if (!isIncompat && mk.proba >= complementThreshold) {
      selected.push(mk)
    }
  }

  return selected
}

function TicketRecommendation({ byMatch, preds, meta, getMatch, seuil, seuilMax }) {
  const matchIds = Object.keys(byMatch).map(Number)
  const recs = matchIds.map(mid => ({
    match: getMatch(mid),
    pred: preds[mid],
    rec: buildRecommendation(preds[mid], seuil, seuilMax),
  })).filter(r => r.rec && r.rec.length > 0)

  if (recs.length === 0) return null

  return (
    <div style={{ margin: '0 24px 20px' }}>
      {/* Titre section */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
        <div style={{ height: '1px', flex: 1, background: `${meta.color}30` }} />
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ fontSize: '14px' }}>💡</span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', fontWeight: 700, color: meta.color, letterSpacing: '0.15em' }}>
            CE QUE JE PARIERAIS
          </span>
        </div>
        <div style={{ height: '1px', flex: 1, background: `${meta.color}30` }} />
      </div>

      <div style={{
        background: `${meta.color}08`,
        border: `1px solid ${meta.color}30`,
        borderRadius: '8px',
        overflow: 'hidden',
      }}>
        {recs.map(({ match, rec }, i) => {
          const home = match?.home_team?.name || '?'
          const away = match?.away_team?.name || '?'
          const mainBet = rec[0]
          const extraBets = rec.slice(1)

          return (
            <div key={i} style={{
              padding: '14px 16px',
              borderBottom: i < recs.length - 1 ? `1px solid ${meta.color}20` : 'none',
            }}>
              {/* Nom du match si plusieurs */}
              {matchIds.length > 1 && (
                <div style={{
                  display: 'flex', alignItems: 'center', gap: '6px',
                  marginBottom: '10px',
                  fontFamily: 'var(--font-mono)', fontSize: '8px', color: 'var(--text-muted)',
                  letterSpacing: '0.08em',
                }}>
                  {match?.home_team?.crest_url && <img src={match.home_team.crest_url} alt="" width={13} height={13} style={{ objectFit: 'contain' }} onError={e => e.target.style.display='none'} />}
                  <span>{home}</span>
                  <span style={{ color: 'var(--border)' }}>vs</span>
                  <span>{away}</span>
                  {match?.away_team?.crest_url && <img src={match.away_team.crest_url} alt="" width={13} height={13} style={{ objectFit: 'contain' }} onError={e => e.target.style.display='none'} />}
                </div>
              )}

              {/* Pari principal */}
              <div style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                background: `${meta.color}15`,
                border: `1px solid ${meta.color}40`,
                borderRadius: '6px',
                padding: '12px 14px',
                marginBottom: extraBets.length > 0 ? '8px' : '0',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ fontSize: '14px' }}>⭐</span>
                  <div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '8px', color: meta.color, letterSpacing: '0.1em', marginBottom: '2px' }}>
                      PARI PRINCIPAL
                    </div>
                    <div style={{ fontFamily: 'var(--font-display)', fontSize: '15px', color: 'var(--text-primary)', letterSpacing: '0.04em' }}>
                      {mainBet.label}
                    </div>
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontFamily: 'var(--font-display)', fontSize: '24px', color: meta.color, lineHeight: 1 }}>
                    {Math.round(mainBet.proba * 100)}%
                  </div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '7px', color: 'var(--text-muted)', marginTop: '2px' }}>
                    PROBABILITÉ
                  </div>
                </div>
              </div>

              {/* Paris complémentaires */}
              {extraBets.length > 0 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '7px', color: 'var(--text-muted)', letterSpacing: '0.1em', marginBottom: '2px' }}>
                    + PEUVENT COMPLÉTER
                  </div>
                  {extraBets.map((mk, j) => (
                    <div key={j} style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                      background: 'var(--bg-elevated)',
                      border: '1px solid var(--border)',
                      borderRadius: '5px',
                      padding: '8px 12px',
                    }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-secondary)' }}>
                        {mk.label}
                      </span>
                      <span style={{ fontFamily: 'var(--font-display)', fontSize: '13px', color: 'var(--text-secondary)', fontWeight: 600 }}>
                        {Math.round(mk.proba * 100)}%
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
