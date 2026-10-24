"""
Export the aggregate results shown on the CropCast results dashboard.

Reads only saved, aggregate outputs: metrics and breakdown tables, anomaly summaries, run
manifests, the run-comparison record, the latest verification record and the dataset metadata.
It never writes daily prices, arrivals or per-day scores: CEDA's terms do not clearly permit
redistributing them (DEC-019, DEC-022). A check at the end refuses to write any file whose rows
contain a date-like column.

Usage:
    python -m src.reporting.export_dashboard_data            # writes reports/dashboard/*.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from src.config import REPO_ROOT, load_config, resolve_path

SERIES = {"onion_maharashtra": "Onion (Maharashtra)", "potato_uttar_pradesh": "Potato (Uttar Pradesh)"}
MODEL = {"naive": "Naive", "seasonal_naive": "Seasonal naive (7)", "linear_regression": "Linear regression",
         "decision_tree": "Decision tree", "random_forest": "Random forest", "sarima": "Seasonal ARIMA",
         "ets": "ETS (Holt–Winters)"}
METHOD = {"residual": "Residual", "robust": "Robust", "composite": "Composite"}
CLASS = {"Sunday/Monday (composition-prone)": "sun_mon", "coverage anomaly (ISS-003 type)": "coverage",
         "min/max band violation (ISS-002 type)": "band", "other": "other"}
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _f(x, nd=6):
    return None if pd.isna(x) else round(float(x), nd)


def build(cfg: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    t = resolve_path(cfg["paths"]["tables_dir"])
    runs_dir = resolve_path(cfg["paths"]["runs_dir"])
    out: Dict[str, List[Dict[str, Any]]] = {}

    m = pd.read_csv(t / "forecast_test_metrics.csv")
    out["forecast_metrics"] = [{
        "series": SERIES[r.series_id], "model": MODEL[r.model], "model_id": r.model, "n": int(r.n),
        "mae": _f(r.mae), "rmse": _f(r.rmse), "mape_pct": _f(r.mape_pct), "mase": _f(r.mase),
        "mae_vs_naive_pct": _f(r.mae_vs_naive_pct), "dm_stat": _f(r.dm_stat), "p_bh": _f(r.p_bh, 12),
        "verdict": r.verdict, "selected_params": r.selected_params,
    } for r in m.itertuples()]

    b = pd.read_csv(t / "forecast_test_breakdown.csv")
    out["forecast_halves"] = [{"series": SERIES[r.series_id], "period": r.level, "model": MODEL[r.model],
                               "n": int(r.n), "mae": _f(r.mae)}
                              for r in b[b.breakdown == "half_year"].itertuples()]
    wd = b[b.breakdown == "target_weekday"].copy()
    wd["order"] = wd["level"].map(WEEKDAYS.index)
    out["forecast_weekday"] = [{"series": SERIES[r.series_id], "weekday": r.level, "weekday_order": int(r.order),
                                "model": MODEL[r.model], "n": int(r.n), "mae": _f(r.mae)}
                               for r in wd.sort_values(["series_id", "order", "model"]).itertuples()]

    sens = pd.read_csv(t / "anomaly_threshold_sensitivity.csv")
    cls = pd.read_csv(t / "anomaly_event_classes.csv").set_index(["series_id", "method"])
    rows = []
    for r in sens[sens.threshold == 3.0].itertuples():
        k = (r.series_id, r.method)
        counts = {v: (int(cls.at[k, c]) if (k in cls.index and c in cls.columns) else 0) for c, v in CLASS.items()}
        if sum(counts.values()) != int(r.detections):
            raise ValueError(f"{k}: class counts do not add up to detections")
        rows.append({"series": SERIES[r.series_id], "method": METHOD[r.method], "scored_days": int(r.scored_days),
                     "detections": int(r.detections), "rate_pct": _f(r.rate_pct, 4), **counts})
    out["anomaly_classes"] = rows
    out["anomaly_sensitivity"] = [{"series": SERIES[r.series_id], "method": METHOD[r.method], "threshold": _f(r.threshold, 2),
                                   "detections": int(r.detections), "rate_pct": _f(r.rate_pct, 4)} for r in sens.itertuples()]

    s = pd.read_csv(t / "anomaly_shock_recall.csv")
    out["anomaly_shocks"] = [{"series": SERIES[r.series_id], "method": METHOD[r.method], "shock_pct": int(round(100 * r.magnitude)),
                              "recall": _f(r.recall, 4), "false_positive_rate_pct": _f(100 * r.fpr, 4)} for r in s.itertuples()]

    w = pd.read_csv(t / "anomaly_weak_label_agreement.csv")
    out["anomaly_weak_labels"] = [{
        "series": SERIES[r.series_id], "method": METHOD[r.method], "days": int(r.evaluated_days),
        "label_rate": _f(r.label_base_rate, 4), "detections": int(r.tp + r.fp), "precision": _f(r.precision, 4),
        "recall": _f(r.recall, 4), "f1": _f(r.f1, 4), "null_precision": _f(r.null_precision_median, 4),
        "randomisation_p": _f(r.randomisation_p_precision, 4),
    } for r in w.itertuples()]

    meta = json.loads((resolve_path(cfg["paths"]["processed_dir"]) / f"cropcast_analysis_{cfg['dataset']['version']}.meta.json")
                      .read_text(encoding="utf-8"))
    eda = json.loads((t / "eda_summary.json").read_text(encoding="utf-8"))
    out["dataset_coverage"] = [{
        "series": SERIES[r["series_id"]], "calendar_days": int(r["calendar_days"]), "observed_days": int(r["observed_days"]),
        "missing_days": int(r["missing_days"]), "missing_pct": _f(r["missing_pct"], 3),
        "gaps": int(eda["coverage"][r["series_id"]]["gaps"]), "max_gap_days": int(eda["coverage"][r["series_id"]]["max_gap_days"]),
        "flag_modal_outside_bounds": int(meta["flag_counts"][r["series_id"]]["flag_modal_outside_bounds"]),
        "flag_extreme_arrival": int(meta["flag_counts"][r["series_id"]]["flag_extreme_arrival"]),
    } for r in meta["missing_report"]]

    runs = []
    for p in sorted(runs_dir.glob("*/manifest.json")):
        mf = json.loads(p.read_text(encoding="utf-8"))
        runs.append({
            "run_id": mf["run_id"], "kind": mf["kind"], "status": mf["status"],
            "started_at": mf.get("started_at"), "ended_at": mf.get("ended_at"),
            "commit": (mf["git"].get("commit") or "")[:7] if not mf.get("retrospective") else "not recorded",
            "clean_tree_at_start": None if mf.get("retrospective") else (not mf["git"].get("dirty")),
            "code_changed_during_run": mf.get("tree_changed_during_run"),
            "retrospective": bool(mf.get("retrospective")), "artifacts": len(mf.get("artifacts", {})),
            "warnings_counted": int(sum(mf.get("warning_counts", {}).values())),
        })
    out["run_records"] = runs

    cmp_ = json.loads((runs_dir / "reproducibility_comparison_A_vs_B.json").read_text(encoding="utf-8"))
    fc = cmp_["forecasting"]
    out["run_comparison"] = [{
        "series": SERIES[k.split("/")[0]], "model": MODEL[k.split("/")[1]], "bit_identical": bool(v["exact"]),
        "max_relative_difference": float(v["max_rel_diff"]),
        "rule": "within 1e-12 relative" if k.endswith("random_forest") else "exactly equal",
        "passes_rule": bool(v["exact"]) or (k.endswith("random_forest") and v["max_rel_diff"] <= 1e-12),
    } for k, v in fc["predictions"].items()]

    ver = json.loads((runs_dir / "verification_latest.json").read_text(encoding="utf-8"))
    out["verification"] = [{
        "stage": s_["stage"], "passed": bool(s_["passed"]), "seconds": s_["seconds"], "detail": s_["detail"],
        "ran_at": ver["ran_at"], "commit": ver["git"]["commit"][:7], "full": bool(ver["full"]),
    } for s_ in ver["stages"]]
    return out


def guard(datasets: Dict[str, List[Dict[str, Any]]]) -> None:
    """Refuse output that could hold daily source values: no date-valued column in any dataset."""
    for name, rows in datasets.items():
        for row in rows:
            for k, v in row.items():
                if k in ("date", "day", "modal_price", "arrival_qty", "min_price", "max_price", "actual", "forecast", "y_origin"):
                    raise ValueError(f"{name}: column {k!r} could carry daily source values")


def main() -> int:
    cfg = load_config()
    data = build(cfg)
    guard(data)
    out_dir = REPO_ROOT / "reports" / "dashboard"
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, rows in data.items():
        (out_dir / f"{name}.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{name}: {len(rows)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
