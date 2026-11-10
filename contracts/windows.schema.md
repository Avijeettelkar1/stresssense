# `windows.parquet` — A → B

One row per fixed-length window of a subject's signals.

| Column | Type | Meaning |
| --- | --- | --- |
| `subject_id` | string | Subject, e.g. `S2`. |
| `window_id` | int | 0-based window index within the subject. |
| `t_start` | float | Window start time in seconds. |
| `phase` | string | Experimental phase: `baseline`, `stress`, `amusement`, `meditation`, … |
| `label` | int | `1` = stress, `0` = not (per the week-1 label definition). |
| *feature columns* | float | One column per feature, including movement/accelerometer features. Names agreed in week 1 and kept stable. |

**Notes**
- Windowing parameters (length, overlap) are A's choice but must be documented here once fixed.
- `label` is derived from `phase` using the agreed definition (default: stress vs everything else).
