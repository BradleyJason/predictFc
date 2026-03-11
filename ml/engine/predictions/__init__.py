"""Modules de prédiction — une fonction par type de pari."""

from engine.predictions.btts import predict_btts
from engine.predictions.double_chance import predict_double_chance
from engine.predictions.exact_score import predict_exact_score
from engine.predictions.goal_gap import predict_goal_gap
from engine.predictions.result import predict_result
from engine.predictions.total_goals import predict_total_goals

__all__ = [
    "predict_btts",
    "predict_double_chance",
    "predict_exact_score",
    "predict_goal_gap",
    "predict_result",
    "predict_total_goals",
]
