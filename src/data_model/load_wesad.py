"""Load WESAD (one folder per subject, a pickle each). Owner: A.

WESAD pickle layout (per subject): dict with
  'signal' -> {'chest': {ACC, ECG, EMG, EDA, Temp, Resp}, 'wrist': {ACC, BVP, EDA, TEMP}}
  'label'  -> array of ints (0=undef, 1=baseline, 2=stress, 3=amusement, 4=meditation, 5-7=ignore)
"""
from __future__ import annotations

from pathlib import Path

from src.common.config import load_config

SUBJECTS = ["S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9",
            "S10", "S11", "S13", "S14", "S15", "S16", "S17"]  # S1/S12 absent in WESAD


def wesad_root() -> Path:
    return Path(load_config()["data"]["wesad_root"])


def load_subject(subject_id: str) -> dict:
    """TODO(A): read <root>/<subject_id>/<subject_id>.pkl and return the raw dict."""
    raise NotImplementedError("A: implement WESAD pickle loading")


def iter_subjects():
    """TODO(A): yield (subject_id, raw_dict) for each available subject."""
    raise NotImplementedError
