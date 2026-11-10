"""Generate the mock hand-off files for M1 (stdlib only, deterministic).

A commits mocks/scores.csv, B commits mocks/decisions.csv. B and C build against these until A's
real files arrive. Run:  python scripts/make_mocks.py
"""
from __future__ import annotations

import csv
import random
from pathlib import Path

random.seed(42)

ROOT = Path(__file__).resolve().parents[1]
MOCKS = ROOT / "mocks"
MOCKS.mkdir(exist_ok=True)

SUBJECTS = ["S2", "S3", "S4", "S5"]
N_WINDOWS = 8
SPLITS = ["loso", "random"]
SENSOR_CONFIGS = ["wrist", "chest", "all"]


def write_scores() -> None:
    with open(MOCKS / "scores.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["subject_id", "window_id", "split", "sensor_config", "label", "score"])
        for s in SUBJECTS:
            for wid in range(N_WINDOWS):
                label = random.randint(0, 1)
                for split in SPLITS:
                    for cfg in SENSOR_CONFIGS:
                        base = 0.65 if label == 1 else 0.35
                        score = min(max(base + random.uniform(-0.3, 0.3), 0.0), 1.0)
                        w.writerow([s, wid, split, cfg, label, round(score, 4)])


def write_decisions() -> None:
    threshold, margin = 0.6, 0.15
    with open(MOCKS / "decisions.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["subject_id", "window_id", "decision", "adjusted_score", "threshold", "nudge_rate"])
        for s in SUBJECTS:
            acted = 0
            for wid in range(N_WINDOWS):
                adj = round(random.uniform(0.0, 1.0), 4)
                if adj >= threshold:
                    decision = "act"
                    acted += 1
                elif adj >= threshold - margin:
                    decision = "watch"
                else:
                    decision = "none"
                nudge_rate = round(acted / (wid + 1), 4)
                w.writerow([s, wid, decision, adj, threshold, nudge_rate])


if __name__ == "__main__":
    write_scores()
    write_decisions()
    print(f"Wrote {MOCKS / 'scores.csv'} and {MOCKS / 'decisions.csv'}")
