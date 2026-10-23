# CropCast — Reproducibility Policy and Procedure

## 1. One-command verification

```
.venv/Scripts/python -m src.verify
```

This runs ten lightweight stages (environment, raw inputs, dataset rebuild, unit tests, run manifests, forecast-metric recomputation, anomaly recomputation, report tables, notebooks, Git hygiene).
- It prints PASS or FAIL per stage with the reason, and exits 0 only if every stage passes.
- It **never retrains models**; on the development machine it takes a few minutes.
- `--full` additionally recomputes the SARIMA anomaly residuals with the production code (several minutes).

**Full retraining** is a separate, explicit step:
- `python -m src.forecasting.run` takes about 50 minutes on a 6-core Ryzen 5 5600H.
- `python -m src.anomaly_detection.run` follows it.
- Running `python -m src.reporting.notebooks --execute` runs both inside the notebooks.

## 2. Exactness policy

| Output | Expected agreement | Why |
|---|---|---|
| Raw chunk checksums, audit counts, gaps, alignment | **Exact** | Integer counts and SHA-256 over immutable files |
| Analysis dataset CSV (`cropcast_analysis_v1.csv`) | **Byte-identical, same SHA-256** | Deterministic sort, fixed column order, pandas shortest round-trip float formatting, `\n` line endings. Verified by rebuilding twice and in every `src.verify` run |
| Split boundaries, forecast origin and target dates, naive and seasonal-naive forecasts | **Exact** | Pure indexing |
| Same machine and environment: model forecasts, metrics, anomaly scores | **Identical**, demonstrated by rerunning (§5) | Seeded randomness, single-process SARIMA/ETS, seeded random forest |
| Another machine or BLAS build: SARIMA/ETS/OLS forecasts, metrics, anomaly scores | **Within tolerance (relative 1e-6 on metrics)**; not guaranteed bit-identical | Floating-point reduction order in BLAS/LAPACK and optimiser paths can differ across CPUs and library builds |
| EDA figures (PNG) | Visually equivalent, not byte-identical | Matplotlib output can vary with font availability and version |

The independent verifiers (`src.reporting.verify_results`, `src.reporting.verify_anomaly`) compare recomputed values with a tolerance of 1e-6 (relative and absolute).

## 3. Randomness and other sources of non-determinism

- **Seeds:**
  - One seed, `random_seed` in `configs/config.json` (20261023), feeds the scikit-learn `random_state` (decision tree, random forest), the block bootstrap in EDA, shock positions and the randomisation baseline in the anomaly study.
  - `src.experiment.seed_everything` also seeds Python's `random` and NumPy's global generator at the start of each runner.
- **Parallelism:**
  - The random forest uses `n_jobs = 4`. scikit-learn draws per-tree seeds from `random_state` before parallel fitting, so the fitted trees are identical for any number of jobs.
  - **Tested correction:** the ensemble *prediction* is not bit-identical across different `n_jobs` values. It differs by about 1e-16, because parallel prediction accumulates tree outputs in a different order.
  - **Further tested finding (ISS-012):** with parallel prediction, results are not bit-identical *even at the same* `n_jobs`, because thread order varies between runs.
  - Since forecasting protocol run B, `FeatureModel` fits in parallel and **predicts serially** (`n_jobs = 1` after fitting). That makes random-forest forecasts bit-identical across repeated runs and across `n_jobs`.
  - Run A (the first, retrospective run) used parallel prediction, so its random-forest forecasts can differ from run B by about 1e-16 relative.
  - SARIMA and ETS run single-process, although NumPy and SciPy may use multithreaded BLAS internally (the cross-machine caveat above).
- **Hash seeds:** outputs that are built from sets are sorted before they are written. The same-machine rerun (§5) found no hash-order effects, but this has not been checked line by line.
- **Parallelism and seeds (tested):** `tests/test_reproducibility.py` checks:
  - the trees are bit-identical across `n_jobs`;
  - the ensemble agrees to 1e-12 across `n_jobs` (observed difference about 1e-16);
  - predictions are bit-identical at the same `n_jobs`;
  - Python and NumPy seeding is applied.
- **Not controlled:**
  - BLAS threading and CPU instruction sets.
  - The matplotlib font fallback (Times New Roman is used where installed, otherwise DejaVu Serif).

## 4. Run records

Each forecasting or anomaly run writes `reports/runs/<run_id>/manifest.json` with:
- the run ID, kind, status and UTC start/end times;
- the Git commit and a dirty-tree flag;
- the full configuration snapshot and its SHA-256;
- the dataset version and CSV SHA-256;
- software versions and seeds;
- the SHA-256 of every output artifact.

**Status lifecycle:**
- `running` is written at start.
- `completed` is written only after all outputs are written and hashed.
- `failed` is written, with the error, on an exception.

Every per-model record in `reports/experiment_log.jsonl` carries the run ID and a configuration hash computed from the dataset version, the seed, the feature definition and the model parameters.

**What `src.verify` checks:**
- The latest run of each kind is `completed`.
- The outputs on disk match the hashes in the manifest, so later partial runs cannot silently replace results.
- The configuration and dataset have not changed since the run.
- Each logged configuration hash can be recomputed from its stored fields.

## 5. Evidence of reproducibility

The run history is recorded in `docs/experiment_log.md` (EXP-001 to EXP-004) and `reports/runs/`. Demonstrated on the development machine (Python 3.11.9, Windows 11):

| Run pair | Provenance | Agreement under the §2/§3 rules |
|---|---|---|
| Forecasting run A (retrospective) vs run B (`debc531`, clean, no change during run) | Run A's executed code is **not recorded**; only its outputs are verified | 13/14 prediction columns bit-identical; random forest ≤ 2.34e-16 relative (ISS-012); metrics ≤ 1.0e-15; selection, verdicts and configuration hashes identical; AIC and validation tables equal at run A's 6-digit storage precision |
| Anomaly run 1 (`cd56566`, one unrelated file added mid-run) vs run 2 (`debc531`, clean) | Both recorded | All 7 result tables exactly equal |
| Dataset rebuilds | — | Byte-identical (SHA-256 `b5f21e02…`) on every rebuild, including inside notebook 01 |

The machine-readable record is `reports/runs/reproducibility_comparison_A_vs_B.json` (`python -m src.reporting.compare_runs`). An interrupted attempt (`forecasting-20261023T200219Z-d206cfb6`) is marked `interrupted` and is never used (ISS-016).

## 6. Data access

CEDA data is not redistributed (`data/raw/README.md`). A fresh user needs a free CEDA API key to recreate `data/raw/`, using the ingestion command in the README.

Without CEDA access, `tests/test_pipeline_fixture.py` runs the whole pipeline end to end on a **synthetic, legally distributable fixture**:
- generated raw chunks, a manifest, an overlapping pilot chunk and missing days;
- synthetic ICTD-format labels.

It exercises the audit, deterministic dataset rebuild, forecasting runner, independent metric recomputation, anomaly runner and run manifests.

## 7. System requirements

- Python 3.11 and the packages in `requirements.txt` (`docs/environment.md`).
- **Notebook execution:** an IPython kernel (`ipykernel`, pinned). `nbclient` uses the `python3` kernel of the active environment.
- **PDF export:** Microsoft Word on Windows, through COM (`src/reporting/build_report.py --pdf`). The `.docx` is produced without Word. On other platforms, export the `.docx` to PDF with any word processor; this step is not automated there.
