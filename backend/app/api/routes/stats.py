"""Route pour les statistiques détaillées d'un match (forme, H2H, moyennes)."""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.match import Match

logger = logging.getLogger(__name__)
router = APIRouter(tags=["stats"])

# ── Schémas réponse ───────────────────────────────────────────────────────────

class MatchResult(BaseModel):
    date: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    result: str
    competition: str

class TeamForm(BaseModel):
    team_id: int
    team_name: str
    crest_url: Optional[str] = None
    played: int
    wins: int
    draws: int
    losses: int
    goals_scored: int
    goals_conceded: int
    goals_scored_avg: float
    goals_conceded_avg: float
    win_pct: float
    clean_sheets: int
    form_5: list[str]
    last_5: list[MatchResult]

class H2HResult(BaseModel):
    total_played: int
    home_wins: int
    away_wins: int
    draws: int
    last_5: list[MatchResult]

class MatchStatsOut(BaseModel):
    match_id: int
    is_finished: bool
    # Résultat du match courant (si FINISHED)
    match_result: Optional[MatchResult] = None
    home_stats: TeamForm
    away_stats: TeamForm
    h2h: H2HResult


# ── Helpers ───────────────────────────────────────────────────────────────────

def _team_form(
    db: Session,
    team_id: int,
    exclude_match_id: Optional[int],  # None = inclure tous les matchs
    n: int = 10,
) -> list[Match]:
    conditions = [
        Match.status == "FINISHED",
        or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
    ]
    if exclude_match_id is not None:
        conditions.append(Match.id != exclude_match_id)

    stmt = (
        select(Match)
        .where(and_(*conditions))
        .order_by(Match.match_date.desc())
        .limit(n)
    )
    return list(db.scalars(stmt).all())


def _result_for_team(match: Match, team_id: int) -> str:
    if match.home_score is None or match.away_score is None:
        return "?"
    if match.home_team_id == team_id:
        if match.home_score > match.away_score:  return "W"
        if match.home_score == match.away_score: return "D"
        return "L"
    else:
        if match.away_score > match.home_score:  return "W"
        if match.away_score == match.home_score: return "D"
        return "L"


def _goals_for_team(match: Match, team_id: int) -> tuple[int, int]:
    if match.home_score is None or match.away_score is None:
        return 0, 0
    if match.home_team_id == team_id:
        return match.home_score, match.away_score
    return match.away_score, match.home_score


def _build_match_result(match: Match, team_id: int) -> MatchResult:
    home_name = (match.home_team.short_name or match.home_team.name) if match.home_team else "?"
    away_name = (match.away_team.short_name or match.away_team.name) if match.away_team else "?"
    return MatchResult(
        date=match.match_date.strftime("%d/%m/%Y"),
        home_team=home_name,
        away_team=away_name,
        home_score=match.home_score or 0,
        away_score=match.away_score or 0,
        result=_result_for_team(match, team_id),
        competition=match.competition.code if match.competition else "?",
    )


def _compute_team_stats(
    db: Session,
    team_id: int,
    team_name: str,
    crest_url: Optional[str],
    exclude_match_id: Optional[int],  # None = inclure le match courant (FINISHED)
) -> TeamForm:
    matches = _team_form(db, team_id, exclude_match_id, n=10)

    wins = draws = losses = goals_scored = goals_conceded = clean_sheets = 0
    for m in matches:
        r = _result_for_team(m, team_id)
        gs, gc = _goals_for_team(m, team_id)
        goals_scored   += gs
        goals_conceded += gc
        if gc == 0: clean_sheets += 1
        if r == "W":   wins   += 1
        elif r == "D": draws  += 1
        else:          losses += 1

    played = len(matches)
    last_5_matches = matches[:5]

    return TeamForm(
        team_id=team_id,
        team_name=team_name,
        crest_url=crest_url,
        played=played,
        wins=wins,
        draws=draws,
        losses=losses,
        goals_scored=goals_scored,
        goals_conceded=goals_conceded,
        goals_scored_avg=round(goals_scored / played, 2) if played else 0,
        goals_conceded_avg=round(goals_conceded / played, 2) if played else 0,
        win_pct=round(wins / played * 100, 1) if played else 0,
        clean_sheets=clean_sheets,
        form_5=[_result_for_team(m, team_id) for m in last_5_matches],
        last_5=[_build_match_result(m, team_id) for m in last_5_matches],
    )


def _get_team_ids(db: Session, team_id: int) -> list[int]:
    """Retourne tous les IDs correspondant à la même équipe (doublons nom/api_football_id)."""
    from app.models.team import Team
    from sqlalchemy import text

    team = db.get(Team, team_id)
    if not team:
        return [team_id]

    ids = set([team_id])

    # 1. Même api_football_id
    if team.api_football_id:
        rows = db.execute(
            text("SELECT id FROM teams WHERE api_football_id = :aid"),
            {"aid": team.api_football_id}
        ).fetchall()
        for r in rows:
            ids.add(r[0])

    # 2. Nom similaire (normalise : retire FC, AS, US, SC, etc.)
    import re
    def normalize(n: str) -> str:
        n = n.lower()
        for prefix in [r"^fc\s+", r"^as\s+", r"^us\s+", r"^sc\s+", r"^ac\s+", r"^rc\s+", r"^cd\s+", r"^rcd\s+"]:
            n = re.sub(prefix, "", n)
        return n.strip()

    base = normalize(team.name)
    all_teams = db.execute(text("SELECT id, name FROM teams")).fetchall()
    for t in all_teams:
        if normalize(t[1]) == base:
            ids.add(t[0])

    return list(ids)


def _compute_h2h(
    db: Session,
    home_team_id: int,
    away_team_id: int,
    exclude_match_id: Optional[int],
) -> H2HResult:
    # Récupère tous les IDs équivalents (doublons historiques)
    home_ids = _get_team_ids(db, home_team_id)
    away_ids = _get_team_ids(db, away_team_id)

    conditions = [
        Match.status == "FINISHED",
        or_(
            and_(Match.home_team_id.in_(home_ids), Match.away_team_id.in_(away_ids)),
            and_(Match.home_team_id.in_(away_ids), Match.away_team_id.in_(home_ids)),
        ),
    ]
    if exclude_match_id is not None:
        conditions.append(Match.id != exclude_match_id)

    stmt = (
        select(Match)
        .where(and_(*conditions))
        .order_by(Match.match_date.desc())
        .limit(10)
    )
    matches = list(db.scalars(stmt).all())

    home_wins = away_wins = draws = 0
    for m in matches:
        if m.home_score is None or m.away_score is None:
            continue
        if m.home_team_id == home_team_id:
            if m.home_score > m.away_score:    home_wins += 1
            elif m.home_score == m.away_score: draws     += 1
            else:                              away_wins += 1
        else:
            if m.away_score > m.home_score:    home_wins += 1
            elif m.away_score == m.home_score: draws     += 1
            else:                              away_wins += 1

    last_5 = [_build_match_result(m, home_team_id) for m in matches[:5]]

    return H2HResult(
        total_played=len(matches),
        home_wins=home_wins,
        away_wins=away_wins,
        draws=draws,
        last_5=last_5,
    )


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.get("/matches/{match_id}/stats", response_model=MatchStatsOut)
def get_match_stats(match_id: int, db: Session = Depends(get_db)) -> MatchStatsOut:
    """Stats détaillées pour les deux équipes.

    - Si le match est FINISHED : inclut le match dans les stats (forme, H2H)
      et retourne match_result avec le score final.
    - Si le match est à venir : exclut le match des stats (comportement original).
    """
    match = db.scalar(select(Match).where(Match.id == match_id))
    if not match:
        raise HTTPException(status_code=404, detail=f"Match {match_id} introuvable.")
    if not match.home_team_id or not match.away_team_id:
        raise HTTPException(status_code=422, detail="Équipes non assignées pour ce match.")

    home_team = match.home_team
    away_team = match.away_team
    is_finished = match.status == "FINISHED"

    # Pour les matchs terminés : on inclut ce match dans les stats (exclude=None)
    # Pour les matchs à venir : on l'exclut (exclude=match_id)
    exclude_id = None if is_finished else match_id

    home_stats = _compute_team_stats(
        db, home_team.id, home_team.name, home_team.crest_url,
        exclude_match_id=exclude_id,
    )
    away_stats = _compute_team_stats(
        db, away_team.id, away_team.name, away_team.crest_url,
        exclude_match_id=exclude_id,
    )
    h2h = _compute_h2h(db, home_team.id, away_team.id, exclude_match_id=exclude_id)

    # Résultat du match courant si FINISHED
    match_result = None
    if is_finished and match.home_score is not None:
        match_result = _build_match_result(match, home_team.id)

    return MatchStatsOut(
        match_id=match_id,
        is_finished=is_finished,
        match_result=match_result,
        home_stats=home_stats,
        away_stats=away_stats,
        h2h=h2h,
    )
