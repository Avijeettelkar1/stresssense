"""Per-window feature extraction. Owner: A.

Features are grouped by sensor location so the sensor-config comparison (wrist / chest / all)
is just a column filter on the prefix. Each channel gets a small set of robust statistics
computed in pure numpy (no heavy deps), named <loc>_<channel>_<stat>, e.g. wrist_bvp_mean.
"""
from __future__ import annotations

import numpy as np

from src.data_model.load_wesad import iter_channels

SENSOR_PREFIXES = {
    "wrist": ("wrist_",),
    "chest": ("chest_",),
    "all": ("wrist_", "chest_"),
}

META_COLUMNS = ["subject_id", "window_id", "t_start", "phase", "label"]


def feature_columns(all_columns, sensor_config: str):
    """Select feature columns belonging to a sensor configuration."""
    prefixes = SENSOR_PREFIXES[sensor_config]
    return [c for c in all_columns if c.startswith(prefixes) and c not in META_COLUMNS]


def _stats(seg: np.ndarray) -> dict:
    seg = np.asarray(seg, dtype=float)
    seg = seg[np.isfinite(seg)]
    if seg.size == 0:
        return {k: 0.0 for k in
                ("mean", "std", "min", "max", "range", "median", "iqr", "slope")}
    p25, p75 = np.percentile(seg, [25, 75])
    slope = 0.0
    if seg.size >= 2:
        x = np.linspace(0.0, 1.0, seg.size)
        slope = float(np.polyfit(x, seg, 1)[0])
    return {
        "mean": float(np.mean(seg)),
        "std": float(np.std(seg)),
        "min": float(np.min(seg)),
        "max": float(np.max(seg)),
        "range": float(np.max(seg) - np.min(seg)),
        "median": float(np.median(seg)),
        "iqr": float(p75 - p25),
        "slope": slope,
    }


def extract_window(raw: dict, t_start: float, win_sec: float) -> dict:
    """Compute all features for the window [t_start, t_start + win_sec) seconds."""
    feats: dict[str, float] = {}
    for loc, chan, fs, arr in iter_channels(raw):
        i0 = int(round(t_start * fs))
        i1 = int(round((t_start + win_sec) * fs))
        seg = arr[i0:i1]
        for stat, value in _stats(seg).items():
            feats[f"{loc}_{chan}_{stat}"] = value
    return feats
