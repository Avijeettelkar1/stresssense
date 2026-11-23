"""Workstream B pipeline runner: scores.csv -> baseline -> gate -> decisions.csv.

Stages:
  decisions : adjust scores (RQ3 baseline) -> gate -> handoff/decisions.csv  (contract B->C)
  compare   : gated policy vs always-act, inappropriate-intervention counts (RQ4) -> artifacts/
  rq3       : fair contest global vs label-free vs label-budgeted, per person (RQ3) -> artifacts/
  all       : decisions -> compare -> rq3

Reads A's scores. Until A ships the real file, use --mock to read mocks/scores.csv.

Usage:
  python scripts/run_reliability.py --stage all --mock
  python scripts/run_reliability.py --stage decisions --mode label-free
  python scripts/run_reliability.py --stage compare --mode label-budgeted --budget 1
  python scripts/run_reliability.py --stage rq3
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from src.common.config import ROOT, set_seeds
from src.common import io
from src.reliability.baseline import adjust_scores, evaluate_rq3, summarise_rq3
from src.reliability.gate import always_act, decide, intervention_errors


def _load_scores(args) -> pd.DataFrame:
    df = io.read_table("scores", use_mock=args.mock)
    df = df[(df["split"] == args.split) & (df["sensor_config"] == args.sensor_config)]
    if df.empty:
        raise SystemExit(f"No scores for split={args.split} sensor_config={args.sensor_config}")
    return df.reset_index(drop=True)


def stage_decisions(args):
    scores = _load_scores(args)
    adjusted = adjust_scores(scores, mode=args.mode, budget=args.budget)
    decisions = decide(adjusted, threshold=args.threshold, watch_margin=args.watch_margin)
    if args.mock:
        # Fake input must never land in handoff/ (the real hand-off folder): keep it local.
        io.validate(decisions, "decisions")
        path = ROOT / "artifacts" / "decisions_from_mock.csv"
        path.parent.mkdir(exist_ok=True)
        decisions.to_csv(path, index=False)
    else:
        path = io.write_table(decisions, "decisions")
    counts = decisions["decision"].value_counts().to_dict()
    print(f"[decisions] mode={args.mode} -> {counts}")
    print(f"[decisions] wrote {len(decisions)} rows -> {path}")


def stage_compare(args):
    scores = _load_scores(args)
    adjusted = adjust_scores(scores, mode=args.mode, budget=args.budget)
    gated = decide(adjusted, threshold=args.threshold, watch_margin=args.watch_margin)

    merged = scores.merge(gated[["subject_id", "window_id", "decision"]],
                          on=["subject_id", "window_id"])
    y = merged["label"].to_numpy()

    rows = [
        {"policy": "always_act", **intervention_errors(always_act(merged) == "act", y)},
        {"policy": f"gate[{args.mode}]", **intervention_errors(merged["decision"].to_numpy() == "act", y)},
    ]
    table = pd.DataFrame(rows)
    out = ROOT / "artifacts"
    out.mkdir(exist_ok=True)
    table.to_csv(out / "rq4_comparison.csv", index=False)
    print("\n[compare] RQ4: inappropriate interventions (lower false_alarm is the win):\n")
    print(table.to_string(index=False))
    print(f"\n[compare] wrote -> {out / 'rq4_comparison.csv'}")


def stage_rq3(args):
    scores = _load_scores(args)
    per_person = evaluate_rq3(scores, n_draws=args.draws, seed=args.seed)
    summary = summarise_rq3(per_person)

    out = ROOT / "artifacts"
    out.mkdir(exist_ok=True)
    per_person.to_csv(out / "rq3_per_person.csv", index=False)
    summary.to_csv(out / "rq3_summary.csv", index=False)

    print(f"\n[rq3] split={args.split} sensors={args.sensor_config}: one alarm line for everyone "
          "vs personal lines (balanced accuracy per person)\n")
    print(summary.round(3).to_string(index=False))
    table = per_person.pivot(index="subject_id", columns="method", values="balanced_acc")
    table = table[list(summary["method"])].sort_values("global")
    print("\n[rq3] per person, worst first under one line for everyone:\n")
    print(table.round(3).to_string())
    print(f"\n[rq3] wrote -> {out / 'rq3_per_person.csv'} and {out / 'rq3_summary.csv'}")


def main():
    p = argparse.ArgumentParser(description="Workstream B pipeline (baseline -> gate -> decisions)")
    p.add_argument("--stage", choices=["decisions", "compare", "rq3", "all"], default="all")
    p.add_argument("--mock", action="store_true", help="read mocks/scores.csv instead of the real file")
    p.add_argument("--mode", choices=["global", "label-free", "label-budgeted"], default="label-free")
    p.add_argument("--split", default="loso")
    p.add_argument("--sensor-config", default="all")
    p.add_argument("--threshold", type=float, default=0.6)
    p.add_argument("--watch-margin", type=float, default=0.15)
    p.add_argument("--budget", type=int, default=1,
                   help="label-budgeted: number of stressed AND of calm moments the person labels")
    p.add_argument("--draws", type=int, default=30,
                   help="rq3: random repeats of which moments the person labels")
    args = p.parse_args()

    args.seed = set_seeds()
    stages = ["decisions", "compare", "rq3"] if args.stage == "all" else [args.stage]
    for s in stages:
        {"decisions": stage_decisions, "compare": stage_compare, "rq3": stage_rq3}[s](args)


if __name__ == "__main__":
    main()
