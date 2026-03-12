import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'

export default function Profile() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  return (
    <div style={{ maxWidth: '600px', margin: '0 auto', padding: '36px 24px' }}>
      <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '48px', color: 'var(--text-primary)', marginBottom: '24px' }}>
        PROFIL
      </h1>
      <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: '6px', padding: '24px' }}>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '8px' }}>EMAIL</div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: '14px', color: 'var(--text-primary)', marginBottom: '24px' }}>{user?.email}</div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '8px' }}>RÔLE</div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: '14px', color: 'var(--accent-green)', marginBottom: '32px' }}>ADMINISTRATEUR</div>
        <button
          onClick={() => { logout(); navigate('/login') }}
          style={{
            padding: '10px 20px', background: 'transparent',
            border: '1px solid rgba(255,68,85,0.4)', borderRadius: '4px',
            color: '#ff5566', fontFamily: 'var(--font-mono)',
            fontSize: '11px', letterSpacing: '0.1em', cursor: 'pointer',
          }}
        >
          ⊗ DÉCONNEXION
        </button>
      </div>
    </div>
  )
}
