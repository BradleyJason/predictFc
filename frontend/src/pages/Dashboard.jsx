import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getLiveMatches, getMatches, getValueBetsSummary } from '../services/api'
import { fmtDateShort, STATUS_META } from '../utils'

export default function Dashboard() {
  const [live,      setLive]      = useState([])
  const [upcoming,  setUpcoming]  = useState([])
  const [vbSummary, setVbSummary] = useState(null)
  const [loading,   setLoading]   = useState(true)

  useEffect(() => {
    const now  = new Date()
    const to   = new Date(now); to.setDate(now.getDate() + 3)
    Promise.all([
      getLiveMatches(),
      getMatches({ limit: 6, date_from: now.toISOString().split('T')[0], date_to: to.toISOString().split('T')[0] }),
      getValueBetsSummary().catch(() => ({ data: null })),
    ]).then(([liveRes, upRes, vbRes]) => {
      setLive(liveRes.data || [])
      setUpcoming((upRes.data?.matches || []).filter(m => m.status !== 'FINISHED' && m.status !== 'IN_PLAY').slice(0, 6))
      setVbSummary(vbRes.data)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '40px 24px' }}>

      {/* ── Hero ── */}
      <div style={{ marginBottom: '56px', position: 'relative' }}>
        <div style={{
          position: 'absolute', top: '-20px', left: '-10px',
          fontFamily: 'var(--font-display)', fontSize: 'clamp(80px, 15vw, 140px)',
          color: 'rgba(0,255,136,0.03)', letterSpacing: '0.05em',
          pointerEvents: 'none', userSelect: 'none', lineHeight: 1,
        }}>PREDICT</div>
        <div style={{ position: 'relative', zIndex: 1 }}>
          <div style={{
            fontFamily: 'var(--font-mono)', fontSize: '10px',
            letterSpacing: '0.3em', color: 'var(--accent-green)',
            marginBottom: '12px',
          }}>
            ◆ ANALYSE STATISTIQUE FOOTBALL
          </div>
          <h1 style={{
            fontFamily: 'var(--font-display)',
            fontSize: 'clamp(48px, 8vw, 88px)',
            letterSpacing: '0.04em',
            color: 'var(--text-primary)',
            lineHeight: 0.95, margin: 0, marginBottom: '16px',
          }}>
            PREDICTFC<span style={{ color: 'var(--accent-green)' }}>.</span>
          </h1>
          <p style={{
            fontFamily: 'var(--font-mono)', fontSize: '12px',
            color: 'var(--text-muted)', letterSpacing: '0.08em',
            lineHeight: 1.7, maxWidth: '480px',
          }}>
            Prédictions basées sur Dixon-Coles + XGBoost · 41 000+ matchs analysés · Value bets en temps réel
          </p>
          <div style={{ display: 'flex', gap: '12px', marginTop: '24px', flexWrap: 'wrap' }}>
            <Link to="/matches" style={{
              padding: '12px 24px',
              background: 'var(--accent-green)', color: '#06060e',
              fontFamily: 'var(--font-mono)', fontSize: '11px',
              fontWeight: 700, letterSpacing: '0.15em',
              textDecoration: 'none', borderRadius: '4px',
              boxShadow: '0 0 24px rgba(0,255,136,0.2)',
              transition: 'all 0.2s ease',
            }}>
              → VOIR LES MATCHS
            </Link>
            <Link to="/value-bets" style={{
              padding: '12px 24px',
              background: 'transparent',
              border: '1px solid var(--border)',
              color: 'var(--text-secondary)',
              fontFamily: 'var(--font-mono)', fontSize: '11px',
              fontWeight: 700, letterSpacing: '0.15em',
              textDecoration: 'none', borderRadius: '4px',
              transition: 'all 0.2s ease',
            }}>
              ◆ VALUE BETS
            </Link>
          </div>
        </div>
      </div>

      {/* ── Stats modèle ── */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
        gap: '12px', marginBottom: '48px',
      }}>
        {[
          { label: 'MATCHS ANALYSÉS',  value: '41 314',  unit: '',    color: 'var(--accent-green)' },
          { label: 'ACCURACY MODÈLE',  value: '52.3',    unit: '%',   color: 'var(--accent-cyan)'  },
          { label: 'ROI SIMULÉ',        value: '+5.9',    unit: '%',   color: 'var(--accent-green)' },
          { label: 'COMPÉTITIONS',      value: '36',      unit: '',    color: 'var(--accent-amber)' },
          { label: 'VALUE BETS DISPO',  value: vbSummary ? vbSummary.total : '—', unit: '', color: '#ff6b35' },
        ].map(({ label, value, unit, color }) => (
          <div key={label} style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border)',
            borderRadius: '4px', padding: '20px',
            position: 'relative', overflow: 'hidden',
          }}>
            <div style={{
              position: 'absolute', bottom: 0, left: 0, right: 0, height: '2px',
              background: `linear-gradient(90deg, transparent, ${color}, transparent)`,
              opacity: 0.4,
            }} />
            <div style={{
              fontFamily: 'var(--font-mono)', fontSize: '28px',
              fontWeight: 700, color, lineHeight: 1, marginBottom: '6px',
            }}>
              {value}<span style={{ fontSize: '14px' }}>{unit}</span>
            </div>
            <div style={{
              fontFamily: 'var(--font-mono)', fontSize: '8px',
              letterSpacing: '0.16em', color: 'var(--text-muted)',
            }}>
              {label}
            </div>
          </div>
        ))}
      </div>

      {/* ── Live ── */}
      {live.length > 0 && (
        <Section title="EN COURS" accent="var(--accent-green)" badge={live.length} link="/matches?tab=live">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '10px' }}>
            {live.map((m) => <MiniMatchCard key={m.id} match={m} live />)}
          </div>
        </Section>
      )}

      {/* ── Prochains matchs ── */}
      {upcoming.length > 0 && (
        <Section title="PROCHAINS MATCHS" accent="var(--accent-cyan)" link="/matches">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '10px' }}>
            {upcoming.map((m) => <MiniMatchCard key={m.id} match={m} />)}
          </div>
        </Section>
      )}

      {/* ── Value Bets summary ── */}
      {vbSummary && vbSummary.total > 0 && (
        <Section title="VALUE BETS" accent="#ff6b35" link="/value-bets">
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '12px',
          }}>
            {[
              { label: 'TOTAL DÉTECTÉES', value: vbSummary.total,  color: '#ff6b35' },
              { label: 'FORTES (>10%)',   value: vbSummary.strong, color: '#ff4455' },
              { label: 'ROI MOY. ATTENDU',value: `+${vbSummary.avg_roi?.toFixed(1)}%`, color: 'var(--accent-green)' },
            ].map(({ label, value, color }) => (
              <div key={label} style={{
                background: 'var(--bg-surface)', border: '1px solid var(--border)',
                borderRadius: '4px', padding: '16px 20px',
              }}>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '24px', fontWeight: 700, color, marginBottom: '4px' }}>
                  {value}
                </div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '8px', letterSpacing: '0.14em', color: 'var(--text-muted)' }}>
                  {label}
                </div>
              </div>
            ))}
          </div>
          <Link to="/value-bets" style={{
            display: 'inline-flex', marginTop: '14px',
            fontFamily: 'var(--font-mono)', fontSize: '10px',
            letterSpacing: '0.12em', color: '#ff6b35',
            textDecoration: 'none',
          }}>
            VOIR TOUTES LES VALUE BETS →
          </Link>
        </Section>
      )}
    </div>
  )
}

function Section({ title, accent, badge, link, children }) {
  return (
    <div style={{ marginBottom: '48px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ width: '3px', height: '20px', background: accent, borderRadius: '2px', boxShadow: `0 0 8px ${accent}` }} />
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', fontWeight: 700, letterSpacing: '0.18em', color: 'var(--text-secondary)' }}>
            {title}
          </span>
          {badge > 0 && (
            <span style={{
              background: accent, color: '#06060e',
              fontFamily: 'var(--font-mono)', fontSize: '9px', fontWeight: 700,
              padding: '1px 7px', borderRadius: '10px',
              animation: 'pulseGlow 1.4s infinite',
            }}>{badge}</span>
          )}
        </div>
        {link && (
          <Link to={link} style={{
            fontFamily: 'var(--font-mono)', fontSize: '9px',
            letterSpacing: '0.12em', color: 'var(--text-muted)',
            textDecoration: 'none', transition: 'color 0.15s',
          }}
          onMouseEnter={(e) => e.target.style.color = accent}
          onMouseLeave={(e) => e.target.style.color = 'var(--text-muted)'}
          >
            VOIR TOUT →
          </Link>
        )}
      </div>
      {children}
    </div>
  )
}

function MiniMatchCard({ match, live }) {
  const home = match.home_team?.short_name || match.home_team?.name || '—'
  const away = match.away_team?.short_name || match.away_team?.name || '—'
  return (
    <Link to={`/match/${match.id}`} style={{
      display: 'block', textDecoration: 'none',
      background: 'var(--bg-surface)',
      border: `1px solid ${live ? 'rgba(0,255,136,0.2)' : 'var(--border)'}`,
      borderRadius: '4px', padding: '14px 16px',
      transition: 'all 0.2s ease',
    }}
    onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'rgba(0,255,136,0.4)'; e.currentTarget.style.transform = 'translateY(-1px)' }}
    onMouseLeave={(e) => { e.currentTarget.style.borderColor = live ? 'rgba(0,255,136,0.2)' : 'var(--border)'; e.currentTarget.style.transform = 'none' }}
    >
      {/* Compétition */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          {match.competition?.crest_url && (
            <img src={match.competition.crest_url} alt="" width={14} height={14}
              style={{ objectFit: 'contain' }} onError={(e) => e.target.style.display = 'none'} />
          )}
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', color: 'var(--text-muted)', letterSpacing: '0.06em' }}>
            {match.competition?.name || '—'}
          </span>
        </div>
        {live && (
          <span style={{
            fontFamily: 'var(--font-mono)', fontSize: '8px', fontWeight: 700,
            color: 'var(--accent-green)', letterSpacing: '0.1em',
            animation: 'pulseGlow 1.4s infinite',
          }}>● LIVE</span>
        )}
      </div>

      {/* Teams + score */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', alignItems: 'center', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          {match.home_team?.crest_url && (
            <img src={match.home_team.crest_url} alt="" width={20} height={20}
              style={{ objectFit: 'contain', flexShrink: 0 }} onError={(e) => e.target.style.display = 'none'} />
          )}
          <span style={{ fontFamily: 'var(--font-display)', fontSize: '14px', color: 'var(--text-primary)', letterSpacing: '0.02em', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {home}
          </span>
        </div>
        <span style={{
          fontFamily: 'var(--font-mono)', fontSize: live ? '16px' : '10px',
          fontWeight: live ? 700 : 400,
          color: live ? 'var(--text-primary)' : 'var(--text-muted)',
          letterSpacing: live ? '0.05em' : '0.15em',
          padding: live ? '0' : '3px 6px',
          border: live ? 'none' : '1px solid var(--border)',
          borderRadius: '2px', flexShrink: 0,
        }}>
          {live ? `${match.home_score ?? 0}—${match.away_score ?? 0}` : 'VS'}
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', justifyContent: 'flex-end' }}>
          <span style={{ fontFamily: 'var(--font-display)', fontSize: '14px', color: 'var(--text-primary)', letterSpacing: '0.02em', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', textAlign: 'right' }}>
            {away}
          </span>
          {match.away_team?.crest_url && (
            <img src={match.away_team.crest_url} alt="" width={20} height={20}
              style={{ objectFit: 'contain', flexShrink: 0 }} onError={(e) => e.target.style.display = 'none'} />
          )}
        </div>
      </div>

      {/* Date */}
      {!live && (
        <div style={{ marginTop: '10px', fontFamily: 'var(--font-mono)', fontSize: '9px', color: 'var(--text-muted)', letterSpacing: '0.04em' }}>
          {fmtDateShort(match.match_date)}
        </div>
      )}
    </Link>
  )
}
