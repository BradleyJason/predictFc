import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getMatch, getMatchStats, getPrediction } from '../services/api'
import PredictionBar from '../components/PredictionBar'
import ConfidenceGauge from '../components/ConfidenceGauge'

function fmtDateFull(str) {
  if (!str) return '—'
  return new Date(str).toLocaleDateString('fr-FR', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

const RESULT_COLOR = { W: '#00ff88', D: '#ffcc00', L: '#ff4455' }

export default function MatchDetail() {
  const { id } = useParams()

  const [match,      setMatch]      = useState(null)
  const [matchErr,   setMatchErr]   = useState(null)
  const [matchLoad,  setMatchLoad]  = useState(true)
  const [stats,      setStats]      = useState(null)
  const [statsLoad,  setStatsLoad]  = useState(true)
  const [prediction, setPrediction] = useState(null)
  const [predLoad,   setPredLoad]   = useState(false)
  const [predErr,    setPredErr]    = useState(null)
  const [analyzed,   setAnalyzed]   = useState(false)

  useEffect(() => {
    getMatch(id)
      .then((r) => { setMatch(r.data); setMatchLoad(false) })
      .catch(() => { setMatchErr('Match introuvable.'); setMatchLoad(false) })
    getMatchStats(id)
      .then((r) => { setStats(r.data); setStatsLoad(false) })
      .catch(() => setStatsLoad(false))
  }, [id])

  const handleAnalyze = (forceRefresh = false) => {
    setPredLoad(true)
    setPredErr(null)
    getPrediction(id, forceRefresh)
      .then((r) => { setPrediction(r.data); setPredLoad(false); setAnalyzed(true) })
      .catch(() => { setPredErr("Erreur lors de l'analyse."); setPredLoad(false) })
  }

  if (matchLoad) return <PageLoader />
  if (matchErr)  return <PageError message={matchErr} />

  const isFinished = match.status === 'FINISHED'

  return (
    <div className="page-container" style={{ maxWidth: '1200px', margin: '0 auto', padding: '36px 24px' }}>
      <Link to="/" className="back-link">← RETOUR AUX MATCHS</Link>

      <MatchHeader match={match} />

      {isFinished ? (
        /* ── Vue match terminé : stats H2H uniquement, pas d'analyse ── */
        <div style={{ marginTop: '24px' }}>
          {statsLoad ? (
            <MiniLoader />
          ) : stats ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <FormCard home={stats.home_stats} away={stats.away_stats} />
              <H2HCard h2h={stats.h2h} homeStats={stats.home_stats} awayStats={stats.away_stats} />
              <Last5Card home={stats.home_stats} away={stats.away_stats} />
            </div>
          ) : (
            <NoStats />
          )}
        </div>
      ) : (
        /* ── Vue match à venir : stats + analyse côte à côte ── */
        <div
          className="match-detail-layout"
          style={{
            display: 'grid',
            gridTemplateColumns: analyzed ? '1fr 1fr' : '1fr auto',
            gap: '20px',
            marginTop: '24px',
            alignItems: 'start',
          }}
        >
          {/* Colonne gauche : Stats */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {statsLoad ? (
              <MiniLoader />
            ) : stats ? (
              <>
                <TeamComparisonCard home={stats.home_stats} away={stats.away_stats} />
                <FormCard home={stats.home_stats} away={stats.away_stats} />
                <H2HCard h2h={stats.h2h} homeStats={stats.home_stats} awayStats={stats.away_stats} />
                <Last5Card home={stats.home_stats} away={stats.away_stats} />
              </>
            ) : (
              <NoStats />
            )}
          </div>

          {/* Colonne droite : Analyse */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {!analyzed ? (
              <div>
                <AnalyzeButton loading={predLoad} onClick={() => handleAnalyze(false)} />
                {predErr && <ErrorBanner message={predErr} />}
              </div>
            ) : (
              <>
                <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <button
                    onClick={() => handleAnalyze(true)}
                    style={{
                      fontFamily: 'var(--font-mono)', fontSize: '10px', letterSpacing: '0.12em',
                      color: 'var(--text-muted)', background: 'transparent',
                      border: '1px solid var(--border)', borderRadius: '3px',
                      padding: '6px 14px', cursor: 'pointer',
                    }}
                  >
                    ↺ RAFRAÎCHIR
                  </button>
                </div>
                {prediction && <PredictionSections prediction={prediction} />}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

/* ── Match Header ── */
function MatchHeader({ match }) {
  const home = match.home_team?.name || '—'
  const away = match.away_team?.name || '—'

  return (
    <div style={{
      background: 'var(--bg-surface)', border: '1px solid var(--border)',
      borderRadius: '4px', padding: '28px 32px',
      position: 'relative', overflow: 'hidden', marginTop: '20px',
    }}>
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '2px', background: 'linear-gradient(90deg, transparent, var(--accent-cyan) 40%, var(--accent-green) 60%, transparent)' }} />

      {/* Compétition */}
      <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '24px' }}>
        {match.competition?.crest_url && (
          <img src={match.competition.crest_url} alt="" width={20} height={20} style={{ objectFit: 'contain' }} onError={(e) => { e.target.style.display = 'none' }} />
        )}
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)', letterSpacing: '0.06em' }}>
          {match.competition?.name}{match.matchday ? ` · JOURNÉE ${match.matchday}` : ''}
        </span>
      </div>

      {/* Équipes */}
      <div
        className="match-header-teams"
        style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', alignItems: 'center', gap: '20px', marginBottom: '20px' }}
      >
        {/* Domicile */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {match.home_team?.crest_url && (
            <img
              className="match-header-logo-lg"
              src={match.home_team.crest_url} alt="" width={48} height={48}
              style={{ objectFit: 'contain' }}
              onError={(e) => { e.target.style.display = 'none' }}
            />
          )}
          <div>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(18px, 3vw, 36px)', letterSpacing: '0.03em', color: 'var(--text-primary)', lineHeight: 1, marginBottom: '4px' }}>{home}</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', letterSpacing: '0.16em', color: 'var(--text-muted)' }}>DOMICILE</div>
          </div>
        </div>

        {/* Score / VS */}
        <div className="match-header-score" style={{ textAlign: 'center' }}>
          {match.status === 'FINISHED' && match.home_score != null ? (
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '36px', fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '0.04em' }}>
              {match.home_score}&thinsp;—&thinsp;{match.away_score}
            </span>
          ) : (
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', letterSpacing: '0.22em', color: 'var(--text-muted)', padding: '10px 18px', border: '1px solid var(--border)', borderRadius: '3px', display: 'inline-block' }}>VS</span>
          )}
        </div>

        {/* Extérieur */}
        <div className="match-header-away" style={{ display: 'flex', alignItems: 'center', gap: '12px', justifyContent: 'flex-end' }}>
          <div className="match-away-text" style={{ textAlign: 'right' }}>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(18px, 3vw, 36px)', letterSpacing: '0.03em', color: 'var(--text-primary)', lineHeight: 1, marginBottom: '4px' }}>{away}</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', letterSpacing: '0.16em', color: 'var(--text-muted)' }}>EXTÉRIEUR</div>
          </div>
          {match.away_team?.crest_url && (
            <img
              className="match-header-logo-lg"
              src={match.away_team.crest_url} alt="" width={48} height={48}
              style={{ objectFit: 'contain' }}
              onError={(e) => { e.target.style.display = 'none' }}
            />
          )}
        </div>
      </div>

      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)', letterSpacing: '0.06em', textTransform: 'capitalize' }}>
        {fmtDateFull(match.match_date)}
      </div>
    </div>
  )
}

/* ── Comparaison stats globales ── */
function TeamComparisonCard({ home, away }) {
  const rows = [
    { label: 'Victoires',       h: home.wins,             a: away.wins,             max: Math.max(home.played, away.played) },
    { label: 'Buts marqués',    h: home.goals_scored,     a: away.goals_scored,     max: Math.max(home.goals_scored, away.goals_scored) || 1 },
    { label: 'Buts encaissés',  h: home.goals_conceded,   a: away.goals_conceded,   max: Math.max(home.goals_conceded, away.goals_conceded) || 1, inverse: true },
    { label: 'Moy. buts/match', h: home.goals_scored_avg, a: away.goals_scored_avg, max: Math.max(home.goals_scored_avg, away.goals_scored_avg) || 1, dec: 1 },
    { label: 'Clean sheets',    h: home.clean_sheets,     a: away.clean_sheets,     max: Math.max(home.clean_sheets, away.clean_sheets) || 1 },
    { label: '% victoires',     h: home.win_pct,          a: away.win_pct,          max: 100, suffix: '%' },
  ]

  return (
    <StatCard title="COMPARAISON — 10 DERNIERS MATCHS">
      <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: '8px', marginBottom: '16px', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {home.crest_url && <img src={home.crest_url} alt="" width={22} height={22} style={{ objectFit: 'contain' }} onError={(e) => { e.target.style.display = 'none' }} />}
          <span style={{ fontFamily: 'var(--font-display)', fontSize: '13px', color: 'var(--accent-cyan)', letterSpacing: '0.03em' }}>{home.team_name}</span>
        </div>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '8px', color: 'var(--text-muted)', letterSpacing: '0.1em', textAlign: 'center' }}>VS</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', justifyContent: 'flex-end' }}>
          <span style={{ fontFamily: 'var(--font-display)', fontSize: '13px', color: '#ff6b35', letterSpacing: '0.03em', textAlign: 'right' }}>{away.team_name}</span>
          {away.crest_url && <img src={away.crest_url} alt="" width={22} height={22} style={{ objectFit: 'contain' }} onError={(e) => { e.target.style.display = 'none' }} />}
        </div>
      </div>

      {rows.map(({ label, h, a, max, dec, suffix, inverse }) => {
        const hVal   = dec ? h.toFixed(dec) : h
        const aVal   = dec ? a.toFixed(dec) : a
        const hPct   = Math.min((h / max) * 100, 100)
        const aPct   = Math.min((a / max) * 100, 100)
        const hColor = inverse ? (h <= a ? '#00ff88' : '#ff4455') : (h >= a ? '#00ff88' : '#ff4455')
        const aColor = inverse ? (a <= h ? '#00ff88' : '#ff4455') : (a >= h ? '#00ff88' : '#ff4455')

        return (
          <div key={label} style={{ marginBottom: '12px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: '8px', alignItems: 'center', marginBottom: '4px' }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', fontWeight: 700, color: hColor }}>{hVal}{suffix || ''}</span>
              <span className="stat-comparison-label" style={{ fontFamily: 'var(--font-mono)', fontSize: '8px', color: 'var(--text-muted)', letterSpacing: '0.08em', textAlign: 'center', minWidth: '80px' }}>{label}</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', fontWeight: 700, color: aColor, textAlign: 'right' }}>{aVal}{suffix || ''}</span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 4px 1fr', gap: '3px', alignItems: 'center' }}>
              <div style={{ height: '3px', background: 'var(--border)', borderRadius: '2px', overflow: 'hidden', display: 'flex', justifyContent: 'flex-end' }}>
                <div style={{ height: '100%', width: `${hPct}%`, background: hColor, borderRadius: '2px', boxShadow: `0 0 6px ${hColor}66` }} />
              </div>
              <div />
              <div style={{ height: '3px', background: 'var(--border)', borderRadius: '2px', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${aPct}%`, background: aColor, borderRadius: '2px', boxShadow: `0 0 6px ${aColor}66` }} />
              </div>
            </div>
          </div>
        )
      })}
    </StatCard>
  )
}

/* ── Forme récente ── */
function FormCard({ home, away }) {
  return (
    <StatCard title="FORME RÉCENTE — 5 DERNIERS MATCHS">
      <div className="two-col-stats" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {[{ stats: home }, { stats: away }].map(({ stats }, idx) => (
          <div key={idx}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
              {stats.crest_url && <img src={stats.crest_url} alt="" width={16} height={16} style={{ objectFit: 'contain' }} onError={(e) => { e.target.style.display = 'none' }} />}
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', color: 'var(--text-muted)', letterSpacing: '0.08em' }}>{stats.team_name}</span>
            </div>
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              {stats.form_5.map((r, i) => (
                <div key={i} style={{ width: '32px', height: '32px', borderRadius: '3px', background: `${RESULT_COLOR[r]}22`, border: `1px solid ${RESULT_COLOR[r]}`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', fontWeight: 700, color: RESULT_COLOR[r] }}>{r}</span>
                </div>
              ))}
              {stats.form_5.length === 0 && (
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-muted)' }}>—</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </StatCard>
  )
}

/* ── H2H ── */
function H2HCard({ h2h, homeStats, awayStats }) {
  if (h2h.total_played === 0) return (
    <StatCard title="CONFRONTATIONS DIRECTES">
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)' }}>Aucune confrontation directe en BDD.</span>
    </StatCard>
  )

  const total = h2h.total_played

  return (
    <StatCard title={`H2H — ${total} CONFRONTATIONS`}>
      <div style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', height: '8px', borderRadius: '4px', overflow: 'hidden', gap: '2px', marginBottom: '8px' }}>
          <div style={{ flex: h2h.home_wins, background: '#00ff88', minWidth: h2h.home_wins ? '4px' : 0 }} />
          <div style={{ flex: h2h.draws,     background: '#ffcc00', minWidth: h2h.draws     ? '4px' : 0 }} />
          <div style={{ flex: h2h.away_wins, background: '#ff6b35', minWidth: h2h.away_wins ? '4px' : 0 }} />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', textAlign: 'center' }}>
          <div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '18px', fontWeight: 700, color: '#00ff88' }}>{h2h.home_wins}</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '8px', color: 'var(--text-muted)', letterSpacing: '0.08em' }}>{homeStats.team_name}</div>
          </div>
          <div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '18px', fontWeight: 700, color: '#ffcc00' }}>{h2h.draws}</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '8px', color: 'var(--text-muted)', letterSpacing: '0.08em' }}>NULS</div>
          </div>
          <div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '18px', fontWeight: 700, color: '#ff6b35' }}>{h2h.away_wins}</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '8px', color: 'var(--text-muted)', letterSpacing: '0.08em' }}>{awayStats.team_name}</div>
          </div>
        </div>
      </div>

      {h2h.last_5.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '8px', color: 'var(--text-muted)', letterSpacing: '0.12em', marginBottom: '4px' }}>DERNIÈRES RENCONTRES</div>
          {h2h.last_5.map((m, i) => <MiniMatchRow key={i} match={m} />)}
        </div>
      )}
    </StatCard>
  )
}

/* ── Derniers matchs ── */
function Last5Card({ home, away }) {
  return (
    <StatCard title="DERNIERS MATCHS">
      <div className="two-col-stats" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
        {[{ stats: home }, { stats: away }].map(({ stats }, idx) => (
          <div key={idx}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
              {stats.crest_url && <img src={stats.crest_url} alt="" width={14} height={14} style={{ objectFit: 'contain' }} onError={(e) => { e.target.style.display = 'none' }} />}
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '8px', color: 'var(--text-muted)', letterSpacing: '0.08em' }}>{stats.team_name}</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
              {stats.last_5.map((m, i) => <MiniMatchRow key={i} match={m} />)}
            </div>
          </div>
        ))}
      </div>
    </StatCard>
  )
}

function MiniMatchRow({ match }) {
  const color = RESULT_COLOR[match.result] || 'var(--text-muted)'
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '5px 8px', background: 'var(--bg-elevated)', borderRadius: '2px', borderLeft: `2px solid ${color}` }}>
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '8px', color: 'var(--text-muted)', flexShrink: 0, width: '60px' }}>{match.date}</span>
      <span style={{ fontFamily: 'var(--font-display)', fontSize: '11px', color: 'var(--text-primary)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
        {match.home_team} {match.home_score}—{match.away_score} {match.away_team}
      </span>
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', fontWeight: 700, color, flexShrink: 0 }}>{match.result}</span>
    </div>
  )
}

/* ── Prédictions ── */
function PredictionSections({ prediction }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      <StatCard title="RÉSULTAT 1X2">
        <PredictionBar label="DOMICILE"  value={prediction.home_win_proba} delay={80}  barHeight={5} />
        <PredictionBar label="NUL"       value={prediction.draw_proba}     delay={180} barHeight={5} />
        <PredictionBar label="EXTÉRIEUR" value={prediction.away_win_proba} delay={280} barHeight={5} />
        {prediction.predicted_home_score != null && (
          <div style={{ marginTop: '14px', padding: '10px 14px', background: 'var(--bg-elevated)', borderRadius: '3px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', letterSpacing: '0.14em', color: 'var(--text-muted)' }}>SCORE PRÉDIT</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)' }}>
              {prediction.predicted_home_score?.toFixed(1)}&thinsp;—&thinsp;{prediction.predicted_away_score?.toFixed(1)}
            </span>
          </div>
        )}
      </StatCard>

      <StatCard title="OVER / UNDER">
        {[
          { label: 'OVER 0.5', value: prediction.over_05_proba },
          { label: 'OVER 1.5', value: prediction.over_15_proba },
          { label: 'OVER 2.5', value: prediction.over_25_proba },
          { label: 'OVER 3.5', value: prediction.over_35_proba },
          { label: 'OVER 4.5', value: prediction.over_45_proba },
        ].map(({ label, value }, i) => (
          <PredictionBar key={label} label={label} value={value} delay={80 + i * 100} />
        ))}
      </StatCard>

      <StatCard title="LES DEUX ÉQUIPES MARQUENT">
        <PredictionBar label="OUI" value={prediction.btts_proba}            delay={100} barHeight={6} />
        <PredictionBar label="NON" value={1 - (prediction.btts_proba ?? 0)} delay={200} barHeight={6} />
      </StatCard>

      <StatCard title="DOUBLE CHANCE">
        <PredictionBar label="1X — DOM. OU NUL" value={prediction.home_draw_proba} delay={100} />
        <PredictionBar label="X2 — EXT. OU NUL" value={prediction.away_draw_proba} delay={200} />
        <PredictionBar label="12 — DOM. OU EXT." value={prediction.home_away_proba} delay={300} />
      </StatCard>

      {prediction.top_scores?.length > 0 && (
        <StatCard title="SCORES EXACTS LES PLUS PROBABLES">
          {prediction.top_scores.slice(0, 5).map((s, i) => (
            <ExactScoreRow key={i} rank={i + 1} home={s.home} away={s.away} probability={s.proba} delay={100 + i * 80} />
          ))}
        </StatCard>
      )}

      {prediction.confidence_score != null && (
        <StatCard title="INDICE DE CONFIANCE">
          <ConfidenceGauge score={prediction.confidence_score} />
        </StatCard>
      )}

      {prediction.disclaimer && (
        <div style={{ padding: '12px 16px', border: '1px solid var(--border)', borderRadius: '3px', fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-muted)', lineHeight: 1.7 }}>
          ⚠ {prediction.disclaimer}
        </div>
      )}
    </div>
  )
}

/* ── Shared components ── */
function StatCard({ title, children }) {
  return (
    <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: '4px', padding: '20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
        <span style={{ color: 'var(--accent-green)', fontSize: '7px' }}>◆</span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', fontWeight: 600, letterSpacing: '0.16em', color: 'var(--text-muted)' }}>{title}</span>
      </div>
      {children}
    </div>
  )
}

function AnalyzeButton({ loading, onClick }) {
  return (
    <button onClick={onClick} disabled={loading} className="analyze-btn">
      {loading
        ? <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px' }}><span style={{ color: 'var(--accent-green)', animation: 'pulseGlow 1s infinite' }}>■ ■ ■</span> ANALYSE EN COURS...</span>
        : '⬡  ANALYSER CE MATCH'}
    </button>
  )
}

function ExactScoreRow({ rank, home, away, probability, delay }) {
  const [filled, setFilled] = useState(false)
  const pct = Math.round((probability ?? 0) * 100)
  useEffect(() => { const t = setTimeout(() => setFilled(true), delay); return () => clearTimeout(t) }, [delay])
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '10px' }}>
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-muted)', width: '18px' }}>#{rank}</span>
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', width: '44px' }}>{home}&thinsp;-&thinsp;{away}</span>
      <div style={{ flex: 1, height: '3px', background: 'var(--border)', borderRadius: '2px', overflow: 'hidden' }}>
        <div style={{ height: '100%', width: filled ? `${Math.min(pct * 5, 100)}%` : '0%', background: 'var(--accent-cyan)', borderRadius: '2px', transition: 'width 0.9s cubic-bezier(0.4,0,0.2,1)', boxShadow: '0 0 6px rgba(0,204,255,0.55)' }} />
      </div>
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '14px', fontWeight: 600, color: 'var(--accent-cyan)', minWidth: '40px', textAlign: 'right' }}>{pct}%</span>
    </div>
  )
}

function MiniLoader() {
  return (
    <div style={{ padding: '40px', textAlign: 'center', fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)', letterSpacing: '0.1em' }}>
      <span style={{ color: 'var(--accent-green)', animation: 'pulseGlow 1.4s infinite' }}>■ ■ ■</span>
    </div>
  )
}

function NoStats() {
  return (
    <div style={{ padding: '20px', fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)' }}>
      Stats non disponibles pour ce match.
    </div>
  )
}

function ErrorBanner({ message }) {
  return (
    <div style={{ marginTop: '14px', padding: '12px 16px', border: '1px solid rgba(255,68,85,0.3)', background: 'rgba(255,68,85,0.05)', borderRadius: '3px', fontFamily: 'var(--font-mono)', fontSize: '11px', color: '#ff5566' }}>
      ⚠ {message}
    </div>
  )
}

function PageLoader() {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '70vh', flexDirection: 'column', gap: '16px', fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-muted)', letterSpacing: '0.12em' }}>
      <span style={{ color: 'var(--accent-green)', fontSize: '20px', animation: 'pulseGlow 1.3s ease-in-out infinite' }}>■ ■ ■</span>
      CHARGEMENT...
    </div>
  )
}

function PageError({ message }) {
  return (
    <div style={{ maxWidth: '600px', margin: '80px auto', padding: '24px' }}>
      <Link to="/" className="back-link">← RETOUR</Link>
      <div style={{ padding: '18px', border: '1px solid rgba(255,68,85,0.3)', background: 'rgba(255,68,85,0.05)', borderRadius: '3px', fontFamily: 'var(--font-mono)', color: '#ff5566', fontSize: '12px' }}>
        ⚠ {message}
      </div>
    </div>
  )
}
