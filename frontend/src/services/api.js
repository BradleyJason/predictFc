import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

export const getMatches = (params = {}) =>
  api.get('/matches', { params })

export const getMatch = (id) =>
  api.get(`/matches/${id}`)

export const getPrediction = (matchId, forceRefresh = false) =>
  api.get(`/predictions/${matchId}`, { params: { force_refresh: forceRefresh } })

export const generateSmartTicket = (matchIds, mode = 'combined') =>
  api.post('/smart-ticket', { match_ids: matchIds, mode })
