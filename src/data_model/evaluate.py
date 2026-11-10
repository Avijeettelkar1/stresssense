"""Evaluation -> scores.csv. Owner: A. (RQ1, RQ2)

CRITICAL: the headline evaluation is LEAVE-ONE-SUBJECT-OUT, not a random split that mixes a
person's windows across train and test. We also emit a `random` split purely as a contrast to
show why subject-independent evaluation matters.

    from sklearn.model_selection import LeaveOneGroupOut
    logo = LeaveOneGroupOut()
    for train_idx, test_idx in logo.split(X, y, groups=subject_ids):
        ...   # the held-out subject is unseen during training (RQ1)

Writes scores.csv with: subject_id, window_id, split, sensor_config, label, score.
Run once per sensor_config in config['sensor_configs'].
"""
from __future__ import annotations


def run_evaluation():
    """TODO(A): loop sensor configs x {loso, random}, collect per-window scores, write via io.write_table(df, 'scores')."""
    raise NotImplementedError


def per_subject_metrics(scores_df):
    """RQ2: return mean, per-user, worst-user, variance and the distribution per (split, sensor_config)."""
    raise NotImplementedError
