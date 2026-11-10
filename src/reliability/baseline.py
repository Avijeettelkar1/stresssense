"""Personal baseline / calibration. Owner: B. (RQ3)

Three variants to compare against the global population model:
  - global         : no per-user adaptation (the reference)
  - label-free     : normalise a user's scores using only their own unlabelled score distribution
  - label-budgeted : allow a small, fixed number of labelled windows per user to calibrate

Goal is NOT just higher average accuracy — report who improves, who does not, and whether the
performance DISPARITY between users shrinks (especially the worst user).
"""
from __future__ import annotations


def adjust_scores(scores_df, mode: str = "global"):
    """TODO(B): return scores with an `adjusted_score` per the chosen mode."""
    raise NotImplementedError
