# PredictFC — Instructions pour Claude Code

## 🎯 Vision du projet
Application web de prédiction de matchs de football basée sur des modèles
statistiques et ML. L'app prédit : résultat 1X2, score exact, total buts,
BTTS, chance double, écart de buts, qualification, buteurs/passeurs probables,
et génère un Smart Ticket (combiné optimal automatique).

## 👤 Profil développeur
- Langage principal : Python (niveau intermédiaire-avancé)
- Objectif : apprendre en construisant — expliquer les choix techniques
- IDE : VS Code + Claude Code dans WSL Ubuntu sur Windows
- Approche : pas à pas, chaque étape testable avant de passer à la suivante

---

## 🏗️ Stack technique

| Couche | Outil | Version |
|--------|-------|---------|
| Backend | FastAPI + SQLAlchemy + Alembic | Python 3.11+ |
| Base de données | Supabase (PostgreSQL) | - |
| ML | scikit-learn + XGBoost + scipy | - |
| Tracking ML | MLflow + DVC + DagsHub | - |
| Frontend | React + TailwindCSS + Recharts | Node 20 |
| Tests backend | pytest + ruff | - |
| Tests frontend | Playwright | - |
| CI/CD | GitHub Actions | - |
| Containerisation | Docker + docker-compose | - |
| Hébergement | Render | - |
| Dépendances | Poetry | - |

---

## 🌿 Système de branches
```
main        → production stable, jamais de push direct
staging     → pré-production, tests finaux
develop     → intégration, branche de travail principale
feature/*   → nouvelles fonctionnalités → PR vers develop
experiment/ → expériences ML → PR vers develop si validé
release/*   → develop → staging → main
hotfix/*    → depuis main → merge vers main ET develop
```

**Règle absolue** : toujours travailler sur `develop` ou une branche dédiée.
Ne jamais committer directement sur `main` ou `staging`.

---

## 📝 Conventions de commits (Conventional Commits)
```
feat(scope): description
fix(scope): description
data(scope): description
experiment(scope): description
refactor(scope): description
test(scope): description
chore(scope): description
docs(scope): description
```

Scopes valides : `api`, `model`, `pipeline`, `frontend`, `db`, `ml`, `infra`, `smart-ticket`

Exemples :
- `feat(api): add smart-ticket endpoint`
- `experiment(ml): tune xgboost max_depth hyperparameter`
- `data(pipeline): add ligue1 2024 season ingestion`

---

## 📁 Structure du projet
```
predictfc/
├── .claude/          # Config Claude Code (skills, CLAUDE.md)
├── .github/          # Workflows CI/CD + PR template
├── backend/          # FastAPI — API REST + services
│   ├── app/
│   │   ├── api/      # Routes FastAPI
│   │   ├── core/     # DB, security
│   │   ├── models/   # SQLAlchemy models
│   │   ├── schemas/  # Pydantic schemas
│   │   └── services/ # Logique métier
│   └── tests/
├── ml/               # Pipeline ML complet
│   ├── data/         # Données (gitignored, versionnées DVC)
│   ├── pipelines/    # Pipeline DVC déclaratif
│   ├── models/       # Modèles ML (Poisson, XGBoost)
│   ├── engine/       # Moteur de prédictions + Smart Ticket
│   └── tracking/     # Config MLflow + DagsHub
├── frontend/         # React + TailwindCSS
├── infra/            # Docker + docker-compose
└── docs/             # ARCHITECTURE.md, API_CONTRACT.md, etc.
```

---

## 🧠 Architecture ML — règles importantes

### Modèles disponibles
1. **Double Poisson** (baseline) — prédit la distribution de scores P(i,j)
2. **XGBoost** (amélioration) — classification 1X2 + régression buts
3. **Modèle joueur** (phase 3) — buteurs/passeurs probables via xG/xA

### La matrice de scores est le cœur du système
Toutes les prédictions se déduisent de P(score_A=i, score_B=j) :
- 1X2 → somme des triangles de la matrice
- Over/Under → somme des cases où i+j > seuil
- BTTS → somme des cases où i>0 ET j>0
- Score exact → case individuelle (i,j)
- Écart de buts → diagonales de la matrice
- Qualification → simulation Monte Carlo basée sur la matrice

### Smart Ticket — règles de sélection
- Probabilité minimum : 60% par défaut (configurable)
- Maximum 3 sélections par ticket
- Vérifier la corrélation entre paris avant de combiner
- Toujours afficher un score de confiance global (0-100)
- Toujours afficher le disclaimer légal

---

## 🗄️ Base de données — règles

- ORM : SQLAlchemy avec Alembic pour les migrations
- Toujours créer une migration Alembic pour chaque changement de schéma
- Ne jamais modifier la BDD directement — toujours passer par les migrations
- Connexion via `DATABASE_URL` dans les variables d'environnement

---

## 🔐 Sécurité — règles absolues

- Ne jamais hardcoder de secrets dans le code
- Toutes les clés API dans `.env` (jamais committé)
- `.env.example` toujours mis à jour quand on ajoute une variable
- Les secrets de prod dans GitHub Secrets uniquement

---

## ✅ Qualité du code

- Lint : `ruff` (pas flake8, pas black séparément)
- Tests : `pytest` avec coverage minimum 80%
- Toujours écrire les tests avant de merger sur develop
- Chaque fonction doit avoir une docstring
- Type hints obligatoires sur toutes les fonctions Python

---

## 🚀 Commandes du quotidien
```bash
make install      # Installer toutes les dépendances
make dev          # Lancer l'environnement local complet
make test         # Tests + lint
make train        # Pipeline DVC complet
make lint         # Ruff uniquement
make db-migrate   # Appliquer les migrations Alembic
```

---

## 📊 Ligues supportées

- Ligue 1 (France) — code : FL1
- Premier League (Angleterre) — code : PL
- Champions League (UEFA) — code : CL
- La Liga (Espagne) — code : PD
- Bundesliga (Allemagne) — code : BL1
- Serie A (Italie) — code : SA

Source : football-data.org API v4

---

## ⚠️ Disclaimer légal (obligatoire dans l'UI)

Toujours afficher dans l'interface :
"Ces prédictions sont basées sur des modèles statistiques.
Aucune prédiction n'est garantie. Jouez responsablement
et uniquement sur des plateformes agréées ANJ."

