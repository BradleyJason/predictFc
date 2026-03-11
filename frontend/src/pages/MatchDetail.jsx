import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getMatch, getPrediction } from '../services/api'
import PredictionBar from '../components/PredictionBar'
import ConfidenceGauge from '../components/ConfidenceGauge'

/* ── Helpers ── */
function fmtDateFull(str) {
  if (!str) return '—'
  const d = new Date(str)
  return d.toLocaleDateString('fr-FR', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/* ═══════════════════════════════════════════
   Page component
═══════════════════════════════════════════ */
export default function MatchDetail() {
  const { id } = useParams()

  const [match,       setMatch]       = useState(null)
  const [matchErr,    setMatchErr]    = useState(null)
  const [matchLoad,   setMatchLoad]   = useState(true)

  const [prediction,  setPrediction]  = useState(null)
  const [predLoad,    setPredLoad]    = useState(false)
  const [predErr,     setPredErr]     = useState(null)
  const [analyzed,    setAnalyzed]    = useState(false)

  /* Load match */
  useEffect(() => {
    getMatch(id)
      .then((r) => { setMatch(r.data); setMatchLoad(false) })
      .catch(() => { setMatchErr('Match introuvable.'); setMatchLoad(false) })
  }, [id])

  const handleAnalyze = (forceRefresh = false) => {
    setPredLoad(true)
    setPredErr(null)
    getPrediction(id, forceRefresh)
      .then((r) => {
        setPrediction(r.data)
        setPredLoad(false)
        setAnalyzed(true)
      })
      .catch(() => {
        setPredErr("Erreur lors de l'analyse. Le modèle est-il entraîné ?")
        setPredLoad(false)
      })
  }

  if (matchLoad) return <PageLoader />
  if (matchErr)  return <PageError message={matchErr} />

  return (
    <div style={{ maxWidth: '1020px', margin: '0 auto', padding: '36px 24px' }}>
      <Link to="/" className="back-link">← RETOUR AUX MATCHS</Link>

      {/* Match card header */}
      <MatchHeader match={match} />

      {/* Analyse CTA */}
      {!analyzed && (
        <div style={{ marginTop: '32px' }}>
          <AnalyzeButton loading={predLoad} onClick={() => handleAnalyze(false)} />
          {predErr && <ErrorBanner message={predErr} />}
        </div>
      )}

      {/* Refresh button (once analyzed) */}
      {analyzed && !predLoad && (
        <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'flex-end' }}>
          <button
            onClick={() => handleAnalyze(true)}
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '10px',
              letterSpacing: '0.12em',
              color: 'var(--text-muted)',
              background: 'transparent',
              border: '1px solid var(--border)',
              borderRadius: '3px',
              padding: '6px 14px',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
          >
            ↺ RAFRAÎCHIR
          </button>
        </div>
      )}

      {/* Prediction sections */}
      {analyzed && prediction && (
        <PredictionSections prediction={prediction} />
      )}
    </div>
  )
}

/* ═══════════════════════════════════════════
   Sub-components
═══════════════════════════════════════════ */

function MatchHeader({ match }) {
  const home = match.home_team?.name || '—'
  const away = match.away_team?.name || '—'

  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        borderRadius: '4px',
        padding: '32px',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Top accent line */}
      <div
        style={{
          position: 'absolute',
          top: 0, left: 0, right: 0,
          height: '2px',
          background: 'linear-gradient(90deg, transparent, var(--accent-cyan) 40%, var(--accent-green) 60%, transparent)',
        }}
      />

      {/* Competition badge */}
      <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '28px' }}>
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '11px',
            fontWeight: 700,
            background: 'var(--accent-cyan)',
            color: '#06060e',
            padding: '3px 9px',
            borderRadius: '2px',
            letterSpacing: '0.08em',
          }}
        >
          {match.competition?.code || '—'}
        </span>
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '11px',
            color: 'var(--text-muted)',
            letterSpacing: '0.06em',
          }}
        >
          {match.competition?.name}
          {match.matchday ? ` · JOURNÉE ${match.matchday}` : ''}
        </span>
      </div>

      {/* Teams */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr auto 1fr',
          alignItems: 'center',
          gap: '20px',
          marginBottom: '28px',
        }}
      >
        {/* Home */}
        <div>
          <div
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: 'clamp(24px, 4.5vw, 44px)',
              letterSpacing: '0.03em',
              color: 'var(--text-primary)',
              lineHeight: 1,
              marginBottom: '4px',
            }}
          >
            {home}
          </div>
          <div
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '9px',
              letterSpacing: '0.16em',
              color: 'var(--text-muted)',
            }}
          >
            DOMICILE
          </div>
        </div>

        {/* Score or VS */}
        <div style={{ textAlign: 'center' }}>
          {match.status === 'FINISHED' && match.home_score != null ? (
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '36px',
                fontWeight: 700,
                color: 'var(--text-primary)',
                letterSpacing: '0.04em',
              }}
            >
              {match.home_score}&thinsp;—&thinsp;{match.away_score}
            </span>
          ) : (
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '12px',
                letterSpacing: '0.22em',
                color: 'var(--text-muted)',
                padding: '10px 18px',
                border: '1px solid var(--border)',
                borderRadius: '3px',
                display: 'inline-block',
              }}
            >
              VS
            </span>
          )}
        </div>

        {/* Away */}
        <div style={{ textAlign: 'right' }}>
          <div
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: 'clamp(24px, 4.5vw, 44px)',
              letterSpacing: '0.03em',
              color: 'var(--text-primary)',
              lineHeight: 1,
              marginBottom: '4px',
            }}
          >
            {away}
          </div>
          <div
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '9px',
              letterSpacing: '0.16em',
              color: 'var(--text-muted)',
            }}
          >
            EXTÉRIEUR
          </div>
        </div>
      </div>

      {/* Date */}
      <div
        style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '11px',
          color: 'var(--text-muted)',
          letterSpacing: '0.06em',
          textTransform: 'capitalize',
        }}
      >
        {fmtDateFull(match.match_date)}
      </div>
    </div>
  )
}

function AnalyzeButton({ loading, onClick }) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className="analyze-btn"
    >
      {loading ? (
        <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px' }}>
          <span style={{ color: 'var(--accent-green)', animation: 'pulseGlow 1s ease-in-out infinite' }}>
            ■ ■ ■
          </span>
          ANALYSE EN COURS...
        </span>
      ) : (
        '⬡  ANALYSER CE MATCH'
      )}
    </button>
  )
}

/* Prediction layout: 2-col grids + full-width sections */
function PredictionSections({ prediction }) {
  return (
    <div className="animate-fade-in" style={{ marginTop: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>

      {/* Row 1: 1X2 + Over/Under */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px' }}>
        <PredCard title="RÉSULTAT 1X2">
          <PredictionBar label="DOMICILE"   value={prediction.home_win_proba} delay={80}  barHeight={5} />
          <PredictionBar label="NUL"        value={prediction.draw_proba}     delay={180} barHeight={5} />
          <PredictionBar label="EXTÉRIEUR"  value={prediction.away_win_proba} delay={280} barHeight={5} />

          {prediction.predicted_home_score != null && (
            <div
              style={{
                marginTop: '18px',
                padding: '10px 14px',
                background: 'var(--bg-elevated)',
                borderRadius: '3px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <span
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '9px',
                  letterSpacing: '0.14em',
                  color: 'var(--text-muted)',
                }}
              >
                SCORE PRÉDIT
              </span>
              <span
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '20px',
                  fontWeight: 700,
                  color: 'var(--text-primary)',
                  letterSpacing: '0.06em',
                }}
              >
                {prediction.predicted_home_score?.toFixed(1)}&thinsp;—&thinsp;{prediction.predicted_away_score?.toFixed(1)}
              </span>
            </div>
          )}
        </PredCard>

        <PredCard title="OVER / UNDER">
          {[
            { label: 'OVER 0.5', value: prediction.over_05_proba },
            { label: 'OVER 1.5', value: prediction.over_15_proba },
            { label: 'OVER 2.5', value: prediction.over_25_proba },
            { label: 'OVER 3.5', value: prediction.over_35_proba },
            { label: 'OVER 4.5', value: prediction.over_45_proba },
          ].map(({ label, value }, i) => (
            <PredictionBar key={label} label={label} value={value} delay={80 + i * 100} />
          ))}
        </PredCard>
      </div>

      {/* Row 2: BTTS + Double Chance */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px' }}>
        <PredCard title="LES DEUX ÉQUIPES MARQUENT">
          <PredictionBar label="OUI" value={prediction.btts_proba}            delay={100} barHeight={6} />
          <PredictionBar label="NON" value={1 - (prediction.btts_proba ?? 0)} delay={200} barHeight={6} />
        </PredCard>

        <PredCard title="DOUBLE CHANCE">
          <PredictionBar label="1X — DOM. OU NUL" value={prediction.home_draw_proba} delay={100} />
          <PredictionBar label="X2 — EXT. OU NUL" value={prediction.away_draw_proba} delay={200} />
          <PredictionBar label="12 — DOM. OU EXT." value={prediction.home_away_proba} delay={300} />
        </PredCard>
      </div>

      {/* Row 3: Top exact scores (full width) */}
      {prediction.top_scores?.length > 0 && (
        <PredCard title="SCORES EXACTS LES PLUS PROBABLES">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {prediction.top_scores.slice(0, 5).map((s, i) => (
              <ExactScoreRow
                key={i}
                rank={i + 1}
                home={s.home}
                away={s.away}
                probability={s.probability}
                delay={100 + i * 80}
              />
            ))}
          </div>
        </PredCard>
      )}

      {/* Row 4: Confidence gauge */}
      {prediction.confidence_score != null && (
        <PredCard title="ANALYSE GLOBALE">
          <ConfidenceGauge score={prediction.confidence_score} />
        </PredCard>
      )}

      {/* Disclaimer */}
      {prediction.disclaimer && (
        <div
          style={{
            padding: '14px 18px',
            border: '1px solid var(--border)',
            borderRadius: '3px',
            fontFamily: 'var(--font-mono)',
            fontSize: '10px',
            color: 'var(--text-muted)',
            lineHeight: 1.7,
            letterSpacing: '0.03em',
          }}
        >
          ⚠&nbsp;&nbsp;{prediction.disclaimer}
        </div>
      )}
    </div>
  )
}

/* Card container with section header */
function PredCard({ title, children }) {
  return (
    <div
      className="animate-fade-up"
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        borderRadius: '4px',
        padding: '22px',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          marginBottom: '18px',
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
          {title}
        </span>
      </div>
      {children}
    </div>
  )
}

/* Exact score row with mini bar */
function ExactScoreRow({ rank, home, away, probability, delay }) {
  const [filled, setFilled] = useState(false)
  const pct = Math.round(probability * 100)

  useEffect(() => {
    const t = setTimeout(() => setFilled(true), delay)
    return () => clearTimeout(t)
  }, [delay])

  /* Scale bar: max expected ~20%, so multiply x4 capped at 100 */
  const barWidth = Math.min(pct * 5, 100)

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
      <span
        style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '10px',
          color: 'var(--text-muted)',
          width: '18px',
          flexShrink: 0,
          letterSpacing: '0.04em',
        }}
      >
        #{rank}
      </span>
      <span
        style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '18px',
          fontWeight: 700,
          color: 'var(--text-primary)',
          width: '44px',
          flexShrink: 0,
          letterSpacing: '0.04em',
        }}
      >
        {home}&thinsp;-&thinsp;{away}
      </span>
      <div
        style={{
          flex: 1,
          height: '3px',
          background: 'var(--border)',
          borderRadius: '2px',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            height: '100%',
            width: filled ? `${barWidth}%` : '0%',
            background: 'var(--accent-cyan)',
            borderRadius: '2px',
            transition: `width 0.9s cubic-bezier(0.4, 0, 0.2, 1)`,
            boxShadow: '0 0 6px rgba(0,204,255,0.55)',
          }}
        />
      </div>
      <span
        style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '14px',
          fontWeight: 600,
          color: 'var(--accent-cyan)',
          textShadow: '0 0 8px rgba(0,204,255,0.45)',
          minWidth: '40px',
          textAlign: 'right',
          flexShrink: 0,
        }}
      >
        {pct}%
      </span>
    </div>
  )
}

/* Error banner inside the page */
function ErrorBanner({ message }) {
  return (
    <div
      style={{
        marginTop: '14px',
        padding: '12px 16px',
        border: '1px solid rgba(255,68,85,0.3)',
        background: 'rgba(255,68,85,0.05)',
        borderRadius: '3px',
        fontFamily: 'var(--font-mono)',
        fontSize: '11px',
        color: '#ff5566',
        letterSpacing: '0.05em',
      }}
    >
      ⚠ {message}
    </div>
  )
}

/* Full-page loader */
function PageLoader() {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '70vh',
        flexDirection: 'column',
        gap: '16px',
        fontFamily: 'var(--font-mono)',
        fontSize: '12px',
        color: 'var(--text-muted)',
        letterSpacing: '0.12em',
      }}
    >
      <span
        style={{
          color: 'var(--accent-green)',
          fontSize: '20px',
          animation: 'pulseGlow 1.3s ease-in-out infinite',
        }}
      >
        ■ ■ ■
      </span>
      CHARGEMENT...
    </div>
  )
}

/* Full-page error */
function PageError({ message }) {
  return (
    <div style={{ maxWidth: '600px', margin: '80px auto', padding: '24px' }}>
      <Link to="/" className="back-link">← RETOUR</Link>
      <div
        style={{
          padding: '18px',
          border: '1px solid rgba(255,68,85,0.3)',
          background: 'rgba(255,68,85,0.05)',
          borderRadius: '3px',
          fontFamily: 'var(--font-mono)',
          color: '#ff5566',
          fontSize: '12px',
        }}
      >
        ⚠ {message}
      </div>
    </div>
  )
}
