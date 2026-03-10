# PredictFC ⚽

Application de prédiction de matchs de football basée sur des modèles statistiques et ML.

## Prédictions disponibles
- Résultat du match (1X2)
- Score exact probable
- Total de buts (Over/Under 0.5 / 1.5 / 2.5 / 3.5 / 4.5)
- Les deux équipes marquent (BTTS)
- Chance double (1X / X2 / 12)
- Écart de buts (handicap)
- Qualification (phases éliminatoires — Monte Carlo)
- Buteurs/Passeurs probables
- **Smart Ticket** — combiné optimal généré automatiquement

## Stack
- **Backend** : FastAPI + SQLAlchemy + Supabase (PostgreSQL)
- **ML** : scikit-learn + XGBoost + scipy (Double Poisson)
- **Tracking** : MLflow + DVC + DagsHub
- **Frontend** : React + TailwindCSS + Recharts
- **CI/CD** : GitHub Actions + Docker + Render

## Ligues supportées
- Ligue 1 🇫🇷
- Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿
- Champions League 🇪🇺
- La Liga 🇪🇸
- Bundesliga 🇩🇪
- Serie A 🇮🇹

## Setup local
```bash
# Cloner le repo
git clone https://github.com/USERNAME/predictfc.git
cd predictfc

# Configurer les variables d'environnement
cp .env.example .env
# Editer .env avec tes clés

# Installer les dépendances
make install

# Lancer en local
make dev
```

## Branches
| Branche | Rôle |
|---------|------|
| `main` | Production stable |
| `staging` | Pré-production |
| `develop` | Intégration |
| `feature/*` | Nouvelles fonctionnalités |
| `experiment/*` | Expériences ML |
| `hotfix/*` | Corrections urgentes |

## Disclaimer
> Ces prédictions sont basées sur des modèles statistiques.
> Aucune prédiction n'est garantie. Jouez responsablement
> et uniquement sur des plateformes agréées ANJ.
