"""Modèle XGBoost pour prédiction de résultat 1X2 (Phase 3E).

Approche complémentaire au Dixon-Coles :
- Dixon-Coles modélise les lambdas de Poisson (force attaque/défense)
- XGBoost apprend directement les probabilités H/D/A depuis les features de forme

Features utilisées :
- home_goals_scored_avg5   : moyenne buts marqués domicile sur 5 derniers matchs
- home_goals_conceded_avg5 : moyenne buts encaissés domicile
- home_points_avg5         : moyenne points domicile (V=3, N=1, D=0)
- home_gd_avg5             : moyenne différence de buts domicile
- home_win_rate5           : taux de victoires domicile
- (idem pour away_*)
- home_advantage           : booléen domicile (toujours 1 ici, gardé pour cohérence)
- diff_goals_scored        : écart offensif home - away
- diff_goals_conceded      : écart défensif home - away
- diff_points              : écart de forme home - away

Fusion avec Dixon-Coles :
    final = w_dc * proba_dc + w_xgb * proba_xgb
    avec w_dc=0.6, w_xgb=0.4 par défaut
"""

import logging
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import log_loss, accuracy_score

logger = logging.getLogger(__name__)

# Features de base issues du pipeline preprocess
BASE_FEATURES = [
    "home_advantage",
    "home_goals_scored_avg5",
    "home_goals_conceded_avg5",
    "home_points_avg5",
    "home_gd_avg5",
    "home_win_rate5",
    "away_goals_scored_avg5",
    "away_goals_conceded_avg5",
    "away_points_avg5",
    "away_gd_avg5",
    "away_win_rate5",
]

# Features derivees (calculees au moment du fit/predict)
DERIVED_FEATURES = [
    "diff_goals_scored",
    "diff_goals_conceded",
    "diff_points",
    "diff_gd",
]

ALL_FEATURES = BASE_FEATURES + DERIVED_FEATURES

# Mapping result -> label numerique
RESULT_TO_INT = {"H": 0, "D": 1, "A": 2}
INT_TO_RESULT = {0: "H", 1: "D", 2: "A"}


def _add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute les features derivees (differences home - away).
    
    Ces features capturent directement l'ecart de forme entre les deux equipes,
    ce qui est plus informatif que les valeurs absolues seules.
    
    Args:
        df: DataFrame avec les features de base.
        
    Returns:
        DataFrame enrichi avec les colonnes derivees.
    """
    df = df.copy()
    df["diff_goals_scored"]   = df["home_goals_scored_avg5"]   - df["away_goals_scored_avg5"]
    df["diff_goals_conceded"] = df["home_goals_conceded_avg5"] - df["away_goals_conceded_avg5"]
    df["diff_points"]         = df["home_points_avg5"]         - df["away_points_avg5"]
    df["diff_gd"]             = df["home_gd_avg5"]             - df["away_gd_avg5"]
    return df


class XGBoostModel:
    """Modele XGBoost de classification multiclasse H/D/A.
    
    Attributes:
        model:      XGBClassifier entraine.
        is_fitted:  True apres fit().
        train_acc:  Accuracy sur le train set.
        val_acc:    Accuracy sur le validation set.
        val_logloss: Log-loss sur le validation set (metrique principale).
    """

    def __init__(self) -> None:
        self.model: xgb.XGBClassifier | None = None
        self.is_fitted: bool = False
        self.train_acc: float = 0.0
        self.val_acc: float = 0.0
        self.val_logloss: float = 0.0

    def fit(self, df: pd.DataFrame) -> dict:
        """Entraine le modele sur le DataFrame de features.
        
        Le DataFrame doit contenir les colonnes BASE_FEATURES + "result".
        On utilise un split temporel : 85% train, 15% validation.
        Le split temporel est crucial en ML sportif pour eviter le data leakage
        (on ne doit pas predire le passe depuis le futur).
        
        Args:
            df: DataFrame issu du pipeline preprocess (features.parquet).
            
        Returns:
            Dict avec les metriques d'entrainement.
        """
        # 1. Nettoyage
        df = df.dropna(subset=BASE_FEATURES + ["result"]).copy()
        df = _add_derived_features(df)
        
        # Encoder la target H->0, D->1, A->2
        df["target"] = df["result"].map(RESULT_TO_INT)
        
        # 2. Split temporel (pas aleatoire : evite le leakage)
        df = df.sort_values("match_date")
        split_idx = int(len(df) * 0.85)
        train_df = df.iloc[:split_idx]
        val_df   = df.iloc[split_idx:]
        
        X_train = train_df[ALL_FEATURES]
        y_train = train_df["target"]
        X_val   = val_df[ALL_FEATURES]
        y_val   = val_df["target"]
        
        logger.info(
            "XGBoost fit: %d train, %d val | periode val: %s -> %s",
            len(train_df), len(val_df),
            val_df["match_date"].min(), val_df["match_date"].max(),
        )
        
        # 3. Modele XGBoost
        # num_class=3 : classification multiclasse H/D/A
        # softprob    : output = probabilites (pas labels)
        # eval_metric : mlogloss = multiclass log-loss
        self.model = xgb.XGBClassifier(
            objective="multi:softprob",
            num_class=3,
            eval_metric="mlogloss",
            n_estimators=500,
            learning_rate=0.02,
            max_depth=3,
            subsample=0.7,
            colsample_bytree=0.7,
            min_child_weight=10,
            gamma=0.5,
            random_state=42,
            verbosity=0,
        )
        
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False,
        )
        
        # 4. Metriques
        train_preds = self.model.predict(X_train)
        val_preds   = self.model.predict(X_val)
        val_probas  = self.model.predict_proba(X_val)
        
        self.train_acc   = accuracy_score(y_train, train_preds)
        self.val_acc     = accuracy_score(y_val, val_preds)
        self.val_logloss = log_loss(y_val, val_probas)
        self.is_fitted   = True
        
        metrics = {
            "train_samples": len(train_df),
            "val_samples":   len(val_df),
            "train_acc":     round(self.train_acc, 4),
            "val_acc":       round(self.val_acc, 4),
            "val_logloss":   round(self.val_logloss, 4),
            "features":      ALL_FEATURES,
        }
        
        logger.info(
            "XGBoost entraine : train_acc=%.3f val_acc=%.3f val_logloss=%.4f",
            self.train_acc, self.val_acc, self.val_logloss,
        )
        return metrics

    def predict(
        self,
        home_features: dict,
        away_features: dict,
    ) -> dict[str, float]:
        """Predit les probabilites H/D/A pour un match.
        
        Args:
            home_features: Dict avec les features de l'equipe domicile
                           (goals_scored_avg5, goals_conceded_avg5, points_avg5,
                            gd_avg5, win_rate5).
            away_features: Dict avec les features de l'equipe exterieure.
            
        Returns:
            Dict {"home_win": float, "draw": float, "away_win": float}.
        """
        if not self.is_fitted or self.model is None:
            raise RuntimeError("Modele non entraine. Appeler fit() d'abord.")
        
        row = {
            "home_advantage":             1.0,
            "home_goals_scored_avg5":     home_features.get("goals_scored_avg5", 1.5),
            "home_goals_conceded_avg5":   home_features.get("goals_conceded_avg5", 1.5),
            "home_points_avg5":           home_features.get("points_avg5", 1.5),
            "home_gd_avg5":               home_features.get("gd_avg5", 0.0),
            "home_win_rate5":             home_features.get("win_rate5", 0.4),
            "away_goals_scored_avg5":     away_features.get("goals_scored_avg5", 1.5),
            "away_goals_conceded_avg5":   away_features.get("goals_conceded_avg5", 1.5),
            "away_points_avg5":           away_features.get("points_avg5", 1.5),
            "away_gd_avg5":               away_features.get("gd_avg5", 0.0),
            "away_win_rate5":             away_features.get("win_rate5", 0.4),
        }
        
        df_row = pd.DataFrame([row])
        df_row = _add_derived_features(df_row)
        
        probas = self.model.predict_proba(df_row[ALL_FEATURES])[0]
        
        return {
            "home_win": float(probas[0]),
            "draw":     float(probas[1]),
            "away_win": float(probas[2]),
        }

    def feature_importance(self) -> dict[str, float]:
        """Retourne l'importance des features (pour debug/analyse).
        
        Returns:
            Dict feature_name -> score d'importance normalise.
        """
        if not self.is_fitted or self.model is None:
            return {}
        scores = self.model.feature_importances_
        return {f: round(float(s), 4) for f, s in zip(ALL_FEATURES, scores)}
