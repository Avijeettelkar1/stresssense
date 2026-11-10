"""Risk-controlled recommendation gate -> decisions.csv. Owner: B. (RQ4)

An uncertainty-aware policy that does not always act:
  high-confidence stress -> "act"
  low-confidence         -> "watch" (observe more / no intervention)
  otherwise              -> "none"

RQ4 compares this gate against an "always act on predicted stress" policy and counts how many
inappropriate interventions each causes.

Writes decisions.csv: subject_id, window_id, decision, adjusted_score, threshold, nudge_rate.
"""
from __future__ import annotations


def decide(adjusted_scores_df, threshold: float = 0.6, watch_margin: float = 0.15):
    """TODO(B): map adjusted scores to act/watch/none, track nudge_rate, write via io.write_table(df, 'decisions')."""
    raise NotImplementedError


def always_act(scores_df, threshold: float = 0.5):
    """Baseline policy for the RQ4 comparison: act whenever score >= threshold, never abstain."""
    raise NotImplementedError
