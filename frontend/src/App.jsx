import { Routes, Route } from 'react-router-dom'
import { ThemeProvider } from './context/ThemeContext'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import MatchDetail from './pages/MatchDetail'
import SmartTicket from './pages/SmartTicket'
import Guide from './pages/Guide'
import NotFound from './pages/NotFound'

export default function App() {
  return (
    <ThemeProvider>
      <div style={{
        position: 'relative', zIndex: 1,
        width: '100%', maxWidth: '100vw', overflowX: 'hidden',
      }}>
        <Navbar />
        <main style={{ paddingTop: '64px', width: '100%', overflowX: 'hidden' }}>
          <Routes>
            <Route path="/"             element={<Dashboard />} />
            <Route path="/match/:id"    element={<MatchDetail />} />
            <Route path="/smart-ticket" element={<SmartTicket />} />
            <Route path="/guide"        element={<Guide />} />
            <Route path="*"             element={<NotFound />} />
          </Routes>
        </main>
      </div>
    </ThemeProvider>
  )
}
