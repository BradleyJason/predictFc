import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getLiveMatches, getMatches, getValueBetsSummary } from '../services/api'
import { fmtDateShort } from '../utils'

const FEATURES = [
  {
    icon: '⚡',
    title: 'Pronostics instantanés',
    desc: 'Clique sur n\'importe quel match pour obtenir une analyse complète : qui est favori, les probabilités, les buts attendus.',
    color: 'var(--accent-green)',
  },
  {
    icon: '💎',
    title: 'Value Bets',
    desc: 'On détecte les cotes sous-évaluées par les bookmakers — les paris où la vraie probabilité est meilleure que ce qu\'ils affichent.',
    color: 'var(--accent-cyan)',
  },
  {
    icon: '🎟️',
    title: 'Smart Ticket',
    desc: 'Sélectionne plusieurs matchs et on génère automatiquement le ticket combiné le plus solide pour maximiser tes chances.',
    color: 'var(--accent-amber)',
  },
]

export default function Dashboard() {
  const [live,      setLive]      = useState([])
  const [upcoming,  setUpcoming]  = useState([])
  const [vbSummary, setVbSummary] = useState(null)

  useEffect(() => {
    const now = new Date()
    const to  = new Date(now); to.setDate(now.getDate() + 3)
    Promise.all([
      getLiveMatches(),
      getMatches({
        limit:     6,
        date_from: now.toISOString().split('T')[0],
        date_to:   to.toISOString().split('T')[0],
      }),
      getValueBetsSummary().catch(() => ({ data: null })),
    ]).then(([liveRes, upRes, vbRes]) => {
      setLive(liveRes.data || [])
      setUpcoming(
        (upRes.data?.matches || [])
          .filter(m => m.status !== 'FINISHED' && m.status !== 'IN_PLAY')
          .slice(0, 6)
      )
      setVbSummary(vbRes.data)
    }).catch(() => {})
  }, [])

  return (
    <div style={{ maxWidth: '1060px', margin: '0 auto', padding: '40px 24px' }}>

      {/* ── Hero ── */}
      <div style={{ marginBottom: '52px', textAlign: 'center' }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: '8px',
          background: 'rgba(0,255,136,0.08)', border: '1px solid rgba(0,255,136,0.2)',
          borderRadius: '20px', padding: '5px 14px', marginBottom: '20px',
        }}>
          <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent-green)', animation: 'pulseGlow 1.4s infinite', display: 'inline-block' }} />
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--accent-green)', letterSpacing: '0.1em' }}>
            {live.length > 0 ? `${live.length} MATCH${live.length > 1 ? 'S' : ''} EN DIRECT` : 'ANALYSE EN TEMPS RÉEL'}
          </span>
        </div>

        <h1 style={{
          fontFamily: 'var(--font-display)',
          fontSize: 'clamp(40px, 8vw, 80px)',
          color: 'var(--text-primary)',
          letterSpacing: '0.04em', margin: '0 0 16px',
          lineHeight: 1,
        }}>
          PARIE PLUS<br />
          <span style={{ color: 'var(--accent-green)' }}>INTELLIGEMMENT</span>
        </h1>

        <p style={{
          fontFamily: 'var(--font-mono)', fontSize: '13px',
          color: 'var(--text-muted)', lineHeight: 1.8,
          maxWidth: '520px', margin: '0 auto 28px',
        }}>
          PredictFC analyse des milliers de matchs pour te donner les meilleures chances de gagner.
          Pas besoin d'être expert — on fait le travail pour toi.
        </p>

        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
          <Link to="/matches" style={{
            padding: '13px 28px',
            background: 'var(--accent-green)', color: '#06060e',
            fontFamily: 'var(--font-mono)', fontSize: '11px',
            fontWeight: 700, letterSpacing: '0.15em',
            textDecoration: 'none', borderRadius: '4px',
            boxShadow: '0 0 28px rgba(0,255,136,0.25)',
          }}>
            → VOIR LES MATCHS
          </Link>
          <Link to="/value-bets" style={{
            padding: '13px 28px', background: 'transparent',
            border: '1px solid var(--border)', color: 'var(--text-secondary)',
            fontFamily: 'var(--font-mono)', fontSize: '11px',
            fontWeight: 700, letterSpacing: '0.15em',
            textDecoration: 'none', borderRadius: '4px',
          }}>
            💎 MEILLEURES COTES
          </Link>
        </div>
      </div>

      {/* ── Ce qu'on peut faire ── */}
      <div style={{ marginBottom: '52px' }}>
        <SectionTitle>QUE PEUT-ON FAIRE ?</SectionTitle>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '14px', marginTop: '16px',
        }}>
          {FEATURES.map(({ icon, title, desc, color }) => (
            <div key={title} style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border)',
              borderRadius: '6px', padding: '24px',
              transition: 'border-color 0.2s',
            }}
            onMouseEnter={(e) => e.currentTarget.style.borderColor = color + '50'}
            onMouseLeave={(e) => e.currentTarget.style.borderColor = 'var(--border)'}
            >
              <div style={{ fontSize: '28px', marginBottom: '12px' }}>{icon}</div>
              <div style={{
                fontFamily: 'var(--font-display)', fontSize: '16px',
                color: 'var(--text-primary)', marginBottom: '10px', letterSpacing: '0.03em',
              }}>
                {title}
              </div>
              <div style={{
                fontFamily: 'var(--font-mono)', fontSize: '11px',
                color: 'var(--text-muted)', lineHeight: 1.7,
              }}>
                {desc}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Chiffres clés (vulgarisés) ── */}
      <div style={{ marginBottom: '52px' }}>
        <SectionTitle>EN CHIFFRES</SectionTitle>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '12px', marginTop: '16px',
        }}>
          {[
            { value: '41 000+', label: 'Matchs analysés',       sub: 'depuis 2019',           color: 'var(--accent-green)' },
            { value: '36',      label: 'Compétitions suivies',  sub: 'dont les 5 grands championnats', color: 'var(--accent-cyan)' },
            { value: '+5.9%',   label: 'Rentabilité moyenne',   sub: 'sur les value bets',    color: 'var(--accent-amber)' },
            { value: vbSummary?.total ?? '—', label: 'Value bets actives', sub: 'en ce moment', color: '#ff6b35' },
          ].map(({ value, label, sub, color }) => (
            <div key={label} style={{
              background: 'var(--bg-surface)', border: '1px solid var(--border)',
              borderRadius: '6px', padding: '20px',
            }}>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: '32px', color, lineHeight: 1, marginBottom: '8px' }}>
                {value}
              </div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '3px' }}>
                {label}
              </div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', color: 'var(--text-muted)', letterSpacing: '0.04em' }}>
                {sub}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Live ── */}
      {live.length > 0 && (
        <Section title="⚡ EN DIRECT MAINTENANT" accent="var(--accent-green)" badge={live.length} link="/matches?tab=live">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '10px' }}>
            {live.map(m => <MiniMatchCard key={m.id} match={m} live />)}
          </div>
        </Section>
      )}

      {/* ── Prochains matchs ── */}
      {upcoming.length > 0 && (
        <Section title="📅 PROCHAINS MATCHS" accent="var(--accent-cyan)" link="/matches">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '10px' }}>
            {upcoming.map(m => <MiniMatchCard key={m.id} match={m} />)}
          </div>
          <Link to="/matches" style={{
            display: 'inline-flex', marginTop: '14px',
            fontFamily: 'var(--font-mono)', fontSize: '10px',
            letterSpacing: '0.1em', color: 'var(--text-muted)',
            textDecoration: 'none',
          }}>
            VOIR TOUS LES MATCHS →
          </Link>
        </Section>
      )}

      {/* ── Value Bets callout ── */}
      {vbSummary && vbSummary.total > 0 && (
        <div style={{
          background: 'linear-gradient(135deg, rgba(255,107,53,0.08), rgba(0,255,136,0.04))',
          border: '1px solid rgba(255,107,53,0.25)',
          borderRadius: '8px', padding: '28px 32px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          gap: '20px', flexWrap: 'wrap',
        }}>
          <div>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: '22px', color: 'var(--text-primary)', marginBottom: '6px', letterSpacing: '0.03em' }}>
              💎 {vbSummary.total} cote{vbSummary.total > 1 ? 's' : ''} sous-évaluée{vbSummary.total > 1 ? 's' : ''} détectée{vbSummary.total > 1 ? 's' : ''}
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)', lineHeight: 1.6 }}>
              Nos algorithmes ont trouvé des paris où les bookmakers ont mal évalué les chances réelles.
              {vbSummary.strong > 0 && <span style={{ color: '#ff4455' }}> {vbSummary.strong} opportunité{vbSummary.strong > 1 ? 's' : ''} forte{vbSummary.strong > 1 ? 's' : ''}.</span>}
            </div>
          </div>
          <Link to="/value-bets" style={{
            padding: '12px 22px', background: 'rgba(255,107,53,0.15)',
            border: '1px solid rgba(255,107,53,0.4)',
            borderRadius: '4px', color: '#ff6b35',
            fontFamily: 'var(--font-mono)', fontSize: '10px',
            fontWeight: 700, letterSpacing: '0.12em',
            textDecoration: 'none', whiteSpace: 'nowrap',
            transition: 'all 0.2s',
          }}>
            VOIR LES VALUE BETS →
          </Link>
        </div>
      )}
    </div>
  )
}

function SectionTitle({ children }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
      <div style={{ width: '3px', height: '18px', background: 'var(--border)', borderRadius: '2px' }} />
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', fontWeight: 700, letterSpacing: '0.2em', color: 'var(--text-muted)' }}>
        {children}
      </span>
    </div>
  )
}

function Section({ title, accent, badge, link, children }) {
  return (
    <div style={{ marginBottom: '48px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ width: '3px', height: '20px', background: accent, borderRadius: '2px', boxShadow: `0 0 8px ${accent}` }} />
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', fontWeight: 700, letterSpacing: '0.14em', color: 'var(--text-secondary)' }}>
            {title}
          </span>
          {badge > 0 && (
            <span style={{ background: accent, color: '#06060e', fontFamily: 'var(--font-mono)', fontSize: '9px', fontWeight: 700, padding: '1px 7px', borderRadius: '10px', animation: 'pulseGlow 1.4s infinite' }}>
              {badge}
            </span>
          )}
        </div>
        {link && (
          <Link to={link} style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', letterSpacing: '0.1em', color: 'var(--text-muted)', textDecoration: 'none' }}>
            VOIR TOUT →
          </Link>
        )}
      </div>
      {children}
    </div>
  )
}

function MiniMatchCard({ match: m, live }) {
  const home = m.home_team?.short_name || m.home_team?.name || '—'
  const away = m.away_team?.short_name || m.away_team?.name || '—'
  return (
    <Link to={`/match/${m.id}`} style={{
      display: 'block', textDecoration: 'none',
      background: 'var(--bg-surface)',
      border: `1px solid ${live ? 'rgba(0,255,136,0.2)' : 'var(--border)'}`,
      borderRadius: '6px', padding: '14px 16px',
      transition: 'all 0.2s ease',
    }}
    onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'rgba(0,255,136,0.4)'; e.currentTarget.style.transform = 'translateY(-2px)' }}
    onMouseLeave={(e) => { e.currentTarget.style.borderColor = live ? 'rgba(0,255,136,0.2)' : 'var(--border)'; e.currentTarget.style.transform = 'none' }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          {m.competition?.crest_url && (
            <img src={m.competition.crest_url} alt="" width={14} height={14} style={{ objectFit: 'contain' }} onError={(e) => e.target.style.display = 'none'} />
          )}
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', color: 'var(--text-muted)' }}>
            {m.competition?.name || '—'}
          </span>
        </div>
        {live
          ? <span style={{ fontFamily: 'var(--font-mono)', fontSize: '8px', fontWeight: 700, color: 'var(--accent-green)', animation: 'pulseGlow 1.4s infinite' }}>● EN DIRECT</span>
          : <span style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', color: 'var(--text-muted)' }}>{fmtDateShort(m.match_date)}</span>
        }
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', alignItems: 'center', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          {m.home_team?.crest_url && <img src={m.home_team.crest_url} alt="" width={20} height={20} style={{ objectFit: 'contain', flexShrink: 0 }} onError={(e) => e.target.style.display = 'none'} />}
          <span style={{ fontFamily: 'var(--font-display)', fontSize: '13px', color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{home}</span>
        </div>
        <span style={{
          fontFamily: 'var(--font-mono)', flexShrink: 0,
          fontSize: live ? '15px' : '10px', fontWeight: live ? 700 : 400,
          color: live ? 'var(--text-primary)' : 'var(--text-muted)',
          padding: live ? '0' : '2px 6px',
          border: live ? 'none' : '1px solid var(--border)', borderRadius: '2px',
        }}>
          {live ? `${m.home_score ?? 0}—${m.away_score ?? 0}` : 'VS'}
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', justifyContent: 'flex-end' }}>
          <span style={{ fontFamily: 'var(--font-display)', fontSize: '13px', color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', textAlign: 'right' }}>{away}</span>
          {m.away_team?.crest_url && <img src={m.away_team.crest_url} alt="" width={20} height={20} style={{ objectFit: 'contain', flexShrink: 0 }} onError={(e) => e.target.style.display = 'none'} />}
        </div>
      </div>
    </Link>
  )
}
