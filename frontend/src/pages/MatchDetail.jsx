import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  getMatch, getPrediction, getMatchOdds, getMatchLineups,
  getMatchStats, getMatchRawStats, generateSmartTicket
} from '../services/api'
import { fmtDateShort, STATUS_META } from '../utils'

/* ─── PALETTE GLOBALE (référence pour toute l'app) ───────────────────────────
   --accent-green  : #00ff88   actions primaires, victoire, safe
   --accent-amber  : #ffb000   avertissement, nul, danger
   --accent-cyan   : #00c8ff   équipe extérieure, info
   --accent-red    : #ff4455   défaite, rouge, erreur
   --text-primary  : blanc
   --text-secondary: gris clair
   --text-muted    : gris foncé
   --bg-surface    : fond carte
   --bg-elevated   : fond élément surélevé
   --border        : bordure standard
─────────────────────────────────────────────────────────────────────────────── */

const R = {
  green : 'var(--accent-green)',
  amber : '#ffb000',
  cyan  : 'var(--accent-cyan,#00c8ff)',
  red   : '#ff4455',
  muted : 'var(--text-muted)',
  sec   : 'var(--text-secondary)',
  pri   : 'var(--text-primary)',
}

const resultColor = r => r === 'W' ? R.green : r === 'D' ? R.amber : R.red
const resultBg    = r => r === 'W' ? 'rgba(0,255,136,0.12)' : r === 'D' ? 'rgba(255,176,0,0.12)' : 'rgba(255,68,85,0.12)'
const probColor   = p => p >= 60 ? R.green : p >= 45 ? R.amber : R.red

/* ─── COMPOSANT PRINCIPAL ───────────────────────────────────────────────────── */

export default function MatchDetail() {
  const { id } = useParams()
  const [match,     setMatch]     = useState(null)
  const [teamStats, setTeamStats] = useState(null)
  const [rawStats,  setRawStats]  = useState(null)
  const [odds,      setOdds]      = useState(null)
  const [loading,   setLoading]   = useState(true)
  const [error,     setError]     = useState(null)
  const [tab,       setTab]       = useState('overview')
  const [modal,     setModal]     = useState(null)
  const [pred,      setPred]      = useState(null)
  const [predLoad,  setPredLoad]  = useState(false)
  const [predErr,   setPredErr]   = useState(null)
  const [tickMode,  setTickMode]  = useState('single')
  const [ticket,    setTicket]    = useState(null)
  const [tickLoad,  setTickLoad]  = useState(false)
  const [tickErr,   setTickErr]   = useState(null)

  useEffect(() => {
    setLoading(true)
    setTab('overview')
    getMatch(id)
      .then(r => {
        setMatch(r.data)
        setLoading(false)
        Promise.all([
          getMatchStats(id).catch(() => null),
          getMatchRawStats(id).catch(() => null),
          getMatchOdds(id).catch(() => null),
        ]).then(([ts, rs, od]) => {
          if (ts?.data) setTeamStats(ts.data)
          if (rs?.data) setRawStats(rs.data)
          if (od?.data) setOdds(od.data)
        })
      })
      .catch(() => { setError('Match introuvable.'); setLoading(false) })
  }, [id])

  const openAnalyse = async () => {
    setModal('analyse')
    if (pred || predLoad) return
    setPredLoad(true); setPredErr(null)
    try { const r = await getPrediction(id); setPred(r.data) }
    catch (e) { setPredErr(e?.response?.data?.detail || 'Erreur lors de l\'analyse.') }
    setPredLoad(false)
  }

  const openTicket = () => { setModal('ticket'); setTicket(null); setTickErr(null) }

  const doTicket = async () => {
    setTickLoad(true); setTickErr(null)
    const modeMap = { single: 'simple', danger_single: 'hot' }
    try { const r = await generateSmartTicket([parseInt(id)], modeMap[tickMode] || 'simple'); setTicket(r.data) }
    catch (e) { setTickErr(e?.response?.data?.detail || 'Impossible de générer le ticket.') }
    setTickLoad(false)
  }

  if (loading) return <PageLoader />
  if (error)   return <PageError msg={error} />

  const home   = match.home_team
  const away   = match.away_team
  const isLive = ['IN_PLAY','PAUSED','HALFTIME'].includes(match.status)
  const isDone = match.status === 'FINISHED'
  const isSoon = ['SCHEDULED','TIMED'].includes(match.status)
  const meta   = STATUS_META?.[match.status] || { label: match.status, color: R.muted }

  const TABS_DONE = [
    { key: 'overview', label: 'STATISTIQUES' },
    { key: 'form',     label: 'FORME' },
  ]
  const TABS_SOON = [
    { key: 'overview', label: 'APERÇU' },
    { key: 'form',     label: 'FORME & STATS' },
    { key: 'h2h',      label: 'H2H' },
    { key: 'odds',     label: 'COTES' },
    { key: 'lineups',  label: 'COMPOSITIONS' },
  ]
  const TABS_LIVE = [
    { key: 'overview', label: 'EN DIRECT' },
    { key: 'form',     label: 'FORME' },
  ]
  const tabs = isDone ? TABS_DONE : isLive ? TABS_LIVE : TABS_SOON

  return (
    <div style={{ maxWidth: 960, margin: '0 auto', padding: '28px 20px' }}>

      {/* Breadcrumb */}
      <nav style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 }}>
        <Link to="/matches" style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: R.muted, letterSpacing: '0.1em', textDecoration: 'none' }}>← MATCHS</Link>
        <span style={{ color: 'var(--border)' }}>/</span>
        {match.competition?.crest_url && <img src={match.competition.crest_url} alt="" width={14} height={14} style={{ objectFit: 'contain' }} onError={e => e.target.style.display='none'} />}
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: R.muted }}>{match.competition?.name}</span>
      </nav>

      {/* ── HERO ── */}
      <div style={{
        background: 'var(--bg-surface)', borderRadius: 8, padding: '28px 24px', marginBottom: 16,
        border: `1px solid ${isLive ? 'rgba(0,255,136,0.35)' : 'var(--border)'}`,
        position: 'relative', overflow: 'hidden',
      }}>
        {isLive && <div style={{ position:'absolute', top:0, left:0, right:0, height:2, background:'linear-gradient(90deg,transparent,var(--accent-green),transparent)' }} />}

        {/* Meta */}
        <div style={{ textAlign: 'center', marginBottom: 20 }}>
          <span style={{ fontFamily:'var(--font-mono)', fontSize:9, fontWeight:700, letterSpacing:'0.12em', padding:'4px 14px', borderRadius:12, background:`${meta.color}18`, color:meta.color, border:`1px solid ${meta.color}30` }}>
            {isLive && <span style={{ marginRight:5, animation:'pulseGlow 1.4s infinite' }}>●</span>}
            {meta.label}
          </span>
          <div style={{ fontFamily:'var(--font-mono)', fontSize:10, color:R.muted, marginTop:6 }}>
            {fmtDateShort(match.match_date)}
            {match.venue   && <span> · {match.venue}</span>}
            {match.referee && <span> · {match.referee}</span>}
          </div>
          {(match.matchday || match.round) && (
            <div style={{ fontFamily:'var(--font-mono)', fontSize:9, color:R.muted, marginTop:2 }}>
              {match.matchday && `Journée ${match.matchday}`}{match.round && ` · ${match.round}`}
            </div>
          )}
        </div>

        {/* Score / VS */}
        <div style={{ display:'grid', gridTemplateColumns:'1fr auto 1fr', alignItems:'center', gap:16 }}>
          <TeamHero team={home} align="right" />
          <div style={{ textAlign:'center', minWidth:120 }}>
            {isDone || isLive ? (
              <>
                <div style={{ fontFamily:'var(--font-display)', fontSize:58, fontWeight:700, color:R.pri, lineHeight:1, letterSpacing:'0.04em' }}>
                  {match.home_score ?? 0}<span style={{ color:'var(--border)', margin:'0 6px', fontSize:40 }}>—</span>{match.away_score ?? 0}
                </div>
                {isLive && <div style={{ fontFamily:'var(--font-mono)', fontSize:8, color:R.green, marginTop:4, animation:'pulseGlow 1.4s infinite', letterSpacing:'0.1em' }}>EN DIRECT</div>}
                {isDone && <div style={{ fontFamily:'var(--font-mono)', fontSize:8, color:R.muted, marginTop:4, letterSpacing:'0.1em' }}>SCORE FINAL</div>}
              </>
            ) : (
              <div style={{ fontFamily:'var(--font-mono)', fontSize:14, color:R.muted, letterSpacing:'0.2em' }}>VS</div>
            )}
          </div>
          <TeamHero team={away} align="left" />
        </div>

        {/* Boutons — match à venir uniquement */}
        {isSoon && (
          <div style={{ display:'flex', gap:10, justifyContent:'center', marginTop:24, flexWrap:'wrap' }}>
            <Btn onClick={openAnalyse} variant="primary">ANALYSER LE MATCH</Btn>
            <Btn onClick={openTicket}  variant="ghost">SMART TICKET</Btn>
          </div>
        )}
      </div>

      {/* ── TABS ── */}
      <div style={{ display:'flex', gap:2, borderBottom:'1px solid var(--border)', marginBottom:16, overflowX:'auto' }}>
        {tabs.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)} style={{
            padding:'9px 18px', background:'transparent', border:'none', cursor:'pointer',
            borderBottom: tab===t.key ? `2px solid ${R.green}` : '2px solid transparent',
            color: tab===t.key ? R.green : R.muted,
            fontFamily:'var(--font-mono)', fontSize:9, fontWeight:600, letterSpacing:'0.12em',
            marginBottom:-1, transition:'all 0.15s', whiteSpace:'nowrap',
          }}>{t.label}</button>
        ))}
      </div>

      {/* ── CONTENU ── */}
      {isDone && tab==='overview' && <StatsTab rawStats={rawStats} home={home} away={away} />}
      {isDone && tab==='form'     && <FormAfterTab teamStats={teamStats} home={home} away={away} />}

      {isLive && tab==='overview' && <StatsTab rawStats={rawStats} home={home} away={away} live />}
      {isLive && tab==='form'     && <FormAfterTab teamStats={teamStats} home={home} away={away} />}

      {isSoon && tab==='overview' && <UpcomingOverview teamStats={teamStats} home={home} away={away} />}
      {isSoon && tab==='form'     && <UpcomingForm teamStats={teamStats} home={home} away={away} />}
      {isSoon && tab==='h2h'      && <H2HTab teamStats={teamStats} home={home} away={away} />}
      {isSoon && tab==='odds'     && <OddsTab odds={odds} home={home} away={away} />}
      {isSoon && tab==='lineups'  && <Empty msg="Compositions non disponibles avant le match." />}

      {/* ── MODALS ── */}
      {modal==='analyse' && (
        <Modal onClose={() => setModal(null)} title="ANALYSE DU MATCH">
          {predLoad && <ModalSkel />}
          {predErr  && <Err msg={predErr} />}
          {pred && !predLoad && <AnalyseContent pred={pred} home={home} away={away} />}
        </Modal>
      )}

      {modal==='ticket' && (
        <Modal onClose={() => setModal(null)} title="SMART TICKET">
          <TicketPanel
            mode={tickMode} setMode={setTickMode}
            onGenerate={doTicket} loading={tickLoad}
            ticket={ticket} error={tickErr}
          />
        </Modal>
      )}
    </div>
  )
}

/* ═══════════════════════════════════════════════════════════════
   TABS — MATCH TERMINÉ / LIVE
═══════════════════════════════════════════════════════════════ */

function StatsTab({ rawStats, home, away, live }) {
  const stats = rawStats?.stats || []
  const hs = stats.find(s => s.side === 'HOME')
  const as = stats.find(s => s.side === 'AWAY')

  if (!hs && !as) return <Empty msg={live ? 'Statistiques live en cours de chargement...' : 'Les statistiques détaillées de ce match ne sont pas encore disponibles. Elles sont importées progressivement pour les matchs récents (API Football).'} />

  const SECTIONS = [
    {
      title: 'ATTAQUE',
      rows: [
        { key:'shots_total',    label:'Tirs totaux'        },
        { key:'shots_on_goal',  label:'Tirs cadrés'        },
        { key:'shots_off_goal', label:'Tirs non cadrés'    },
        { key:'shots_blocked',  label:'Tirs bloqués'       },
        { key:'corner_kicks',   label:'Corners'            },
        { key:'expected_goals', label:'xG (buts attendus)', dec:2 },
      ]
    },
    {
      title: 'POSSESSION & CONSTRUCTION',
      rows: [
        { key:'ball_possession',  label:'Possession',        unit:'%' },
        { key:'passes_total',     label:'Passes totales'              },
        { key:'passes_accurate',  label:'Passes réussies'             },
        { key:'passes_pct',       label:'Précision passes',  unit:'%' },
      ]
    },
    {
      title: 'DÉFENSE & DISCIPLINE',
      rows: [
        { key:'goalkeeper_saves', label:'Arrêts du gardien' },
        { key:'fouls',            label:'Fautes'            },
        { key:'offsides',         label:'Hors-jeux'         },
        { key:'yellow_cards',     label:'Cartons jaunes'    },
        { key:'red_cards',        label:'Cartons rouges'    },
      ]
    },
  ]

  return (
    <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
      {/* Header équipes sticky */}
      <div style={{ display:'grid', gridTemplateColumns:'1fr 180px 1fr', alignItems:'center', gap:8, padding:'10px 16px', background:'var(--bg-elevated)', borderRadius:6, border:'1px solid var(--border)', position:'sticky', top:0, zIndex:10 }}>
        <TeamPill team={home} color={R.green} />
        <span style={{ fontFamily:'var(--font-mono)', fontSize:8, color:R.muted, textAlign:'center', letterSpacing:'0.1em' }}>STAT</span>
        <TeamPill team={away} color={R.cyan} right />
      </div>

      {SECTIONS.map(sec => {
        const rows = sec.rows.filter(r => {
          const hv = hs?.[r.key]; const av = as?.[r.key]
          return hv != null || av != null
        })
        if (!rows.length) return null
        return (
          <div key={sec.title} style={{ background:'var(--bg-surface)', border:'1px solid var(--border)', borderRadius:6, overflow:'hidden' }}>
            <div style={{ padding:'8px 16px', background:'var(--bg-elevated)', borderBottom:'1px solid var(--border)' }}>
              <span style={{ fontFamily:'var(--font-mono)', fontSize:8, letterSpacing:'0.15em', color:R.muted }}>{sec.title}</span>
            </div>
            {rows.map((r, i) => {
              const hv   = hs?.[r.key] ?? null
              const av   = as?.[r.key] ?? null
              const hNum = parseFloat(hv) || 0
              const aNum = parseFloat(av) || 0
              const tot  = hNum + aNum
              const hPct = tot > 0 ? (hNum / tot) * 100 : 50
              const fmt  = v => v == null ? '—' : r.dec ? parseFloat(v).toFixed(r.dec) : r.unit === '%' ? `${v}%` : v
              const hBetter = hNum > aNum
              const aBetter = aNum > hNum

              return (
                <div key={r.key} style={{ padding:'10px 16px', borderBottom: i<rows.length-1 ? '1px solid var(--border)' : 'none' }}>
                  <div style={{ display:'grid', gridTemplateColumns:'1fr 180px 1fr', alignItems:'center', gap:8, marginBottom:6 }}>
                    <span style={{ fontFamily:'var(--font-display)', fontSize:17, fontWeight:700, color: hBetter ? R.green : R.pri }}>
                      {fmt(hv)}
                    </span>
                    <span style={{ fontFamily:'var(--font-mono)', fontSize:8, color:R.muted, textAlign:'center', letterSpacing:'0.06em' }}>{r.label}</span>
                    <span style={{ fontFamily:'var(--font-display)', fontSize:17, fontWeight:700, textAlign:'right', color: aBetter ? R.cyan : R.pri }}>
                      {fmt(av)}
                    </span>
                  </div>
                  {tot > 0 && (
                    <div style={{ height:3, background:'var(--bg-elevated)', borderRadius:2, overflow:'hidden' }}>
                      <div style={{ height:'100%', display:'flex' }}>
                        <div style={{ width:`${hPct}%`, background: hBetter ? R.green : 'var(--border)', transition:'width 0.5s' }} />
                        <div style={{ flex:1, background: aBetter ? R.cyan : 'var(--border)' }} />
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )
      })}

      <InfoBox>
        Les statistiques avancées (xA, duels, distance, pressing) seront disponibles dans une prochaine mise à jour.
      </InfoBox>
    </div>
  )
}

function FormAfterTab({ teamStats, home, away }) {
  const hs = teamStats?.home_stats
  const as = teamStats?.away_stats
  if (!hs && !as) return <Empty msg="Forme des équipes non disponible." />
  return (
    <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12 }}>
      {[{ s:hs, team:home }, { s:as, team:away }].map(({ s, team }) =>
        s ? <MiniTeamCard key={team?.id} stats={s} team={team} /> : null
      )}
    </div>
  )
}

/* ═══════════════════════════════════════════════════════════════
   TABS — MATCH À VENIR
═══════════════════════════════════════════════════════════════ */

function UpcomingOverview({ teamStats, home, away }) {
  const hs = teamStats?.home_stats
  const as = teamStats?.away_stats
  if (!hs && !as) return <Empty msg="Statistiques en cours de chargement..." />

  return (
    <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
      {/* Cartes stats côte à côte */}
      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12 }}>
        {hs && <TeamFullCard stats={hs} team={home} side="DOMICILE" color={R.green} />}
        {as && <TeamFullCard stats={as} team={away} side="EXTÉRIEUR" color={R.cyan} />}
      </div>
      {/* Comparaison métriques clés */}
      {hs && as && <DirectComparison hs={hs} as={as} home={home} away={away} />}
    </div>
  )
}

function TeamFullCard({ stats: s, team, side, color }) {
  return (
    <div style={{ background:'var(--bg-surface)', border:`1px solid var(--border)`, borderRadius:6, padding:16, borderTop:`3px solid ${color}` }}>
      {/* Header */}
      <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:14 }}>
        {team?.crest_url && <img src={team.crest_url} alt="" width={28} height={28} style={{ objectFit:'contain' }} onError={e=>e.target.style.display='none'} />}
        <div>
          <div style={{ fontFamily:'var(--font-display)', fontSize:14, color:R.pri }}>{team?.name}</div>
          <div style={{ fontFamily:'var(--font-mono)', fontSize:7, color, letterSpacing:'0.12em' }}>{side}</div>
        </div>
      </div>

      {/* Forme 5 */}
      <MicroLabel>FORME RÉCENTE</MicroLabel>
      <div style={{ display:'flex', gap:4, margin:'6px 0 14px' }}>
        {(s.form_5 || []).map((r, i) => (
          <div key={i} style={{ width:28, height:28, borderRadius:4, display:'flex', alignItems:'center', justifyContent:'center', background:resultBg(r), fontFamily:'var(--font-mono)', fontSize:11, fontWeight:700, color:resultColor(r) }}>{r}</div>
        ))}
      </div>

      {/* Stats clés */}
      <MicroLabel>PERFORMANCE GÉNÉRALE</MicroLabel>
      <div style={{ marginTop:8, display:'flex', flexDirection:'column', gap:0 }}>
        {[
          { label:'V / N / D',           value:`${s.wins} / ${s.draws} / ${s.losses}` },
          { label:'Matchs joués',         value:s.played },
          { label:'Buts marqués/match',   value:s.goals_scored_avg, color: s.goals_scored_avg >= 1.5 ? R.green : R.sec },
          { label:'Buts encaissés/match', value:s.goals_conceded_avg, color: s.goals_conceded_avg <= 1 ? R.green : s.goals_conceded_avg >= 2 ? R.red : R.amber },
          { label:'Clean sheets',         value:s.clean_sheets },
          { label:'% victoires',          value:`${s.win_pct}%`, color: s.win_pct >= 50 ? R.green : s.win_pct >= 35 ? R.amber : R.red },
        ].map(({ label, value, color: c }, i, arr) => (
          <div key={label} style={{ display:'flex', justifyContent:'space-between', alignItems:'center', padding:'7px 0', borderBottom: i<arr.length-1 ? '1px solid var(--border)' : 'none' }}>
            <span style={{ fontFamily:'var(--font-mono)', fontSize:9, color:R.muted }}>{label}</span>
            <span style={{ fontFamily:'var(--font-display)', fontSize:15, color: c || R.pri, fontWeight:600 }}>{value ?? '—'}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function DirectComparison({ hs, as, home, away }) {
  const metrics = [
    { label:'BUTS / MATCH',        hv:hs.goals_scored_avg,   av:as.goals_scored_avg,   higher:true  },
    { label:'ENCAISSÉS / MATCH',   hv:hs.goals_conceded_avg, av:as.goals_conceded_avg, higher:false },
    { label:'% VICTOIRES',         hv:hs.win_pct,            av:as.win_pct,            higher:true  },
    { label:'CLEAN SHEETS',        hv:hs.clean_sheets,       av:as.clean_sheets,       higher:true  },
  ]
  return (
    <div style={{ background:'var(--bg-surface)', border:'1px solid var(--border)', borderRadius:6, padding:'16px 20px' }}>
      <MicroLabel>COMPARAISON DIRECTE</MicroLabel>
      <div style={{ marginTop:14, display:'flex', flexDirection:'column', gap:14 }}>
        {metrics.map(({ label, hv, av, higher }) => {
          const hNum = parseFloat(hv)||0, aNum = parseFloat(av)||0
          const tot  = hNum+aNum
          const hPct = tot > 0 ? (hNum/tot)*100 : 50
          const hW   = higher ? hNum>aNum : hNum<aNum
          const aW   = higher ? aNum>hNum : aNum<hNum
          return (
            <div key={label}>
              <div style={{ display:'grid', gridTemplateColumns:'1fr auto 1fr', alignItems:'center', gap:12, marginBottom:6 }}>
                <span style={{ fontFamily:'var(--font-display)', fontSize:18, color:hW?R.green:R.sec, fontWeight:hW?700:400 }}>{hv??'—'}</span>
                <span style={{ fontFamily:'var(--font-mono)', fontSize:8, color:R.muted, letterSpacing:'0.1em', whiteSpace:'nowrap' }}>{label}</span>
                <span style={{ fontFamily:'var(--font-display)', fontSize:18, color:aW?R.cyan:R.sec, fontWeight:aW?700:400, textAlign:'right' }}>{av??'—'}</span>
              </div>
              {tot > 0 && (
                <div style={{ height:4, background:'var(--bg-elevated)', borderRadius:2, overflow:'hidden' }}>
                  <div style={{ height:'100%', display:'flex' }}>
                    <div style={{ width:`${hPct}%`, background:hW?R.green:'var(--border)', transition:'width 0.5s' }} />
                    <div style={{ flex:1, background:aW?R.cyan:'var(--border)' }} />
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

function UpcomingForm({ teamStats, home, away }) {
  const hs = teamStats?.home_stats
  const as = teamStats?.away_stats
  if (!hs && !as) return <Empty msg="Données de forme non disponibles." />
  return (
    <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
      {[{ s:hs, team:home }, { s:as, team:away }].map(({ s, team }) =>
        s ? <Last5Card key={team?.id} stats={s} team={team} /> : null
      )}
    </div>
  )
}

function Last5Card({ stats: s, team }) {
  return (
    <div style={{ background:'var(--bg-surface)', border:'1px solid var(--border)', borderRadius:6, padding:20 }}>
      {/* Header équipe */}
      <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:16 }}>
        {team?.crest_url && <img src={team.crest_url} alt="" width={24} height={24} style={{ objectFit:'contain' }} onError={e=>e.target.style.display='none'} />}
        <span style={{ fontFamily:'var(--font-display)', fontSize:16, color:R.pri }}>{team?.name}</span>
      </div>

      {/* Forme */}
      <MicroLabel>FORME (5 DERNIERS MATCHS)</MicroLabel>
      <div style={{ display:'flex', gap:6, margin:'8px 0 18px' }}>
        {(s.form_5||[]).map((r,i) => (
          <div key={i} style={{ width:32, height:32, borderRadius:4, display:'flex', alignItems:'center', justifyContent:'center', background:resultBg(r), border:`1px solid ${resultColor(r)}40`, fontFamily:'var(--font-mono)', fontSize:12, fontWeight:700, color:resultColor(r) }}>{r}</div>
        ))}
      </div>

      {/* Détail 5 derniers matchs */}
      <MicroLabel>DÉTAIL DES MATCHS</MicroLabel>
      <div style={{ display:'flex', flexDirection:'column', gap:4, marginTop:8 }}>
        {(s.last_5||[]).map((m,i) => (
          <div key={i} style={{ display:'grid', gridTemplateColumns:'64px 1fr auto 1fr 28px 48px', alignItems:'center', gap:8, padding:'7px 10px', background:'var(--bg-elevated)', borderRadius:3 }}>
            <span style={{ fontFamily:'var(--font-mono)', fontSize:8, color:R.muted }}>{m.date}</span>
            <span style={{ fontFamily:'var(--font-display)', fontSize:11, color:R.sec, textAlign:'right', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{m.home_team}</span>
            <span style={{ fontFamily:'var(--font-mono)', fontSize:13, fontWeight:700, color:R.pri, textAlign:'center', whiteSpace:'nowrap' }}>{m.home_score}—{m.away_score}</span>
            <span style={{ fontFamily:'var(--font-display)', fontSize:11, color:R.sec, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{m.away_team}</span>
            <div style={{ width:22, height:22, borderRadius:3, display:'flex', alignItems:'center', justifyContent:'center', background:resultBg(m.result), fontFamily:'var(--font-mono)', fontSize:9, fontWeight:700, color:resultColor(m.result) }}>{m.result}</div>
            <span style={{ fontFamily:'var(--font-mono)', fontSize:7, color:R.muted, textAlign:'right', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{m.competition}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function H2HTab({ teamStats, home, away }) {
  const h2h = teamStats?.h2h?.last_5 || []
  const h2hMeta = teamStats?.h2h || {}
  if (!h2h.length) return <Empty msg="Pas de confrontations directes disponibles." />

  const homeW = h2hMeta.home_wins ?? h2h.filter(m => m.result==='W').length
  const draws = h2hMeta.draws ?? h2h.filter(m => m.result==='D').length
  const awayW = h2hMeta.away_wins ?? h2h.filter(m => m.result==='L').length
  const totalGoals = h2h.reduce((acc,m) => acc + (m.home_score||0) + (m.away_score||0), 0)
  const avgGoals   = (totalGoals / h2h.length).toFixed(1)
  const btts       = h2h.filter(m => m.home_score>0 && m.away_score>0).length
  const over25     = h2h.filter(m => (m.home_score+m.away_score) > 2).length

  return (
    <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
      {/* Bilan */}
      <div style={{ background:'var(--bg-surface)', border:'1px solid var(--border)', borderRadius:6, padding:'18px 20px' }}>
        <MicroLabel>BILAN DES CONFRONTATIONS</MicroLabel>
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:10, marginTop:12 }}>
          {[
            { label: home?.short_name||home?.name, value:homeW, color:R.green },
            { label: 'Nuls',                        value:draws, color:R.amber },
            { label: away?.short_name||away?.name,  value:awayW, color:R.cyan  },
          ].map(({ label, value, color }) => (
            <div key={label} style={{ textAlign:'center', padding:'14px 10px', background:'var(--bg-elevated)', borderRadius:4 }}>
              <div style={{ fontFamily:'var(--font-display)', fontSize:36, color, lineHeight:1 }}>{value}</div>
              <div style={{ fontFamily:'var(--font-mono)', fontSize:8, color:R.muted, marginTop:4, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{label}</div>
            </div>
          ))}
        </div>
        {/* Stats H2H */}
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:10, marginTop:10 }}>
          {[
            { label:'MOY. BUTS/MATCH', value:avgGoals },
            { label:`BTTS (${h2h.length} matchs)`, value:`${btts}/${h2h.length}` },
            { label:'OVER 2.5',        value:`${over25}/${h2h.length}` },
          ].map(({ label, value }) => (
            <div key={label} style={{ textAlign:'center', padding:'10px', background:'var(--bg-elevated)', borderRadius:4 }}>
              <div style={{ fontFamily:'var(--font-display)', fontSize:20, color:R.pri }}>{value}</div>
              <div style={{ fontFamily:'var(--font-mono)', fontSize:7, color:R.muted, marginTop:3, letterSpacing:'0.08em' }}>{label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Historique */}
      <div style={{ background:'var(--bg-surface)', border:'1px solid var(--border)', borderRadius:6, padding:'18px 20px' }}>
        <MicroLabel>HISTORIQUE</MicroLabel>
        <div style={{ display:'flex', flexDirection:'column', gap:4, marginTop:10 }}>
          {h2h.map((m,i) => (
            <div key={i} style={{ display:'grid', gridTemplateColumns:'64px 1fr auto 1fr 28px 48px', alignItems:'center', gap:8, padding:'7px 10px', background:'var(--bg-elevated)', borderRadius:3 }}>
              <span style={{ fontFamily:'var(--font-mono)', fontSize:8, color:R.muted }}>{m.date}</span>
              <span style={{ fontFamily:'var(--font-display)', fontSize:11, color:R.sec, textAlign:'right', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{m.home_team}</span>
              <span style={{ fontFamily:'var(--font-mono)', fontSize:13, fontWeight:700, color:R.pri, textAlign:'center', whiteSpace:'nowrap' }}>{m.home_score}—{m.away_score}</span>
              <span style={{ fontFamily:'var(--font-display)', fontSize:11, color:R.sec, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{m.away_team}</span>
              <div style={{ width:22, height:22, borderRadius:3, display:'flex', alignItems:'center', justifyContent:'center', background:resultBg(m.result), fontFamily:'var(--font-mono)', fontSize:9, fontWeight:700, color:resultColor(m.result) }}>{m.result}</div>
              <span style={{ fontFamily:'var(--font-mono)', fontSize:7, color:R.muted, textAlign:'right', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{m.competition}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function OddsTab({ odds, home, away }) {
  const arr = odds?.odds || []
  if (!arr.length) return <Empty msg="Aucune cote disponible pour ce match." />
  return (
    <div style={{ display:'flex', flexDirection:'column', gap:8 }}>
      <div style={{ display:'grid', gridTemplateColumns:'1fr repeat(3,80px)', gap:8, padding:'6px 14px' }}>
        <span style={{ fontFamily:'var(--font-mono)', fontSize:8, color:R.muted, letterSpacing:'0.1em' }}>BOOKMAKER</span>
        {[home?.short_name||'1','NUL',away?.short_name||'2'].map(l => (
          <span key={l} style={{ fontFamily:'var(--font-mono)', fontSize:8, color:R.muted, textAlign:'center', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{l}</span>
        ))}
      </div>
      {arr.map((o,i) => (
        <div key={i} style={{ display:'grid', gridTemplateColumns:'1fr repeat(3,80px)', gap:8, padding:'12px 14px', background:'var(--bg-surface)', border:'1px solid var(--border)', borderRadius:4, alignItems:'center' }}>
          <span style={{ fontFamily:'var(--font-mono)', fontSize:11, color:R.pri }}>{o.bookmaker||`Bookmaker ${i+1}`}</span>
          {[o.home_win, o.draw, o.away_win].map((v,j) => (
            <span key={j} style={{ fontFamily:'var(--font-display)', fontSize:16, fontWeight:600, color:R.sec, textAlign:'center' }}>{v?.toFixed(2)??'—'}</span>
          ))}
        </div>
      ))}
    </div>
  )
}

/* ═══════════════════════════════════════════════════════════════
   MODAL ANALYSE
═══════════════════════════════════════════════════════════════ */

function AnalyseContent({ pred, home, away }) {
  const homeP = Math.round((pred.home_win_proba||0)*100)
  const drawP = Math.round((pred.draw_proba||0)*100)
  const awayP = Math.round((pred.away_win_proba||0)*100)
  const best  = homeP>=awayP && homeP>=drawP ? 'home' : awayP>=homeP && awayP>=drawP ? 'away' : 'draw'
  const bestLabel = best==='home' ? (home?.short_name||home?.name) : best==='away' ? (away?.short_name||away?.name) : 'Match nul'
  const bestP = best==='home' ? homeP : best==='away' ? awayP : drawP

  return (
    <div style={{ display:'flex', flexDirection:'column', gap:14 }}>
      {/* Pronostic principal */}
      <div style={{ background:'rgba(0,255,136,0.05)', border:'1px solid rgba(0,255,136,0.2)', borderRadius:6, padding:'14px 18px', display:'flex', justifyContent:'space-between', alignItems:'center', flexWrap:'wrap', gap:12 }}>
        <div>
          <MicroLabel>NOTRE PRONOSTIC</MicroLabel>
          <div style={{ fontFamily:'var(--font-display)', fontSize:22, color:R.pri, marginTop:6 }}>{bestLabel}</div>
          <div style={{ fontFamily:'var(--font-mono)', fontSize:10, color:R.muted, marginTop:3 }}>{bestP}% de probabilité</div>
        </div>
        <ConfBadge score={pred.confidence_score} />
      </div>

      {/* Score prédit */}
      {pred.predicted_home_score != null && (
        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', padding:'12px 18px', background:'var(--bg-elevated)', border:'1px solid var(--border)', borderRadius:6 }}>
          <div>
            <MicroLabel>SCORE LE PLUS PROBABLE</MicroLabel>
            <div style={{ fontFamily:'var(--font-display)', fontSize:26, color:R.pri, marginTop:4 }}>
              {Math.round(pred.predicted_home_score)} — {Math.round(pred.predicted_away_score)}
            </div>
          </div>
          {pred.exact_score_proba != null && (
            <div style={{ textAlign:'right' }}>
              <div style={{ fontFamily:'var(--font-display)', fontSize:18, color:R.amber }}>{Math.round(pred.exact_score_proba*100)}%</div>
              <div style={{ fontFamily:'var(--font-mono)', fontSize:8, color:R.muted }}>de chances</div>
            </div>
          )}
        </div>
      )}

      {/* 1X2 */}
      <div style={{ background:'var(--bg-elevated)', border:'1px solid var(--border)', borderRadius:6, padding:'14px 18px' }}>
        <MicroLabel>RÉSULTAT FINAL (1X2)</MicroLabel>
        <div style={{ marginTop:12 }}>
          <ProbBar label={home?.short_name||home?.name||'Domicile'} value={homeP} color={R.green} best={best==='home'} />
          <ProbBar label="Match nul"                                  value={drawP} color={R.amber} best={best==='draw'} />
          <ProbBar label={away?.short_name||away?.name||'Extérieur'}  value={awayP} color={R.cyan}  best={best==='away'} />
        </div>
      </div>

      {/* Marchés supplémentaires */}
      <div style={{ background:'var(--bg-elevated)', border:'1px solid var(--border)', borderRadius:6, padding:'14px 18px' }}>
        <MicroLabel>MARCHÉS SUPPLÉMENTAIRES</MicroLabel>
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:6, marginTop:10 }}>
          {[
            { label:'Les deux marquent (BTTS)', value:Math.round((pred.btts_proba||0)*100)      },
            { label:'Plus de 1.5 buts',          value:Math.round((pred.over_15_proba||0)*100)  },
            { label:'Plus de 2.5 buts',          value:Math.round((pred.over_25_proba||0)*100)  },
            { label:'Plus de 3.5 buts',          value:Math.round((pred.over_35_proba||0)*100)  },
            { label:'Chance double 1X',          value:Math.round((pred.home_draw_proba||0)*100)},
            { label:'Chance double X2',          value:Math.round((pred.away_draw_proba||0)*100)},
            { label:'Chance double 12',          value:Math.round((pred.home_away_proba||0)*100)},
          ].map(({ label, value }) => (
            <div key={label} style={{ display:'flex', justifyContent:'space-between', alignItems:'center', padding:'7px 10px', background:'var(--bg-surface)', borderRadius:3, border:'1px solid var(--border)' }}>
              <span style={{ fontFamily:'var(--font-mono)', fontSize:9, color:R.muted }}>{label}</span>
              <span style={{ fontFamily:'var(--font-display)', fontSize:15, color:probColor(value), fontWeight:700 }}>{value}%</span>
            </div>
          ))}
        </div>
      </div>

      {pred.disclaimer && (
        <div style={{ fontFamily:'var(--font-mono)', fontSize:8, color:R.muted, lineHeight:1.6, padding:'8px 10px', background:'var(--bg-elevated)', borderRadius:4 }}>
          {pred.disclaimer}
        </div>
      )}
    </div>
  )
}

/* ═══════════════════════════════════════════════════════════════
   MODAL SMART TICKET — Paris simples uniquement (1 match)
   Vert = safe (≥60%), Orange/Ambre = danger (35-59%)
═══════════════════════════════════════════════════════════════ */

function TicketPanel({ mode, setMode, onGenerate, loading, ticket, error }) {
  const MODES = [
    {
      key:   'single',
      label: 'SIMPLE SAFE',
      desc:  'Pari à plus haute probabilité · ≥ 60%',
      color: R.green,
      bg:    'rgba(0,255,136,0.08)',
      border:'rgba(0,255,136,0.35)',
    },
    {
      key:   'danger_single',
      label: 'SIMPLE DANGER',
      desc:  'Pari risqué mais rentable · 35–59%',
      color: R.amber,
      bg:    'rgba(255,176,0,0.08)',
      border:'rgba(255,176,0,0.35)',
    },
  ]

  const active = MODES.find(m => m.key === mode)

  return (
    <div style={{ display:'flex', flexDirection:'column', gap:14 }}>
      <MicroLabel>TYPE DE PARI</MicroLabel>
      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:8, marginTop:4 }}>
        {MODES.map(m => (
          <div key={m.key} onClick={() => setMode(m.key)} style={{
            padding:'12px 14px', borderRadius:5, cursor:'pointer', transition:'all 0.15s',
            background: mode===m.key ? m.bg : 'var(--bg-elevated)',
            border: `1px solid ${mode===m.key ? m.border : 'var(--border)'}`,
            outline: mode===m.key ? `1px solid ${m.border}` : 'none',
          }}>
            <div style={{ fontFamily:'var(--font-mono)', fontSize:10, fontWeight:700, color: mode===m.key ? m.color : R.sec, marginBottom:4 }}>{m.label}</div>
            <div style={{ fontFamily:'var(--font-mono)', fontSize:8, color:R.muted }}>{m.desc}</div>
          </div>
        ))}
      </div>

      <InfoBox color={active?.color}>
        {mode==='single'
          ? 'Le pari avec la probabilité la plus élevée (≥ 60%) est sélectionné.'
          : 'Un pari à haut ratio mais avec plus de risque (35–59%). Mise réduite recommandée.'}
      </InfoBox>

      {error  && <Err msg={error} />}
      {ticket && <TicketResult ticket={ticket} />}

      <button onClick={onGenerate} disabled={loading} style={{
        width:'100%', padding:13, borderRadius:4, border:'none', cursor: loading ? 'not-allowed' : 'pointer',
        background: mode==='single' ? R.green : R.amber,
        color: '#06060e', fontFamily:'var(--font-mono)', fontSize:11, fontWeight:700, letterSpacing:'0.14em',
        opacity: loading ? 0.7 : 1, transition:'all 0.2s',
        boxShadow: loading ? 'none' : `0 0 20px ${mode==='single' ? 'rgba(0,255,136,0.2)' : 'rgba(255,176,0,0.2)'}`,
      }}>
        {loading ? 'GÉNÉRATION...' : 'GÉNÉRER LE TICKET'}
      </button>
    </div>
  )
}

function TicketResult({ ticket }) {
  return (
    <div style={{ background:'rgba(0,255,136,0.05)', border:'1px solid rgba(0,255,136,0.25)', borderRadius:6, padding:14 }}>
      <MicroLabel>TICKET GÉNÉRÉ</MicroLabel>
      <div style={{ marginTop:10, display:'flex', flexDirection:'column', gap:4 }}>
        {(ticket.selections||[]).map((s,i) => (
          <div key={i} style={{ display:'flex', justifyContent:'space-between', alignItems:'center', padding:'8px 0', borderBottom: i<ticket.selections.length-1 ? '1px solid var(--border)' : 'none' }}>
            <span style={{ fontFamily:'var(--font-mono)', fontSize:10, color:R.pri }}>{s.label}</span>
            <span style={{ fontFamily:'var(--font-display)', fontSize:14, color:probColor(Math.round((s.probability||0)*100)), fontWeight:700 }}>{Math.round((s.probability||0)*100)}%</span>
          </div>
        ))}
      </div>
      {ticket.combined_proba != null && (
        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginTop:10, paddingTop:10, borderTop:'1px solid var(--border)' }}>
          <span style={{ fontFamily:'var(--font-mono)', fontSize:9, color:R.muted, letterSpacing:'0.1em' }}>PROBABILITÉ</span>
          <span style={{ fontFamily:'var(--font-display)', fontSize:22, color:R.green }}>{Math.round((ticket.combined_proba||0)*100)}%</span>
        </div>
      )}
      {ticket.correlated_warning && (
        <div style={{ marginTop:8, fontFamily:'var(--font-mono)', fontSize:8, color:R.amber, padding:'6px 8px', background:'rgba(255,176,0,0.08)', borderRadius:3 }}>
          {ticket.correlated_warning}
        </div>
      )}
    </div>
  )
}

/* ═══════════════════════════════════════════════════════════════
   COMPOSANTS ATOMIQUES
═══════════════════════════════════════════════════════════════ */

function TeamHero({ team, align }) {
  if (!team) return <div />
  const r = align==='right'
  return (
    <div style={{ display:'flex', flexDirection:'column', alignItems: r?'flex-end':'flex-start', gap:8 }}>
      {team.crest_url && <img src={team.crest_url} alt={team.name} width={60} height={60} style={{ objectFit:'contain' }} onError={e=>e.target.style.display='none'} />}
      <div style={{ fontFamily:'var(--font-display)', fontSize:'clamp(13px,2.2vw,20px)', color:R.pri, textAlign: r?'right':'left', lineHeight:1.2 }}>{team.name}</div>
      {team.country && <div style={{ fontFamily:'var(--font-mono)', fontSize:9, color:R.muted }}>{team.country}</div>}
    </div>
  )
}

function TeamPill({ team, color, right }) {
  return (
    <div style={{ display:'flex', alignItems:'center', gap:6, justifyContent: right?'flex-end':'flex-start' }}>
      {right && team?.crest_url && <img src={team.crest_url} alt="" width={16} height={16} style={{ objectFit:'contain' }} onError={e=>e.target.style.display='none'} />}
      <span style={{ fontFamily:'var(--font-display)', fontSize:12, color }}>{team?.short_name||team?.name}</span>
      {!right && team?.crest_url && <img src={team.crest_url} alt="" width={16} height={16} style={{ objectFit:'contain' }} onError={e=>e.target.style.display='none'} />}
    </div>
  )
}

function MiniTeamCard({ stats: s, team }) {
  return (
    <div style={{ background:'var(--bg-surface)', border:'1px solid var(--border)', borderRadius:6, padding:'14px 16px' }}>
      <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:10 }}>
        {team?.crest_url && <img src={team.crest_url} alt="" width={20} height={20} style={{ objectFit:'contain' }} onError={e=>e.target.style.display='none'} />}
        <span style={{ fontFamily:'var(--font-display)', fontSize:13, color:R.pri }}>{team?.name}</span>
      </div>
      <div style={{ display:'flex', gap:4, marginBottom:10 }}>
        {(s.form_5||[]).map((r,i) => (
          <div key={i} style={{ width:24, height:24, borderRadius:3, display:'flex', alignItems:'center', justifyContent:'center', background:resultBg(r), fontFamily:'var(--font-mono)', fontSize:9, fontWeight:700, color:resultColor(r) }}>{r}</div>
        ))}
      </div>
      <div style={{ display:'flex', gap:16 }}>
        {[
          { label:'Joués', value:s.played              },
          { label:'Victoires', value:s.wins,   color:R.green },
          { label:'Nuls', value:s.draws,  color:R.amber },
          { label:'Défaites', value:s.losses, color:R.red   },
        ].map(({ label, value, color }) => (
          <div key={label} style={{ textAlign:'center' }}>
            <div style={{ fontFamily:'var(--font-display)', fontSize:18, color:color||R.pri, lineHeight:1 }}>{value??'—'}</div>
            <div style={{ fontFamily:'var(--font-mono)', fontSize:7, color:R.muted, marginTop:2 }}>{label}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

function ProbBar({ label, value, color, best }) {
  return (
    <div style={{ marginBottom:10 }}>
      <div style={{ display:'flex', justifyContent:'space-between', marginBottom:4 }}>
        <span style={{ fontFamily:'var(--font-display)', fontSize:12, color: best?R.pri:R.sec }}>{label}</span>
        <span style={{ fontFamily:'var(--font-display)', fontSize:18, color, fontWeight:700 }}>{value}%</span>
      </div>
      <div style={{ height:4, background:'var(--bg-surface)', borderRadius:2, overflow:'hidden' }}>
        <div style={{ height:'100%', width:`${value}%`, background:color, borderRadius:2, boxShadow: best?`0 0 8px ${color}`:'none' }} />
      </div>
    </div>
  )
}

function ConfBadge({ score }) {
  const s = score||50
  const c = s>=70 ? { label:'HAUTE CONFIANCE',   color:R.green, dots:'◆◆◆' }
          : s>=50 ? { label:'CONFIANCE MOYENNE',  color:R.amber, dots:'◆◆◇' }
          :         { label:'FAIBLE CONFIANCE',   color:R.red,   dots:'◆◇◇' }
  return (
    <div style={{ background:`${c.color}10`, border:`1px solid ${c.color}30`, borderRadius:6, padding:'10px 14px', textAlign:'center', minWidth:100 }}>
      <div style={{ fontFamily:'var(--font-mono)', fontSize:13, color:c.color }}>{c.dots}</div>
      <div style={{ fontFamily:'var(--font-mono)', fontSize:7, color:c.color, letterSpacing:'0.1em', marginTop:2 }}>{c.label}</div>
      <div style={{ fontFamily:'var(--font-display)', fontSize:18, color:c.color, marginTop:2 }}>{s}%</div>
    </div>
  )
}

function Modal({ onClose, title, children }) {
  useEffect(() => {
    const h = e => { if (e.key==='Escape') onClose() }
    document.addEventListener('keydown', h)
    return () => document.removeEventListener('keydown', h)
  }, [onClose])
  return (
    <div style={{ position:'fixed', inset:0, zIndex:500, display:'flex', alignItems:'center', justifyContent:'center', padding:20 }}>
      <div style={{ position:'absolute', inset:0, background:'rgba(6,6,14,0.88)', backdropFilter:'blur(6px)' }} onClick={onClose} />
      <div style={{ position:'relative', zIndex:1, width:'100%', maxWidth:560, maxHeight:'88vh', overflowY:'auto', background:'var(--bg-surface)', border:'1px solid var(--border)', borderRadius:8, padding:24, boxShadow:'0 24px 80px rgba(0,0,0,0.6)' }}>
        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:20 }}>
          <span style={{ fontFamily:'var(--font-display)', fontSize:18, color:R.pri }}>{title}</span>
          <button onClick={onClose} style={{ background:'transparent', border:'1px solid var(--border)', borderRadius:4, color:R.muted, cursor:'pointer', padding:'4px 10px', fontFamily:'var(--font-mono)', fontSize:9 }}>ESC</button>
        </div>
        {children}
      </div>
    </div>
  )
}

function Btn({ children, onClick, variant='ghost' }) {
  const styles = {
    primary: { bg:R.green,   color:'#06060e', border:'none',                        shadow:'0 0 20px rgba(0,255,136,0.15)' },
    ghost:   { bg:'transparent', color:R.sec, border:'1px solid var(--border)',      shadow:'none' },
  }
  const s = styles[variant] || styles.ghost
  return (
    <button onClick={onClick} style={{ padding:'11px 24px', cursor:'pointer', fontFamily:'var(--font-mono)', fontSize:10, fontWeight:700, letterSpacing:'0.14em', borderRadius:4, transition:'all 0.2s', background:s.bg, border:s.border, color:s.color, boxShadow:s.shadow }}>
      {children}
    </button>
  )
}

function MicroLabel({ children }) {
  return <div style={{ fontFamily:'var(--font-mono)', fontSize:8, letterSpacing:'0.2em', color:R.muted }}>{children}</div>
}

function InfoBox({ children, color }) {
  const c = color || R.muted
  return (
    <div style={{ padding:'8px 12px', background:`${c}08`, border:`1px solid ${c}20`, borderRadius:4, fontFamily:'var(--font-mono)', fontSize:8, color:R.muted, lineHeight:1.6 }}>
      {children}
    </div>
  )
}

function Empty({ msg }) {
  return (
    <div style={{ background:'var(--bg-surface)', border:'1px solid var(--border)', borderRadius:6, padding:'36px 20px', textAlign:'center' }}>
      <div style={{ fontFamily:'var(--font-mono)', fontSize:10, color:R.muted }}>{msg}</div>
    </div>
  )
}

function Err({ msg }) {
  return (
    <div style={{ background:'rgba(255,68,85,0.08)', border:'1px solid rgba(255,68,85,0.25)', borderRadius:4, padding:'10px 14px', fontFamily:'var(--font-mono)', fontSize:10, color:R.red }}>
      {msg}
    </div>
  )
}

function ModalSkel() {
  return (
    <div style={{ display:'flex', flexDirection:'column', gap:10 }}>
      {[80,56,56].map((h,i) => (
        <div key={i} style={{ height:h, background:'var(--bg-elevated)', borderRadius:4, animation:'shimmer 1.4s infinite', opacity:1-i*0.15 }} />
      ))}
    </div>
  )
}

function PageLoader() {
  return (
    <div style={{ maxWidth:960, margin:'0 auto', padding:'28px 20px' }}>
      <div style={{ height:220, background:'var(--bg-surface)', border:'1px solid var(--border)', borderRadius:8, animation:'shimmer 1.4s infinite' }} />
    </div>
  )
}

function PageError({ msg }) {
  return (
    <div style={{ maxWidth:960, margin:'0 auto', padding:'80px 20px', textAlign:'center' }}>
      <div style={{ fontFamily:'var(--font-display)', fontSize:48, color:R.red, marginBottom:12 }}>⊗</div>
      <div style={{ fontFamily:'var(--font-mono)', fontSize:12, color:R.muted }}>{msg}</div>
      <Link to="/matches" style={{ display:'inline-block', marginTop:16, fontFamily:'var(--font-mono)', fontSize:10, color:R.green, textDecoration:'none' }}>← RETOUR AUX MATCHS</Link>
    </div>
  )
}
