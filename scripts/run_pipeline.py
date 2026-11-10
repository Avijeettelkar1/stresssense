"""Workstream A pipeline runner.

Stages:
  data    : WESAD -> features -> artifacts/windows.parquet   (contract: A->B)
  scores  : windows.parquet -> LOSO + random eval -> artifacts/scores.csv  (contract: A->B)
  metrics : scores.csv -> per-subject + summary tables in reports/  (RQ1, RQ2)
  all     : data -> scores -> metrics

Usage:
  python scripts/run_pipeline.py --stage all
  python scripts/run_pipeline.py --stage data --subjects S2 S3
  python scripts/run_pipeline.py --stage scores
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make the repo root importable so `import src...` works when run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.common.config import ROOT, load_config, set_seeds


def stage_data(args, cfg):
    from src.common import io
    from src.data_model.preprocess import build_all

    print("[data] building windows from WESAD ...")
    windows = build_all(cfg, subjects=args.subjects)
    path = io.write_table(windows, "windows")
    print(f"[data] wrote {len(windows)} windows ({windows['label'].sum()} stress) -> {path}")


def stage_scores(args, cfg):
    from src.data_model.evaluate import run_evaluation

    print("[scores] running LOSO + random evaluation ...")
    run_evaluation(cfg)


def stage_metrics(args, cfg):
    from src.common import io
    from src.data_model.evaluate import per_subject_metrics, summarize

    scores = io.read_table("scores")
    per_subject = per_subject_metrics(scores)
    summary = summarize(per_subject)

    out = ROOT / "artifacts"
    out.mkdir(exist_ok=True)
    per_subject.to_csv(out / "metrics_per_subject.csv", index=False)
    summary.to_csv(out / "metrics_summary.csv", index=False)

    print("\n[metrics] summary (RQ1: compare loso vs random; RQ2: worst_* vs mean_*):\n")
    print(summary.to_string(index=False))
    print(f"\n[metrics] wrote tables -> {out}")


def main():
    p = argparse.ArgumentParser(description="Workstream A pipeline (data -> scores -> metrics)")
    p.add_argument("--stage", choices=["data", "scores", "metrics", "all"], default="all")
    p.add_argument("--subjects", nargs="*", default=None,
                   help="Subset of subject ids, e.g. S2 S3 (default: all available)")
    args = p.parse_args()

    cfg = load_config()
    set_seeds()

    stages = ["data", "scores", "metrics"] if args.stage == "all" else [args.stage]
    for s in stages:
        {"data": stage_data, "scores": stage_scores, "metrics": stage_metrics}[s](args, cfg)


if __name__ == "__main__":
    main()
