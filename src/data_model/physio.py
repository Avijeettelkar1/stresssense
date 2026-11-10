"""Physiological features via neurokit2. Owner: A.

Richer, domain-specific features that usually beat plain statistics for stress detection:
  ECG (chest) / BVP (wrist) -> heart rate + HRV (RMSSD, SDNN)
  EDA (chest + wrist)       -> tonic level (SCL), phasic activity, SCR peak count/amplitude
  RESP (chest)              -> respiration rate + amplitude

Robustness: each estimator is wrapped — a window that is too short or flat yields NaN for that
feature (imputed downstream by the classifier), and if neurokit2 is not installed we degrade to
no physio features rather than crashing.
"""
from __future__ import annotations

import warnings

import numpy as np

try:
    import neurokit2 as nk

    HAVE_NK = True
except Exception:  # pragma: no cover - import guard
    HAVE_NK = False

ECG_KEYS = ("hr_mean", "hr_std", "hrv_rmssd", "hrv_sdnn")
EDA_KEYS = ("scl_mean", "phasic_mean", "scr_count", "scr_amp_mean")
RSP_KEYS = ("rate_mean", "rate_std", "amp_mean")


def _nan(keys) -> dict:
    return {k: np.nan for k in keys}


def _hr_hrv(rate: np.ndarray, peaks, fs: int) -> dict:
    out = {"hr_mean": float(np.nanmean(rate)), "hr_std": float(np.nanstd(rate)),
           "hrv_rmssd": np.nan, "hrv_sdnn": np.nan}
    try:
        hrv = nk.hrv_time(peaks, sampling_rate=fs, show=False)
        out["hrv_rmssd"] = float(hrv["HRV_RMSSD"].iloc[0])
        out["hrv_sdnn"] = float(hrv["HRV_SDNN"].iloc[0])
    except Exception:
        pass
    return out


def ecg_features(sig, fs: int) -> dict:
    if not HAVE_NK:
        return _nan(ECG_KEYS)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            s, i = nk.ecg_process(np.asarray(sig, dtype=float), sampling_rate=fs)
        return _hr_hrv(s["ECG_Rate"].to_numpy(), i["ECG_R_Peaks"], fs)
    except Exception:
        return _nan(ECG_KEYS)


def ppg_features(sig, fs: int) -> dict:
    if not HAVE_NK:
        return _nan(ECG_KEYS)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            s, i = nk.ppg_process(np.asarray(sig, dtype=float), sampling_rate=fs)
        return _hr_hrv(s["PPG_Rate"].to_numpy(), i["PPG_Peaks"], fs)
    except Exception:
        return _nan(ECG_KEYS)


def eda_features(sig, fs: int) -> dict:
    if not HAVE_NK:
        return _nan(EDA_KEYS)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            s, i = nk.eda_process(np.asarray(sig, dtype=float), sampling_rate=fs)
        amp = i.get("SCR_Amplitude", []) if isinstance(i, dict) else []
        return {
            "scl_mean": float(s["EDA_Tonic"].mean()),
            "phasic_mean": float(s["EDA_Phasic"].mean()),
            "scr_count": float(np.nansum(s["SCR_Peaks"].to_numpy())),
            "scr_amp_mean": float(np.nanmean(amp)) if len(amp) else 0.0,
        }
    except Exception:
        return _nan(EDA_KEYS)


def rsp_features(sig, fs: int) -> dict:
    if not HAVE_NK:
        return _nan(RSP_KEYS)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            s, i = nk.rsp_process(np.asarray(sig, dtype=float), sampling_rate=fs)
        return {
            "rate_mean": float(np.nanmean(s["RSP_Rate"].to_numpy())),
            "rate_std": float(np.nanstd(s["RSP_Rate"].to_numpy())),
            "amp_mean": float(np.nanmean(s["RSP_Amplitude"].to_numpy())),
        }
    except Exception:
        return _nan(RSP_KEYS)


# (location, channel) -> feature function
PHYSIO_FUNCS = {
    ("chest", "ecg"): ecg_features,
    ("wrist", "bvp"): ppg_features,
    ("chest", "eda"): eda_features,
    ("wrist", "eda"): eda_features,
    ("chest", "resp"): rsp_features,
}
