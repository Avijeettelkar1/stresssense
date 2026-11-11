"""Verify the WESAD pickle layout matches what load_wesad.py assumes. Owner: A.

Prints one subject's dict keys, signal shapes and label codes, turning the loader's assumptions
into verified facts before a full run. Run this the first time you point at real data.

Usage: python scripts/inspect_wesad.py [S2]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from src.data_model.load_wesad import PHASES, available_subjects, load_subject


def main():
    subj = sys.argv[1] if len(sys.argv) > 1 else (available_subjects() or ["S2"])[0]
    print(f"Inspecting {subj} ...\n")
    raw = load_subject(subj)

    print("subject field:", raw.get("subject"))
    print("top-level keys:", list(raw.keys()))

    sig = raw["signal"]
    for loc in ("chest", "wrist"):
        print(f"\n[{loc}] channels:")
        for ch, arr in sig[loc].items():
            arr = np.asarray(arr)
            print(f"  {ch:6s} shape={arr.shape} dtype={arr.dtype}")

    lab = np.asarray(raw["label"]).ravel()
    vals, counts = np.unique(lab, return_counts=True)
    print("\nlabel codes (code: count -> name):")
    for v, c in zip(vals, counts):
        print(f"  {int(v)}: {int(c):>9d}  -> {PHASES.get(int(v), '(ignored)')}")
    print(f"\nlabel length={len(lab)}  (~{len(lab) / 700:.1f}s at 700 Hz)")
    print("\nIf any channel key or label code above differs from load_wesad.py, that's the one-line fix.")


if __name__ == "__main__":
    main()
