# StressSense

**From wearable stress detection to personalised, uncertainty-aware intervention recommendation.**

A three-person university project (AI in Healthcare / Wearable Computing). We build a pipeline:

```
wearable signals (WESAD)
      → stress-state estimation
      → uncertainty estimation
      → recommendation policy (a risk-controlled gate)
      → non-clinical well-being nudge  (breathing / break / walk / none)
```

> **Not a diagnostic tool.** This does **not** diagnose anxiety, depression, chronic stress or any
> psychiatric illness. It detects patterns associated with the experimental states in the dataset,
> and recommends non-clinical well-being interventions only.

## Research questions

| RQ | Question | Owned by |
| --- | --- | --- |
| **RQ1** Generalisation | How well do models generalise to unseen people? (subject-independent / LOSO, not random mixing) | A |
| **RQ2** Individual disparity | How much does performance vary between people despite similar aggregate scores? (per-user, worst-user, variance) | A |
| **RQ3** Personalisation | Can limited calibration improve the **worst** user vs a global model, and reduce disparity? | B |
| **RQ4** Recommendation reliability | Does an uncertainty-aware gate reduce inappropriate interventions vs always acting? | B |

## Workstreams, owners, branches

| Stream | Branch | Folder(s) | Owns |
| --- | --- | --- | --- |
| **A** Data & model | `a/data-model` | `src/data_model/` | WESAD loading, windowing, features, classifier, LOSO + random-split testing, sensor-config comparison |
| **B** Reliability | `b/reliability` | `src/reliability/` | Personal baseline (global / label-free / label-budgeted), the risk-controlled gate, always-act vs gated comparison |
| **C** Recommender & report | `c/recommender` | `src/recommender/`, `report/` | Adaptive survey, recommender prototype, shared figure style, report & slides |

## Working rules (from the team plan)

- **One owner per folder.** Nobody edits another person's `src/` folder.
- **Contracts are fixed in [`contracts/`](contracts/).** Changing a column needs all three of us to agree in a PR.
- **Data stays out of git.** `data/` and large outputs are git-ignored; set your own path in `config.local.yaml`.
- **Reproducible.** Fixed seeds (`src/common/config.py::set_seeds`) and pinned `requirements.txt`.
- **One review per PR into `main`,** rotating, so everyone sees the whole project.
- Start commit messages with your letter, e.g. `a: add window features`.

## Hand-off files (the contracts)

| File | A → B → C | Lives (real) | Mock (committed) |
| --- | --- | --- | --- |
| `windows.parquet` | A → B | `artifacts/` (git-ignored) | — |
| `scores.csv` | A → B | `artifacts/` (git-ignored) | [`mocks/scores.csv`](mocks/scores.csv) |
| `decisions.csv` | B → C | `artifacts/` (git-ignored) | [`mocks/decisions.csv`](mocks/decisions.csv) |

B and C build against the **mocks** first, then switch to the real files when they arrive.
Column definitions: [`contracts/`](contracts/).

## Getting started

```bash
# 1. environment
python -m venv .venv
.venv\Scripts\activate          # Windows (PowerShell: .venv\Scripts\Activate.ps1)
pip install -r requirements.txt

# 2. local config (git-ignored) — point it at your WESAD download
cp config.example.yaml config.local.yaml   # Windows: copy config.example.yaml config.local.yaml
#   then edit data.wesad_root

# 3. generate the mock hand-off files (M1)
python scripts/make_mocks.py

# 4. sanity-check the contracts
pytest
```

### Workstream A pipeline (data → model → scores)

Once `data.wesad_root` points at your WESAD download:

```bash
python scripts/run_pipeline.py --stage all          # data → scores → metrics
python scripts/run_pipeline.py --stage data         # → artifacts/windows.parquet  (A→B)
python scripts/run_pipeline.py --stage scores       # LOSO + random → artifacts/scores.csv  (A→B)
python scripts/run_pipeline.py --stage metrics      # RQ1/RQ2 tables → reports/
python scripts/run_pipeline.py --stage data --subjects S2 S3   # quick subset
```

Stage map: `src/data_model/load_wesad.py` → `preprocess.py` (+ `features.py`) → `windows.parquet`;
`classifier.py` + `evaluate.py` → `scores.csv` (LOSO is the headline, random is the contrast);
`evaluate.per_subject_metrics` → the worst-user / disparity table (RQ2). Windowing and model
settings live under `windows:` and `model:` in `config.example.yaml`.

## Milestones

| # | Date | Done when |
| --- | --- | --- |
| **M1** | Nov 13 | Repo + 3 branches pushed, `contracts/` has the 3 formats, mock `scores.csv` + `decisions.csv` on `main` |
| **M2** | Nov 27 | Real `scores.csv`: LOSO + random split, every subject, each sensor config |
| **M3** | Dec 4 | Gate runs on real scores → real `decisions.csv`; personal baseline works |
| **M4** | Dec 11 | End to end: signals in → suggestion out; first RQ1–RQ4 results |
| **M5** | Jan 4 | Code freeze — only fixes and write-up after this |

Target submission **Jan 13**, hard deadline **Jan 15**.

## Open questions (decide in week 1)

See the team plan. Key ones: who is A/B/C; GitHub vs university GitLab; exact label definition
(default: **stress vs everything else** — baseline + amusement + meditation as negatives);
which sensor configs to compare (default: **wrist / chest / all**); whether the nudge rate is
user-adjustable; whether to run the optional ACI comparison and classmate survey.

## Dataset

**WESAD** (Schmidt et al.) — multimodal physiological + motion signals, one folder per subject with a
pickle each. Download separately; it is **not** committed. Set `data.wesad_root` in `config.local.yaml`.
