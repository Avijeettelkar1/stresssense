"""Check the committed mocks still satisfy the contracts. Run: pytest"""
import csv
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _schemas():
    with open(ROOT / "contracts" / "schemas.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _csv_header(path):
    with open(path, "r", newline="", encoding="utf-8") as f:
        return next(csv.reader(f))


def test_mock_scores_matches_contract():
    required = _schemas()["scores"]["required_columns"].keys()
    header = _csv_header(ROOT / "mocks" / "scores.csv")
    for col in required:
        assert col in header, f"scores.csv missing column: {col}"


def test_mock_decisions_matches_contract():
    required = _schemas()["decisions"]["required_columns"].keys()
    header = _csv_header(ROOT / "mocks" / "decisions.csv")
    for col in required:
        assert col in header, f"decisions.csv missing column: {col}"
