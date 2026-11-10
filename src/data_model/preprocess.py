"""Preprocessing + windowing -> windows.parquet. Owner: A.

Produces the `windows.parquet` contract (see contracts/windows.schema.md):
subject_id, window_id, t_start, phase, label, + one column per feature.
"""
from __future__ import annotations


def make_windows(subject_id, raw):
    """TODO(A): resample, segment into fixed windows, label each window, return rows."""
    raise NotImplementedError("A: windowing + labelling")


def label_from_phase(phase: str, cfg) -> int:
    """stress vs everything else, per config['label'] (week-1 decision)."""
    return int(phase == cfg["label"]["positive_class"])
