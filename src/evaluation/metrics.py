"""
Forecast and detection metrics (Req 5.7, 6.6, 8.5).
"""

from __future__ import annotations

from typing import Dict, Tuple

import numpy as np
from scipy import stats


def _arrays(actual, forecast) -> Tuple[np.ndarray, np.ndarray]:
    a = np.asarray(actual, dtype=float)
    f = np.asarray(forecast, dtype=float)
    if a.size == 0:
        raise ValueError("metric received empty input")
    if a.shape != f.shape:
        raise ValueError(f"shape mismatch: {a.shape} vs {f.shape}")
    return a, f


def mae(actual, forecast) -> float:
    a, f = _arrays(actual, forecast)
    return float(np.mean(np.abs(a - f)))


def rmse(actual, forecast) -> float:
    a, f = _arrays(actual, forecast)
    return float(np.sqrt(np.mean((a - f) ** 2)))


def mape(actual, forecast, near_zero: float = 1e-6) -> Tuple[float, str]:
    """MAPE in percent, with a note when any actual value is zero or near zero (Req 5.7)."""
    a, f = _arrays(actual, forecast)
    small = np.abs(a) <= near_zero
    note = (f"{int(small.sum())} actual values are zero or near zero; MAPE excludes them and is unreliable"
            if small.any() else f"no zero or near-zero actual values (min |actual| = {np.abs(a).min():.6g})")
    ok = ~small
    return float(100 * np.mean(np.abs((a[ok] - f[ok]) / a[ok]))), note


def mase(actual, forecast, insample_naive_mae: float) -> float:
    """Mean absolute scaled error (Hyndman & Koehler, 2006), scaled by the in-sample naive MAE."""
    if insample_naive_mae <= 0:
        raise ValueError("insample_naive_mae must be positive")
    return mae(actual, forecast) / insample_naive_mae


def diebold_mariano(e_model, e_baseline, h: int = 1, loss: str = "absolute") -> Dict[str, float]:
    """
    Diebold-Mariano test of equal predictive accuracy with the Harvey-Leybourne-Newbold
    small-sample correction, two-sided, Student-t with n-1 df. d = L(e_model) - L(e_baseline),
    so a negative statistic means the model has lower loss.
    """
    e1, e2 = _arrays(e_model, e_baseline)
    if loss == "absolute":
        d = np.abs(e1) - np.abs(e2)
    elif loss == "squared":
        d = e1 ** 2 - e2 ** 2
    else:
        raise ValueError(f"unknown loss {loss!r}")
    n = d.size
    if n < 3:
        raise ValueError("diebold_mariano needs at least 3 observations")
    dbar = d.mean()
    gamma = [np.mean((d[k:] - dbar) * (d[:n - k] - dbar)) for k in range(h)]
    var = (gamma[0] + 2 * sum(gamma[1:])) / n
    if var <= 0:
        return {"dm_stat": float("nan"), "p_value": float("nan"), "mean_loss_diff": float(dbar), "n": n}
    dm = dbar / np.sqrt(var)
    hln = np.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    stat = hln * dm
    p = 2 * stats.t.sf(abs(stat), df=n - 1)
    return {"dm_stat": float(stat), "p_value": float(p), "mean_loss_diff": float(dbar), "n": n}


def precision_recall_f1(y_true, y_pred) -> Dict[str, float]:
    """Precision, recall and F1 for binary labels. Undefined ratios are returned as NaN."""
    t = np.asarray(y_true, dtype=bool)
    p = np.asarray(y_pred, dtype=bool)
    if t.size == 0:
        raise ValueError("precision_recall_f1 received empty input")
    if t.shape != p.shape:
        raise ValueError("shape mismatch")
    tp = int((t & p).sum())
    fp = int((~t & p).sum())
    fn = int((t & ~p).sum())
    precision = tp / (tp + fp) if tp + fp else float("nan")
    recall = tp / (tp + fn) if tp + fn else float("nan")
    f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else float("nan")
    return {"precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": fp, "fn": fn}
