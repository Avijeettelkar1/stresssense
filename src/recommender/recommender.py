"""Recommender prototype. Owner: C.

Consumes decisions.csv and turns each `act`/`watch`/`none` into a non-clinical well-being
suggestion. The intervention is SIMULATED — we do not claim clinical effectiveness.
"""
from __future__ import annotations

INTERVENTIONS = [
    "breathing exercise",
    "short break",
    "brief walk",
    "relaxation audio",
    "mindfulness exercise",
    "no intervention",
]


def recommend(decision: str, context: dict | None = None) -> str:
    """TODO(C): pick a suggestion. 'none'/'watch' usually -> 'no intervention'; 'act' -> a nudge
    possibly refined by the adaptive survey answers."""
    raise NotImplementedError
