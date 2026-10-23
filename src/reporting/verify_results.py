"""
Independent verification of reported forecasting results (Phase 9).

Recomputes MAE, RMSE, MAPE, MASE and Diebold-Mariano/HLN statistics, plus the BH adjustment,
directly from the saved prediction files and the frozen dataset, then compares them with
`reports/tables/forecast_test_metrics.csv`. Also checks that the test predictions cover exactly
the protocol's test targets and that actual values equal the dataset values.

Usage:
    python -m src.reporting.verify_results
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

from src.config import load_config, resolve_path
from src.data.dataset import load_dataset
from src.forecasting.models import split_origins

TOL = 1e-6


def dm_hln(e_model: np.ndarray, e_base: np.ndarray) -> tuple[float, float]:
    """Written separately from src.evaluation.metrics so the check is independent (h = 1, absolute loss)."""
    d = np.abs(e_model) - np.abs(e_base)
    n = len(d)
    var = np.mean((d - d.mean()) ** 2) / n
    stat = d.mean() / np.sqrt(var) * np.sqrt((n - 1) / n)
    return stat, 2 * stats.t.sf(abs(stat), n - 1)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics", help="metrics CSV (default: tables_dir/forecast_test_metrics.csv)")
    parser.add_argument("--forecasts-dir", help="directory of test_<series>.csv (default: forecasts_dir)")
    args = parser.parse_args(argv)
    cfg = load_config()
    tables = resolve_path(cfg["paths"]["tables_dir"])
    fdir = Path(args.forecasts_dir) if args.forecasts_dir else resolve_path(cfg["paths"]["forecasts_dir"])
    reported = pd.read_csv(args.metrics or tables / "forecast_test_metrics.csv")
    df = load_dataset(cfg)
    split = cfg["forecasting"]["split"]
    problems, rows = [], []
    pvals = {}
    for sid, g in df.groupby("series_id"):
        g = g.sort_values("date").reset_index(drop=True)
        n = len(g)
        sp = split_origins(n, split["train"], split["validation"])
        f = pd.read_csv(fdir / f"test_{sid}.csv", parse_dates=["origin_date", "target_date"])
        expected_targets = g["date"].iloc[[t + 1 for t in sp["test"]]].reset_index(drop=True)
        if not f["target_date"].reset_index(drop=True).equals(expected_targets):
            problems.append(f"{sid}: test target dates differ from the protocol split")
        actual_ds = g.set_index("date").loc[f["target_date"], "modal_price"].to_numpy()
        if not np.array_equal(actual_ds, f["actual"].to_numpy()):
            problems.append(f"{sid}: saved actuals differ from dataset values")
        if (f["target_date"] <= f["origin_date"]).any():
            problems.append(f"{sid}: a target date is not after its origin")
        y = g["modal_price"].to_numpy()
        a_end = sp["train_end"]
        insample = np.mean(np.abs(y[1:a_end] - y[:a_end - 1]))
        models = [c for c in f.columns if c not in ("origin_index", "origin_date", "target_date", "y_origin", "actual")]
        for m in models:
            e = f["actual"].to_numpy() - f[m].to_numpy()
            if not np.isfinite(f[m]).all():
                problems.append(f"{sid}/{m}: non-finite forecasts")
            rec = {"series_id": sid, "model": m, "mae": np.mean(np.abs(e)), "rmse": np.sqrt(np.mean(e ** 2)),
                   "mape_pct": 100 * np.mean(np.abs(e) / f["actual"]), "mase": np.mean(np.abs(e)) / insample}
            if m != "naive":
                stat, p = dm_hln(e, f["actual"].to_numpy() - f["naive"].to_numpy())
                rec["dm_stat"], rec["p_value"] = stat, p
                pvals[(sid, m)] = p
            rows.append(rec)
    mine = pd.DataFrame(rows)
    keys = list(pvals)
    _, p_bh, *_ = multipletests([pvals[k] for k in keys], method="fdr_bh")
    mine["p_bh"] = [dict(zip(keys, p_bh)).get((r.series_id, r.model), np.nan) for r in mine.itertuples()]
    merged = reported.merge(mine, on=["series_id", "model"], suffixes=("_reported", "_recomputed"))
    if len(merged) != len(reported) or len(merged) != len(mine):
        problems.append("model sets differ between the report table and the saved predictions")
    for col in ("mae", "rmse", "mape_pct", "mase", "dm_stat", "p_value", "p_bh"):
        a, b = merged[f"{col}_reported"].to_numpy(float), merged[f"{col}_recomputed"].to_numpy(float)
        both_nan = np.isnan(a) & np.isnan(b)
        bad = ~both_nan & ~np.isclose(a, b, rtol=TOL, atol=TOL)
        if bad.any():
            problems.append(f"{col}: {int(bad.sum())} mismatches")
    summary = {"rows_checked": int(len(merged)), "columns_checked": 7, "problems": problems}
    print(json.dumps(summary, indent=2))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
