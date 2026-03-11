"""Preprocessing ML — calcule les features par match depuis la BDD.

Features produites (toutes basées sur les 5 derniers matchs de chaque équipe) :
- goals_scored_avg5       : moyenne buts marqués
- goals_conceded_avg5     : moyenne buts encaissés
- points_avg5             : moyenne points (3=victoire, 1=nul, 0=défaite)
- gd_avg5                 : moyenne goal difference
- win_rate5               : taux de victoire

Toutes les features sont préfixées home_ ou away_ dans le fichier final.

Output : ml/data/processed/features.parquet

Usage:
    python ml/pipelines/preprocess.py
    python ml/pipelines/preprocess.py --output ml/data/processed/features.parquet
"""

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

# Ajoute backend/ au path pour importer les settings
_BACKEND_PATH = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(_BACKEND_PATH))

from app.core.config import settings  # noqa: E402

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("predictfc.preprocess")

# ---------------------------------------------------------------------------
# Chargement des données
# ---------------------------------------------------------------------------

_MATCHES_QUERY = text("""
    SELECT
        m.id          AS match_id,
        m.external_id,
        m.competition_id,
        m.home_team_id,
        m.away_team_id,
        m.match_date,
        m.status,
        m.home_score,
        m.away_score,
        m.matchday,
        m.stage
    FROM matches m
    WHERE m.status = 'FINISHED'
      AND m.home_score IS NOT NULL
      AND m.away_score IS NOT NULL
    ORDER BY m.match_date ASC
""")


def load_matches(engine) -> pd.DataFrame:
    """Charge tous les matchs terminés depuis la BDD.

    Args:
        engine: Engine SQLAlchemy connecté.

    Returns:
        DataFrame avec les colonnes brutes du match.
    """
    with engine.connect() as conn:
        df = pd.read_sql(_MATCHES_QUERY, conn, parse_dates=["match_date"])
    logger.info("%d matchs chargés depuis la BDD.", len(df))
    return df


# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------

_ROLLING_WINDOW = 5


def _compute_team_perspective(matches_df: pd.DataFrame) -> pd.DataFrame:
    """Transforme les matchs en vue par équipe (une ligne par équipe par match).

    Chaque match produit deux lignes : une pour l'équipe domicile,
    une pour l'équipe extérieure.

    Args:
        matches_df: DataFrame des matchs terminés.

    Returns:
        DataFrame avec colonnes: match_id, match_date, team_id, goals_scored,
        goals_conceded, is_home, competition_id.
    """
    home = matches_df[
        ["match_id", "match_date", "home_team_id", "away_team_id",
         "home_score", "away_score", "competition_id"]
    ].copy()
    home = home.rename(columns={
        "home_team_id": "team_id",
        "away_team_id": "opp_id",
        "home_score": "goals_scored",
        "away_score": "goals_conceded",
    })
    home["is_home"] = True

    away = matches_df[
        ["match_id", "match_date", "away_team_id", "home_team_id",
         "away_score", "home_score", "competition_id"]
    ].copy()
    away = away.rename(columns={
        "away_team_id": "team_id",
        "home_team_id": "opp_id",
        "away_score": "goals_scored",
        "home_score": "goals_conceded",
    })
    away["is_home"] = False

    team_df = pd.concat([home, away], ignore_index=True)
    team_df = team_df.sort_values(["team_id", "match_date"]).reset_index(drop=True)
    return team_df


def _add_team_rolling_features(team_df: pd.DataFrame) -> pd.DataFrame:
    """Calcule les features rolling (sur 5 matchs) pour chaque équipe.

    Utilise shift(1) pour éviter la fuite de données (le match courant
    n'est PAS inclus dans son propre calcul).

    Args:
        team_df: DataFrame vue-équipe produit par _compute_team_perspective().

    Returns:
        Même DataFrame enrichi des colonnes rolling.
    """
    # Points par match
    team_df["points"] = np.where(
        team_df["goals_scored"] > team_df["goals_conceded"], 3,
        np.where(team_df["goals_scored"] == team_df["goals_conceded"], 1, 0),
    )
    team_df["won"] = (team_df["goals_scored"] > team_df["goals_conceded"]).astype(int)
    team_df["gd"] = team_df["goals_scored"] - team_df["goals_conceded"]

    rolling_cols = {
        "goals_scored": "goals_scored_avg5",
        "goals_conceded": "goals_conceded_avg5",
        "points": "points_avg5",
        "gd": "gd_avg5",
        "won": "win_rate5",
    }

    for src, dst in rolling_cols.items():
        team_df[dst] = (
            team_df.groupby("team_id")[src]
            .transform(
                lambda x: x.shift(1)  # noqa: B023
                .rolling(_ROLLING_WINDOW, min_periods=1)
                .mean()
            )
        )

    return team_df


def compute_features(matches_df: pd.DataFrame) -> pd.DataFrame:
    """Calcule toutes les features ML pour l'ensemble des matchs.

    Args:
        matches_df: DataFrame des matchs terminés (sortie de load_matches()).

    Returns:
        DataFrame prêt pour l'entraînement avec features home_* et away_*,
        la variable cible `result` (H/D/A) et les métadonnées du match.
    """
    if matches_df.empty:
        logger.warning("Aucun match disponible pour le feature engineering.")
        return pd.DataFrame()

    logger.info("Calcul des features sur %d matchs...", len(matches_df))

    # 1. Vue par équipe + rolling features
    team_df = _compute_team_perspective(matches_df)
    team_df = _add_team_rolling_features(team_df)

    # 2. Sépare home et away pour merger sur le match
    feature_cols = [
        "goals_scored_avg5",
        "goals_conceded_avg5",
        "points_avg5",
        "gd_avg5",
        "win_rate5",
    ]

    home_feats = (
        team_df[team_df["is_home"]][["match_id", "team_id"] + feature_cols]
        .rename(columns={c: f"home_{c}" for c in feature_cols})
        .rename(columns={"team_id": "home_team_id"})
    )
    away_feats = (
        team_df[~team_df["is_home"]][["match_id", "team_id"] + feature_cols]
        .rename(columns={c: f"away_{c}" for c in feature_cols})
        .rename(columns={"team_id": "away_team_id"})
    )

    # 3. Merge avec les matchs originaux
    features = (
        matches_df
        .merge(home_feats, on=["match_id", "home_team_id"], how="left")
        .merge(away_feats, on=["match_id", "away_team_id"], how="left")
    )

    # 4. Variable cible 1X2
    features["result"] = np.where(
        features["home_score"] > features["away_score"], "H",
        np.where(features["home_score"] == features["away_score"], "D", "A"),
    )

    # 5. Home advantage (toujours 1, mais utile comme feature explicite)
    features["home_advantage"] = 1

    logger.info(
        "Features calculées. Shape final : %s | NaN : %d",
        features.shape,
        features[home_feats.columns.difference(["match_id", "home_team_id"]).tolist()
                  + away_feats.columns.difference(["match_id", "away_team_id"]).tolist()
                  ].isna().sum().sum(),
    )
    return features


# ---------------------------------------------------------------------------
# Sauvegarde
# ---------------------------------------------------------------------------

_OUTPUT_COLS = [
    "match_id",
    "external_id",
    "competition_id",
    "home_team_id",
    "away_team_id",
    "match_date",
    "matchday",
    "stage",
    "home_score",
    "away_score",
    "result",
    "home_advantage",
    # Home rolling features
    "home_goals_scored_avg5",
    "home_goals_conceded_avg5",
    "home_points_avg5",
    "home_gd_avg5",
    "home_win_rate5",
    # Away rolling features
    "away_goals_scored_avg5",
    "away_goals_conceded_avg5",
    "away_points_avg5",
    "away_gd_avg5",
    "away_win_rate5",
]


def save_features(features: pd.DataFrame, output_path: Path) -> None:
    """Sauvegarde les features au format Parquet.

    Args:
        features: DataFrame des features à sauvegarder.
        output_path: Chemin du fichier .parquet de sortie.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cols = [c for c in _OUTPUT_COLS if c in features.columns]
    features[cols].to_parquet(output_path, index=False, engine="pyarrow")
    logger.info(
        "Features sauvegardées → %s (%d lignes, %d colonnes)",
        output_path,
        len(features),
        len(cols),
    )


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------


def run(output_path: Path | None = None) -> None:
    """Lance le pipeline de preprocessing complet.

    Args:
        output_path: Chemin de sortie du fichier parquet.
            Défaut: ml/data/processed/features.parquet.
    """
    if output_path is None:
        output_path = (
            Path(__file__).resolve().parent.parent / "data" / "processed" / "features.parquet"
        )

    logger.info("Démarrage preprocessing → %s", output_path)

    engine = create_engine(settings.database_url, pool_pre_ping=True)
    matches_df = load_matches(engine)

    if matches_df.empty:
        logger.warning("Aucun match FINISHED en BDD — preprocessing ignoré.")
        return

    features = compute_features(matches_df)
    save_features(features, output_path)
    logger.info("Preprocessing terminé.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Preprocessing ML — features depuis BDD → Parquet"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Chemin du fichier parquet de sortie.",
    )
    args = parser.parse_args()
    run(output_path=args.output)
