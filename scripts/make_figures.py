"""Friday figures (RQ1, RQ2, RQ3, movement check) -> artifacts/figures/*.png

Reads only small files that are already in handoff/ (no WESAD needed):
  handoff/scores.csv            A's real scores (RQ1, RQ2, S14 picture, RQ3)
  handoff/movement_check.csv    optional, from the Colab movement test (figure 5)

Usage:
  python scripts/make_figures.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.common import io
from src.common.config import ROOT, set_seeds
from src.data_model.evaluate import per_subject_metrics, summarize
from src.recommender.figures import use_style
from src.reliability.baseline import (RISE_GRID, WARMUP, _by_person, evaluate_rq3, grade,
                                      personal_baseline, predict_label_free)

# Categorical slots (fixed order) + neutral ink, from the shared dataviz reference palette.
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#d3d1c7"
SENSORS = ["wrist", "chest", "all"]
OUT = ROOT / "artifacts" / "figures"


def _style():
    use_style()
    plt.rcParams.update({"text.color": INK, "axes.labelcolor": INK2, "xtick.color": INK2,
                         "ytick.color": INK2, "axes.edgecolor": GRID, "grid.color": GRID,
                         "axes.titleweight": "normal", "axes.titlesize": 12})


def _save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {OUT / name}")


def _bar_labels(ax, bars):
    for b in bars:
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.015, f"{b.get_height():.2f}",
                ha="center", va="bottom", fontsize=9, color=INK2)


def fig1_rq1(summary):
    """Fair (new person) vs unfair (random mix): average and worst person."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    x, w = np.arange(len(SENSORS)), 0.36
    for ax, col, title in [(axes[0], "mean_bal_acc", "Average person"),
                           (axes[1], "worst_bal_acc", "Worst person")]:
        for i, (split, colr, name) in enumerate([("loso", BLUE, "Fair test: new person"),
                                                 ("random", ORANGE, "Unfair test: random mix")]):
            vals = [summary.query("split == @split and sensor_config == @s")[col].iloc[0]
                    for s in SENSORS]
            bars = ax.bar(x + (i - 0.5) * (w + 0.02), vals, w, color=colr, label=name)
            _bar_labels(ax, bars)
        ax.axhline(0.5, color=INK2, lw=1, ls="--")
        ax.set_xticks(x, SENSORS)
        ax.set_ylim(0, 1.12)
        ax.set_title(title)
        ax.grid(axis="x", visible=False)
    axes[0].set_ylabel("Balanced accuracy")
    axes[0].text(2.45, 0.52, "guessing", fontsize=8, color=INK2, ha="right")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, frameon=False, fontsize=9,
               bbox_to_anchor=(0.5, -0.06))
    fig.suptitle("RQ1: the random mix flatters the model; the worst new person sits at guessing", y=1.03)
    _save(fig, "fig1_rq1_fair_vs_unfair.png")


def fig2_rq2(metrics):
    """Every person's balanced accuracy, fair test, all sensors."""
    m = metrics.query("split == 'loso' and sensor_config == 'all'").sort_values("balanced_acc")
    colors = [ORANGE if s == "S14" else BLUE for s in m["subject_id"]]
    fig, ax = plt.subplots(figsize=(8, 5.5))
    bars = ax.barh(m["subject_id"], m["balanced_acc"], color=colors, height=0.7)
    for b, v in zip(bars, m["balanced_acc"]):
        ax.text(v + 0.01, b.get_y() + b.get_height() / 2, f"{v:.2f}", va="center",
                fontsize=8, color=INK2)
    ax.axvline(0.5, color=INK2, lw=1, ls="--")
    ax.axvline(m["balanced_acc"].mean(), color=INK, lw=1)
    ax.text(m["balanced_acc"].mean() + 0.01, -0.9, f"average {m['balanced_acc'].mean():.2f}",
            fontsize=8, color=INK)
    ax.text(0.51, len(m) - 0.4, "guessing", fontsize=8, color=INK2)
    ax.set_xlim(0, 1.1)
    ax.set_xlabel("Balanced accuracy (fair test, all sensors)")
    ax.grid(axis="y", visible=False)
    ax.set_title("RQ2: a good average hides people the model fails (S14 at 0.50)")
    _save(fig, "fig2_rq2_per_person.png")


def fig3_s14(scores):
    """S14's windows: stressed score higher than calm, but all below the 0.5 line."""
    s14 = scores.query("subject_id == 'S14'").sort_values("window_id")
    rng = np.random.default_rng(0)
    fig, ax = plt.subplots(figsize=(9, 3.4))
    for lab, colr, name in [(0, BLUE, "calm minutes"), (1, ORANGE, "stressed minutes")]:
        d = s14[s14["label"] == lab]
        ax.scatter(d["score"], lab + rng.uniform(-0.18, 0.18, len(d)), s=36, color=colr,
                   edgecolor="white", linewidth=1, label=f"{name} ({len(d)})", zorder=3)
    line = personal_baseline(s14["score"].to_numpy()) + 0.15
    ax.axvline(0.5, color=INK, lw=1.5, ls="--")
    ax.text(0.51, 1.42, "one alarm line for everyone (0.5)", fontsize=8, color=INK)
    ax.axvline(line, color=AQUA, lw=1.5)
    ax.text(line + 0.01, -0.55, f"S14's personal line ({line:.2f})", fontsize=8, color=INK)
    ax.set_yticks([0, 1], ["calm", "stressed"])
    ax.set_ylim(-0.7, 1.6)
    ax.set_xlim(-0.02, 1.0)
    ax.set_xlabel("Stress score from the model (S14 never seen in training)")
    ax.grid(axis="y", visible=False)
    ax.legend(loc="center right", frameon=False, fontsize=8)
    ax.set_title("S14: the model ranks stress above calm every time (AUROC 1.00), "
                 "but never reaches 0.5")
    _save(fig, "fig3_s14_scores.png")


def fig4_rq3(per_person):
    """Per person: one line for everyone vs personal baseline vs ask 1+1."""
    t = per_person.pivot(index="subject_id", columns="method", values="balanced_acc")
    t = t.sort_values("global", ascending=False)
    y = np.arange(len(t))
    fig, ax = plt.subplots(figsize=(8, 6))
    for col, colr, name, off in [("global", INK2, "one line for everyone", -0.22),
                                 ("label-free", BLUE, "personal baseline (no questions)", 0.0),
                                 ("label-budgeted k=1", ORANGE, "ask 1 stressed + 1 calm", 0.22)]:
        ax.scatter(t[col], y + off, s=40, color=colr, edgecolor="white", linewidth=1.5,
                   label=f"{name}: worst {t[col].min():.2f}", zorder=3)
    for i, (_, r) in enumerate(t.iterrows()):
        ax.plot([r.min(), r.max()], [i, i], color=GRID, lw=1, zorder=1)
    ax.axvline(0.5, color=INK2, lw=1, ls="--")
    ax.set_yticks(y, t.index)
    ax.set_xlim(0.45, 1.03)
    ax.set_xlabel("Balanced accuracy (fair test, all sensors)")
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower left", frameon=False, fontsize=8)
    ax.set_title("RQ3: personal lines lift the worst person from 0.50 to about 0.84")
    _save(fig, "fig4_rq3_before_after.png")


def fig6_rise_sweep(scores):
    """How R (the rise above your calm) was chosen: every value we tried, graded on all 15."""
    people = _by_person(scores)
    rows = []
    for rise in RISE_GRID:
        g = pd.DataFrame([grade(predict_label_free(s, rise)[WARMUP:], y[WARMUP:])
                          for s, y in people.values()])
        rows.append({"rise": rise, "mean": g["balanced_acc"].mean(), "worst": g["balanced_acc"].min(),
                     "caught": g["stress_caught"].mean(), "alone": g["calm_left_alone"].mean()})
    t = pd.DataFrame(rows)
    best = t.loc[t["mean"].idxmax(), "rise"]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharex=True)
    for ax, cols, title in [
        (axes[0], [("mean", BLUE, "average person"), ("worst", ORANGE, "worst person")],
         "Grade for each R we tried (balanced accuracy)"),
        (axes[1], [("caught", BLUE, "stress caught"), ("alone", AQUA, "calm left alone")],
         "Why there's a sweet spot"),
    ]:
        for col, colr, name in cols:
            ax.plot(t["rise"], t[col], color=colr, lw=2, marker="o", ms=7,
                    markeredgecolor="white", markeredgewidth=1.5, label=name, zorder=3)
        ax.axvline(best, color=INK2, lw=1, ls="--", zorder=1)
        ax.set_title(title)
        ax.set_xlabel("R = how far above your own calm level counts as stressed")
        ax.set_xticks(list(RISE_GRID))
        ax.legend(loc="lower right", frameon=False, fontsize=9)
    m = t.set_index("rise").loc[best]
    axes[0].annotate(f"R = {best:.2f}: average {m['mean']:.3f}", (best, m["mean"]),
                     xytext=(best + 0.03, m["mean"] + 0.04), fontsize=9, color=INK,
                     arrowprops={"arrowstyle": "-", "color": INK2, "lw": 0.8})
    axes[0].set_ylim(0.4, 1.02)
    axes[1].set_ylim(0.4, 1.02)
    fig.suptitle("RQ3: we tested every rise value; 0.15 works best (and is picked for all 15 "
                 "people when chosen on the other 14)", y=1.03)
    _save(fig, "fig6_rq3_choosing_R.png")


def fig5_movement(path):
    """Retrained without the 16 movement numbers: does performance hold?"""
    if not path.exists():
        print(f"  skipped fig5: {path} not found (run the Colab movement check first)")
        return
    summ = summarize(per_subject_metrics(pd.read_csv(path)))
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    x, w = np.arange(len(SENSORS)), 0.36
    for ax, col, title in [(axes[0], "mean_bal_acc", "Balanced accuracy (average person)"),
                           (axes[1], "mean_auroc", "AUROC (average person)")]:
        for i, (split, colr, name) in enumerate([("with_movement", BLUE, "with movement"),
                                                 ("no_movement", AQUA, "without movement")]):
            vals = [summ.query("split == @split and sensor_config == @s")[col].iloc[0]
                    for s in SENSORS]
            _bar_labels(ax, ax.bar(x + (i - 0.5) * (w + 0.02), vals, w, color=colr, label=name))
        ax.set_xticks(x, SENSORS)
        ax.set_ylim(0, 1.12)
        ax.set_title(title)
        ax.grid(axis="x", visible=False)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, frameon=False, fontsize=9,
               bbox_to_anchor=(0.5, -0.06))
    fig.suptitle("Movement check: removing all movement data barely changes anything", y=1.03)
    _save(fig, "fig5_movement_check.png")


def main():
    set_seeds()
    _style()
    scores = io.read_table("scores")
    metrics = per_subject_metrics(scores)
    summary = summarize(metrics)
    loso_all = scores.query("split == 'loso' and sensor_config == 'all'")

    print("[figures] drawing ...")
    fig1_rq1(summary)
    fig2_rq2(metrics)
    fig3_s14(loso_all)
    fig4_rq3(evaluate_rq3(loso_all, budgets=(1,)))
    fig5_movement(ROOT / "handoff" / "movement_check.csv")
    fig6_rise_sweep(loso_all)
    print(f"[figures] done -> {OUT}")


if __name__ == "__main__":
    main()
