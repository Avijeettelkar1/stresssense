"""Personal baseline / calibration. Owner: B. (RQ3)

RQ3 asks: can a little per-person calibration help the WORST person and make people more equal,
compared with one alarm line for everyone? We compare three honest ways of turning A's stress
`score` (0..1, from the leave-one-person-out model) into a stressed / not-stressed call:

  global          stressed if  score >= 0.5
                  One line for everyone. The "before".

  label-free      baseline(person) = average score of the person's first WARMUP windows
                  rise             = score - baseline(person)
                  stressed if  rise >= R
                  No questions asked. Assumes the first minutes of wearing are calm (true in
                  WESAD, where the baseline phase comes first). R is the same for everyone and is
                  chosen on the OTHER people only, never on the person being graded.

  label-budgeted  The person tells us k stressed and k calm moments.
                  line(person) = (mean score of their stressed examples
                                  + mean score of their calm examples) / 2
                  stressed if  score >= line(person)
                  The labelled windows and their direct neighbours (which share half their data)
                  are left out of grading. Which moments are asked is random, so we repeat
                  n_draws times and average.

Fair grading: the first WARMUP windows of every person are a warm-up for label-free, so they are
graded for NO method. Each person is graded with balanced accuracy, then we report the average
person, the worst person and the spread.

This replaces the earlier draft, which (a) used each person's whole recording, i.e. the future,
and (b) took the first 10 windows as the label budget; those are always baseline in WESAD, so it
never saw a stressed example, and it graded on the same windows it calibrated on.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

MODES = ("global", "label-free", "label-budgeted")

WARMUP = 10                                    # ~5.5 min with 60 s windows every 30 s
GLOBAL_THRESHOLD = 0.5
RISE_GRID = (0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40)


# --------------------------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------------------------
def _by_person(scores_df: pd.DataFrame) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """{subject_id: (scores, labels)}, each person's windows in time order."""
    df = scores_df.sort_values(["subject_id", "window_id"])
    return {s: (g["score"].to_numpy(dtype=float), g["label"].to_numpy(dtype=int))
            for s, g in df.groupby("subject_id", sort=True)}


def grade(stressed: np.ndarray, labels: np.ndarray) -> dict:
    """Balanced accuracy = (share of stress caught + share of calm left alone) / 2."""
    stressed, labels = np.asarray(stressed, bool), np.asarray(labels, int)
    n_stress, n_calm = int((labels == 1).sum()), int((labels == 0).sum())
    if n_stress == 0 or n_calm == 0:
        return {"balanced_acc": np.nan, "stress_caught": np.nan, "calm_left_alone": np.nan}
    caught = (stressed & (labels == 1)).sum() / n_stress
    left_alone = (~stressed & (labels == 0)).sum() / n_calm
    return {"balanced_acc": (caught + left_alone) / 2,
            "stress_caught": caught, "calm_left_alone": left_alone}


def personal_baseline(scores: np.ndarray, warmup: int = WARMUP) -> float:
    """The person's calm level: average score over their first `warmup` windows (no labels)."""
    return float(np.mean(scores[:warmup]))


# --------------------------------------------------------------------------------------------
# The three ways of deciding "stressed"
# --------------------------------------------------------------------------------------------
def predict_global(scores: np.ndarray, threshold: float = GLOBAL_THRESHOLD) -> np.ndarray:
    return scores >= threshold


def predict_label_free(scores: np.ndarray, rise: float, warmup: int = WARMUP) -> np.ndarray:
    return (scores - personal_baseline(scores, warmup)) >= rise


def choose_rise(people: dict, exclude: str | None, warmup: int = WARMUP,
                grid=RISE_GRID) -> float:
    """Pick R that gives the best average balanced accuracy on everyone EXCEPT `exclude`."""
    def avg_ba(rise):
        vals = [grade(predict_label_free(s, rise, warmup)[warmup:], y[warmup:])["balanced_acc"]
                for p, (s, y) in people.items() if p != exclude and len(s) > warmup]
        return np.nanmean(vals) if vals else -np.inf
    return float(max(grid, key=avg_ba))


def budget_line(scores: np.ndarray, labels: np.ndarray, k: int, rng: np.random.Generator):
    """Ask k stressed + k calm moments at random. Return (personal line, asked indices) or None."""
    pos, neg = np.flatnonzero(labels == 1), np.flatnonzero(labels == 0)
    if len(pos) < k or len(neg) < k:
        return None
    asked_pos = rng.choice(pos, k, replace=False)
    asked_neg = rng.choice(neg, k, replace=False)
    line = (scores[asked_pos].mean() + scores[asked_neg].mean()) / 2.0
    return float(line), np.concatenate([asked_pos, asked_neg])


def _graded_mask(n: int, warmup: int, asked=()) -> np.ndarray:
    """Windows that count for grading: after warm-up, minus asked windows and their neighbours."""
    mask = np.zeros(n, bool)
    mask[warmup:] = True
    for i in asked:
        mask[max(0, i - 1):i + 2] = False
    return mask


# --------------------------------------------------------------------------------------------
# RQ3 contest
# --------------------------------------------------------------------------------------------
def evaluate_rq3(scores_df: pd.DataFrame, budgets=(1, 2, 3, 5), n_draws: int = 30,
                 warmup: int = WARMUP, seed: int = 42) -> pd.DataFrame:
    """One row per (person, method): balanced accuracy, stress caught, calm left alone."""
    people = _by_person(scores_df)
    rng = np.random.default_rng(seed)
    rows = []
    for person, (s, y) in people.items():
        if len(s) <= warmup:
            continue
        graded = _graded_mask(len(s), warmup)

        g = grade(predict_global(s)[graded], y[graded])
        rows.append({"subject_id": person, "method": "global", "setting": GLOBAL_THRESHOLD, **g})

        rise = choose_rise(people, exclude=person, warmup=warmup)
        g = grade(predict_label_free(s, rise, warmup)[graded], y[graded])
        rows.append({"subject_id": person, "method": "label-free", "setting": rise,
                     "baseline": personal_baseline(s, warmup), **g})

        for k in budgets:
            draws = []
            for _ in range(n_draws):
                got = budget_line(s, y, k, rng)
                if got is None:
                    continue
                line, asked = got
                mask = _graded_mask(len(s), warmup, asked)
                draws.append({"setting": line, **grade((s >= line)[mask], y[mask])})
            if draws:
                avg = pd.DataFrame(draws).mean().to_dict()
                rows.append({"subject_id": person, "method": f"label-budgeted k={k}", **avg})
    return pd.DataFrame(rows)


def summarise_rq3(per_person: pd.DataFrame) -> pd.DataFrame:
    """Average person, worst person (and who), spread: the RQ3 headline table."""
    out = []
    for method, g in per_person.groupby("method", sort=False):
        worst = g.loc[g["balanced_acc"].idxmin()]
        out.append({"method": method,
                    "mean_bal_acc": g["balanced_acc"].mean(),
                    "worst_bal_acc": worst["balanced_acc"],
                    "worst_subject": worst["subject_id"],
                    "std_bal_acc": g["balanced_acc"].std(),
                    "mean_stress_caught": g["stress_caught"].mean(),
                    "mean_calm_left_alone": g["calm_left_alone"].mean()})
    return pd.DataFrame(out)


# --------------------------------------------------------------------------------------------
# Adjusted score for the gate (decisions.csv)
# --------------------------------------------------------------------------------------------
def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def adjust_scores(scores_df: pd.DataFrame, mode: str = "global", budget: int = 1,
                  warmup: int = WARMUP, seed: int = 42) -> pd.DataFrame:
    """Return `scores_df` with an `adjusted_score` column for the gate.

    adjusted_score is centred on the person's own alarm line: 0.5 means "exactly on the line",
    above 0.5 means above it. For global, adjusted_score is the raw score (line 0.5).
    label-budgeted uses one random draw of `budget` stressed + `budget` calm moments.
    """
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}, got {mode!r}")

    df = scores_df.sort_values(["subject_id", "window_id"]).copy()
    if mode == "global":
        df["adjusted_score"] = df["score"].astype(float)
        return df.reset_index(drop=True)

    people = _by_person(df)
    rng = np.random.default_rng(seed)
    parts = []
    for person, g in df.groupby("subject_id", sort=True):
        s, y = people[person]
        if mode == "label-free":
            line = personal_baseline(s, warmup) + choose_rise(people, exclude=person, warmup=warmup)
        else:
            got = budget_line(s, y, budget, rng)
            line = got[0] if got else GLOBAL_THRESHOLD
        g = g.copy()
        # Steep squash so the 0..1 range stays readable: 0.5 = on the personal line.
        g["adjusted_score"] = np.round(_sigmoid(10.0 * (s - line)), 6)
        parts.append(g)
    return pd.concat(parts, ignore_index=True)
