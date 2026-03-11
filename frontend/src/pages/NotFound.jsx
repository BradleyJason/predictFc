import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div style={{ maxWidth: '600px', margin: '0 auto', padding: '80px 24px', textAlign: 'center' }}>
      <div style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(80px, 15vw, 140px)', color: 'var(--border-bright)', letterSpacing: '0.05em', lineHeight: 1, marginBottom: '16px' }}>
        404
      </div>
      <div style={{ width: '44px', height: '2px', background: 'var(--accent-green)', margin: '0 auto 20px', boxShadow: '0 0 10px var(--accent-green)' }} />
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', letterSpacing: '0.14em', color: 'var(--text-muted)', marginBottom: '32px' }}>
        PAGE INTROUVABLE
      </div>
      <div style={{ fontFamily: 'var(--font-ui)', fontSize: '14px', color: 'var(--text-secondary)', lineHeight: 1.7, marginBottom: '40px' }}>
        Cette page n'existe pas ou a été déplacée.
      </div>
      <Link to="/" className="nav-link active" style={{ padding: '10px 24px', fontSize: '11px' }}>
        ← RETOUR À L'ACCUEIL
      </Link>
    </div>
  )
}
