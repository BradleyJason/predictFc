import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import MatchDetail from './pages/MatchDetail'
import SmartTicket from './pages/SmartTicket'

export default function App() {
  return (
    <div style={{ position: 'relative', zIndex: 1 }}>
      <Navbar />
      <main style={{ paddingTop: '64px' }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/match/:id" element={<MatchDetail />} />
          <Route path="/smart-ticket" element={<SmartTicket />} />
        </Routes>
      </main>
    </div>
  )
}
