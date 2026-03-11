import { Link } from 'react-router-dom'

const SECTIONS = [
  {
    icon: '⬡',
    title: 'Comment fonctionnent les prédictions ?',
    content: `PredictFC utilise un modèle mathématique appelé Dixon-Coles, spécialement conçu pour le football. Il analyse l'historique de chaque équipe (buts marqués, buts encaissés, résultats) sur plusieurs saisons pour estimer la "force" de chaque équipe en attaque et en défense.

À partir de ces forces, le modèle calcule la probabilité de chaque score possible (0-0, 1-0, 2-1...) puis regroupe ces probabilités pour obtenir les différents types de paris.`,
  },
  {
    icon: '◈',
    title: 'Que signifient les pourcentages ?',
    content: `Les pourcentages indiquent la probabilité qu'un événement se produise selon notre modèle. Par exemple, "Domicile 65%" signifie que l'équipe à domicile a 65 chances sur 100 de gagner d'après les données historiques.

Un pourcentage élevé ne garantit pas le résultat — le football reste imprévisible. Ces chiffres sont des indicateurs statistiques, pas des certitudes.`,
  },
  {
    icon: '◉',
    title: 'Les types de paris disponibles',
    items: [
      { label: '1X2', desc: 'Résultat final : victoire domicile (1), match nul (X) ou victoire extérieur (2).' },
      { label: 'Over/Under', desc: 'Le nombre total de buts sera supérieur (Over) ou inférieur (Under) à un seuil donné (0.5, 1.5, 2.5...).' },
      { label: 'BTTS', desc: 'Les deux équipes marquent au moins un but chacune (Yes) ou non (No).' },
      { label: 'Double Chance', desc: 'Couvre deux résultats sur trois : 1X (dom. ou nul), X2 (ext. ou nul), 12 (dom. ou ext.).' },
      { label: 'Score exact', desc: 'Le score précis à la fin du match. Les probabilités sont naturellement plus basses.' },
    ],
  },
  {
    icon: '▲',
    title: 'Smart Ticket — 3 modes',
    items: [
      { label: 'SMART TICKET', desc: 'Combiné optimisé : plusieurs paris sur différents matchs, sélectionnés pour leur indépendance (anti-corrélation). Probabilité ≥ 60%.' },
      { label: 'SIMPLE', desc: 'Un seul pari par match, le plus probable. Idéal pour jouer en simple. Probabilité ≥ 60%.' },
      { label: '🔥 DANGER ZONE', desc: 'Paris à plus haute valeur avec des cotes élevées. Probabilité 35–59%. Risque plus élevé, gain potentiel plus fort.' },
    ],
  },
  {
    icon: '◆',
    title: "L'indice de confiance",
    content: `Le score de confiance (0–100) mesure la fiabilité globale de l'analyse. Il tient compte de plusieurs facteurs : la quantité de données disponibles pour les deux équipes, la cohérence des résultats passés et la clarté du favori.

Un score élevé (>70) indique que le modèle a beaucoup de données et que les équipes ont des profils bien définis. Un score faible peut indiquer peu d'historique ou des équipes très imprévisibles.`,
  },
  {
    icon: '⚠',
    title: 'Avertissement responsable',
    content: `PredictFC est un outil d'analyse statistique à but éducatif et informatif. Les prédictions sont basées sur des données historiques et ne garantissent aucun résultat futur.

Les paris sportifs comportent des risques financiers. Jouez de manière responsable, ne misez jamais plus que vous ne pouvez vous permettre de perdre. Si vous pensez avoir un problème avec les jeux d'argent, contactez Joueurs Info Service au 09 74 75 13 13.`,
    warning: true,
  },
]

export default function Guide() {
  return (
    <div style={{ maxWidth: '860px', margin: '0 auto', padding: '36px 24px' }}>
      {/* Header */}
      <div style={{ marginBottom: '40px' }}>
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(36px, 6vw, 56px)', letterSpacing: '0.04em', color: 'var(--text-primary)', lineHeight: 1, margin: 0, marginBottom: '8px' }}>
          GUIDE
        </h1>
        <div style={{ width: '44px', height: '2px', background: 'var(--accent-green)', boxShadow: '0 0 10px var(--accent-green)', marginBottom: '12px' }} />
        <p style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)', letterSpacing: '0.1em' }}>
          COMMENT UTILISER PREDICTFC · COMPRENDRE LES PROBABILITÉS
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {SECTIONS.map((section, i) => (
          <GuideCard key={i} section={section} delay={i * 60} />
        ))}
      </div>

      {/* CTA */}
      <div style={{ marginTop: '40px', display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
        <Link to="/" className="nav-link active" style={{ padding: '10px 20px', fontSize: '11px' }}>
          → VOIR LES MATCHS
        </Link>
        <Link to="/smart-ticket" className="nav-link" style={{ padding: '10px 20px', fontSize: '11px' }}>
          → SMART TICKET
        </Link>
      </div>
    </div>
  )
}

function GuideCard({ section, delay }) {
  const borderColor = section.warning ? 'rgba(255,204,0,0.25)' : 'var(--border)'
  const bg          = section.warning ? 'rgba(255,204,0,0.04)' : 'var(--bg-surface)'
  const iconColor   = section.warning ? 'var(--accent-amber)' : 'var(--accent-green)'

  return (
    <div className="animate-fade-up" style={{ background: bg, border: `1px solid ${borderColor}`, borderRadius: '4px', padding: '24px', animationDelay: `${delay}ms` }}>
      {/* Titre */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
        <span style={{ color: iconColor, fontSize: '14px' }}>{section.icon}</span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', fontWeight: 700, letterSpacing: '0.14em', color: 'var(--text-secondary)' }}>
          {section.title.toUpperCase()}
        </span>
      </div>

      {/* Texte */}
      {section.content && (
        <div style={{ fontFamily: 'var(--font-ui)', fontSize: '14px', color: 'var(--text-secondary)', lineHeight: 1.8, whiteSpace: 'pre-line' }}>
          {section.content}
        </div>
      )}

      {/* Liste items */}
      {section.items && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {section.items.map((item, i) => (
            <div key={i} style={{ display: 'flex', gap: '14px', padding: '10px 14px', background: 'var(--bg-elevated)', borderRadius: '3px', borderLeft: '2px solid var(--accent-cyan)' }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', fontWeight: 700, color: 'var(--accent-cyan)', letterSpacing: '0.08em', flexShrink: 0, minWidth: '80px', paddingTop: '1px' }}>
                {item.label}
              </span>
              <span style={{ fontFamily: 'var(--font-ui)', fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                {item.desc}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
