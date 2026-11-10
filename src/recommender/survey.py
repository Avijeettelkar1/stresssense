"""Adaptive survey. Owner: C.

A short branching questionnaire that refines the recommendation without becoming a clinical
instrument. `next_question` returns the next question given the answers so far, or None when done.
"""
from __future__ import annotations

from src.recommender.recommender import INTERVENTIONS

QUESTIONS = {
    "minutes_available": {
        "text": "How many minutes do you have right now?",
        "type": "number",
    },
    "can_leave_desk": {
        "text": "Can you step away from your desk?",
        "type": "bool",
    },
    "prefers": {
        "text": "Any preference for how to take the break?",
        "type": "choice",
        "choices": [i for i in INTERVENTIONS if i != "no intervention"],
    },
}


def next_question(answers: dict) -> dict | None:
    """Adaptive order: ask time first; skip the 'leave desk' question when there's no time."""
    if "minutes_available" not in answers:
        return {"id": "minutes_available", **QUESTIONS["minutes_available"]}

    short_on_time = (answers.get("minutes_available") or 0) < 2
    if not short_on_time and "can_leave_desk" not in answers:
        return {"id": "can_leave_desk", **QUESTIONS["can_leave_desk"]}

    if "prefers" not in answers:
        return {"id": "prefers", **QUESTIONS["prefers"]}

    return None
