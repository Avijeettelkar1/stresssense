"""Stress classifier. Owner: A.

Returns an sklearn Pipeline (median imputer + scaler + random forest) exposing predict_proba, so
the `score` column is a probability of stress.
"""
from __future__ import annotations

from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def build_model(cfg: dict | None = None, seed: int = 42):
    model_cfg = (cfg or {}).get("model", {}) if cfg else {}
    n_estimators = int(model_cfg.get("n_estimators", 200))

    estimator = RandomForestClassifier(
        n_estimators=n_estimators, random_state=seed,
        class_weight="balanced", n_jobs=-1,
    )

    # Impute first: physio features can be NaN when a window is too short/flat for an estimator.
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("clf", estimator),
    ])
