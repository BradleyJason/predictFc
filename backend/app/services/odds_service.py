"""Service cotes bookmakers (Phase 4C).

Concept cle — probabilites implicites :
  Une cote de 1.85 signifie que le bookmaker estime P(home) = 1/1.85 = 54.1%
  Mais la somme depasse 100% (marge bookmaker ~5-8%).
  On normalise pour obtenir des probas reelles : P_norm = P_brute / somme_totale

Blend final :
  prediction = w_model * P_model + w_bookie * P_bookie
  Avec w_bookie eleve car les cotes sont tres predictives.
"""
import logging
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.match_odds import MatchOdds
from app.services.api_football_client import api_football_client

logger = logging.getLogger(__name__)

# Bookmakers preferes par ordre de priorite (les plus fiables)
PREFERRED_BOOKMAKERS = [6, 1, 11, 8, 3]  # Bwin, 10Bet, 888sport, Betway, Betclic
PREFERRED_BOOKMAKER_NAME = "Bwin"


def _extract_odds_from_bookmaker(bets: list[dict]) -> dict:
    """Extrait H/D/A, Over2.5, BTTS depuis la liste de bets d un bookmaker.

    Args:
        bets: Liste de paris du bookmaker (ex: Match Winner, Goals Over/Under...)

    Returns:
        Dict avec home_win, draw, away_win, over_25, under_25, btts_yes, btts_no
        Valeurs None si non disponibles.
    """
    result = {
        "home_win": None, "draw": None, "away_win": None,
        "over_25": None, "under_25": None,
        "btts_yes": None, "btts_no": None,
    }

    for bet in bets:
        name = bet.get("name", "")
        values = {v["value"]: float(v["odd"]) for v in bet.get("values", []) if v.get("odd")}

        if name == "Match Winner":
            result["home_win"] = values.get("Home")
            result["draw"]     = values.get("Draw")
            result["away_win"] = values.get("Away")

        elif name == "Goals Over/Under" or name == "Over/Under":
            result["over_25"]  = values.get("Over 2.5")
            result["under_25"] = values.get("Under 2.5")

        elif name == "Both Teams Score":
            result["btts_yes"] = values.get("Yes")
            result["btts_no"]  = values.get("No")

    return result


def odds_to_probas(home_win: float, draw: float, away_win: float) -> dict:
    """Convertit les cotes H/D/A en probabilites normalisees.

    Retire la marge du bookmaker (overround) par normalisation.

    Exemple :
      cotes = 1.85 / 3.40 / 4.20
      P_brutes = 0.541 / 0.294 / 0.238  (somme = 1.073 = marge 7.3%)
      P_norm   = 0.504 / 0.274 / 0.222  (somme = 1.000)

    Args:
        home_win: Cote victoire domicile (ex: 1.85)
        draw:     Cote match nul (ex: 3.40)
        away_win: Cote victoire exterieur (ex: 4.20)

    Returns:
        Dict avec home_win_proba, draw_proba, away_win_proba normalises.
    """
    p_home = 1.0 / home_win
    p_draw = 1.0 / draw
    p_away = 1.0 / away_win
    total  = p_home + p_draw + p_away  # Overround bookmaker

    margin = (total - 1.0) * 100
    logger.debug("Marge bookmaker : %.1f%%", margin)

    return {
        "home_win_proba": p_home / total,
        "draw_proba":     p_draw / total,
        "away_win_proba": p_away / total,
    }


def import_odds_for_match(match_id: int, db: Session) -> bool:
    """Importe les cotes depuis api-football pour un match.

    Args:
        match_id: ID interne du match.

    Returns:
        True si des cotes ont ete importees, False sinon.
    """
    match = db.get(Match, match_id)
    if not match or not match.api_football_id:
        logger.warning("Match %d sans api_football_id, skip.", match_id)
        return False

    try:
        bookmakers = api_football_client.get_odds(match.api_football_id)
    except Exception as exc:
        logger.error("Erreur API odds match %d : %s", match_id, exc)
        return False

    if not bookmakers:
        logger.info("Aucune cote disponible pour match %d", match_id)
        return False

    # Choisir le bookmaker prefere disponible
    chosen = None
    for bk_id in PREFERRED_BOOKMAKERS:
        for bk in bookmakers:
            if bk.get("id") == bk_id:
                chosen = bk
                break
        if chosen:
            break

    # Fallback : premier bookmaker disponible
    if not chosen:
        chosen = bookmakers[0]

    bk_name = chosen.get("name", "Unknown")
    bk_id   = chosen.get("id", 0)
    raw     = _extract_odds_from_bookmaker(chosen.get("bets", []))

    if not raw["home_win"] or not raw["draw"] or not raw["away_win"]:
        logger.warning("Cotes H/D/A manquantes pour match %d (%s)", match_id, bk_name)
        return False

    # Upsert : supprimer l ancienne entree si elle existe
    existing = db.execute(
        select(MatchOdds).where(
            MatchOdds.match_id == match_id,
            MatchOdds.bookmaker_id == bk_id,
        )
    ).scalar_one_or_none()

    if existing:
        existing.home_win      = raw["home_win"]
        existing.draw          = raw["draw"]
        existing.away_win      = raw["away_win"]
        existing.over_25       = raw["over_25"]
        existing.under_25      = raw["under_25"]
        existing.btts_yes      = raw["btts_yes"]
        existing.btts_no       = raw["btts_no"]
        existing.bookmaker_name= bk_name
    else:
        odds = MatchOdds(
            match_id       = match_id,
            bookmaker_id   = bk_id,
            bookmaker_name = bk_name,
            home_win       = raw["home_win"],
            draw           = raw["draw"],
            away_win       = raw["away_win"],
            over_25        = raw["over_25"],
            under_25       = raw["under_25"],
            btts_yes       = raw["btts_yes"],
            btts_no        = raw["btts_no"],
        )
        db.add(odds)

    db.commit()
    logger.info(
        "Cotes importees match %d (%s) : H=%.2f D=%.2f A=%.2f",
        match_id, bk_name, raw["home_win"], raw["draw"], raw["away_win"],
    )
    return True


def get_odds_for_match(match_id: int, db: Session) -> MatchOdds | None:
    """Retourne les cotes BDD pour un match (bookmaker prefere)."""
    return db.execute(
        select(MatchOdds)
        .where(MatchOdds.match_id == match_id)
        .order_by(MatchOdds.fetched_at.desc())
    ).scalar_one_or_none()


def blend_with_odds(
    model_probas: dict,
    odds: MatchOdds,
    w_model: float = 0.35,
    w_bookie: float = 0.65,
) -> dict:
    """Fusionne les probabilites modele avec les probabilites implicites bookmaker.

    Les cotes bookmakers sont tres predictives (meilleurs que la plupart des modeles).
    On leur donne donc un poids majoritaire de 65%.

    Poids par defaut :
      - Modele (DC + XGBoost) : 35%
      - Bookmaker              : 65%

    Args:
        model_probas: Dict avec home_win_proba, draw_proba, away_win_proba du modele.
        odds:         Objet MatchOdds depuis la BDD.
        w_model:      Poids du modele (defaut 0.35).
        w_bookie:     Poids du bookmaker (defaut 0.65).

    Returns:
        Dict avec probabilites blendees et normalisees.
    """
    bookie_probas = odds_to_probas(odds.home_win, odds.draw, odds.away_win)

    hw = w_model * model_probas["home_win_proba"] + w_bookie * bookie_probas["home_win_proba"]
    dr = w_model * model_probas["draw_proba"]     + w_bookie * bookie_probas["draw_proba"]
    aw = w_model * model_probas["away_win_proba"] + w_bookie * bookie_probas["away_win_proba"]
    total = hw + dr + aw

    blended = {
        "home_win_proba":  hw / total,
        "draw_proba":      dr / total,
        "away_win_proba":  aw / total,
        "bookie_home":     bookie_probas["home_win_proba"],
        "bookie_draw":     bookie_probas["draw_proba"],
        "bookie_away":     bookie_probas["away_win_proba"],
        "bookie_name":     odds.bookmaker_name,
        "odds_home_win":   odds.home_win,
        "odds_draw":       odds.draw,
        "odds_away_win":   odds.away_win,
    }

    logger.info(
        "Blend odds : modele=(%.2f/%.2f/%.2f) bookie=(%.2f/%.2f/%.2f) -> (%.2f/%.2f/%.2f)",
        model_probas["home_win_proba"], model_probas["draw_proba"], model_probas["away_win_proba"],
        bookie_probas["home_win_proba"], bookie_probas["draw_proba"], bookie_probas["away_win_proba"],
        blended["home_win_proba"], blended["draw_proba"], blended["away_win_proba"],
    )
    return blended
