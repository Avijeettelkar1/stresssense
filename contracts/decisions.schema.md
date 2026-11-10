# `decisions.csv` — B → C

One row per window, giving the gate's decision. This is what C's recommender turns into a suggestion.

| Column | Type | Meaning |
| --- | --- | --- |
| `subject_id` | string | Subject, e.g. `S2`. |
| `window_id` | int | Matches `windows.parquet` / `scores.csv`. |
| `decision` | string | `act` (recommend intervention), `watch` (observe more / low confidence), or `none`. |
| `adjusted_score` | float | Score after the personal-baseline adjustment. |
| `threshold` | float | Gate threshold used for this decision. |
| `nudge_rate` | float | Running share of windows that triggered `act` (so C can show how often it nudges). |

**Notes**
- `watch` is the uncertainty-aware case (RQ4): the system chooses **not** to act when confidence is low.
- C should treat `decision` as the source of truth and use `adjusted_score`/`nudge_rate` for display only.
