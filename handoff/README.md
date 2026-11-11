# handoff/

The **real** contract files that pass between workstreams, committed here (each < 1 MB) so the
producing owner commits them and the consuming workstream pulls them via git.

| File | Producer → Consumer | Status |
| --- | --- | --- |
| `windows.parquet` | A → B | optional (large-ish; commit if useful) |
| `scores.csv` | A → B | **present** — real LOSO + random scores, 15 subjects |
| `decisions.csv` | B → C | added by B |

These replace the `mocks/` versions: run a pipeline without `--mock` to read/write here.
Raw data and bulky generated outputs still stay out of git (`data/`, `artifacts/`).
Formats are fixed in [`../contracts/`](../contracts/) — a column change needs a 3-way PR.
