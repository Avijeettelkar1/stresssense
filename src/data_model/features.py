"""Per-window feature extraction. Owner: A.

Group features by sensor so the sensor-config comparison (wrist / chest / all) is a column filter:
feature names are prefixed, e.g. wrist_bvp_hr_mean, chest_eda_scl_mean, wrist_acc_std, ...
Consider neurokit2 for HR/EDA/RESP features.
"""
from __future__ import annotations

SENSOR_PREFIXES = {
    "wrist": ("wrist_",),
    "chest": ("chest_",),
    "all": ("wrist_", "chest_"),
}


def feature_columns(all_columns, sensor_config: str):
    """Select feature columns belonging to a sensor configuration."""
    prefixes = SENSOR_PREFIXES[sensor_config]
    return [c for c in all_columns if c.startswith(prefixes)]


def extract(window) -> dict:
    """TODO(A): compute time/frequency features for one window."""
    raise NotImplementedError
