"""
Compare two runs' artifacts under the predefined reproducibility rules (docs/reproducibility.md §2-§3).

Forecasting, run A (retrospective) vs run B:
  - test predictions: exact equality for every model except random_forest; random_forest within
    relative 1e-12 (ISS-012: run A used parallel prediction). Actual maxima are reported.
  - SARIMA AIC table, selected configurations, verdicts: exact.
  - metrics: exact except random_forest rows (relative 1e-12).
Anomaly, run 1 vs run 2: every table exactly equal (no random-forest component).

Usage:
    python -m src.reporting.compare_runs --forecast-a <dir> --forecast-b <dir> [--anomaly-1 <dir> --anomaly-2 <dir>]
Each directory contains the run's artifacts (forecasts/, tables/) as copied into reports/runs/<run>/artifacts.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RF_RTOL = 1e-12
NON_MODEL = {"origin_index", "origin_date", "target_date", "y_origin", "actual"}


def rel_diff(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    return float(np.max(np.abs(a - b) / np.maximum(np.abs(b), 1e-300))) if a.size else 0.0


def compare_forecasts(a: Path, b: Path) -> dict:
    out = {"problems": [], "predictions": {}, "metrics": {}}
    for fa in sorted((a / "forecasts").glob("test_*.csv")):
        sid = fa.stem[5:]
        A, B = pd.read_csv(fa), pd.read_csv(b / "forecasts" / fa.name)
        for col in NON_MODEL:
            if not A[col].equals(B[col]):
                out["problems"].append(f"{sid}: column {col} differs")
        for m in [c for c in A.columns if c not in NON_MODEL]:
            exact = bool((A[m].to_numpy() == B[m].to_numpy()).all())
            rd = rel_diff(B[m], A[m])
            out["predictions"][f"{sid}/{m}"] = {"exact": exact, "max_rel_diff": rd}
            if m == "random_forest":
                if rd > RF_RTOL:
                    out["problems"].append(f"{sid}/{m}: max relative difference {rd:.3e} > {RF_RTOL}")
            elif not exact:
                out["problems"].append(f"{sid}/{m}: predictions not exactly equal (max rel diff {rd:.3e})")
    ta, tb = a / "tables", b / "tables"
    # Run A's tables were written at 6 significant digits (ISS-013). For those, the rule is exact:
    # run B rounded to 6 significant digits must equal run A.
    legacy = (ta / "forecast_test_metrics_full_precision.csv").exists()
    sig6 = lambda v: float(f"{v:.6g}")
    for name, keys, numeric, rf_rows in (
            ("forecast_sarima_aic.csv", ["series_id", "p", "q", "P", "Q"], ["aic", "ljung_box_p_lag14"], False),
            ("forecast_validation_results.csv", ["series_id", "family", "params"], ["val_mae", "val_rmse"], True)):
        A, B = pd.read_csv(ta / name), pd.read_csv(tb / name)
        m = A.merge(B, on=keys, suffixes=("_A", "_B"), validate="one_to_one")
        if len(m) != len(A) or len(m) != len(B):
            out["problems"].append(f"{name}: row sets differ")
            continue
        if "config_hash_A" in m and not (m["config_hash_A"] == m["config_hash_B"]).all():
            out["problems"].append(f"{name}: config hashes differ")
        for c in numeric:
            b = m[c + "_B"].map(sig6) if legacy else m[c + "_B"]
            diff = m[c + "_A"] != b
            if rf_rows:  # random-forest validation MAEs may differ in the last ulp (ISS-012)
                rf = m["family"] == "random_forest"
                rd = ((m[c + "_A"] - m[c + "_B"]).abs() / m[c + "_B"].abs())
                diff = (diff & ~rf) | (rf & (rd > (5e-6 if legacy else RF_RTOL)))
            out.setdefault("tables", {})[f"{name}/{c}"] = "equal" if not diff.any() else f"{int(diff.sum())} differ"
            if diff.any():
                out["problems"].append(f"{name}/{c}: {int(diff.sum())} rows differ")
    ma = pd.read_csv(ta / "forecast_test_metrics_full_precision.csv" if (ta / "forecast_test_metrics_full_precision.csv").exists()
                     else ta / "forecast_test_metrics.csv").set_index(["series_id", "model"]).sort_index()
    mb = pd.read_csv(tb / "forecast_test_metrics.csv").set_index(["series_id", "model"]).sort_index()
    if not ma.index.equals(mb.index):
        out["problems"].append("model sets differ")
        return out
    for col in ("selected_params", "verdict", "config_hash"):
        if not ma[col].equals(mb[col]):
            out["problems"].append(f"{col} differs: {list(ma.index[ma[col] != mb[col]])}")
    for col in ("mae", "rmse", "mape_pct", "mase", "dm_stat", "p_value", "p_bh"):
        for idx in ma.index:
            va, vb = ma.at[idx, col], mb.at[idx, col]
            if pd.isna(va) and pd.isna(vb):
                continue
            rd = abs(va - vb) / max(abs(vb), 1e-300)
            key = f"{idx[0]}/{idx[1]}/{col}"
            out["metrics"][key] = rd
            # DM statistics of every model share the naive baseline; only RF errors differ, and BH p-values
            # are coupled across rows, so p_bh is compared with the RF tolerance everywhere
            tol = RF_RTOL if (idx[1] == "random_forest" or col == "p_bh") else 0.0
            if rd > tol:
                out["problems"].append(f"{key}: relative difference {rd:.3e} > {tol}")
    out["max_metric_rel_diff"] = max(out["metrics"].values()) if out["metrics"] else 0.0
    return out


def compare_anomaly(a: Path, b: Path) -> dict:
    out = {"problems": [], "tables": {}}
    for fa in sorted((a / "tables").glob("anomaly_*.csv")):
        if "convergence" in fa.name:
            continue  # produced by the diagnostic, not by the run
        fb = b / "tables" / fa.name
        if not fb.exists():
            out["problems"].append(f"{fa.name} missing in run 2")
            continue
        A, B = pd.read_csv(fa), pd.read_csv(fb)
        same = A.equals(B)
        out["tables"][fa.name] = same
        if not same:
            out["problems"].append(f"{fa.name} differs")
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--forecast-a")
    p.add_argument("--forecast-b")
    p.add_argument("--anomaly-1")
    p.add_argument("--anomaly-2")
    args = p.parse_args()
    result = {}
    if args.forecast_a and args.forecast_b:
        result["forecasting"] = compare_forecasts(Path(args.forecast_a), Path(args.forecast_b))
    if args.anomaly_1 and args.anomaly_2:
        result["anomaly"] = compare_anomaly(Path(args.anomaly_1), Path(args.anomaly_2))
    print(json.dumps(result, indent=1, default=str))
    return 0 if all(not r["problems"] for r in result.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
