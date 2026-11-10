"""Load WESAD (one folder per subject, a pickle each). Owner: A.

WESAD pickle (per subject SX/SX.pkl, pickled under Python 2 -> read with latin1):
  'subject' -> 'SX'
  'signal'  -> {'chest': {ACC, ECG, EMG, EDA, Temp, Resp}, 'wrist': {ACC, BVP, EDA, TEMP}}
  'label'   -> int array at 700 Hz:
               0 = undefined/transient, 1 = baseline, 2 = stress,
               3 = amusement, 4 = meditation, 5/6/7 = ignore
"""
from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np

from src.common.config import load_config

# Subjects shipped with WESAD (S1 and S12 do not exist).
SUBJECTS = ["S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9",
            "S10", "S11", "S13", "S14", "S15", "S16", "S17"]

LABEL_FS = 700
CHEST_FS = 700
WRIST_FS = {"ACC": 32, "BVP": 64, "EDA": 4, "TEMP": 4}

# WESAD label code -> phase name we keep (others are dropped).
PHASES = {1: "baseline", 2: "stress", 3: "amusement", 4: "meditation"}


def wesad_root() -> Path:
    return Path(load_config()["data"]["wesad_root"])


def subject_pickle(subject_id: str) -> Path:
    return wesad_root() / subject_id / f"{subject_id}.pkl"


def load_subject(subject_id: str) -> dict:
    """Load one subject's raw WESAD dict."""
    path = subject_pickle(subject_id)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Set data.wesad_root in config.local.yaml to your WESAD folder."
        )
    with open(path, "rb") as f:
        return pickle.load(f, encoding="latin1")


def available_subjects() -> list[str]:
    """Subjects actually present under wesad_root."""
    return [s for s in SUBJECTS if subject_pickle(s).exists()]


def _acc_magnitude(acc: np.ndarray) -> np.ndarray:
    acc = np.asarray(acc, dtype=float)
    if acc.ndim == 2 and acc.shape[1] == 3:
        return np.linalg.norm(acc, axis=1)
    return acc.ravel()


def iter_channels(raw: dict):
    """Yield (location, channel, fs, signal_1d) for every usable channel.

    ACC is reduced to its magnitude so each channel is 1-D. Channel names are lowercased,
    e.g. ('chest', 'ecg', 700, arr) -> feature prefix 'chest_ecg_'.
    """
    sig = raw["signal"]

    chest = sig["chest"]
    yield ("chest", "acc", CHEST_FS, _acc_magnitude(chest["ACC"]))
    for key, name in [("ECG", "ecg"), ("EMG", "emg"), ("EDA", "eda"),
                      ("Temp", "temp"), ("Resp", "resp")]:
        yield ("chest", name, CHEST_FS, np.asarray(chest[key], dtype=float).ravel())

    wrist = sig["wrist"]
    yield ("wrist", "acc", WRIST_FS["ACC"], _acc_magnitude(wrist["ACC"]))
    for key, name in [("BVP", "bvp"), ("EDA", "eda"), ("TEMP", "temp")]:
        yield ("wrist", name, WRIST_FS[key], np.asarray(wrist[key], dtype=float).ravel())


def labels(raw: dict) -> np.ndarray:
    return np.asarray(raw["label"]).ravel()
