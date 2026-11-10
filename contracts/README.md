# Contracts

These are the **fixed formats** of the files that pass between workstreams. They let A, B and C work
alone against agreed columns.

**Rule: changing any column requires all three of us to agree in a pull request.** If you need a new
column, open a PR that edits `schemas.yaml` *and* the relevant `*.schema.md`, and get both teammates
to approve before anyone writes code against it.

| File | Producer → Consumer | Format | Schema |
| --- | --- | --- | --- |
| `windows.parquet` | A → B | parquet | [windows.schema.md](windows.schema.md) |
| `scores.csv` | A → B | csv | [scores.schema.md](scores.schema.md) |
| `decisions.csv` | B → C | csv | [decisions.schema.md](decisions.schema.md) |

`schemas.yaml` is the machine-readable version. `src/common/io.py` validates every read/write against
it, and `tests/test_contracts.py` checks the committed mocks still match.
