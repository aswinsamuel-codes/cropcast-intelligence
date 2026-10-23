"""
Diagnostic for SARIMA maximum-likelihood convergence in the anomaly study (Phase 1 verification).

Replays the exact refit schedule of `src.anomaly_detection.run.sarima_residuals`: the same origins,
the same warm-start chaining and the same `maxiter`. For every refit it records convergence,
iterations, the log-likelihood and any warnings. For each non-converged fit it refits the same data
from a cold start (falling back to a warm start with a larger iteration budget) (diagnostic only) and measures the effect on residuals, scores and
detections in the segment that fit governs. Saved results are never modified.

Usage:
    python -m src.reporting.diagnose_sarima_convergence
"""

from __future__ import annotations

import json
import warnings
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from src.anomaly_detection.run import AnomalyRunner, scores_for
from src.config import load_config, resolve_path
from src.data.dataset import load_dataset
from src.features.build import build_features
from src.forecasting.models import SarimaModel, SeriesData, split_origins

DIAGNOSTIC_MAXITER = 2000


def _fit(model: SarimaModel, t: int) -> Dict[str, Any]:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        model.fit(t)
    r = model.res.mle_retvals or {}
    return {"converged": bool(r.get("converged", False)), "iterations": r.get("iterations"),
            "llf": float(model.res.llf), "warnings": sorted({f"{w.category.__name__}: {str(w.message)[:80]}" for w in caught})}


def _segment_residuals(data: SeriesData, order: pd.Series, fit_at: int, origins: List[int], params) -> Dict[int, float]:
    """One-step log residuals for `origins` from a model with fixed `params`, fitted at `fit_at` and then advanced."""
    m = SarimaModel(data, (int(order.p), 1, int(order.q)), (int(order.P), 0, int(order.Q), 7))
    m.res = m._model(data.logy[:fit_at + 1]).filter(params)
    m.n_seen = fit_at + 1
    out = {}
    for t in origins:
        m.update(t)
        out[t + 1] = data.logy[t + 1] - np.log(m.forecast(t))
    return out


def main() -> int:
    cfg = load_config()
    a = cfg["anomaly"]
    runner = AnomalyRunner(cfg)
    df = load_dataset(cfg)
    tables = resolve_path(cfg["paths"]["tables_dir"])
    saved = pd.read_csv(tables / "anomaly_scores.csv", parse_dates=["date"])
    rows, impacts = [], []
    for sid, g in df.groupby("series_id"):
        g = g.sort_values("date").reset_index(drop=True)
        data = SeriesData(build_features(g))
        order = runner.best_order(sid)
        n, burn, every = len(g), a["residual_burn_in_market_days"], a["residual_refit_every"]
        origins = list(range(burn, n - 1))
        model = SarimaModel(data, (int(order.p), 1, int(order.q)), (int(order.P), 0, int(order.Q), 7))
        sp = split_origins(n, cfg["forecasting"]["split"]["train"], cfg["forecasting"]["split"]["validation"])
        seg_start = sp["test"][0] + 1
        fit_positions = [t for i, t in enumerate(origins) if i % every == 0]
        for t in fit_positions:
            start = model.start_params
            info = _fit(model, t)
            period = "train" if t + 1 < sp["train_end"] else ("validation" if t + 1 < seg_start else "test")
            rows.append({"series_id": sid, "context": "residual walk-forward", "fit_origin": t,
                         "fit_origin_date": str(g.at[t, "date"].date()), "period_of_governed_targets": period, **info,
                         "warnings": "; ".join(info["warnings"])})
            if not info["converged"]:
                diag = SarimaModel(data, model.order, model.seasonal_order, maxiter=DIAGNOSTIC_MAXITER)
                diag.start_params = start
                dinfo = _fit(diag, t)
                # Same data from statsmodels' default (cold) start values: an independent optimum to compare with
                cold = SarimaModel(data, model.order, model.seasonal_order, maxiter=DIAGNOSTIC_MAXITER)
                cinfo = _fit(cold, t)
                if cinfo["converged"]:
                    diag, dinfo = cold, dict(cinfo, start="cold")
                else:
                    dinfo = dict(dinfo, start="warm, larger maxiter")
                seg = [o for o in origins if t <= o < t + every]
                r_orig = _segment_residuals(data, order, t, seg, model.res.params)
                r_diag = _segment_residuals(data, order, t, seg, diag.res.params)
                saved_s = saved[saved.series_id == sid].reset_index(drop=True)
                diff = max(abs(r_orig[k] - r_diag[k]) for k in r_orig)
                replay_vs_saved = max(abs(r_orig[k] - saved_s.at[k, "raw_residual"]) for k in r_orig)
                # Score impact: substitute diagnostic residuals in the segment and recompute scores
                resid_full = pd.Series(saved_s["raw_residual"].to_numpy())
                alt = resid_full.copy()
                for k, v in r_diag.items():
                    alt.iloc[k] = v
                logy = pd.Series(np.log(g["modal_price"].to_numpy()))
                wd = g["date"].dt.day_of_week
                sc_o = scores_for(logy, wd, resid_full.dropna(), a)
                sc_d = scores_for(logy, wd, alt.dropna(), a)
                det_changes = {m: int(((sc_o[m].abs() > a["threshold"]) != (sc_d[m].abs() > a["threshold"])).sum())
                               for m in ("residual", "robust", "composite")}
                impacts.append({"series_id": sid, "fit_origin": t, "fit_origin_date": str(g.at[t, "date"].date()),
                                "segment_targets": f"{g.at[seg[0] + 1, 'date'].date()}..{g.at[seg[-1] + 1, 'date'].date()}",
                                "period": period, "original_iterations": info["iterations"], "original_llf": info["llf"],
                                "original_warnflag": model.res.mle_retvals.get("warnflag"), "diagnostic_start": dinfo["start"],
                                "diagnostic_converged": dinfo["converged"], "diagnostic_iterations": dinfo["iterations"],
                                "diagnostic_llf": dinfo["llf"], "llf_original_minus_diagnostic": info["llf"] - dinfo["llf"],
                                "max_abs_param_change": float(np.max(np.abs(model.res.params - diag.res.params))),
                                "max_abs_residual_change": float(diff),
                                "replay_matches_saved_residuals": bool(replay_vs_saved < 1e-9),
                                "detection_changes_at_threshold_all_days": det_changes})
        # Shock evaluation: one frozen fit at seg_start - 1 without warm start (identical clean data in every run)
        shock_model = SarimaModel(data, model.order, model.seasonal_order)
        info = _fit(shock_model, seg_start - 1)
        rows.append({"series_id": sid, "context": "shock evaluation (frozen fit, all 40 runs)", "fit_origin": seg_start - 1,
                     "fit_origin_date": str(g.at[seg_start - 1, "date"].date()), "period_of_governed_targets": "test",
                     **info, "warnings": "; ".join(info["warnings"])})
    fits = pd.DataFrame(rows)
    fits.to_csv(tables / "anomaly_sarima_convergence.csv", index=False)
    with open(tables / "anomaly_sarima_convergence_impact.json", "w", encoding="utf-8") as f:
        json.dump(impacts, f, indent=2, default=str)
    summary = fits.groupby(["series_id", "context"]).agg(fits=("converged", "size"),
                                                         non_converged=("converged", lambda s: int((~s).sum())))
    print(summary.to_string())
    print(json.dumps(impacts, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
