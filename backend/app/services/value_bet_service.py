"""Value Bet Detector — Phase 4F.

Concept :
  Une value bet existe quand notre modele estime une probabilite
  superieure a la probabilite implicite du bookmaker.

  Value = P_modele * cote - 1
  Si Value > 0  -> value bet (le bookmaker sous-evalue cet evenement)
  Si Value > 0.05 -> value bet significative (5% de marge)

  Exemple :
    Cote home = 2.10  -> P_implicite = 1/2.10 = 47.6%
    Notre modele      -> P_modele    = 55%
    Value = 0.55 * 2.10 - 1 = 0.155  -> +15.5% de value !

  ROI attendu sur le long terme = moyenne des values positives.
"""
import logging
from dataclasses import dataclass
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.match_odds import MatchOdds
from app.models.prediction import Prediction

logger = logging.getLogger(__name__)

# Seuil minimum pour considerer une value bet
VALUE_BET_THRESHOLD = 0.05   # 5% minimum
# Seuil pour une value bet forte
VALUE_BET_STRONG    = 0.10   # 10%
# Probabilite minimum du modele (eviter les paris sur des evenements trop improbables)
MIN_MODEL_PROBA     = 0.25


@dataclass
class ValueBet:
    """Represente une value bet detectee."""
    match_id:       int
    market:         str    # "home_win", "draw", "away_win", "over_25", "btts"
    model_proba:    float  # Probabilite selon notre modele
    implied_proba:  float  # Probabilite implicite du bookmaker
    odd:            float  # Cote brute
    value:          float  # Value = model_proba * odd - 1
    bookmaker:      str
    strength:       str    # "strong" | "normal"

    @property
    def expected_roi(self) -> float:
        """ROI attendu en pourcentage."""
        return self.value * 100

    def to_dict(self) -> dict:
        return {
            "match_id":      self.match_id,
            "market":        self.market,
            "model_proba":   round(self.model_proba, 4),
            "implied_proba": round(self.implied_proba, 4),
            "odd":           round(self.odd, 2),
            "value":         round(self.value, 4),
            "expected_roi":  round(self.expected_roi, 2),
            "bookmaker":     self.bookmaker,
            "strength":      self.strength,
        }


def _compute_value(model_proba: float, odd: float) -> float:
    """Calcule la value d une bet.

    Args:
        model_proba : probabilite estimee par notre modele (0-1)
        odd         : cote brute du bookmaker (ex: 2.10)

    Returns:
        Value = model_proba * odd - 1
        Positif = value bet, negatif = pas de value.
    """
    return model_proba * odd - 1.0


def detect_value_bets(match_id: int, db: Session) -> list[ValueBet]:
    """Detecte les value bets pour un match.

    Compare les probabilites de notre modele avec les cotes bookmakers.
    Retourne uniquement les bets avec value > VALUE_BET_THRESHOLD.

    Args:
        match_id : ID interne du match
        db       : session SQLAlchemy

    Returns:
        Liste de ValueBet triee par value decroissante.
    """
    # Recuperer la prediction
    pred = db.execute(
        select(Prediction)
        .where(Prediction.match_id == match_id)
        .order_by(Prediction.created_at.desc())
    ).scalar_one_or_none()

    if not pred:
        logger.debug("Pas de prediction pour match %d", match_id)
        return []

    # Recuperer les cotes
    odds = db.execute(
        select(MatchOdds)
        .where(MatchOdds.match_id == match_id)
        .order_by(MatchOdds.id)
    ).scalars().all()

    if not odds:
        logger.debug("Pas de cotes pour match %d", match_id)
        return []

    # Prendre le premier bookmaker disponible
    best_odds = odds[0]
    bookmaker = best_odds.bookmaker_name or "Unknown"

    value_bets = []

    # Marches a analyser : (nom_marche, proba_modele, cote_bookmaker)
    markets = []

    if pred.home_win_proba and best_odds.home_win:
        markets.append(("home_win", pred.home_win_proba, best_odds.home_win))

    if pred.draw_proba and best_odds.draw:
        markets.append(("draw", pred.draw_proba, best_odds.draw))

    if pred.away_win_proba and best_odds.away_win:
        markets.append(("away_win", pred.away_win_proba, best_odds.away_win))

    if pred.over_25_proba and best_odds.over_25:
        markets.append(("over_25", pred.over_25_proba, best_odds.over_25))

    if pred.btts_proba and best_odds.btts_yes:
        markets.append(("btts", pred.btts_proba, best_odds.btts_yes))

    for market, model_proba, odd in markets:
        if model_proba < MIN_MODEL_PROBA:
            continue

        implied_proba = 1.0 / odd if odd > 0 else 1.0
        value = _compute_value(model_proba, odd)

        if value >= VALUE_BET_THRESHOLD:
            strength = "strong" if value >= VALUE_BET_STRONG else "normal"
            value_bets.append(ValueBet(
                match_id      = match_id,
                market        = market,
                model_proba   = model_proba,
                implied_proba = implied_proba,
                odd           = odd,
                value         = value,
                bookmaker     = bookmaker,
                strength      = strength,
            ))
            logger.info(
                "Value bet %s | %s | odd=%.2f | model=%.1f%% vs implied=%.1f%% | value=+%.1f%%",
                strength, market, odd,
                model_proba * 100, implied_proba * 100, value * 100,
            )

    # Trier par value decroissante
    value_bets.sort(key=lambda x: x.value, reverse=True)
    return value_bets


def scan_upcoming_value_bets(db: Session, min_value: float = VALUE_BET_THRESHOLD) -> list[dict]:
    """Scanne tous les matchs a venir avec cotes et predictions.

    Utile pour le tableau de bord Value Bets du frontend.

    Returns:
        Liste de value bets avec infos match, triee par value.
    """
    from sqlalchemy.orm import joinedload

    # Matchs SCHEDULED avec cotes ET prediction
    matches_with_odds = db.execute(
        select(Match.id)
        .join(MatchOdds, MatchOdds.match_id == Match.id)
        .join(Prediction, Prediction.match_id == Match.id)
        .where(Match.status.in_(["SCHEDULED", "TIMED"]))
        .distinct()
    ).scalars().all()

    all_value_bets = []
    for match_id in matches_with_odds:
        bets = detect_value_bets(match_id, db)
        for bet in bets:
            if bet.value >= min_value:
                # Enrichir avec infos match
                match = db.execute(
                    select(Match)
                    .options(
                        joinedload(Match.home_team),
                        joinedload(Match.away_team),
                        joinedload(Match.competition),
                    )
                    .where(Match.id == match_id)
                ).unique().scalar_one()

                bet_dict = bet.to_dict()
                bet_dict.update({
                    "match_date":  match.match_date.isoformat() if match.match_date else None,
                    "home_team":   match.home_team.name if match.home_team else None,
                    "away_team":   match.away_team.name if match.away_team else None,
                    "competition": match.competition.name if match.competition else None,
                })
                all_value_bets.append(bet_dict)

    all_value_bets.sort(key=lambda x: x["value"], reverse=True)
    logger.info("Scan value bets : %d bets detectes sur %d matchs",
                len(all_value_bets), len(matches_with_odds))
    return all_value_bets
