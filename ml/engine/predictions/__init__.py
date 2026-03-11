"""Modules de prédiction — une fonction par type de pari."""

from ml.engine.predictions.btts import predict_btts
from ml.engine.predictions.double_chance import predict_double_chance
from ml.engine.predictions.exact_score import predict_exact_score
from ml.engine.predictions.goal_gap import predict_goal_gap
from ml.engine.predictions.result import predict_result
from ml.engine.predictions.total_goals import predict_total_goals

__all__ = [
    "predict_btts",
    "predict_double_chance",
    "predict_exact_score",
    "predict_goal_gap",
    "predict_result",
    "predict_total_goals",
]
