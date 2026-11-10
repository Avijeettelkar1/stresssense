"""Config loading and seeding. Jointly owned (change via PR)."""
from __future__ import annotations

import os
import random
from pathlib import Path

import yaml

# Repo root = two levels up from this file (src/common/config.py).
ROOT = Path(__file__).resolve().parents[2]


def load_config() -> dict:
    """Load config.local.yaml if present, else the committed example."""
    local = ROOT / "config.local.yaml"
    path = local if local.exists() else ROOT / "config.example.yaml"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def set_seeds(seed: int | None = None) -> int:
    """Seed Python, PYTHONHASHSEED and numpy so results are reproducible."""
    if seed is None:
        seed = int(load_config().get("seed", 42))
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import numpy as np

        np.random.seed(seed)
    except ImportError:
        pass
    return seed
