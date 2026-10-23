# CropCast

**A Data-Driven Framework for Agricultural Commodity Price Forecasting and Market-Relative Anomaly Detection**
Academic project — Data Science Ecosystem (DSE), course 23CS2024 · Problem reference SIH1647

CropCast studies daily state-level wholesale prices and arrivals for **Maharashtra onion** and **Uttar Pradesh potato** (2016–2022) from the CEDA Agri Market Data API. It provides:
- a checksum-verified data pipeline;
- exploratory analysis;
- a pre-registered, leakage-free forecasting comparison against naive baselines;
- an exploratory, causal anomaly-screening study.

## Results at a glance (verified)

| Question | Finding |
|---|---|
| Does any model beat the naive next-day forecast? | **Onion:** no (all five candidates within ±5% of naive MAE; no BH-adjusted DM test significant). **Potato:** yes, all five (random forest −26.3% MAE, BH p < 0.001), but mostly by anticipating weekly reporting-composition effects (exploratory). |
| What does anomaly screening of state aggregates find? | 26–54% of detections are data-coverage or Sunday/Monday composition events. ICTD weak labels cover 59–72% of days and are uninformative (no agreement beyond chance). Synthetic shocks: potato shocks of ±10% are detected; onion needs ±30–50%. |
| Is it reproducible? | The dataset rebuilds byte-identically. Two full forecasting runs agree (13/14 prediction columns bit-identical, random forest ≤ 2.3e-16). Two anomaly runs are exactly equal. All metrics are independently recomputed from saved predictions. |

Deliverables: `reports/final_report.pdf` / `.docx` (source `reports/final_report.md`), `reports/eda_report.md`, `reports/experiment_results.md`, `reports/anomaly_analysis.md`, `reports/literature_review.md`, and executed notebooks in `notebooks/`. Reproducibility policy and evidence: `docs/reproducibility.md`.


## Repository layout

| Path | Contents |
|---|---|
| `configs/config.json` | All paths, the random seed, and dataset, forecasting and anomaly parameters |
| `src/data/` | CEDA ingestion (`ingest_ceda.py`), offline audit (`validate.py`), frozen dataset build (`dataset.py`) |
| `src/features/` | Leakage-safe feature construction and feature-availability audit |
| `src/forecasting/` | Models, walk-forward evaluation, experiment runner |
| `src/anomaly_detection/` | Causal anomaly scores, shock injection, anomaly runner |
| `src/evaluation/` | MAE, RMSE, MAPE, MASE, Diebold–Mariano (HLN), precision/recall/F1 |
| `src/analysis/eda.py` | Exploratory data analysis |
| `src/reporting/` | Notebook builder and Markdown-to-Word/PDF report renderer |
| `notebooks/` | `01_data_audit`, `02_eda`, `03_forecasting`, `04_anomaly_analysis` (executed) |
| `figures/` | All figures (each carries the CEDA credit) |
| `reports/` | Feasibility report, literature review, EDA report, experiment results, anomaly analysis, final report (`.md`, `.docx`, `.pdf`), tables, forecasts, run log |
| `docs/` | Charter, requirements, protocols, environment, and the decision, research, experiment, issue, milestone and meeting logs |
| `tests/` | Unit tests (standard-library `unittest`) |
| `data/` | Local raw and processed data (**not committed**); provenance READMEs and dataset metadata are tracked |

## Setup

Requires Python 3.11 (tested with 3.11.9 on Windows 11). See `docs/environment.md`.

```
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
```

Use `.venv/bin/python` on Linux or macOS.

## Data acquisition

CEDA data is not redistributed in this repository: its terms permit non-commercial use with attribution but do not clearly permit redistribution. To rebuild the data:
1. Register for a free CEDA API key at https://api.ceda.ashoka.edu.in/.
2. Copy `.env.example` to `.env` and set `CEDA_API_KEY`.
3. Run the extraction. It makes 56 requests at ≤ 40 per hour, about 90 minutes, and can be resumed from checkpoints:

```
.venv/Scripts/python -m src.data.ingest_ceda --all-approved --start-date 2016-01-01 --end-date 2022-12-31 --chunk-months 6
```

Provenance (source, retrieval dates, checksums) is recorded in `data/raw/README.md` and `data/raw/ceda_manifest.json`.

## Reproduce all results

Quick integrity check (no retraining, a few minutes): `.venv/Scripts/python -m src.verify`

Full reproduction, run from the repository root in this order:

```
.venv/Scripts/python -m src.data.validate --output data/raw/m2_validation_audit.json
.venv/Scripts/python -m src.data.dataset
.venv/Scripts/python -m src.analysis.eda
.venv/Scripts/python -m src.forecasting.run
.venv/Scripts/python -m src.anomaly_detection.run
.venv/Scripts/python -m src.reporting.notebooks --execute
.venv/Scripts/python -m src.reporting.build_report reports/final_report.md --pdf
.venv/Scripts/python -m unittest discover -s tests
```

What each step does:
1. `src.data.validate` audits the raw data offline. It must report `passed: true`.
2. `src.data.dataset` builds the frozen dataset. Its CSV SHA-256 must equal `csv_sha256` in `data/processed/cropcast_analysis_v1.meta.json`.
3. `src.analysis.eda` writes the EDA outputs to `reports/tables/` and `figures/`.
4. `src.forecasting.run` runs the forecasting experiments (tens of minutes; every-step refits on test).
5. `src.anomaly_detection.run` runs anomaly screening. It needs the SARIMA AIC table from step 4.
6. `src.reporting.notebooks --execute` re-runs the full pipeline inside the notebooks.
7. `src.reporting.build_report` renders the report. The `--pdf` option needs Microsoft Word.
8. `unittest` runs the tests.

Every experiment run appends its configuration hash, parameters, software versions and metrics to `reports/experiment_log.jsonl`.

## Data credit

Data: CEDA Agri Market Data, Centre for Economic Data and Analysis (CEDA), Ashoka University; original source DMI, Ministry of Agriculture and Farmers Welfare (Agmarknet). Non-commercial academic use.
