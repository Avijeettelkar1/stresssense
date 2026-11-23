"""Movement check: is the model detecting stress, or just movement?

During WESAD's stress phase people speak and gesture; in the other phases they mostly sit still.
So we retrain the same model, with the same fair test (leave-one-person-out), twice:
  with_movement : all features (what produced handoff/scores.csv)
  no_movement   : the same features minus the 16 movement ones (chest_acc_* and wrist_acc_*)
If performance holds without movement, the model reads the body's stress reaction.

Reads  : handoff/windows.parquet   (made by run_pipeline.py --stage data; no WESAD needed here)
Writes : handoff/movement_check.csv (same columns as scores.csv; `split` = with_movement /
         no_movement), used by scripts/make_figures.py for figure 5.

Usage:
  python scripts/run_movement_check.py
  python scripts/run_movement_check.py --out artifacts/movement_check_local.csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from src.common import io
from src.common.config import ROOT, load_config, set_seeds
from src.data_model.evaluate import _oof_scores, per_subject_metrics, summarize
from src.data_model.features import feature_columns

MOVEMENT_TAG = "_acc_"   # chest_acc_mean, wrist_acc_std, ...


def main():
    p = argparse.ArgumentParser(description="Retrain with vs without movement features (LOSO)")
    p.add_argument("--out", default="handoff/movement_check.csv",
                   help="where to write the scores (relative to the repo root)")
    args = p.parse_args()

    cfg = load_config()
    seed = set_seeds()
    windows = io.read_table("windows")
    y, groups = windows["label"].to_numpy(), windows["subject_id"].to_numpy()

    frames = []
    for sensors in cfg.get("sensor_configs", ["wrist", "chest", "all"]):
        cols = feature_columns(windows.columns, sensors)
        for name, use in [("with_movement", cols),
                          ("no_movement", [c for c in cols if MOVEMENT_TAG not in c])]:
            print(f"  {sensors:5s} / {name:13s}: {len(use)} features ...")
            scores = _oof_scores(windows[use].to_numpy(float), y, groups, "loso", cfg, seed)
            frames.append(pd.DataFrame({
                "subject_id": windows["subject_id"], "window_id": windows["window_id"],
                "split": name, "sensor_config": sensors, "label": y, "score": scores.round(6),
            }))
    result = pd.concat(frames, ignore_index=True)

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(out, index=False)

    print("\n[movement] fair test, with vs without movement (per-person averages):\n")
    print(summarize(per_subject_metrics(result)).round(3).to_string(index=False))

    original = io.read_table("scores").query("split == 'loso'")
    m = result[result["split"] == "with_movement"].merge(
        original, on=["subject_id", "window_id", "sensor_config"], suffixes=("", "_orig"))
    diff = (m["score"] - m["score_orig"]).abs().max()
    print(f"\n[movement] reproduction check: largest difference between with_movement and "
          f"handoff/scores.csv = {diff:.4f}  (0 = identical; small values come from package "
          f"versions)")
    print(f"[movement] wrote {len(result)} rows -> {out}")


if __name__ == "__main__":
    main()
