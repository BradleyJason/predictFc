"""Modèle Double Poisson avec correction Dixon-Coles (1997) + pondération temporelle.

Nouveautés Phase 3A :
- Paramètre `xi` : pondération temporelle exponentielle (matchs récents pèsent plus)
- `form_weight_home` / `form_weight_away` : multiplicateurs de forme sur les lambdas
- `fit()` accepte une colonne `days_ago` optionnelle

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
# Correction Dixon-Coles τ
# ---------------------------------------------------------------------------

def _tau_vec(
    x: np.ndarray,
    y: np.ndarray,
    lh: np.ndarray,
    la: np.ndarray,
    rho: float,
) -> np.ndarray:
    """Facteur de correction Dixon-Coles vectorisé (utilisé dans la NLL).

    Corrige la sous/sur-représentation des scores faibles (0-0, 1-0, 0-1, 1-1)
    par rapport au double Poisson pur.

    Args:
        x:   Buts domicile observés.
        y:   Buts extérieur observés.
        lh:  Lambda domicile.
        la:  Lambda extérieur.
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
    """Facteur de correction Dixon-Coles scalaire (utilisé dans la matrice finale).

    Args:
        x:   Buts domicile.
        y:   Buts extérieur.
        lh:  Lambda domicile.
        la:  Lambda extérieur.
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
    """Double Poisson avec correction Dixon-Coles + pondération temporelle.

    Pour chaque match (équipe i à domicile, équipe j à l'extérieur) :
        λ_home = exp(α_i - β_j + γ) * form_weight_home
        λ_away = exp(α_j - β_i)     * form_weight_away

    La pondération temporelle assigne à chaque match un poids :
        w = exp(-xi * days_ago)
    → les matchs récents influencent plus l'estimation des paramètres.

    Attributes:
        max_goals:  Taille de la matrice de scores.
        xi:         Taux de décroissance temporelle (0 = pas de pondération).
        teams:      Liste des IDs d'équipes vus à l'entraînement.
        attack:     Forces d'attaque par équipe.
        defense:    Forces défensives par équipe.
        home_adv:   Avantage domicile.
        rho:        Paramètre de correction Dixon-Coles.
    """

    def __init__(self, max_goals: int = 6, xi: float = 0.0015) -> None:
        """Initialise le modèle.

        Args:
            max_goals: Score maximum considéré dans la matrice.
            xi:        Taux de décroissance temporelle.
                       0.0015 ≈ matchs de 2 ans pèsent ~33% d'un match récent.
                       0 = tous les matchs pèsent pareil (comportement original).
        """
        self.max_goals = max_goals
        self.xi = xi
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
        """Estime les paramètres par MLE avec pondération temporelle optionnelle.

        Args:
            df: DataFrame avec colonnes obligatoires :
                  home_team_id, away_team_id, home_score, away_score
                Colonne optionnelle :
                  days_ago (int) — nombre de jours écoulés depuis le match.
                  Si absente, tous les matchs ont le même poids (xi ignoré).

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

        # ── Calcul des poids temporels ──────────────────────────────────────
        # Si days_ago est disponible et xi > 0 : w = exp(-xi * days_ago)
        # Sinon : tous les poids = 1.0
        if "days_ago" in df.columns and self.xi > 0:
            days = df["days_ago"].fillna(df["days_ago"].median()).to_numpy(dtype=float)
            weights = np.exp(-self.xi * days)
            weights = weights / weights.mean()  # normalisation : moyenne = 1
            logger.info(
                "Pondération temporelle xi=%.4f | poids min=%.3f max=%.3f",
                self.xi,
                weights.min(),
                weights.max(),
            )
        else:
            weights = np.ones(len(df), dtype=float)
            logger.info("Pas de pondération temporelle (days_ago absent ou xi=0).")

        # ── Index des équipes ───────────────────────────────────────────────
        all_teams = sorted(
            set(df["home_team_id"].unique()) | set(df["away_team_id"].unique())
        )
        self.teams = all_teams
        self._team_idx = {t: i for i, t in enumerate(all_teams)}
        n = len(all_teams)

        home_idx = df["home_team_id"].map(self._team_idx).to_numpy(dtype=int)
        away_idx = df["away_team_id"].map(self._team_idx).to_numpy(dtype=int)
        home_scores = df["home_score"].to_numpy(dtype=int)
        away_scores = df["away_score"].to_numpy(dtype=int)

        # ── Optimisation L-BFGS-B ──────────────────────────────────────────
        # params[:n]   = attack[0..n-1]
        # params[n:2n] = defense[0..n-1]
        # params[2n]   = home_adv
        # params[2n+1] = rho
        x0 = np.zeros(2 * n + 2)
        x0[2 * n] = 0.3
        x0[2 * n + 1] = -0.1

        bounds = [(None, None)] * (2 * n) + [(None, None), (-0.5, 0.5)]

        result = minimize(
            fun=self._neg_log_likelihood,
            x0=x0,
            args=(n, home_idx, away_idx, home_scores, away_scores, weights),
            method="L-BFGS-B",
            bounds=bounds,
            options={"maxfun": 100_000, "maxiter": 1_000, "ftol": 1e-9, "gtol": 1e-6},
        )

        if not result.success:
            logger.warning(
                "L-BFGS-B non convergé après %d itérations : %s",
                result.nit,
                result.message,
            )

        params = result.x

        # ── Centrage (identifiabilité) ──────────────────────────────────────
        # α_i - β_j est invariant par translation → on centre pour stabiliser.
        mu = params[:n].mean()
        self.attack = params[:n] - mu
        self.defense = params[n : 2 * n] - mu
        self.home_adv = float(params[2 * n])
        self.rho = float(params[2 * n + 1])
        self._fitted = True

        logger.info(
            "PoissonModel ajusté — %d matchs, %d équipes | "
            "home_adv=%.3f  rho=%.3f  NLL=%.1f",
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
        weights: np.ndarray,
    ) -> float:
        """Log-vraisemblance négative Dixon-Coles pondérée.

        Chaque match contribue à la NLL proportionnellement à son poids w_i :
            NLL = -Σ w_i * [log P_poisson(x_i|λ_h) + log P_poisson(y_i|λ_a) + log τ_i]

        Args:
            params:      Vecteur [attack×n, defense×n, home_adv, rho].
            n:           Nombre d'équipes.
            home_idx:    Indices des équipes à domicile.
            away_idx:    Indices des équipes à l'extérieur.
            home_scores: Scores observés domicile.
            away_scores: Scores observés extérieur.
            weights:     Poids temporels par match (même longueur que home_idx).

        Returns:
            NLL pondérée (scalaire à minimiser).
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

        # ── Pondération temporelle ──────────────────────────────────────────
        # Sans pondération (weights = ones), c'est strictement équivalent
        # à l'ancienne NLL non pondérée.
        return float(-np.sum(weights * (ll + log_tau)))

    # ------------------------------------------------------------------
    # Prédiction
    # ------------------------------------------------------------------

    def predict(
        self,
        home_team_id: int,
        away_team_id: int,
        form_weight_home: float = 1.0,
        form_weight_away: float = 1.0,
    ) -> np.ndarray:
        """Prédit la matrice de scores P(i,j) pour un match.

        Args:
            home_team_id:      ID de l'équipe à domicile.
            away_team_id:      ID de l'équipe à l'extérieur.
            form_weight_home:  Multiplicateur forme domicile (1.0 = neutre).
                               > 1.0 → équipe en forme, lambdas augmentés.
                               < 1.0 → équipe en mauvaise forme.
            form_weight_away:  Idem pour l'extérieur.

        Returns:
            Matrice numpy (max_goals+1, max_goals+1) où
            matrix[i, j] = P(home_score=i, away_score=j), somme ≈ 1.
        """
        if not self._fitted:
            raise RuntimeError("Appelez fit() avant predict().")

        lh, la = self._lambdas(home_team_id, away_team_id)

        # Application des multiplicateurs de forme
        lh *= max(0.5, min(form_weight_home, 2.0))  # clamp [0.5, 2.0]
        la *= max(0.5, min(form_weight_away, 2.0))

        return self._build_matrix(lh, la)

    def expected_goals(
        self,
        home_team_id: int,
        away_team_id: int,
        form_weight_home: float = 1.0,
        form_weight_away: float = 1.0,
    ) -> tuple[float, float]:
        """Retourne (λ_home, λ_away) après application des poids de forme.

        Args:
            home_team_id:     ID domicile.
            away_team_id:     ID extérieur.
            form_weight_home: Multiplicateur forme domicile.
            form_weight_away: Multiplicateur forme extérieur.

        Returns:
            Tuple (lambda_home, lambda_away).
        """
        lh, la = self._lambdas(home_team_id, away_team_id)
        lh *= max(0.5, min(form_weight_home, 2.0))
        la *= max(0.5, min(form_weight_away, 2.0))
        return lh, la

    def _lambdas(self, home_id: int, away_id: int) -> tuple[float, float]:
        """Calcule λ_home et λ_away bruts (sans forme), avec fallback si équipe inconnue."""
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
            lh: Lambda domicile (après application de la forme).
            la: Lambda extérieur.

        Returns:
            Matrice (max_goals+1, max_goals+1) normalisée.
        """
        n = self.max_goals + 1
        scores = np.arange(n)

        p_home = poisson.pmf(scores, lh)
        p_away = poisson.pmf(scores, la)
        matrix = np.outer(p_home, p_away)

        for i in range(min(2, n)):
            for j in range(min(2, n)):
                matrix[i, j] *= _tau_scalar(i, j, lh, la, self.rho)

        total = matrix.sum()
        if total > 0:
            matrix /= total

        return matrix
