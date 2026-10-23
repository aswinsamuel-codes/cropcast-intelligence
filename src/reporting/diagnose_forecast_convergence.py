"""
Diagnostic for SARIMA convergence in the forecasting experiment (run B).

Replays the exact SARIMA fit sequence of `src.forecasting.run`:
  - the training-set AIC grid (one fit per order),
  - validation walk-forward (refit every `validation_refit_every`) for the top-k AIC orders,
  - test walk-forward (refit every step) for the selected order,
and records convergence for every fit. For each non-converged *test* fit it refits from a cold start
and recomputes that step's forecast, then reports the effect on SARIMA's test MAE and on its
Diebold-Mariano comparison with naive. Saved results are never modified.

Usage:
    python -m src.reporting.diagnose_forecast_convergence
"""

from __future__ import annotations

import json
import warnings

import numpy as np
import pandas as pd

from src.config import load_config, resolve_path
from src.data.dataset import load_dataset
from src.evaluation.metrics import diebold_mariano, mae
from src.features.build import build_features
from src.forecasting.models import SarimaModel, SeriesData, split_origins
from src.forecasting.run import grid


def fit_logged(model: SarimaModel, t: int) -> dict:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        model.fit(t)
    r = model.res.mle_retvals or {}
    return {"converged": bool(r.get("converged", False)), "iterations": r.get("iterations"),
            "warnflag": r.get("warnflag"), "llf": float(model.res.llf),
            "estimation_warnings": sum(1 for w in caught if w.category.__name__ == "EstimationWarning")}


def main() -> int:
    cfg = load_config()
    fc, ms = cfg["forecasting"], cfg["forecasting"]["models"]["sarima"]
    tables = resolve_path(cfg["paths"]["tables_dir"])
    sel = pd.read_csv(tables / "forecast_test_selection.csv")
    val = pd.read_csv(tables / "forecast_validation_results.csv")
    fdir = resolve_path(cfg["paths"]["forecasts_dir"])
    df = load_dataset(cfg)
    rows, impact = [], {}
    for sid, g in df.groupby("series_id"):
        data = SeriesData(build_features(g))
        sp = split_origins(len(data.y), fc["split"]["train"], fc["split"]["validation"])
        orders = lambda p: ((p["p"], ms["d"], p["q"]), (p["P"], 0, p["Q"], ms["seasonal_period"]))
        for p in grid(ms["grid"]):  # AIC grid: one fresh fit each
            o, so = orders(p)
            rows.append({"series_id": sid, "stage": "aic_grid", "order": f"{o}{so}", "origin": sp["train_end"] - 1,
                         **fit_logged(SarimaModel(data, o, so, maxiter=ms["maxiter"]), sp["train_end"] - 1)})
        for _, r in val[(val.series_id == sid) & (val.family == "sarima")].iterrows():
            p = json.loads(r["params"])
            o, so = orders(p)
            m = SarimaModel(data, o, so, maxiter=ms["maxiter"])
            for i, t in enumerate(sp["validation"]):
                if i % fc["validation_refit_every"] == 0:
                    rows.append({"series_id": sid, "stage": "validation", "order": f"{o}{so}", "origin": t, **fit_logged(m, t)})
        p = json.loads(sel[(sel.series_id == sid) & (sel.model == "sarima")]["selected_params"].iloc[0])
        o, so = orders(p)
        m = SarimaModel(data, o, so, maxiter=ms["maxiter"])
        f = pd.read_csv(fdir / f"test_{sid}.csv")
        alt = f["sarima"].to_numpy().copy()
        replay = []
        for i, t in enumerate(sp["test"]):
            info = fit_logged(m, t)
            fc_warm = m.forecast(t)
            replay.append(fc_warm)
            rows.append({"series_id": sid, "stage": "test", "order": f"{o}{so}", "origin": t, **info})
            if not info["converged"]:
                cold = SarimaModel(data, o, so, maxiter=2000)
                cinfo = fit_logged(cold, t)
                if cinfo["converged"]:
                    alt[i] = cold.forecast(t)
        replay = np.array(replay)
        e_naive = f["naive"] - f["actual"]
        dm_orig = diebold_mariano(f["sarima"] - f["actual"], e_naive)
        dm_alt = diebold_mariano(alt - f["actual"], e_naive)
        n_test_nc = sum(1 for r in rows if r["series_id"] == sid and r["stage"] == "test" and not r["converged"])
        impact[sid] = {"selected_order": f"{o}{so}", "test_fits": len(sp["test"]), "test_non_converged": n_test_nc,
                       "replay_equals_saved_forecasts": bool(np.array_equal(replay, f["sarima"].to_numpy())),
                       "test_mae_saved": mae(f["actual"], f["sarima"]), "test_mae_cold_substituted": mae(f["actual"], alt),
                       "max_abs_forecast_change": float(np.max(np.abs(alt - f["sarima"].to_numpy()))),
                       "dm_stat_saved": dm_orig["dm_stat"], "dm_stat_cold_substituted": dm_alt["dm_stat"],
                       "p_value_saved": dm_orig["p_value"], "p_value_cold_substituted": dm_alt["p_value"]}
    fits = pd.DataFrame(rows)
    fits.to_csv(tables / "forecast_sarima_convergence.csv", index=False)
    with open(tables / "forecast_sarima_convergence_impact.json", "w", encoding="utf-8") as fh:
        json.dump(impact, fh, indent=2, default=str)
    print(fits.groupby(["series_id", "stage"]).agg(fits=("converged", "size"),
                                                   non_converged=("converged", lambda s: int((~s).sum())),
                                                   estimation_warnings=("estimation_warnings", "sum")).to_string())
    print("total non-converged:", int((~fits.converged).sum()))
    print(json.dumps(impact, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
