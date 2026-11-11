"""Preprocessing + windowing -> windows.parquet. Owner: A.

Slides a fixed window over each subject, labels each window by the majority WESAD code (keeping
only reasonably pure windows in baseline/stress/amusement/meditation), and attaches features.
Produces the windows.parquet contract (contracts/windows.schema.md).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.common.config import load_config
from src.data_model import features as F
from src.data_model.load_wesad import LABEL_FS, PHASES, labels, load_subject

DEFAULTS = {"window_sec": 60.0, "overlap": 0.5, "min_purity": 0.9}


def _window_cfg(cfg: dict) -> dict:
    out = dict(DEFAULTS)
    out.update(cfg.get("windows", {}) or {})
    return out


def _majority_label(label_slice: np.ndarray):
    """Return (code, purity) for the most common label in the slice."""
    vals, counts = np.unique(label_slice, return_counts=True)
    i = int(np.argmax(counts))
    return int(vals[i]), float(counts[i] / counts.sum())


def make_windows(subject_id: str, raw: dict, cfg: dict | None = None) -> pd.DataFrame:
    cfg = cfg or load_config()
    label_cfg = cfg.get("label", {})
    positive = label_cfg.get("positive_class", "stress")
    wc = _window_cfg(cfg)
    win, overlap, min_purity = wc["window_sec"], wc["overlap"], wc["min_purity"]
    step = win * (1.0 - overlap)
    use_physio = bool((cfg.get("features", {}) or {}).get("physio", True))

    lab = labels(raw)
    duration = len(lab) / LABEL_FS

    rows = []
    window_id = 0
    t = 0.0
    while t + win <= duration:
        sl = lab[int(t * LABEL_FS):int((t + win) * LABEL_FS)]
        code, purity = _majority_label(sl)
        if code in PHASES and purity >= min_purity:
            phase = PHASES[code]
            row = {
                "subject_id": subject_id,
                "window_id": window_id,
                "t_start": round(t, 3),
                "phase": phase,
                "label": int(phase == positive),
            }
            row.update(F.extract_window(raw, t, win, use_physio=use_physio))
            rows.append(row)
            window_id += 1
        t += step
    return pd.DataFrame(rows)


def build_all(cfg: dict | None = None, subjects: list[str] | None = None) -> pd.DataFrame:
    """Build windows for every (available) subject and concatenate."""
    from src.data_model.load_wesad import available_subjects

    cfg = cfg or load_config()
    subjects = subjects or available_subjects()
    if not subjects:
        raise RuntimeError("No WESAD subjects found. Check data.wesad_root in config.local.yaml.")
    frames = []
    for s in subjects:
        df = make_windows(s, load_subject(s), cfg)
        print(f"  {s}: {len(df)} windows ({int(df['label'].sum())} stress)")
        frames.append(df)
    return pd.concat(frames, ignore_index=True)
