import { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import Sidebar from './Sidebar'
import Footer from './Footer'
import Navbar from './Navbar'

export default function AppLayout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { pathname } = useLocation()

  // Fermer sidebar sur changement de route (mobile)
  useEffect(() => { setSidebarOpen(false) }, [pathname])

  return (
    <div style={{ display: 'flex', minHeight: '100vh', flexDirection: 'column' }}>
      {/* Sidebar desktop fixe + drawer mobile */}
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Contenu principal décalé à droite sur desktop */}
      <div className="main-with-sidebar" style={{
        display: 'flex', flexDirection: 'column', flex: 1,
      }}>
        {/* Navbar top (mobile uniquement pour hamburger) */}
        <Navbar onMenuToggle={() => setSidebarOpen((o) => !o)} />

        <main style={{ flex: 1, paddingTop: '60px' }}>
          {children}
        </main>

        <Footer />
      </div>
    </div>
  )
}
