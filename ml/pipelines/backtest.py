"""Backtesting des modeles de prediction PredictFC (Phase 3F).

Methodology :
- On rejoue les predictions sur les matchs FINISHED avec features disponibles
- Split temporel : on entraine sur les N premiers matchs, on predit le reste
- On compare DC seul vs Ensemble DC+XGBoost
- Metriques : accuracy, calibration, ROI simulé

Metriques calculees :
- Accuracy      : % de bons resultats predits (H/D/A)
- Log-loss      : qualite des probabilites (plus bas = mieux)
- Brier score   : autre mesure de calibration [0,1]
- Calibration   : quand on dit X%, est-ce que ca arrive X% du temps ?
- ROI simule    : si on mise sur le resultat le plus probable, quel ROI ?
"""

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import log_loss, brier_score_loss
from sklearn.calibration import calibration_curve

# Ajouter le chemin ML
ML_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(ML_PATH))

from models.poisson_model import PoissonModel
from models.xgboost_model import XGBoostModel, _add_derived_features, BASE_FEATURES, ALL_FEATURES, RESULT_TO_INT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RESULT_TO_INT = {"H": 0, "D": 1, "A": 2}
INT_TO_RESULT = {0: "H", 1: "D", 2: "A"}


def run_backtest(
    df: pd.DataFrame,
    train_ratio: float = 0.7,
    min_train_matches: int = 500,
) -> dict:
    """Lance le backtesting sur le dataset complet.

    On utilise un split temporel strict :
    - Les 70% premiers matchs (chronologiques) = entrainement
    - Les 30% suivants = test (jamais vus pendant l'entrainement)

    Args:
        df:                  DataFrame features (features.parquet).
        train_ratio:         Ratio train/test.
        min_train_matches:   Minimum de matchs pour entrainer.

    Returns:
        Dict avec toutes les metriques.
    """
    # 1. Nettoyage et tri chronologique
    df = df.dropna(subset=BASE_FEATURES + ["result", "home_score", "away_score"]).copy()
    df = df.sort_values("match_date").reset_index(drop=True)
    df = _add_derived_features(df)
    df["target"] = df["result"].map(RESULT_TO_INT)

    split_idx = max(int(len(df) * train_ratio), min_train_matches)
    train_df = df.iloc[:split_idx].copy()
    test_df  = df.iloc[split_idx:].copy()

    logger.info("Backtest : %d train, %d test", len(train_df), len(test_df))
    logger.info("Periode test : %s -> %s",
                test_df["match_date"].min(), test_df["match_date"].max())

    # 2. Entrainer Dixon-Coles sur train
    logger.info("Entrainement Dixon-Coles...")
    dc_model = PoissonModel()
    dc_train = train_df[["home_team_id", "away_team_id", "home_score", "away_score"]].copy()
    dc_train.columns = ["home_team_id", "away_team_id", "home_score", "away_score"]
    dc_model.fit(dc_train)

    # 3. Entrainer XGBoost sur train
    logger.info("Entrainement XGBoost...")
    xgb_model = XGBoostModel()
    xgb_model.fit(train_df)

    # 4. Predictions sur test
    logger.info("Calcul des predictions sur %d matchs...", len(test_df))

    dc_probas  = []  # [[p_H, p_D, p_A], ...]
    xgb_probas = []
    ens_probas = []  # ensemble 60/40
    true_labels = test_df["target"].tolist()

    for _, row in test_df.iterrows():
        # Dixon-Coles
        try:
            matrix = dc_model.predict(
                int(row["home_team_id"]),
                int(row["away_team_id"]),
            )
            # Calculer H/D/A depuis la matrice de scores
            p_h = float(np.sum(np.tril(matrix, -1)))   # home_score > away_score
            p_d = float(np.sum(np.diag(matrix)))        # egalite
            p_a = float(np.sum(np.triu(matrix, 1)))    # away_score > home_score
            total = p_h + p_d + p_a
            dc_p = [p_h/total, p_d/total, p_a/total]
        except Exception:
            dc_p = [1/3, 1/3, 1/3]

        # XGBoost
        try:
            home_feat = {
                "goals_scored_avg5":   row["home_goals_scored_avg5"],
                "goals_conceded_avg5": row["home_goals_conceded_avg5"],
                "points_avg5":         row["home_points_avg5"],
                "gd_avg5":             row["home_gd_avg5"],
                "win_rate5":           row["home_win_rate5"],
            }
            away_feat = {
                "goals_scored_avg5":   row["away_goals_scored_avg5"],
                "goals_conceded_avg5": row["away_goals_conceded_avg5"],
                "points_avg5":         row["away_points_avg5"],
                "gd_avg5":             row["away_gd_avg5"],
                "win_rate5":           row["away_win_rate5"],
            }
            xgb_p_dict = xgb_model.predict(home_feat, away_feat)
            xgb_p = [xgb_p_dict["home_win"], xgb_p_dict["draw"], xgb_p_dict["away_win"]]
        except Exception:
            xgb_p = [1/3, 1/3, 1/3]

        # Ensemble 60/40
        ens_p = [
            0.6 * dc_p[i] + 0.4 * xgb_p[i]
            for i in range(3)
        ]
        total_ens = sum(ens_p)
        ens_p = [p / total_ens for p in ens_p]

        dc_probas.append(dc_p)
        xgb_probas.append(xgb_p)
        ens_probas.append(ens_p)

    # 5. Metriques
    y_true = np.array(true_labels)

    def compute_metrics(probas: list, name: str) -> dict:
        probas_arr = np.array(probas)
        preds = np.argmax(probas_arr, axis=1)

        accuracy  = float(np.mean(preds == y_true))
        logloss   = log_loss(y_true, probas_arr, labels=[0,1,2])

        # Brier score multiclasse = moyenne des 3 Brier binaires
        brier = np.mean([
            brier_score_loss(
                (y_true == c).astype(int),
                probas_arr[:, c]
            )
            for c in range(3)
        ])

        # Accuracy par résultat
        acc_h = float(np.mean(preds[y_true==0] == 0)) if np.any(y_true==0) else 0
        acc_d = float(np.mean(preds[y_true==1] == 1)) if np.any(y_true==1) else 0
        acc_a = float(np.mean(preds[y_true==2] == 2)) if np.any(y_true==2) else 0

        # ROI simule : mise 1 unite sur le resultat le plus probable
        # Cote implicite = 1/proba (sans marge bookmaker)
        roi_gains = []
        for i, pred in enumerate(preds):
            proba_pred = probas_arr[i, pred]
            cote = 1.0 / proba_pred if proba_pred > 0 else 1.0
            if pred == y_true[i]:
                roi_gains.append(cote - 1)  # gain
            else:
                roi_gains.append(-1)         # perte
        roi = float(np.mean(roi_gains)) * 100  # en %

        logger.info(
            "%s : acc=%.3f logloss=%.4f brier=%.4f roi=%.1f%%",
            name, accuracy, logloss, brier, roi
        )
        return {
            "name":       name,
            "n_matches":  len(y_true),
            "accuracy":   round(accuracy, 4),
            "logloss":    round(logloss, 4),
            "brier":      round(brier, 4),
            "acc_home":   round(acc_h, 4),
            "acc_draw":   round(acc_d, 4),
            "acc_away":   round(acc_a, 4),
            "roi_pct":    round(roi, 2),
        }

    results = {
        "train_matches":  len(train_df),
        "test_matches":   len(test_df),
        "test_period_start": str(test_df["match_date"].min())[:10],
        "test_period_end":   str(test_df["match_date"].max())[:10],
        "baseline_accuracy": round(float(np.mean(y_true == 0)), 4),  # toujours predire H
        "dixon_coles":    compute_metrics(dc_probas,  "Dixon-Coles"),
        "xgboost":        compute_metrics(xgb_probas, "XGBoost"),
        "ensemble":       compute_metrics(ens_probas, "Ensemble 60/40"),
    }
    return results


if __name__ == "__main__":
    import json
    features_path = Path(__file__).parent.parent / "data" / "processed" / "features.parquet"
    df = pd.read_parquet(features_path)
    results = run_backtest(df)

    print()
    print("=" * 60)
    print("RAPPORT BACKTESTING PREDICTFC")
    print("=" * 60)
    print(f"Train : {results['train_matches']} matchs")
    print(f"Test  : {results['test_matches']} matchs ({results['test_period_start']} -> {results['test_period_end']})")
    print(f"Baseline (toujours H) : {results['baseline_accuracy']*100:.1f}%")
    print()
    print(f"{'Modele':<25} {'Accuracy':>10} {'LogLoss':>10} {'Brier':>10} {'ROI%':>8}")
    print("-" * 65)
    for key in ["dixon_coles", "xgboost", "ensemble"]:
        m = results[key]
        print(f"{m['name']:<25} {m['accuracy']*100:>9.1f}% {m['logloss']:>10.4f} {m['brier']:>10.4f} {m['roi_pct']:>7.1f}%")
    print()
    print("Accuracy par type de résultat (Ensemble):")
    ens = results["ensemble"]
    print(f"  Victoire domicile : {ens['acc_home']*100:.1f}%")
    print(f"  Match nul         : {ens['acc_draw']*100:.1f}%")
    print(f"  Victoire exterieur: {ens['acc_away']*100:.1f}%")
