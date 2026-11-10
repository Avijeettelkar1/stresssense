"""Evaluation -> scores.csv. Owner: A. (RQ1, RQ2)

Headline evaluation is LEAVE-ONE-SUBJECT-OUT (subject-independent). We also emit a `random` split
(subjects mixed across train/test) ONLY as a contrast, to show why LOSO matters for RQ1.

Produces scores.csv (contracts/scores.schema.md):
    subject_id, window_id, split, sensor_config, label, score
with one row per (window x split x sensor_config). Every window is in the held-out fold exactly
once, so each gets an out-of-fold probability.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from sklearn.model_selection import LeaveOneGroupOut, StratifiedKFold

from src.common.config import load_config, set_seeds
from src.common import io
from src.data_model.classifier import build_model
from src.data_model.features import feature_columns


def _pos_index(model) -> int:
    classes = list(model.classes_)
    return classes.index(1) if 1 in classes else len(classes) - 1


def _oof_scores(X, y, groups, split: str, cfg: dict, seed: int) -> np.ndarray:
    """Return an out-of-fold stress probability for every row."""
    scores = np.full(len(y), np.nan)
    if split == "loso":
        splitter = LeaveOneGroupOut().split(X, y, groups=groups)
    else:
        n_splits = min(5, int(np.bincount(y).min()))
        n_splits = max(n_splits, 2)
        splitter = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed).split(X, y)

    for train_idx, test_idx in splitter:
        model = build_model(cfg, seed=seed)
        model.fit(X[train_idx], y[train_idx])
        proba = model.predict_proba(X[test_idx])[:, _pos_index(model)]
        scores[test_idx] = proba
    return scores


def run_evaluation(cfg: dict | None = None) -> pd.DataFrame:
    cfg = cfg or load_config()
    seed = set_seeds()
    windows = io.read_table("windows")

    y = windows["label"].to_numpy()
    groups = windows["subject_id"].to_numpy()
    all_cols = list(windows.columns)

    frames = []
    for sensor_config in cfg.get("sensor_configs", ["wrist", "chest", "all"]):
        cols = feature_columns(all_cols, sensor_config)
        X = windows[cols].to_numpy(dtype=float)
        for split in ("loso", "random"):
            print(f"  {sensor_config:5s} / {split:6s}: fitting on {len(cols)} features ...")
            scores = _oof_scores(X, y, groups, split, cfg, seed)
            frames.append(pd.DataFrame({
                "subject_id": windows["subject_id"],
                "window_id": windows["window_id"],
                "split": split,
                "sensor_config": sensor_config,
                "label": y,
                "score": np.round(scores, 6),
            }))

    scores_df = pd.concat(frames, ignore_index=True)
    path = io.write_table(scores_df, "scores")
    print(f"Wrote {len(scores_df)} rows -> {path}")
    return scores_df


def per_subject_metrics(scores_df: pd.DataFrame) -> pd.DataFrame:
    """RQ2: per-(split, sensor_config, subject) AUROC and balanced accuracy."""
    out = []
    grouped = scores_df.groupby(["split", "sensor_config", "subject_id"])
    for (split, cfg, subj), g in grouped:
        y, s = g["label"].to_numpy(), g["score"].to_numpy()
        try:
            auroc = roc_auc_score(y, s) if len(np.unique(y)) > 1 else np.nan
        except ValueError:
            auroc = np.nan
        bal_acc = balanced_accuracy_score(y, (s >= 0.5).astype(int))
        out.append({"split": split, "sensor_config": cfg, "subject_id": subj,
                    "n": len(g), "pos_rate": float(y.mean()),
                    "auroc": auroc, "balanced_acc": bal_acc})
    return pd.DataFrame(out)


def summarize(metrics: pd.DataFrame) -> pd.DataFrame:
    """RQ1/RQ2 headline table: mean, worst-user and spread per (split, sensor_config)."""
    return (metrics.groupby(["split", "sensor_config"])
            .agg(mean_auroc=("auroc", "mean"),
                 worst_auroc=("auroc", "min"),
                 std_auroc=("auroc", "std"),
                 mean_bal_acc=("balanced_acc", "mean"),
                 worst_bal_acc=("balanced_acc", "min"),
                 std_bal_acc=("balanced_acc", "std"))
            .reset_index())
