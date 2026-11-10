"""Recommender prototype. Owner: C.

Consumes B's decisions.csv and turns each act / watch / none into a non-clinical well-being
suggestion, optionally refined by the adaptive survey's answers.

The intervention is SIMULATED — we do not claim clinical effectiveness.
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
    """Pick a suggestion for one window.

    `watch`/`none` -> no intervention (the system chooses not to act).
    `act`          -> a nudge, refined by survey context when present:
        context keys (all optional): minutes_available (int), can_leave_desk (bool),
        prefers (one of INTERVENTIONS).
    """
    context = context or {}
    if decision != "act":
        return "no intervention"

    if context.get("prefers") in INTERVENTIONS:
        return context["prefers"]

    minutes = context.get("minutes_available")
    if minutes is not None and minutes < 2:
        return "breathing exercise"
    if context.get("can_leave_desk"):
        return "brief walk"
    if minutes is not None and minutes >= 10:
        return "mindfulness exercise"
    return "short break"
