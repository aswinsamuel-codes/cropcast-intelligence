"""
Independent verification of the anomaly study (Phase 9).

From the saved `anomaly_scores.csv` and the frozen dataset, using explicit loops written separately
from `src.anomaly_detection.scoring`, this recomputes:
  - the rolling residual z-score (prior 30 values only),
  - the weekday-adjusted robust score,
  - causal standardisation and the composite,
  - burn-in positions, detections at every sensitivity threshold, and
  - weak-label precision, recall and F1 against the ICTD windows.
`--full` also recomputes the SARIMA residuals with the production code and compares them.

Usage:
    python -m src.reporting.verify_anomaly [--full]
"""

from __future__ import annotations

import argparse
import json
import sys

import numpy as np
import pandas as pd

from src.config import load_config, resolve_path
from src.data.dataset import load_dataset

TOL = 1e-6


def z_prior(e: np.ndarray, w: int) -> np.ndarray:
    out = np.full(len(e), np.nan)
    for t in range(w, len(e)):
        win = e[t - w:t]
        if np.isnan(win).any() or np.isnan(e[t]):
            continue
        out[t] = (e[t] - win.mean()) / win.std(ddof=1)
    return out


def robust(logy: np.ndarray, wd: np.ndarray, lw: int, wh: int, sw: int) -> np.ndarray:
    n = len(logy)
    d = np.full(n, np.nan)
    for t in range(lw, n):
        d[t] = logy[t] - np.median(logy[t - lw:t])
    w = np.full(n, np.nan)
    for t in range(n):
        prev = [d[s] for s in range(t) if wd[s] == wd[t]][-wh:]
        # Mirrors pandas rolling(min_periods=wh//2): NaNs in the window are skipped, valid count >= wh//2
        vals = [v for v in prev if not np.isnan(v)]
        if len(prev) >= 1 and len(vals) >= wh // 2:
            w[t] = np.median(vals)
    a = d - w
    out = np.full(n, np.nan)
    for t in range(sw, n):
        win = a[t - sw:t]
        if np.isnan(win).any() or np.isnan(a[t]):
            continue
        mad = np.median(np.abs(win - np.median(win)))
        out[t] = a[t] / (1.4826 * mad)
    return out


def standardize(s: np.ndarray, mp: int) -> np.ndarray:
    out = np.full(len(s), np.nan)
    for t in range(len(s)):
        prior = s[:t][~np.isnan(s[:t])]
        if len(prior) >= mp and not np.isnan(s[t]):
            out[t] = (s[t] - prior.mean()) / prior.std(ddof=1)
    return out


def close(a, b) -> bool:
    a, b = np.asarray(a, float), np.asarray(b, float)
    return bool(np.array_equal(np.isnan(a), np.isnan(b)) and np.allclose(a[~np.isnan(a)], b[~np.isnan(b)], rtol=TOL, atol=TOL))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args()
    cfg = load_config()
    a = cfg["anomaly"]
    tables = resolve_path(cfg["paths"]["tables_dir"])
    scores = pd.read_csv(tables / "anomaly_scores.csv", parse_dates=["date"])
    sens = pd.read_csv(tables / "anomaly_threshold_sensitivity.csv")
    weak = pd.read_csv(tables / "anomaly_weak_label_agreement.csv")
    df = load_dataset(cfg)
    problems, checks = [], 0
    for sid, g in df.groupby("series_id"):
        g = g.sort_values("date").reset_index(drop=True)
        s = scores[scores["series_id"] == sid].reset_index(drop=True)
        if not (s["date"].equals(g["date"]) and np.array_equal(s["modal_price"], g["modal_price"])):
            problems.append(f"{sid}: score rows are not aligned with the dataset")
            continue
        logy = np.log(g["modal_price"].to_numpy())
        wd = g["date"].dt.day_of_week.to_numpy()
        e = s["raw_residual"].to_numpy()
        burn = a["residual_burn_in_market_days"]
        if not (np.isnan(e[:burn + 1]).all() and np.isfinite(e[burn + 1:]).all()):
            problems.append(f"{sid}: residuals do not start exactly after the burn-in of {burn} origins")
        z = z_prior(e, a["zscore_window"])
        rb = robust(logy, wd, a["robust"]["level_window"], a["robust"]["weekday_history"], a["robust"]["scale_window"])
        mp = a["standardize_min_periods"]
        zr, zb = standardize(z, mp), standardize(rb, mp)
        comp = standardize(a["weights"]["residual"] * zr + a["weights"]["robust"] * zb, mp)
        for name, mine, saved in (("raw_residual_z", z, s["raw_residual_z"]), ("raw_robust", rb, s["raw_robust"]),
                                  ("residual", zr, s["residual"]), ("robust", zb, s["robust"]), ("composite", comp, s["composite"])):
            checks += 1
            if not close(mine, saved):
                problems.append(f"{sid}: {name} differs from independent recomputation")
        scored = ~(np.isnan(zr) | np.isnan(zb) | np.isnan(comp))
        if not np.array_equal(scored, s["scored"].to_numpy()):
            problems.append(f"{sid}: scored-day mask differs")
        for k in a["threshold_sensitivity"]:
            for m, arr in (("residual", zr), ("robust", zb), ("composite", comp)):
                checks += 1
                n_det = int((np.abs(arr[scored]) > k).sum())
                rep = sens[(sens.series_id == sid) & (sens.method == m) & np.isclose(sens.threshold, k)]
                if rep.empty or int(rep["detections"].iloc[0]) != n_det:
                    problems.append(f"{sid}/{m}/k={k}: detections {n_det} != reported")
        # Weak labels, recomputed independently from the ICTD file
        spec = cfg["dataset"]["series"][sid]
        lab = pd.read_csv(resolve_path(cfg["paths"]["ictd_labels"][sid]), encoding="utf-8-sig")
        lab = lab[lab["STATENAME"] == spec["ictd_state"]]
        end = pd.Timestamp(lab["ENDDATE"].max())
        pos = lab[(lab[a["weak_labels"]["label_columns"]] == a["weak_labels"]["positive_value"]).any(axis=1)]
        label = np.zeros(len(g), bool)
        for _, r in pos.iterrows():
            label |= ((g["date"] >= pd.Timestamp(r["STARTDATE"])) & (g["date"] <= pd.Timestamp(r["ENDDATE"]))).to_numpy()
        ev = scored & (g["date"] <= end).to_numpy()
        for m, arr in (("residual", zr), ("robust", zb), ("composite", comp)):
            checks += 1
            pred = np.abs(arr[ev]) > a["threshold"]
            t = label[ev]
            tp, fp, fn = int((t & pred).sum()), int((~t & pred).sum()), int((t & ~pred).sum())
            prec = tp / (tp + fp) if tp + fp else np.nan
            rec = tp / (tp + fn) if tp + fn else np.nan
            f1 = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else np.nan
            row = weak[(weak.series_id == sid) & (weak.method == m)].iloc[0]
            if (int(row.tp), int(row.fp), int(row.fn)) != (tp, fp, fn) or not close([prec, rec, f1], [row.precision, row.recall, row.f1]):
                problems.append(f"{sid}/{m}: weak-label metrics differ")
            if not np.isclose(row.label_base_rate, t.mean()):
                problems.append(f"{sid}/{m}: base rate differs")
        if args.full:
            from src.anomaly_detection.run import AnomalyRunner, sarima_residuals
            from src.features.build import build_features
            from src.forecasting.models import SeriesData
            runner = AnomalyRunner(cfg)
            data = SeriesData(build_features(g))
            r = sarima_residuals(data, runner.best_order(sid), list(range(burn, len(g) - 1)), a["residual_refit_every"])
            checks += 1
            if not close(r.reindex(range(len(g))).to_numpy(), e):
                problems.append(f"{sid}: recomputed SARIMA residuals differ")
    print(json.dumps({"checks": checks, "full": args.full, "problems": problems}, indent=2))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
