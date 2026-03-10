# PredictFC — Schéma de Base de Données

## Vue d'ensemble
```
competitions ──< matches >── teams
                   │
                   └──< predictions
                              │
                              └──< smart_tickets

teams ──< players ──< player_stats
```

## Tables

### competitions
```sql
CREATE TABLE competitions (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(10) UNIQUE NOT NULL,  -- PL, FL1, CL...
    name        VARCHAR(100) NOT NULL,
    country     VARCHAR(50),
    season      VARCHAR(10),                  -- 2024-25
    created_at  TIMESTAMP DEFAULT NOW()
);
```

### teams
```sql
CREATE TABLE teams (
    id              SERIAL PRIMARY KEY,
    external_id     INTEGER UNIQUE,           -- ID football-data.org
    name            VARCHAR(100) NOT NULL,
    short_name      VARCHAR(50),
    competition_id  INTEGER REFERENCES competitions(id),
    created_at      TIMESTAMP DEFAULT NOW()
);
```

### players
```sql
CREATE TABLE players (
    id          SERIAL PRIMARY KEY,
    external_id INTEGER UNIQUE,
    name        VARCHAR(100) NOT NULL,
    position    VARCHAR(50),
    team_id     INTEGER REFERENCES teams(id),
    created_at  TIMESTAMP DEFAULT NOW()
);
```

### matches
```sql
CREATE TABLE matches (
    id              SERIAL PRIMARY KEY,
    external_id     INTEGER UNIQUE,
    competition_id  INTEGER REFERENCES competitions(id),
    home_team_id    INTEGER REFERENCES teams(id),
    away_team_id    INTEGER REFERENCES teams(id),
    match_date      TIMESTAMP NOT NULL,
    status          VARCHAR(20),              -- SCHEDULED, FINISHED, LIVE
    home_score      INTEGER,
    away_score      INTEGER,
    matchday        INTEGER,
    stage           VARCHAR(50),              -- REGULAR_SEASON, QUARTER_FINAL...
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);
```

### player_stats
```sql
CREATE TABLE player_stats (
    id          SERIAL PRIMARY KEY,
    player_id   INTEGER REFERENCES players(id),
    match_id    INTEGER REFERENCES matches(id),
    goals       INTEGER DEFAULT 0,
    assists     INTEGER DEFAULT 0,
    minutes     INTEGER DEFAULT 0,
    created_at  TIMESTAMP DEFAULT NOW(),
    UNIQUE(player_id, match_id)
);
```

### predictions
```sql
CREATE TABLE predictions (
    id              SERIAL PRIMARY KEY,
    match_id        INTEGER REFERENCES matches(id),
    model_version   VARCHAR(50),              -- mlflow run_id
    
    -- Résultat 1X2
    home_win_proba  FLOAT,
    draw_proba      FLOAT,
    away_win_proba  FLOAT,
    
    -- Score exact
    predicted_home_score  INTEGER,
    predicted_away_score  INTEGER,
    exact_score_proba     FLOAT,
    
    -- Total buts
    over_05_proba   FLOAT,
    over_15_proba   FLOAT,
    over_25_proba   FLOAT,
    over_35_proba   FLOAT,
    over_45_proba   FLOAT,
    
    -- BTTS
    btts_proba      FLOAT,
    
    -- Chance double
    home_draw_proba FLOAT,   -- 1X
    away_draw_proba FLOAT,   -- X2
    home_away_proba FLOAT,   -- 12
    
    -- Qualification (phases éliminatoires)
    home_qualify_proba  FLOAT,
    away_qualify_proba  FLOAT,
    
    -- Métadonnées
    confidence_score    INTEGER,             -- 0-100
    created_at          TIMESTAMP DEFAULT NOW()
);
```

### smart_tickets
```sql
CREATE TABLE smart_tickets (
    id              SERIAL PRIMARY KEY,
    match_id        INTEGER REFERENCES matches(id),
    prediction_id   INTEGER REFERENCES predictions(id),
    selections      JSONB NOT NULL,          -- [{type, value, proba}]
    combined_proba  FLOAT,
    confidence_score INTEGER,
    mode            VARCHAR(20),             -- simple, combined
    created_at      TIMESTAMP DEFAULT NOW()
);
```

## Index recommandés
```sql
CREATE INDEX idx_matches_date ON matches(match_date);
CREATE INDEX idx_matches_competition ON matches(competition_id);
CREATE INDEX idx_predictions_match ON predictions(match_id);
CREATE INDEX idx_player_stats_player ON player_stats(player_id);
CREATE INDEX idx_player_stats_match ON player_stats(match_id);
```

## Notes importantes
- Toujours passer par les migrations Alembic pour modifier le schéma
- Ne jamais modifier la BDD directement via Supabase dashboard
- Les données brutes football-data.org sont dans ml/data/raw/ (DVC)
- Les features engineered sont dans ml/data/processed/ (DVC)
