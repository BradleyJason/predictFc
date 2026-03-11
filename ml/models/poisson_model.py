"""Modèle Double Poisson avec correction Dixon-Coles (1997).

Estime les paramètres d'attaque et de défense de chaque équipe
par maximum de vraisemblance, puis prédit la distribution de scores P(i,j).

Référence : Dixon, M.J. & Coles, S.G. (1997). Modelling Association Football
Scores and Inefficiencies in the Football Betting Market.
Applied Statistics, 46(2), 265-280.
"""

import logging

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import gammaln
from scipy.stats import poisson

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Correction Dixon-Coles τ(x, y, λ_h, λ_a, ρ)
# Les matchs faibles scores (0-0, 1-0, 0-1, 1-1) sont sous/sur-représentés
# par rapport au double Poisson pur → correction multiplicative.
# ---------------------------------------------------------------------------


def _tau_vec(
    x: np.ndarray,
    y: np.ndarray,
    lh: np.ndarray,
    la: np.ndarray,
    rho: float,
) -> np.ndarray:
    """Facteur de correction Dixon-Coles — version vectorisée (pour le NLL).

    Args:
        x: Buts domicile observés.
        y: Buts extérieur observés.
        lh: Lambda domicile (buts attendus).
        la: Lambda extérieur (buts attendus).
        rho: Paramètre de correction (typiquement proche de -0.1).

    Returns:
        Vecteur de facteurs τ ≥ 0.
    """
    tau = np.ones(len(x), dtype=float)
    m00 = (x == 0) & (y == 0)
    m10 = (x == 1) & (y == 0)
    m01 = (x == 0) & (y == 1)
    m11 = (x == 1) & (y == 1)
    tau[m00] = 1.0 - lh[m00] * la[m00] * rho
    tau[m10] = 1.0 + la[m10] * rho
    tau[m01] = 1.0 + lh[m01] * rho
    tau[m11] = 1.0 - rho
    return tau


def _tau_scalar(x: int, y: int, lh: float, la: float, rho: float) -> float:
    """Facteur de correction Dixon-Coles — version scalaire (pour la matrice).

    Args:
        x: Buts domicile.
        y: Buts extérieur.
        lh: Lambda domicile.
        la: Lambda extérieur.
        rho: Paramètre de correction.

    Returns:
        Facteur multiplicatif τ.
    """
    if x == 0 and y == 0:
        return 1.0 - lh * la * rho
    if x == 1 and y == 0:
        return 1.0 + la * rho
    if x == 0 and y == 1:
        return 1.0 + lh * rho
    if x == 1 and y == 1:
        return 1.0 - rho
    return 1.0


# ---------------------------------------------------------------------------
# Modèle
# ---------------------------------------------------------------------------


class PoissonModel:
    """Double Poisson avec correction Dixon-Coles.

    Pour chaque match (équipe i à domicile, équipe j à l'extérieur) :
        λ_home = exp(α_i - β_j + γ)    (α = attaque, β = défense, γ = avantage domicile)
        λ_away = exp(α_j - β_i)

    La correction Dixon-Coles ajuste les probabilités des scores faibles
    (0-0, 1-0, 0-1, 1-1) grâce au paramètre ρ.

    Attributes:
        max_goals: Taille de la matrice (max_goals+1) × (max_goals+1).
        teams: Liste des IDs d'équipes vus à l'entraînement.
        attack: Tableau des forces d'attaque par équipe (indexé par _team_idx).
        defense: Tableau des forces défensives par équipe.
        home_adv: Avantage domicile (scalaire).
        rho: Paramètre de correction Dixon-Coles.
    """

    def __init__(self, max_goals: int = 5) -> None:
        """Initialise le modèle.

        Args:
            max_goals: Nombre maximum de buts par équipe dans la matrice.
                La matrice résultante est (max_goals+1) × (max_goals+1).
        """
        self.max_goals = max_goals
        self.teams: list[int] = []
        self._team_idx: dict[int, int] = {}
        self.attack: np.ndarray = np.array([])
        self.defense: np.ndarray = np.array([])
        self.home_adv: float = 0.3
        self.rho: float = -0.1
        self._fitted: bool = False

    # ------------------------------------------------------------------
    # Entraînement
    # ------------------------------------------------------------------

    def fit(self, df: pd.DataFrame) -> "PoissonModel":
        """Estime les paramètres attack/defense de chaque équipe par MLE.

        Utilise L-BFGS-B pour minimiser la log-vraisemblance négative
        du modèle Dixon-Coles sur les matchs terminés.

        Args:
            df: DataFrame avec colonnes obligatoires :
                home_team_id (int), away_team_id (int),
                home_score (int), away_score (int).
                Seules les lignes sans NaN dans les scores sont utilisées.

        Returns:
            self — permet le chaînage fit().predict().
        """
        df = df.dropna(subset=["home_score", "away_score"]).copy()
        df["home_score"] = df["home_score"].astype(int)
        df["away_score"] = df["away_score"].astype(int)

        if len(df) < 10:
            raise ValueError(
                f"Pas assez de matchs pour entraîner le modèle ({len(df)} < 10)."
            )

        # Index des équipes
        all_teams = sorted(
            set(df["home_team_id"].unique()) | set(df["away_team_id"].unique())
        )
        self.teams = all_teams
        self._team_idx = {t: i for i, t in enumerate(all_teams)}
        n = len(all_teams)

        # Conversion en indices
        home_idx = df["home_team_id"].map(self._team_idx).to_numpy(dtype=int)
        away_idx = df["away_team_id"].map(self._team_idx).to_numpy(dtype=int)
        home_scores = df["home_score"].to_numpy(dtype=int)
        away_scores = df["away_score"].to_numpy(dtype=int)

        # Vecteur de paramètres initial :
        # params[:n]      = attack[0..n-1]
        # params[n:2n]    = defense[0..n-1]
        # params[2n]      = home_adv
        # params[2n+1]    = rho
        x0 = np.zeros(2 * n + 2)
        x0[2 * n] = 0.3    # home_adv (avantage domicile habituel)
        x0[2 * n + 1] = -0.1  # rho (légère sous-représentation des petits scores)

        # rho contraint dans [-0.5, 0.5] pour garantir τ > 0
        bounds = [(None, None)] * (2 * n) + [(None, None), (-0.5, 0.5)]

        result = minimize(
            fun=self._neg_log_likelihood,
            x0=x0,
            args=(n, home_idx, away_idx, home_scores, away_scores),
            method="L-BFGS-B",
            bounds=bounds,
            options={"maxfun": 100000, "maxiter": 1000, "ftol": 1e-9, "gtol": 1e-6},
        )

        if not result.success:
            logger.warning(
                "Optimisation L-BFGS-B non convergée après %d itérations : %s",
                result.nit,
                result.message,
            )

        params = result.x

        # Centrage des paramètres d'attaque (identifiabilité)
        # α_i - β_j est invariant → on peut centrer α sans changer les λ
        attack_raw = params[:n]
        mu = attack_raw.mean()
        self.attack = attack_raw - mu
        self.defense = params[n : 2 * n] - mu  # même décalage pour rester cohérent
        self.home_adv = float(params[2 * n])
        self.rho = float(params[2 * n + 1])
        self._fitted = True

        logger.info(
            "PoissonModel ajusté — %d matchs, %d équipes | "
            "home_adv=%.3f rho=%.3f NLL=%.1f",
            len(df),
            n,
            self.home_adv,
            self.rho,
            result.fun,
        )
        return self

    @staticmethod
    def _neg_log_likelihood(
        params: np.ndarray,
        n: int,
        home_idx: np.ndarray,
        away_idx: np.ndarray,
        home_scores: np.ndarray,
        away_scores: np.ndarray,
    ) -> float:
        """Log-vraisemblance négative Dixon-Coles (vectorisée).

        Args:
            params: Vecteur [attack×n, defense×n, home_adv, rho].
            n: Nombre d'équipes.
            home_idx: Indices des équipes à domicile.
            away_idx: Indices des équipes à l'extérieur.
            home_scores: Scores observés de l'équipe à domicile.
            away_scores: Scores observés de l'équipe à l'extérieur.

        Returns:
            NLL (à minimiser).
        """
        attack = params[:n]
        defense = params[n : 2 * n]
        home_adv = params[2 * n]
        rho = params[2 * n + 1]

        lh = np.exp(attack[home_idx] - defense[away_idx] + home_adv)
        la = np.exp(attack[away_idx] - defense[home_idx])

        # Log-vraisemblance Poisson de base
        ll = (
            home_scores * np.log(lh) - lh - gammaln(home_scores + 1)
            + away_scores * np.log(la) - la - gammaln(away_scores + 1)
        )

        # Correction Dixon-Coles
        tau = _tau_vec(home_scores, away_scores, lh, la, rho)
        with np.errstate(invalid="ignore", divide="ignore"):
            log_tau = np.where(tau > 1e-10, np.log(tau), -1e6)

        return float(-np.sum(ll + log_tau))

    # ------------------------------------------------------------------
    # Prédiction
    # ------------------------------------------------------------------

    def predict(self, home_team_id: int, away_team_id: int) -> np.ndarray:
        """Prédit la matrice de scores P(i, j) pour un match.

        Args:
            home_team_id: ID interne de l'équipe à domicile.
            away_team_id: ID interne de l'équipe extérieure.

        Returns:
            Matrice numpy de forme (max_goals+1, max_goals+1) où
            matrix[i, j] = P(home_score=i, away_score=j).
            La somme de tous les éléments est ≈ 1.

        Raises:
            RuntimeError: Si fit() n'a pas été appelé.
        """
        if not self._fitted:
            raise RuntimeError("Appelez fit() avant predict().")

        lh, la = self._lambdas(home_team_id, away_team_id)
        return self._build_matrix(lh, la)

    def expected_goals(self, home_team_id: int, away_team_id: int) -> tuple[float, float]:
        """Retourne (λ_home, λ_away) — les buts attendus pour ce match.

        Args:
            home_team_id: ID de l'équipe à domicile.
            away_team_id: ID de l'équipe à l'extérieur.

        Returns:
            Tuple (lambda_home, lambda_away).
        """
        return self._lambdas(home_team_id, away_team_id)

    def _lambdas(self, home_id: int, away_id: int) -> tuple[float, float]:
        """Calcule λ_home et λ_away avec fallback sur la moyenne si équipe inconnue."""
        h_att = self.attack[self._team_idx[home_id]] if home_id in self._team_idx else 0.0
        h_def = self.defense[self._team_idx[home_id]] if home_id in self._team_idx else 0.0
        a_att = self.attack[self._team_idx[away_id]] if away_id in self._team_idx else 0.0
        a_def = self.defense[self._team_idx[away_id]] if away_id in self._team_idx else 0.0

        lh = float(np.exp(h_att - a_def + self.home_adv))
        la = float(np.exp(a_att - h_def))
        return lh, la

    def _build_matrix(self, lh: float, la: float) -> np.ndarray:
        """Construit la matrice P(i,j) avec correction Dixon-Coles.

        Args:
            lh: Lambda de l'équipe à domicile.
            la: Lambda de l'équipe à l'extérieur.

        Returns:
            Matrice (max_goals+1, max_goals+1) normalisée.
        """
        n = self.max_goals + 1
        scores = np.arange(n)

        # Produit externe des PMF Poisson
        p_home = poisson.pmf(scores, lh)  # shape (n,)
        p_away = poisson.pmf(scores, la)  # shape (n,)
        matrix = np.outer(p_home, p_away)  # shape (n, n)

        # Application de la correction Dixon-Coles sur les 4 cases (0/1 × 0/1)
        for i in range(min(2, n)):
            for j in range(min(2, n)):
                matrix[i, j] *= _tau_scalar(i, j, lh, la, self.rho)

        # Renormalisation (la correction peut légèrement modifier la somme)
        total = matrix.sum()
        if total > 0:
            matrix /= total

        return matrix
