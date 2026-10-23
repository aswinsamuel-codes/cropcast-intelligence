"""
Generate the result tables in the final report from saved artifacts, so no reported number is retyped.

Tables live in `reports/final_report.md` between markers:
    <!-- BEGIN TABLE:name -->
    ...generated content...
    <!-- END TABLE:name -->

Usage:
    python -m src.reporting.report_tables            # rewrite the tables in place
    python -m src.reporting.report_tables --check    # exit 1 if any table differs from the artifacts
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Callable, Dict

import pandas as pd

from src.config import REPO_ROOT, load_config, resolve_path

LABEL = {"onion_maharashtra": "Onion (MH)", "potato_uttar_pradesh": "Potato (UP)"}
MODEL_LABEL = {"naive": "Naive", "seasonal_naive": "Seasonal naive (7)", "linear_regression": "Linear regression",
               "decision_tree": "Decision tree", "random_forest": "Random forest", "sarima": "Seasonal ARIMA",
               "ets": "ETS (Holt–Winters)"}
METHOD_LABEL = {"residual": "Residual", "robust": "Robust", "composite": "Composite"}
SHORT_MODEL = {"naive": "Naive", "seasonal_naive": "SN7", "linear_regression": "OLS", "decision_tree": "Tree",
               "random_forest": "RF", "sarima": "SARIMA", "ets": "ETS"}
CLASS_LABEL = {"Sunday/Monday (composition-prone)": "Sun/Mon", "coverage anomaly (ISS-003 type)": "Coverage",
               "min/max band violation (ISS-002 type)": "Band (ISS-002)", "other": "Other"}


def _fmt(x, nd=1):
    return "—" if pd.isna(x) else f"{x:,.{nd}f}"


def _p(x):
    if pd.isna(x):
        return "—"
    return "<0.001" if x < 0.001 else f"{x:.3f}"


def table_forecast_metrics(tables: Path) -> str:
    m = pd.read_csv(tables / "forecast_test_metrics.csv")
    # Short verdict codes keep the table within the page width; the caption defines them
    short = {"no significant difference": "n.s.", "improves on naive": "Better", "baseline": "Baseline",
             "significantly worse than naive": "Worse"}
    lines = ["| Series | Model | MAE | RMSE | MAPE % | MASE | Δ MAE | DM | BH p | Verdict |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in m.iterrows():
        lines.append(f"| {LABEL[r['series_id']].split()[0]} | {MODEL_LABEL[r['model']]} | {_fmt(r['mae'], 2)} | {_fmt(r['rmse'], 2)} | "
                     f"{_fmt(r['mape_pct'], 2)} | {_fmt(r['mase'], 3)} | "
                     f"{'—' if r['model'] == 'naive' else f'{r.mae_vs_naive_pct:+.1f}%'} | {_fmt(r['dm_stat'], 2)} | "
                     f"{_p(r['p_bh'])} | {short[r['verdict']]} |")
    return "\n".join(lines)


def _settings(model: str, params: Dict) -> str:
    if model == "sarima":
        return f"({params['p']},1,{params['q']})({params['P']},0,{params['Q']})₇"
    if model == "ets":
        return "damped additive trend" if params.get("trend") == "add_damped" else "no trend"
    return ", ".join(f"{k}={v}" for k, v in params.items()) or "—"


def table_forecast_settings(tables: Path) -> str:
    """Selected configuration per model, from the saved selection (argmin of validation MAE)."""
    m = pd.read_csv(tables / "forecast_test_metrics.csv")
    lines = ["| Model | Onion (MH) | Potato (UP) |", "|---|---|---|"]
    for model in ("decision_tree", "random_forest", "sarima", "ets"):
        cells = []
        for sid in ("onion_maharashtra", "potato_uttar_pradesh"):
            r = m[(m.series_id == sid) & (m.model == model)].iloc[0]
            cells.append(_settings(model, json.loads(r["selected_params"])))
        lines.append(f"| {MODEL_LABEL[model]} | {cells[0]} | {cells[1]} |")
    return "\n".join(lines)


def table_forecast_halves(tables: Path) -> str:
    b = pd.read_csv(tables / "forecast_test_breakdown.csv")
    b = b[b["breakdown"] == "half_year"]
    models = ["naive", "seasonal_naive", "linear_regression", "decision_tree", "random_forest", "sarima", "ets"]
    lines = ["| Series | Period | n | " + " | ".join(SHORT_MODEL[m] for m in models) + " |",
             "|---|---|---|" + "---|" * len(models)]
    for (sid, level), g in b.groupby(["series_id", "level"]):
        row = g.set_index("model")
        lines.append(f"| {LABEL[sid].split()[0]} | {level} | {int(row['n'].iloc[0])} | "
                     + " | ".join(_fmt(row.at[m, 'mae'], 1) if m in row.index else "—" for m in models) + " |")
    return "\n".join(lines)


def table_anomaly_classes(tables: Path) -> str:
    c = pd.read_csv(tables / "anomaly_event_classes.csv").set_index(["series_id", "method"])
    cols = list(c.columns)
    s = pd.read_csv(tables / "anomaly_threshold_sensitivity.csv")
    s = s[s["threshold"] == 3.0].set_index(["series_id", "method"])
    lines = ["| Series | Score | Scored days | Detections | " + " | ".join(CLASS_LABEL.get(x, x) for x in cols) + " |",
             "|---|---|---|---|" + "---|" * len(cols)]
    # Iterate over every series x score, not only those with events, so zero-detection rows are shown
    for sid in ("onion_maharashtra", "potato_uttar_pradesh"):
        for m in ("residual", "robust", "composite"):
            k = (sid, m)
            counts = [int(c.at[k, x]) if k in c.index else 0 for x in cols]
            if sum(counts) != int(s.at[k, "detections"]):
                raise ValueError(f"{k}: class counts {sum(counts)} != detections {int(s.at[k, 'detections'])}")
            lines.append(f"| {LABEL[sid].split()[0]} | {METHOD_LABEL[m]} | {int(s.at[k, 'scored_days'])} | "
                         f"{int(s.at[k, 'detections'])} ({s.at[k, 'rate_pct']:.2f}%) | " + " | ".join(str(v) for v in counts) + " |")
    return "\n".join(lines)


def table_anomaly_weak(tables: Path) -> str:
    w = pd.read_csv(tables / "anomaly_weak_label_agreement.csv")
    lines = ["| Series | Score | Days | Label rate | Precision | Recall | F1 | Null precision | Rand. p |",
             "|---|---|---|---|---|---|---|---|---|"]
    for _, r in w.iterrows():
        lines.append(f"| {LABEL[r['series_id']].split()[0]} | {METHOD_LABEL[r['method']]} | {int(r['evaluated_days'])} | {r['label_base_rate']:.3f} | "
                     f"{_fmt(r['precision'], 3)} | {_fmt(r['recall'], 3)} | {_fmt(r['f1'], 3)} | {_fmt(r['null_precision_median'], 3)} | "
                     f"{_p(r['randomisation_p_precision'])} |")
    return "\n".join(lines)


def table_anomaly_shocks(tables: Path) -> str:
    s = pd.read_csv(tables / "anomaly_shock_recall.csv")
    p = s.pivot_table(index="magnitude", columns=["series_id", "method"], values="recall")
    f = s.groupby(["series_id", "method"])["fpr"].mean()
    methods = ("residual", "robust", "composite")
    short = {"residual": "Res", "robust": "Rob", "composite": "Com"}
    series = ("onion_maharashtra", "potato_uttar_pradesh")
    lines = ["| Shock | " + " | ".join(f"{LABEL[sid].split()[0]} {short[m]}" for sid in series for m in methods) + " |",
             "|---|" + "---|" * (len(series) * len(methods))]
    for mag, r in p.iterrows():
        lines.append(f"| {mag * 100:+.0f}% | " + " | ".join(f"{r[(sid, m)]:.2f}" for sid in series for m in methods) + " |")
    lines.append("| FPR (clean days) | " + " | ".join(f"{100 * f[(sid, m)]:.2f}%" for sid in series for m in methods) + " |")
    return "\n".join(lines)


TABLES: Dict[str, Callable[[Path], str]] = {
    "forecast_metrics": table_forecast_metrics,
    "forecast_settings": table_forecast_settings,
    "forecast_halves": table_forecast_halves,
    "anomaly_classes": table_anomaly_classes,
    "anomaly_weak": table_anomaly_weak,
    "anomaly_shocks": table_anomaly_shocks,
}
# Matches empty placeholders (adjacent marker lines) as well as filled tables
MARKER = re.compile(r"(<!-- BEGIN TABLE:(\w+) -->\r?\n)(.*?)(<!-- END TABLE:\2 -->)", re.S)


def refresh(text: str, tables: Path) -> str:
    return MARKER.sub(lambda m: m.group(1) + TABLES[m.group(2)](tables) + "\n" + m.group(4), text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--report", default="reports/final_report.md")
    args = parser.parse_args()
    tables = resolve_path(load_config()["paths"]["tables_dir"])
    path = REPO_ROOT / args.report
    text = path.read_text(encoding="utf-8")
    new = refresh(text, tables)
    found = [m.group(2) for m in MARKER.finditer(text)]
    if args.check:
        # A document without any table markers must not pass vacuously
        ok = new == text and bool(found)
        print(json.dumps({"tables_found": found, "up_to_date": ok}))
        return 0 if ok else 1
    path.write_text(new, encoding="utf-8")
    print(f"Refreshed {len(found)} tables: {found}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
