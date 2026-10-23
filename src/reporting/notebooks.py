"""
Build (and optionally execute) the four CropCast notebooks (Req 7).

Notebooks contain narrative plus calls into `src/`; no analysis logic is duplicated inline (Req 7.6).

Usage:
    python -m src.reporting.notebooks            # write notebooks
    python -m src.reporting.notebooks --execute  # write and execute top to bottom (Req 7.5)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

from src.config import REPO_ROOT

SETUP = """import os, sys
from pathlib import Path
# Run from the repository root so `src` and configured relative paths resolve
root = Path.cwd()
while not (root / "configs" / "config.json").exists() and root != root.parent:
    root = root.parent
os.chdir(root)
sys.path.insert(0, str(root))
import json
import pandas as pd
from IPython.display import Image, Markdown, display
from src.config import load_config, resolve_path
cfg = load_config()
tables = resolve_path(cfg["paths"]["tables_dir"])
figs = resolve_path(cfg["paths"]["figures_dir"])
print("Repository root:", root)"""

CREDIT = ("*Data: CEDA Agri Market Data, Centre for Economic Data and Analysis (CEDA), Ashoka University; "
          "original source DMI, Ministry of Agriculture and Farmers Welfare (Agmarknet).*")


def nb_data_audit():
    return [
        new_markdown_cell("# 01 — Data audit\n\nDataset discovery and schema inspection, data-quality statistics, "
                          "and the frozen analysis dataset (Req 7.1). Raw CEDA files must be present in `data/raw/` "
                          "(see `data/raw/README.md`).\n\n" + CREDIT),
        new_code_cell(SETUP),
        new_markdown_cell("## Offline integrity audit of the 56 raw chunks\n`src.data.validate.run_audit` checks the manifest, "
                          "checksums, schemas, duplicates, nulls, numeric rules, coverage and pilot overlap."),
        new_code_cell("from src.data.validate import run_audit\n"
                      "audit = run_audit(manifest_path=resolve_path(cfg['paths']['manifest']), raw_dir=resolve_path(cfg['paths']['raw_dir']))\n"
                      "print('passed:', audit['passed']); print('hard failures:', audit['hard_failures']); print('warnings:', audit['warnings'])\n"
                      "pd.DataFrame({sid: {k: m[k] for k in ['chunks_found','price_records_count','quantity_records_count','duplicate_price_keys',"
                      "'null_values','numeric_violations','modal_bounds_warnings','missing_price_days','price_gaps_count','max_consecutive_price_gap','iou']}"
                      " for sid, m in audit['series_metrics'].items()})"),
        new_markdown_cell("## Build the frozen analysis dataset (v1)\nDeterministic and lossless; the CSV checksum must match "
                          "`data/processed/cropcast_analysis_v1.meta.json`."),
        new_code_cell("from src.data.dataset import build_dataset, write_dataset\n"
                      "df, meta = build_dataset(cfg)\n"
                      "csv_path, meta_path = write_dataset(df, meta, resolve_path(cfg['paths']['processed_dir']), cfg['dataset']['version'])\n"
                      "print(json.loads(meta_path.read_text())['csv_sha256'])\n"
                      "pd.DataFrame(meta['missing_report'])"),
        new_code_cell("pd.DataFrame(meta['flag_counts']).T"),
        new_code_cell("df.groupby('series_id')[['modal_price','min_price','max_price','arrival_qty']].describe().T"),
    ]


def nb_eda():
    return [
        new_markdown_cell("# 02 — Exploratory data analysis\n\nDescriptive statistics, decomposition, correlation analysis "
                          "and visual outputs (Req 7.2). Narrative: `reports/eda_report.md`.\n\n" + CREDIT),
        new_code_cell(SETUP),
        new_code_cell("from src.analysis.eda import run as run_eda\nsummary = run_eda(cfg)\n"
                      "pd.read_csv(tables / 'eda_descriptive_stats.csv').round(3)"),
        new_markdown_cell("## Coverage, seasonality and decomposition choice"),
        new_code_cell("pd.DataFrame(summary['seasonality']).T"),
        new_code_cell("pd.DataFrame(summary['decomposition']).T"),
        new_code_cell("pd.read_csv(tables / 'eda_weekday_profile.csv').round(2)"),
        new_markdown_cell("## Figures"),
        *[new_code_cell(f"display(Image(filename=str(figs / '{f}')))") for f in (
            "fig01_price_series.png", "fig03_missingness_heatmap.png", "fig04_monthly_boxplots.png",
            "fig05_stl_decomposition.png", "fig06_acf_onion_maharashtra.png", "fig06_acf_potato_uttar_pradesh.png",
            "fig08_price_arrival_monthly_changes.png", "fig09_correlation_heatmap.png",
            "fig10_modal_position_iss002.png", "fig12_weekday_composition.png")],
        new_markdown_cell("## Price–arrival association and ISS-002"),
        new_code_cell("pd.DataFrame(summary['price_arrival']).T"),
        new_code_cell("pd.DataFrame(summary['iss002']).T"),
    ]


def nb_forecasting():
    return [
        new_markdown_cell("# 03 — Forecasting\n\nFeature construction, model training, walk-forward evaluation and metrics "
                          "(Req 7.3), following `docs/forecasting_protocol.md` v1.1. **Runtime: tens of minutes** "
                          "(test refits at every step, as Req 5.6 requires).\n\n" + CREDIT),
        new_code_cell(SETUP),
        new_markdown_cell("## Feature-availability audit (Req 4.8)"),
        new_code_cell("from src.features.build import feature_audit_table\nfeature_audit_table()"),
        new_markdown_cell("## Run validation tuning and the walk-forward test"),
        new_code_cell("from src.forecasting.run import Runner\nRunner(cfg).run()"),
        new_code_cell("m = pd.read_csv(tables / 'forecast_test_metrics.csv')\n"
                      "m[['series_id','model','mae','rmse','mape_pct','mase','mae_vs_naive_pct','dm_stat','p_bh','verdict']].round(4)"),
        new_code_cell("v = pd.read_csv(tables / 'forecast_validation_results.csv')\n"
                      "v.sort_values(['series_id','val_mae']).groupby('series_id').head(8)"),
        new_code_cell("b = pd.read_csv(tables / 'forecast_test_breakdown.csv')\n"
                      "b[b.breakdown == 'half_year'].pivot_table(index=['series_id','level'], columns='model', values='mae').round(1)"),
        *[new_code_cell(f"display(Image(filename=str(figs / '{f}')))") for f in (
            "fig13_residuals_onion_maharashtra.png", "fig13_residuals_potato_uttar_pradesh.png", "fig14_test_forecasts.png")],
    ]


def nb_anomaly():
    return [
        new_markdown_cell("# 04 — Anomaly analysis\n\nResidual computation, anomaly-score construction, the ablation study, "
                          "and evaluation against weak labels and synthetic shocks (Req 7.4). Requires "
                          "`reports/tables/forecast_sarima_aic.csv` from notebook 03. Narrative: `reports/anomaly_analysis.md`.\n\n" + CREDIT),
        new_code_cell(SETUP),
        new_code_cell("from src.anomaly_detection.run import AnomalyRunner\nsummary = AnomalyRunner(cfg).run()\n"
                      "{k: v for k, v in summary.items() if k != 'event_classes'}"),
        new_markdown_cell("## Ablation: detections by class (real data)"),
        new_code_cell("pd.read_csv(tables / 'anomaly_event_classes.csv')"),
        new_markdown_cell("## Weak-label agreement (ICTD-IITD; endogenous, not ground truth)"),
        new_code_cell("pd.read_csv(tables / 'anomaly_weak_label_agreement.csv').round(4)"),
        new_markdown_cell("## Synthetic shock recall (reported separately from real-data results; Req 6.6–6.7)"),
        new_code_cell("pd.read_csv(tables / 'anomaly_shock_recall.csv').pivot_table(index=['series_id','magnitude'], columns='method', values='recall').round(3)"),
        *[new_code_cell(f"display(Image(filename=str(figs / '{f}')))") for f in (
            "fig15_anomaly_score_distributions.png", "fig16_shock_recall.png", "fig17_anomaly_timeline.png",
            "fig18_threshold_sensitivity.png")],
    ]


NOTEBOOKS = {
    "01_data_audit.ipynb": nb_data_audit,
    "02_eda.ipynb": nb_eda,
    "03_forecasting.ipynb": nb_forecasting,
    "04_anomaly_analysis.ipynb": nb_anomaly,
}


def build(execute: bool = False, only: list[str] | None = None) -> None:
    out_dir = REPO_ROOT / "notebooks"
    out_dir.mkdir(exist_ok=True)
    for name, fn in NOTEBOOKS.items():
        if only and name not in only:
            continue
        nb = new_notebook(cells=fn(), metadata={"kernelspec": {"name": "python3", "display_name": "Python 3"},
                                                "language_info": {"name": "python"}})
        path = out_dir / name
        if execute:
            NotebookClient(nb, timeout=None, kernel_name="python3",
                           resources={"metadata": {"path": str(out_dir)}}).execute()
        nbformat.write(nb, path)
        print(("Executed " if execute else "Wrote ") + str(path))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--only", nargs="*", help="notebook file names to build")
    args = parser.parse_args()
    build(args.execute, args.only)


if __name__ == "__main__":
    sys.exit(main())
