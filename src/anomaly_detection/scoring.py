"""
Anomaly scoring functions (Req 6). Every rolling statistic uses only observations
strictly before the scored day, so a score at t never depends on data after t.
"""

from __future__ import annotations

from typing import Dict, Iterable, List

import numpy as np
import pandas as pd

MAD_SCALE = 1.4826  # makes the MAD a consistent estimator of the SD under normality


def _check(x: pd.Series, name: str) -> None:
    if x is None or len(x) == 0:
        raise ValueError(f"{name} received an empty series")


def residuals(actual: pd.Series, forecast: pd.Series, log: bool = True) -> pd.Series:
    """Req 6.1: actual minus forecast; on the log scale by default (scale-free)."""
    _check(actual, "residuals")
    if len(actual) != len(forecast):
        raise ValueError("actual and forecast must have equal length")
    return np.log(actual) - np.log(forecast) if log else actual - forecast


def rolling_zscore(e: pd.Series, window: int = 30, min_periods: int | None = None) -> pd.Series:
    """
    Req 6.2: z_t = (e_t - mean(e_{t-window..t-1})) / sd(e_{t-window..t-1}).
    The current value is excluded from its own reference window.
    """
    _check(e, "rolling_zscore")
    prior = e.shift(1).rolling(window=window, min_periods=min_periods or window)
    return (e - prior.mean()) / prior.std(ddof=1)


def robust_weekday_score(logy: pd.Series, weekday: pd.Series, level_window: int = 28,
                         weekday_history: int = 52, scale_window: int = 56) -> pd.Series:
    """
    Market-relative robust score (DEC-017 substitute for the peer-divergence signal):
      d_t = log y_t - median(log y over the previous `level_window` market days)
      w_t = median of d_s over the previous `weekday_history` days with the same weekday (s < t)
      a_t = d_t - w_t
      score_t = a_t / (1.4826 * MAD(a over the previous `scale_window` market days))
    """
    _check(logy, "robust_weekday_score")
    logy = logy.reset_index(drop=True)
    weekday = pd.Series(np.asarray(weekday), index=logy.index)
    d = logy - logy.shift(1).rolling(level_window, min_periods=level_window).median()
    w = pd.Series(np.nan, index=logy.index)
    for day in range(7):
        idx = weekday.index[weekday == day]
        w.loc[idx] = d.loc[idx].shift(1).rolling(weekday_history, min_periods=weekday_history // 2).median()
    a = d - w
    prior = a.shift(1).rolling(scale_window, min_periods=scale_window)
    mad = prior.apply(lambda v: np.median(np.abs(v - np.median(v))), raw=True)
    return a / (MAD_SCALE * mad)


def causal_standardize(s: pd.Series, min_periods: int = 180) -> pd.Series:
    """Standardise with the expanding mean and SD of strictly earlier values (no future data)."""
    _check(s, "causal_standardize")
    prior = s.shift(1).expanding(min_periods=min_periods)
    return (s - prior.mean()) / prior.std(ddof=1)


def composite_score(signals: Dict[str, pd.Series], weights: Dict[str, float], min_periods: int = 180) -> pd.Series:
    """Req 6.4: weighted sum of causally standardised signals. Weights must be non-negative and sum to 1."""
    if not signals:
        raise ValueError("composite_score needs at least one signal")
    if any(w < 0 for w in weights.values()) or not np.isclose(sum(weights.values()), 1.0):
        raise ValueError("weights must be non-negative and sum to 1")
    total = None
    for name, s in signals.items():
        part = weights[name] * causal_standardize(s, min_periods)
        total = part if total is None else total + part
    return total


def inject_shocks(y: pd.Series, positions: Iterable[int], magnitude: float) -> pd.Series:
    """
    Req 6.7: multiply y at the given integer positions by (1 + magnitude). A negative
    magnitude gives a drop. Returns a copy; the input is not modified.
    """
    _check(y, "inject_shocks")
    if magnitude <= -1:
        raise ValueError("magnitude must be > -1 so prices stay positive")
    out = y.copy()
    pos = list(positions)
    if any(p < 0 or p >= len(y) for p in pos):
        raise ValueError("shock position out of range")
    out.iloc[pos] = out.iloc[pos] * (1.0 + magnitude)
    return out


def spaced_positions(lo: int, hi: int, count: int, min_gap: int, rng: np.random.Generator) -> List[int]:
    """Random positions in [lo, hi) at least `min_gap` apart, so injected shocks do not overlap windows."""
    free = (hi - lo) - (count - 1) * min_gap
    if count < 1 or free < count:
        raise ValueError("range too short for the requested number of spaced positions")
    # Draw distinct offsets in the compressed range, then add k * min_gap to the k-th smallest
    picks = np.sort(rng.choice(free, size=count, replace=False))
    return [int(lo + p + k * min_gap) for k, p in enumerate(picks)]
