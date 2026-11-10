"""Workstream C pipeline runner: decisions.csv -> recommendations.

Turns B's decisions into non-clinical suggestions and summarises them. Until B ships the real
decisions.csv, use --mock to read mocks/decisions.csv.

Usage:
  python scripts/run_recommender.py --mock
  python scripts/run_recommender.py --minutes 1          # simulate a "no time" context
  python scripts/run_recommender.py --mock --can-leave-desk
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from src.common.config import ROOT
from src.common import io
from src.recommender.recommender import recommend


def main():
    p = argparse.ArgumentParser(description="Workstream C pipeline (decisions -> recommendations)")
    p.add_argument("--mock", action="store_true", help="read mocks/decisions.csv instead of the real file")
    p.add_argument("--minutes", type=int, default=None, help="simulated minutes available")
    p.add_argument("--can-leave-desk", action="store_true")
    p.add_argument("--prefers", default=None, help="a preferred intervention")
    args = p.parse_args()

    decisions = io.read_table("decisions", use_mock=args.mock)
    context = {
        "minutes_available": args.minutes,
        "can_leave_desk": args.can_leave_desk,
        "prefers": args.prefers,
    }

    decisions = decisions.copy()
    decisions["recommendation"] = decisions["decision"].map(lambda d: recommend(d, context))

    out = ROOT / "artifacts"
    out.mkdir(exist_ok=True)
    path = out / "recommendations.csv"
    decisions.to_csv(path, index=False)

    print("[recommend] decisions:", decisions["decision"].value_counts().to_dict())
    print("[recommend] suggestions:", decisions["recommendation"].value_counts().to_dict())
    print(f"[recommend] wrote {len(decisions)} rows -> {path}")


if __name__ == "__main__":
    main()
