import { Link } from 'react-router-dom'

const STATUS_META = {
  SCHEDULED: { label: 'PROG.',  color: '#ffcc00' },
  TIMED:     { label: 'PROG.',  color: '#ffcc00' },
  IN_PLAY:   { label: 'LIVE',   color: '#00ff88' },
  FINISHED:  { label: 'TERM.',  color: '#44456a' },
  POSTPONED: { label: 'REPOR.', color: '#ff4455' },
  CANCELLED: { label: 'ANNUL.', color: '#ff4455' },
}

function fmtDate(str) {
  if (!str) return '—'
  const d = new Date(str)
  return d.toLocaleDateString('fr-FR', {
    weekday: 'short', day: '2-digit', month: 'short',
    hour: '2-digit', minute: '2-digit',
  })
}

function TeamLogo({ url, name, size = 28 }) {
  if (url) {
    return (
      <img
        src={url}
        alt={name}
        width={size}
        height={size}
        style={{ objectFit: 'contain', flexShrink: 0 }}
        onError={(e) => { e.target.style.display = 'none' }}
      />
    )
  }
  // Fallback : initiales
  return (
    <div style={{
      width: size, height: size, borderRadius: '50%',
      background: 'var(--surface-2)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontSize: '9px', fontFamily: 'var(--font-mono)',
      color: 'var(--text-muted)', flexShrink: 0,
    }}>
      {(name || '?').slice(0, 2).toUpperCase()}
    </div>
  )
}

export default function MatchCard({ match, animationDelay = 0, showAnalyze = true }) {
  const meta = STATUS_META[match.status] || { label: match.status, color: '#44456a' }
  const isFinished = match.status === 'FINISHED'
  const isLive = match.status === 'IN_PLAY'
  const home = match.home_team?.short_name || match.home_team?.name || '—'
  const away = match.away_team?.short_name || match.away_team?.name || '—'

  return (
    <Link
      to={`/match/${match.id}`}
      className="match-card animate-fade-up"
      style={{ animationDelay: `${animationDelay}ms` }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {/* Logo compétition */}
          {match.competition?.crest_url && (
            <img
              src={match.competition.crest_url}
              alt={match.competition.name}
              width={18} height={18}
              style={{ objectFit: 'contain' }}
              onError={(e) => { e.target.style.display = 'none' }}
            />
          )}
          <span style={{
            fontFamily: 'var(--font-mono)', fontSize: '10px', fontWeight: 700,
            letterSpacing: '0.06em', color: 'var(--text-muted)',
          }}>
            {match.competition?.name || match.competition?.code || '—'}
          </span>
          {match.matchday && (
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '0.06em' }}>
              J{match.matchday}
            </span>
          )}
        </div>
        <span style={{
          fontFamily: 'var(--font-mono)', fontSize: '9px', fontWeight: 700,
          letterSpacing: '0.14em', color: meta.color,
          ...(isLive ? { animation: 'pulseGlow 1.4s ease-in-out infinite' } : {}),
        }}>
          {meta.label}
        </span>
      </div>

      {/* Teams */}
      <div style={{ marginBottom: '16px' }}>
        {isFinished && match.home_score != null ? (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', alignItems: 'center', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <TeamLogo url={match.home_team?.crest_url} name={home} />
              <span style={{ fontFamily: 'var(--font-display)', fontSize: '18px', letterSpacing: '0.03em', color: 'var(--text-primary)', lineHeight: 1.1 }}>
                {home}
              </span>
            </div>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)', textAlign: 'center', letterSpacing: '0.05em' }}>
              {match.home_score}&thinsp;—&thinsp;{match.away_score}
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', justifyContent: 'flex-end' }}>
              <span style={{ fontFamily: 'var(--font-display)', fontSize: '18px', letterSpacing: '0.03em', color: 'var(--text-primary)', lineHeight: 1.1, textAlign: 'right' }}>
                {away}
              </span>
              <TeamLogo url={match.away_team?.crest_url} name={away} />
            </div>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', alignItems: 'center', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <TeamLogo url={match.home_team?.crest_url} name={home} />
              <span style={{ fontFamily: 'var(--font-display)', fontSize: '20px', letterSpacing: '0.03em', color: 'var(--text-primary)', lineHeight: 1.1 }}>
                {home}
              </span>
            </div>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '0.18em', padding: '4px 8px', border: '1px solid var(--border)', borderRadius: '2px' }}>
              VS
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', justifyContent: 'flex-end' }}>
              <span style={{ fontFamily: 'var(--font-display)', fontSize: '20px', letterSpacing: '0.03em', color: 'var(--text-primary)', lineHeight: 1.1, textAlign: 'right' }}>
                {away}
              </span>
              <TeamLogo url={match.away_team?.crest_url} name={away} />
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)', letterSpacing: '0.04em' }}>
          {fmtDate(match.match_date)}
        </span>
        <span className="card-analyze-hint" style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '0.1em', transition: 'color 0.2s ease' }}>
          {showAnalyze ? 'ANALYSER →' : 'VOIR STATS →'}
        </span>
      </div>
    </Link>
  )
}
