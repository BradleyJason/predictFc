import { Link } from 'react-router-dom'

const STATUS_META = {
  SCHEDULED:  { label: 'PROG.', color: '#ffcc00' },
  IN_PLAY:    { label: 'LIVE',  color: '#00ff88' },
  FINISHED:   { label: 'TERM.', color: '#44456a' },
  POSTPONED:  { label: 'REPOR.', color: '#ff4455' },
  CANCELLED:  { label: 'ANNUL.', color: '#ff4455' },
}

function fmtDate(str) {
  if (!str) return '—'
  const d = new Date(str)
  return d.toLocaleDateString('fr-FR', {
    weekday: 'short',
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function MatchCard({ match, animationDelay = 0 }) {
  const meta = STATUS_META[match.status] || { label: match.status, color: '#44456a' }
  const isFinished = match.status === 'FINISHED'
  const home = match.home_team?.short_name || match.home_team?.name || '—'
  const away = match.away_team?.short_name || match.away_team?.name || '—'

  return (
    <Link
      to={`/match/${match.id}`}
      className="match-card animate-fade-up"
      style={{ animationDelay: `${animationDelay}ms` }}
    >
      {/* Header row */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '18px',
        }}
      >
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '10px',
              fontWeight: 700,
              letterSpacing: '0.08em',
              color: '#06060e',
              background: 'var(--accent-cyan)',
              padding: '2px 7px',
              borderRadius: '2px',
            }}
          >
            {match.competition?.code || '—'}
          </span>
          {match.matchday && (
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '10px',
                color: 'var(--text-muted)',
                letterSpacing: '0.06em',
              }}
            >
              J{match.matchday}
            </span>
          )}
        </div>
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '9px',
            fontWeight: 700,
            letterSpacing: '0.14em',
            color: meta.color,
          }}
        >
          {meta.label}
        </span>
      </div>

      {/* Teams */}
      <div style={{ marginBottom: '18px' }}>
        {isFinished && match.home_score != null ? (
          /* Finished: show score */
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr auto 1fr',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <span
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: '20px',
                letterSpacing: '0.03em',
                color: 'var(--text-primary)',
                lineHeight: 1.1,
              }}
            >
              {home}
            </span>
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '20px',
                fontWeight: 700,
                color: 'var(--text-primary)',
                textAlign: 'center',
                letterSpacing: '0.05em',
              }}
            >
              {match.home_score}&thinsp;—&thinsp;{match.away_score}
            </span>
            <span
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: '20px',
                letterSpacing: '0.03em',
                color: 'var(--text-primary)',
                lineHeight: 1.1,
                textAlign: 'right',
              }}
            >
              {away}
            </span>
          </div>
        ) : (
          /* Upcoming: show VS */
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr auto 1fr',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <span
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: '22px',
                letterSpacing: '0.03em',
                color: 'var(--text-primary)',
                lineHeight: 1.1,
              }}
            >
              {home}
            </span>
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '10px',
                color: 'var(--text-muted)',
                letterSpacing: '0.18em',
                padding: '4px 8px',
                border: '1px solid var(--border)',
                borderRadius: '2px',
              }}
            >
              VS
            </span>
            <span
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: '22px',
                letterSpacing: '0.03em',
                color: 'var(--text-primary)',
                lineHeight: 1.1,
                textAlign: 'right',
              }}
            >
              {away}
            </span>
          </div>
        )}
      </div>

      {/* Footer */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '11px',
            color: 'var(--text-muted)',
            letterSpacing: '0.04em',
          }}
        >
          {fmtDate(match.match_date)}
        </span>
        <span
          className="card-analyze-hint"
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '10px',
            color: 'var(--text-muted)',
            letterSpacing: '0.1em',
            transition: 'color 0.2s ease',
          }}
        >
          ANALYSER →
        </span>
      </div>
    </Link>
  )
}
