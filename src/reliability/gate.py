"""Risk-controlled recommendation gate -> decisions.csv. Owner: B. (RQ4)

An uncertainty-aware policy that does NOT always act:
  adjusted_score >= threshold                      -> "act"   (recommend an intervention)
  threshold - watch_margin <= adjusted < threshold -> "watch" (low confidence: observe more)
  otherwise                                         -> "none"

RQ4 compares this gate against an "always act on predicted stress" policy and counts how many
inappropriate interventions each produces. The point: a good system sometimes chooses not to act.

Writes decisions.csv (contracts/decisions.schema.md):
    subject_id, window_id, decision, adjusted_score, threshold, nudge_rate
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def decide(adjusted_df: pd.DataFrame, threshold: float = 0.6, watch_margin: float = 0.15) -> pd.DataFrame:
    """Map adjusted scores to act/watch/none, tracking a running per-user nudge rate."""
    df = adjusted_df.sort_values(["subject_id", "window_id"]).copy()
    parts = []
    for _, g in df.groupby("subject_id", sort=False):
        g = g.copy()
        acted, rates, decisions = 0, [], []
        for i, a in enumerate(g["adjusted_score"].to_numpy(dtype=float), start=1):
            if a >= threshold:
                decisions.append("act")
                acted += 1
            elif a >= threshold - watch_margin:
                decisions.append("watch")
            else:
                decisions.append("none")
            rates.append(acted / i)
        g["decision"] = decisions
        g["threshold"] = threshold
        g["nudge_rate"] = np.round(rates, 4)
        parts.append(g)

    out = pd.concat(parts, ignore_index=True)
    return out[["subject_id", "window_id", "decision", "adjusted_score", "threshold", "nudge_rate"]]


def always_act(scores_df: pd.DataFrame, threshold: float = 0.5) -> pd.Series:
    """Baseline policy for the RQ4 contrast: act whenever score >= threshold, never abstain."""
    return np.where(scores_df["score"].to_numpy(dtype=float) >= threshold, "act", "none")


def intervention_errors(decision_is_act: np.ndarray, labels: np.ndarray) -> dict:
    """Count inappropriate interventions (RQ4).

    false_alarm : acted while truly not stressed (label 0)
    missed       : did not act while truly stressed (label 1)
    """
    act = decision_is_act.astype(bool)
    y = labels.astype(bool)
    return {
        "n": int(len(y)),
        "acted": int(act.sum()),
        "false_alarm": int((act & ~y).sum()),
        "missed": int((~act & y).sum()),
    }
