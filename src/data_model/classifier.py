"""Stress classifier. Owner: A.

Returns an sklearn Pipeline (scaler + estimator) exposing predict_proba, so the `score` column
is a probability of stress. Swappable via config['model']['type'] ('rf' default, or 'lightgbm').
"""
from __future__ import annotations

from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def build_model(cfg: dict | None = None, seed: int = 42):
    model_cfg = (cfg or {}).get("model", {}) if cfg else {}
    kind = model_cfg.get("type", "rf")
    n_estimators = int(model_cfg.get("n_estimators", 200))

    if kind == "lightgbm":
        from lightgbm import LGBMClassifier

        estimator = LGBMClassifier(
            n_estimators=n_estimators, random_state=seed, class_weight="balanced", verbose=-1
        )
    else:
        estimator = RandomForestClassifier(
            n_estimators=n_estimators, random_state=seed,
            class_weight="balanced", n_jobs=-1,
        )

    return Pipeline([("scaler", StandardScaler()), ("clf", estimator)])
