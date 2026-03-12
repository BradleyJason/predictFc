import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

// ── Matches ──────────────────────────────────────
export const getMatches      = (params = {}) => api.get('/matches', { params })
export const getMatch        = (id)          => api.get(`/matches/${id}`)
export const getMatchStats   = (id)          => api.get(`/matches/${id}/stats`)
export const getLiveMatches  = ()            => api.get('/live')
export const getTodayMatches = ()            => api.get('/live/today')
export const refreshLive     = ()            => api.post('/live/refresh')

// ── Predictions ───────────────────────────────────
export const getPrediction = (matchId, forceRefresh = false) =>
  api.get(`/predictions/${matchId}`, { params: { force_refresh: forceRefresh } })

// ── Smart Ticket ──────────────────────────────────
export const generateSmartTicket = (matchIds, mode = 'combined') =>
  api.post('/smart-ticket', { match_ids: matchIds, mode })

// ── Competitions ──────────────────────────────────
export const getCompetitions = () => api.get('/competitions')

// ── Odds ─────────────────────────────────────────
export const getMatchOdds    = (matchId) => api.get(`/odds/match/${matchId}`)
export const importMatchOdds = (matchId) => api.post(`/odds/import/${matchId}`)

// ── Injuries ──────────────────────────────────────
export const getMatchInjuries = (matchId) => api.get(`/injuries/match/${matchId}`)

// ── Lineups ───────────────────────────────────────
export const getMatchLineups = (matchId) => api.get(`/lineups/match/${matchId}`)

// ── Value Bets ────────────────────────────────────
export const getValueBets        = (params = {}) => api.get('/value-bets', { params })
export const getMatchValueBets   = (matchId)     => api.get(`/value-bets/match/${matchId}`)
export const getValueBetsSummary = ()            => api.get('/value-bets/summary')

// ── Teams ─────────────────────────────────────────
export const searchTeams = (query)   => api.get('/teams/search', { params: { q: query } })
export const getTeam     = (id)      => api.get(`/teams/${id}`)
export const getMatchRawStats = (id) => api.get(`/matches/${id}/match-stats`)
