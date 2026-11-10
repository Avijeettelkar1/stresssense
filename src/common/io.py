"""Contract-aware readers/writers for the hand-off files. Jointly owned (change via PR).

Every read/write is validated against contracts/schemas.yaml, so a format drift fails loudly
instead of silently corrupting someone else's downstream work.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from .config import ROOT, load_config


@lru_cache(maxsize=1)
def schemas() -> dict:
    with open(ROOT / "contracts" / "schemas.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate(df, name: str):
    """Raise if a dataframe is missing any required column for `name`."""
    required = list(schemas()[name]["required_columns"].keys())
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"{name}: missing required columns {missing}; has {list(df.columns)}")
    return df


def resolve_path(name: str, use_mock: bool = False) -> Path:
    cfg = load_config()
    key = f"mock_{name}" if use_mock else name
    return ROOT / cfg["paths"][key]


def read_table(name: str, use_mock: bool = False):
    """Read a hand-off file ('windows' | 'scores' | 'decisions')."""
    import pandas as pd

    path = resolve_path(name, use_mock)
    df = pd.read_parquet(path) if str(path).endswith(".parquet") else pd.read_csv(path)
    return validate(df, name)


def write_table(df, name: str) -> Path:
    """Validate then write a hand-off file to its real (non-mock) path."""
    path = resolve_path(name)
    validate(df, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    if str(path).endswith(".parquet"):
        df.to_parquet(path, index=False)
    else:
        df.to_csv(path, index=False)
    return path
