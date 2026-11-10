# `scores.csv` — A → B

One row per (window × split × sensor configuration). This is the classifier's output that B's gate
and baseline consume.

| Column | Type | Meaning |
| --- | --- | --- |
| `subject_id` | string | Subject, e.g. `S2`. |
| `window_id` | int | Matches `windows.parquet`. |
| `split` | string | `loso` (leave-one-subject-out) or `random`. |
| `sensor_config` | string | `wrist`, `chest`, or `all`. |
| `label` | int | `1` = stress, `0` = not. |
| `score` | float | Predicted probability of stress, in `[0, 1]`. |

**Notes**
- `loso` rows come from subject-independent evaluation (RQ1); `random` rows from a same-subject-mixed
  split, kept only as a contrast to show why LOSO matters.
- Every subject appears for every `sensor_config` so B can do per-user analysis (RQ2).
