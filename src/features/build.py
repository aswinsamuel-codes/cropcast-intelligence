"""
Feature construction for next-market-day forecasting (Req 4).

All features at forecast origin t (market-day index) are built with shift and
trailing-window operations, so they depend only on rows with index <= t. The
target is the modal price at index t + 1.
"""

from __future__ import annotations

from typing import List

import numpy as np
import pandas as pd

PRICE_LAGS = (1, 2, 3, 5, 7)
ROLLING_WINDOWS = (7, 14)
ARRIVAL_LAGS = (1, 2)


def lag_features(y: pd.Series, lags=PRICE_LAGS) -> pd.DataFrame:
    """price_lag_k = y_{t+1-k}: lag k relative to the target, so price_lag_1 is the origin value."""
    if y.empty:
        raise ValueError("lag_features received an empty series")
    return pd.DataFrame({f"price_lag_{k}": y.shift(k - 1) for k in lags}, index=y.index)


def rolling_features(y: pd.Series, windows=ROLLING_WINDOWS) -> pd.DataFrame:
    """Trailing mean and sample SD over the last `w` market days, ending at the origin inclusive."""
    if y.empty:
        raise ValueError("rolling_features received an empty series")
    out = {}
    for w in windows:
        roll = y.rolling(window=w, min_periods=w)
        out[f"roll_mean_{w}"] = roll.mean()
        out[f"roll_std_{w}"] = roll.std(ddof=1)
    return pd.DataFrame(out, index=y.index)


def build_features(g: pd.DataFrame) -> pd.DataFrame:
    """
    Build the feature table for one series. `g` needs columns date, modal_price and
    arrival_qty, with one row per observed market day. Rows are returned in market-day
    order with an `is_valid` flag (Req 4.7) and a target that is NaN for the final row.
    """
    if g.empty:
        raise ValueError("build_features received an empty DataFrame")
    g = g.sort_values("date").reset_index(drop=True)
    if g["date"].duplicated().any():
        raise ValueError("build_features requires one row per market day")
    y = g["modal_price"].astype(float)
    q = g["arrival_qty"].astype(float)

    feat = pd.DataFrame({"origin_date": g["date"], "target_date": g["date"].shift(-1),
                         "y_origin": y, "target": y.shift(-1)})
    feat = feat.join(lag_features(y)).join(rolling_features(y))
    for k in ARRIVAL_LAGS:
        feat[f"arrival_lag_{k}"] = q.shift(k - 1)
    feat["dow_origin"] = g["date"].dt.day_of_week
    feat["month_origin"] = g["date"].dt.month
    # The next calendar day: whether a day will go unreported is not known at the origin
    feat["dow_target"] = (g["date"] + pd.Timedelta(days=1)).dt.day_of_week
    feat["target_gap_days"] = (feat["target_date"] - feat["origin_date"]).dt.days
    required = [c for c in feat.columns if c.startswith(("price_lag_", "roll_", "arrival_lag_"))]
    feat["is_valid"] = feat[required].notna().all(axis=1)
    return feat


MODEL_INPUT_COLUMNS: List[str] = (
    [f"lr_price_lag_{k}" for k in PRICE_LAGS[1:]]
    + [f"lr_roll_mean_{w}" for w in ROLLING_WINDOWS]
    + [f"rel_roll_std_{w}" for w in ROLLING_WINDOWS]
    + [f"log_arrival_lag_{k}" for k in ARRIVAL_LAGS]
    + ["dow_origin", "month_origin", "dow_target"]
)


def model_inputs(feat: pd.DataFrame) -> pd.DataFrame:
    """Parameter-free, scale-free transformation of the features (log ratios to the origin price)."""
    if feat.empty:
        raise ValueError("model_inputs received an empty DataFrame")
    base = feat["price_lag_1"]
    X = pd.DataFrame(index=feat.index)
    for k in PRICE_LAGS[1:]:
        X[f"lr_price_lag_{k}"] = np.log(feat[f"price_lag_{k}"] / base)
    for w in ROLLING_WINDOWS:
        X[f"lr_roll_mean_{w}"] = np.log(feat[f"roll_mean_{w}"] / base)
        X[f"rel_roll_std_{w}"] = feat[f"roll_std_{w}"] / base
    for k in ARRIVAL_LAGS:
        X[f"log_arrival_lag_{k}"] = np.log1p(feat[f"arrival_lag_{k}"])
    for c in ("dow_origin", "month_origin", "dow_target"):
        X[c] = feat[c]
    return X[MODEL_INPUT_COLUMNS]


def target_log_return(feat: pd.DataFrame) -> pd.Series:
    """r_{t+1} = log(y_{t+1}) - log(y_t)."""
    return np.log(feat["target"] / feat["y_origin"])


def feature_audit_table() -> pd.DataFrame:
    """Req 4.8: each feature, how it is derived, and the latest index it uses."""
    rows = []
    for k in PRICE_LAGS:
        rows.append(("price_lag_%d" % k, f"modal price at market-day index t-{k - 1}", f"t-{k - 1}"))
    for w in ROLLING_WINDOWS:
        rows.append((f"roll_mean_{w}", f"mean of modal price over indices t-{w - 1}..t", "t"))
        rows.append((f"roll_std_{w}", f"sample SD of modal price over indices t-{w - 1}..t", "t"))
    for k in ARRIVAL_LAGS:
        rows.append((f"arrival_lag_{k}", f"arrivals at index t-{k - 1}", f"t-{k - 1}"))
    rows += [("dow_origin", "day of week of the origin date", "t"),
             ("month_origin", "month of the origin date", "t"),
             ("dow_target", "day of week of origin date + 1 calendar day (known in advance)", "t")]
    df = pd.DataFrame(rows, columns=["feature", "derivation", "latest_index_used"])
    df["uses_future_data"] = "No"
    df["leakage_check"] = "tests/test_features.py: perturbing values after t leaves features at t unchanged"
    return df
