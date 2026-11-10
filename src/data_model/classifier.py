"""Stress classifier. Owner: A.

Return a model that exposes predict_proba so scores are probabilities (the `score` column).
Keep it swappable (sklearn estimator or LightGBM) — the gate/baseline only consume scores.
"""
from __future__ import annotations


def build_model(cfg=None):
    """TODO(A): return an unfitted estimator with fit / predict_proba."""
    raise NotImplementedError
