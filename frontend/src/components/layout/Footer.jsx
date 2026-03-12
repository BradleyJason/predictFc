import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer style={{
      borderTop: '1px solid var(--border)',
      background: 'var(--bg-surface)',
      padding: '32px 24px',
      marginTop: 'auto',
    }}>
      <div style={{ maxWidth: '960px', margin: '0 auto' }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
          gap: '32px',
          marginBottom: '28px',
        }}>
          {/* Logo + desc */}
          <div>
            <div style={{
              fontFamily: 'var(--font-display)', fontSize: '18px',
              letterSpacing: '0.05em', color: 'var(--text-primary)',
              marginBottom: '8px',
            }}>
              PREDICT<span style={{ color: 'var(--accent-green)' }}>///</span>FC
            </div>
            <p style={{
              fontFamily: 'var(--font-mono)', fontSize: '9px',
              color: 'var(--text-muted)', letterSpacing: '0.06em',
              lineHeight: 1.7,
            }}>
              Analyse statistique football<br />
              basée sur Dixon-Coles + XGBoost
            </p>
          </div>

          {/* Navigation */}
          <div>
            <div style={{
              fontFamily: 'var(--font-mono)', fontSize: '8px',
              letterSpacing: '0.2em', color: 'var(--text-muted)',
              marginBottom: '12px',
            }}>NAVIGATION</div>
            {[
              { to: '/matches',      label: 'Matchs'       },
              { to: '/value-bets',   label: 'Value Bets'   },
              { to: '/smart-ticket', label: 'Smart Ticket' },
              { to: '/guide',        label: 'Guide'        },
            ].map(({ to, label }) => (
              <Link key={to} to={to} style={{
                display: 'block', marginBottom: '6px',
                fontFamily: 'var(--font-mono)', fontSize: '10px',
                color: 'var(--text-secondary)', textDecoration: 'none',
                letterSpacing: '0.04em', transition: 'color 0.15s',
              }}
              onMouseEnter={(e) => e.target.style.color = 'var(--accent-green)'}
              onMouseLeave={(e) => e.target.style.color = 'var(--text-secondary)'}
              >
                → {label}
              </Link>
            ))}
          </div>

          {/* Jeu responsable */}
          <div>
            <div style={{
              fontFamily: 'var(--font-mono)', fontSize: '8px',
              letterSpacing: '0.2em', color: 'var(--text-muted)',
              marginBottom: '12px',
            }}>JEU RESPONSABLE</div>
            <p style={{
              fontFamily: 'var(--font-mono)', fontSize: '9px',
              color: 'var(--text-muted)', letterSpacing: '0.04em',
              lineHeight: 1.7,
            }}>
              Les paris sportifs comportent<br />
              des risques financiers.<br />
              Joueurs Info Service :<br />
              <span style={{ color: 'var(--accent-cyan)' }}>09 74 75 13 13</span>
            </p>
          </div>
        </div>

        {/* Disclaimer + copyright */}
        <div style={{
          borderTop: '1px solid var(--border)',
          paddingTop: '20px',
          display: 'flex',
          flexWrap: 'wrap',
          gap: '12px',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <p style={{
            fontFamily: 'var(--font-mono)', fontSize: '8px',
            color: 'var(--text-muted)', letterSpacing: '0.04em',
            lineHeight: 1.6, maxWidth: '500px',
          }}>
            ⚠ PredictFC est un outil d'analyse statistique à but informatif. Les prédictions ne garantissent aucun résultat.
          </p>
          <span style={{
            fontFamily: 'var(--font-mono)', fontSize: '8px',
            color: 'var(--text-muted)', letterSpacing: '0.1em',
          }}>
            © 2026 PREDICTFC
          </span>
        </div>
      </div>
    </footer>
  )
}
