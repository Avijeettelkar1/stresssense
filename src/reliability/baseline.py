"""Personal baseline / calibration. Owner: B. (RQ3)

Three ways to turn A's raw stress `score` into an `adjusted_score`, to compare against the global
population model:

  global         : adjusted = score (the reference, no per-user adaptation)
  label-free     : per-user standardisation using only that user's own score distribution
                   (no labels) -> logistic squash back to (0, 1)
  label-budgeted : spend a small fixed number of labelled windows per user to locate the
                   stress/non-stress score midpoint and rescale around it

The research point (RQ3) is NOT higher average accuracy — it is whether the WORST user improves and
whether the disparity between users shrinks. Compare per-user, not just the mean.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

MODES = ("global", "label-free", "label-budgeted")


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def adjust_scores(scores_df: pd.DataFrame, mode: str = "global", budget: int = 10) -> pd.DataFrame:
    """Return `scores_df` with an added `adjusted_score` column."""
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}, got {mode!r}")

    df = scores_df.copy()
    if mode == "global":
        df["adjusted_score"] = df["score"].astype(float)
        return df

    parts = []
    for _, g in df.groupby("subject_id", sort=False):
        g = g.copy()
        s = g["score"].to_numpy(dtype=float)

        if mode == "label-free":
            mu, sd = s.mean(), s.std() + 1e-9
            g["adjusted_score"] = _sigmoid((s - mu) / sd)

        else:  # label-budgeted
            cal = g.head(budget)  # NOTE: simplification — a stricter setup holds these out of eval
            pos = cal.loc[cal["label"] == 1, "score"]
            neg = cal.loc[cal["label"] == 0, "score"]
            if len(pos) and len(neg):
                midpoint = (pos.mean() + neg.mean()) / 2.0
                scale = 4.0 / (abs(pos.mean() - neg.mean()) + 1e-9)
            else:  # not enough labels in the budget — fall back to the user's mean
                midpoint, scale = s.mean(), 1.0
            g["adjusted_score"] = _sigmoid(scale * (s - midpoint))

        parts.append(g)

    return pd.concat(parts, ignore_index=True)
