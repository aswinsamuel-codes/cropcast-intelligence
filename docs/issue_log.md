# CropCast — Issue and Resolution Log

Bugs, failed approaches, and unexpected results are recorded here. Failed experiments must not be omitted.

Each entry records: symptoms, reproduction steps, root cause (if established), attempted solutions, and verified resolution.

---

## Entry Template

```
### ISS-NNN: [Short Description]
- **Date reported:** YYYY-MM-DD
- **Phase / component:** [e.g., Data Pipeline, Feature Engineer, Forecaster]
- **Symptoms:** [What was observed]
- **Reproduction steps:** [Minimal steps to reproduce]
- **Root cause:** [Established cause, or "Under investigation"]
- **Attempted solutions:**
  1. [Approach A — outcome]
  2. [Approach B — outcome]
- **Resolution:** [Final fix applied, or "Unresolved"]
- **Verified by:** [test, manual check, or other evidence]
- **Status:** [Open / Resolved / Accepted limitation]
- **Related files/refs:** [code, notebook, report]
```

---

## Entries

### ISS-001: `.gitignore` rule `data/` excluded the `src/data/` source package
- **Date reported:** 2026-10-23
- **Phase / component:** Repository hygiene / Data Pipeline
- **Symptoms:** `git status --ignored` listed `src/data/` as ignored; only `src/__init__.py` would have been committed, omitting `src/data/ingest_ceda.py`.
- **Reproduction steps:** `git check-ignore -v src/data/ingest_ceda.py` → matched `.gitignore: data/`.
- **Root cause:** An unanchored `data/` pattern matches any directory named `data` at any depth.
- **Attempted solutions:**
  1. Anchored the pattern to the repository root (`/data/`) — successful.
- **Resolution:** `.gitignore` now uses `/data/`.
- **Verified by:** `git check-ignore` still matches `data/raw/ceda_manifest.json` and raw chunk files; `src/data/ingest_ceda.py` and `src/data/__init__.py` now show as untracked (committable).
- **Status:** Resolved
- **Related files/refs:** `.gitignore`, `docs/research_log.md` (RES-011)

### ISS-002: UP Potato `modal_price` outside `[min_price, max_price]` in 137 records
- **Date reported:** 2026-10-23
- **Phase / component:** Data Validation
- **Symptoms:** 136 records with `modal_price < min_price` and 1 with `modal_price > max_price` in `potato_uttar_pradesh` prices. Onion has 0 such records.
- **Reproduction steps:** Load all 14 historical price chunks for `potato_uttar_pradesh` and count records violating `min_price <= modal_price <= max_price`.
- **Root cause:** Under investigation. All below-min cases fall within 2016-03-04 – 2017-04-02 (110 in 2016, 26 in 2017); median shortfall 1.46%, max 7.24%. The time confinement points to a source-side aggregation or reporting regime in that period. An earlier "volume-weighted aggregation" explanation was unverified and has been retracted.
- **Attempted solutions:**
  1. None applied. Records are retained unchanged (no deletion, clipping, or imputation).
- **Resolution:** Unresolved. Update 2026-10-23 (RES-014, RES-015):
  - CEDA methodology documentation is unavailable (README HTTP 404).
  - EDA shows a reporting regime from at least 2016-01 to about 2017-04 in which the modal sits at a median 0.07 of the [min, max] band, against 0.50 afterwards. The 137 violations are its extreme tail.
  - Rows carry `flag_modal_outside_bounds`. Potato min/max prices are excluded from features, and the regime lies in the training period only.
- **Verified by:** Offline re-verification (RES-011).
- **Status:** Open
- **Related files/refs:** `data/raw/ceda/potato_uttar_pradesh/prices_*.json`, `docs/research_log.md` (RES-010, RES-011), DEC-016

### ISS-003: Near-zero Maharashtra Onion arrivals on four dates in 2020
- **Date reported:** 2026-10-23
- **Phase / component:** Data Validation
- **Symptoms:** `quantity` = 5 (2020-04-24), 3 (2020-04-25), 2 (2020-04-28), 14 (2020-10-26), against a series mean of ~16,323. They sit next to the 2020-04 lockdown gaps and immediately after the 10-day gap ending 2020-10-25.
- **Reproduction steps:** Sort onion quantity records ascending.
- **Root cause:** Under investigation; plausibly partial mandi reporting during disruptions. Not confirmed.
- **Attempted solutions:**
  1. None applied; values retained unchanged.
- **Resolution:** Unresolved; to be characterised in M-3 EDA. Any exclusion or flagging rule must be decided explicitly and logged. Update 2026-10-23: the audit's 100×-median screen flags 10 onion arrival values (2–150), dated 2020-03-22, 2020-04-21/22/24/25/28/29, 2020-10-26, 2020-11-14 and 2021-05-01 (RES-013).
- **Verified by:** Offline re-verification (RES-011).
- **Status:** Open
- **Related files/refs:** `data/raw/ceda/onion_maharashtra/quantities_2020-*.json`

### ISS-004: M-2 validation audit not reproducible from committed code
- **Date reported:** 2026-10-23
- **Phase / component:** Reproducibility / Data Validation
- **Symptoms:** `data/raw/m2_validation_audit.json` (reports 137 potato numeric violations) was produced by a script not in the repository. `historical_extraction_summary.json`, produced by `src/data/ingest_ceda.py`, reports 0 numeric violations for the same data because `validate_records` does not check `min_price <= modal_price <= max_price`. No run log of `task-775` was retained.
- **Reproduction steps:** Compare `numeric_violations` for potato prices across the two JSON files; inspect `CedaIngestionPipeline.validate_records`.
- **Root cause:** Validation gate checks were run ad hoc rather than from a committed module; the pipeline validator lacks the modal-bounds check.
- **Attempted solutions:**
  1. Independent offline re-verification script written outside the repository (RES-011); results agree with the audit file on all counts.
  2. Per DEC-016 (approved): added `src/data/validate.py`, a committed offline audit module with 16 unit tests (`tests/test_validate.py`; corrected from "18"), and a non-fatal `modal_bounds_warnings` counter in `validate_records`. Warnings do not affect `is_valid`, so they never trigger a re-fetch.
- **Resolution:** `python -m src.data.validate --output data/raw/m2_validation_audit.json` regenerates the audit offline. The previous ad-hoc file is preserved locally as `data/raw/m2_validation_audit.legacy_adhoc.json`. Schema change: the legacy `price_numeric_violations` (137 for potato, modal-bounds cases included) is replaced by `numeric_violations` (hard failures only, 0) and `modal_bounds_warnings` (137).
- **Verified by:** Regenerated audit equals the legacy audit on every shared field (counts, gaps, IoU, match rate, distribution stats); `validate_records` on the full potato price series returns `is_valid=True`, 0 violations, 137 warnings; 40 / 40 tests pass. The run log for `task-775` cannot be recovered, so its 429 / retry history stays unverified.
- **Status:** Resolved
- **Related files/refs:** `src/data/ingest_ceda.py`, `data/raw/m2_validation_audit.json`, `data/raw/historical_extraction_summary.json`

### ISS-005: Pilot chunks overlap historical H1-2021 chunks and use a different file format
- **Date reported:** 2026-10-23
- **Phase / component:** Data Assembly
- **Symptoms:** `*_2021-01-01_2021-01-15.json` pilot files (4 total) are bare JSON lists without the `metadata` envelope, and duplicate dates in the `*_2021-01-01_2021-06-30.json` chunks.
- **Reproduction steps:** Load both files for any series/endpoint and compare records by date.
- **Root cause:** Pilot run preceded the envelope format; full-range run used different chunk boundaries.
- **Attempted solutions:**
  1. Compared all overlapping records — field-for-field identical (0 differences).
- **Resolution:** Dataset assembly must read only the 14 six-month historical chunks per series/endpoint (or deduplicate on the composite key and assert equality). Raw files are left untouched.
- **Verified by:** Offline re-verification (RES-011).
- **Status:** Accepted limitation
- **Related files/refs:** `data/raw/ceda/*/*_2021-01-01_2021-01-15.json`

### ISS-006: `test_http_500_exponential_backoff_and_retry` exercises nothing
- **Date reported:** 2026-10-23
- **Phase / component:** Test suite
- **Symptoms:** The test configures mocks for an HTTP 500 followed by a success but never calls `make_request` and makes no assertions, so it always passes. HTTP 5xx backoff is therefore untested, and earlier test counts overstate coverage by one.
- **Reproduction steps:** Read `tests/test_ingest_ceda.py`, `TestRateLimitingAndRetries.test_http_500_exponential_backoff_and_retry`.
- **Root cause:** Incomplete test body.
- **Attempted solutions:**
  1. Completed the test body (remediation approved after the final M-2 audit, 2026-10-23).
- **Resolution:** The test now calls `make_request`, asserts a successful result, two `urlopen` calls, and a 4.0s backoff `sleep`.
- **Verified by:** Test passes. 5xx backoff already worked, so the test also passes against the previous code; the fix makes it assert something rather than catching a regression.
- **Status:** Resolved
- **Related files/refs:** `tests/test_ingest_ceda.py`

### ISS-007: M-2 audit accepted empty, truncated, and failed chunks
- **Date reported:** 2026-10-23 (final M-2 audit)
- **Phase / component:** Data Validation (`src/data/validate.py`)
- **Symptoms:** Synthetic probes showed `passed: true` for an empty chunk, a chunk truncated to 5 of 31 days, and a manifest entry with `status: failed`. A price of 1e9 and a quantity of 0 also passed silently.
- **Reproduction steps:** Build an audit fixture (`tests/test_validate.py`), empty or truncate one chunk or edit its manifest status, then run `run_audit`.
- **Root cause:** The audit checked record-level validity but not chunk-level completeness or manifest status, and had no plausibility screening.
- **Attempted solutions:**
  1. Added hard failures for non-`completed` / non-valid manifest entries and for empty expected chunks.
  2. Added warnings for chunks with records on fewer than 90% of calendar days, for zero values, and for values beyond 100× of the field median. These are warnings, not failures, because onion has legitimate reporting gaps and outlier handling is an EDA decision.
- **Resolution:** Implemented in `src/data/validate.py`, with 6 new tests in `tests/test_validate.py`.
- **Verified by:** All 6 new validator tests fail against the previous code (`HEAD` copy run in a scratch directory) and pass now. Real data: `passed: true`, no status, empty-chunk or low-coverage findings (lowest chunk coverage 172/182 = 94.5%), 0 zeros, and 10 onion arrival values beyond 100× of the median (see ISS-003).
- **Status:** Resolved
- **Related files/refs:** `src/data/validate.py`, `tests/test_validate.py`, RES-013

### ISS-008: Pipeline marked empty responses as completed and re-downloaded source-data violations
- **Date reported:** 2026-10-23 (final M-2 audit)
- **Phase / component:** Data Pipeline (`src/data/ingest_ceda.py`)
- **Symptoms:**
  1. A "No data found" response was saved with `status: completed`, `is_valid: true`.
  2. A chunk whose source data had a hard violation (e.g. `min_price > max_price`) was re-downloaded on every rerun, spending quota and overwriting the raw file.
  3. Read timeouts (`TimeoutError`) were not retried.
  4. The "backing up" log message for a corrupt manifest was false: no backup was made.
- **Reproduction steps:** Synthetic probes with mocked `make_request` / `urlopen` (now encoded as tests).
- **Root cause:** Status was always `completed`; re-validation on resume did not distinguish corrupted files from faithful copies of imperfect source data; `TimeoutError` is not a `URLError`; the backup was never implemented.
- **Attempted solutions:**
  1. Empty responses are saved for provenance with `status: "empty"`. On rerun they are read from disk, not re-requested, and the audit reports them as hard failures. Re-requesting one requires deliberately removing its manifest entry.
  2. A file whose SHA-256 matches its manifest entry is kept even if it has validation errors (logged); files without a manifest entry are still re-fetched when invalid.
  3. `TimeoutError` and `ConnectionError` share the URLError backoff path.
  4. A corrupt manifest is copied to `<name>.corrupt-<UTC timestamp>.json` before recreation.
- **Resolution:** Implemented, with 5 new tests in `tests/test_ingest_ceda.py` and an extended `test_corrupt_manifest_recovery` (asserts the backup).
- **Verified by:** 4 of the 5 new tests and the extended corrupt-manifest test fail against the previous code; all pass now. The fifth new test (an unregistered invalid file is still re-fetched) guards behaviour that was deliberately kept and passes on both. No network requests were made.
- **Status:** Resolved
- **Related files/refs:** `src/data/ingest_ceda.py`, `tests/test_ingest_ceda.py`, RES-013

### ISS-009: Documentation inaccuracies found in the final M-2 audit
- **Date reported:** 2026-10-23
- **Phase / component:** Documentation
- **Symptoms:**
  - "18 new tests in `tests/test_validate.py`" (actual: 16), in CHANGELOG, RES-012 and ISS-004.
  - The CHANGELOG described `reports/_ceda_audit.py` as having "rate limit diagnostics", but it has no rate-limit logic.
  - The milestone history's "22/22" test claim did not mention ISS-006.
  - There was no documented runtime environment.
- **Root cause:** Counts were written without being checked against the files; an earlier description was carried forward without verification.
- **Resolution:** Corrected in place with dated annotations; added `docs/environment.md`.
- **Verified by:** `grep -cE '^\s+def test_'` per test file; manual read of `reports/_ceda_audit.py`.
- **Status:** Resolved
- **Related files/refs:** `CHANGELOG.md`, `docs/research_log.md`, `docs/issue_log.md`, `docs/milestone_history.md`, `docs/environment.md`

### ISS-010: First dataset build rounded source values to 10 significant digits
- **Date reported:** 2026-10-23
- **Phase / component:** Data assembly (`src/data/dataset.py`)
- **Symptoms:** The first CSV output used `float_format="%.10g"`, which wrote 1377.952380952381 as 1377.952381. That alters source values, against the no-modification rule.
- **Root cause:** The output format was chosen for compactness, not losslessness.
- **Resolution:** Switched to pandas' default shortest round-trip representation. Caught before any analysis used the file or anything was committed.
- **Verified by:** All 20,320 numeric values compared equal to the raw JSON. Two rebuilds give an identical SHA-256 (`b5f21e02…`).
- **Status:** Resolved
- **Related files/refs:** `src/data/dataset.py`, DEC-019

### ISS-011: scikit-learn parallel warning flooded the forecasting log
- **Date reported:** 2026-10-23
- **Phase / component:** Forecasting (`src/forecasting/run.py`)
- **Symptoms:** The first forecasting run's log grew to 34 MB after 28 result lines, almost all one repeated `UserWarning` from `sklearn/utils/parallel.py` (`sklearn.utils.parallel.delayed` should be used with `sklearn.utils.parallel.Parallel`), emitted once per random-forest tree when `n_jobs > 1`.
- **Root cause:** An interaction between scikit-learn 1.9.1's parallel-config propagation and joblib. It concerns forwarding *thread-local scikit-learn configuration* to workers. CropCast uses the default configuration, so results are unaffected.
- **Resolution:** The warning is filtered by message in `Runner.__init__`, so it also covers notebook 03. The running experiment was not restarted, because the warning does not change computations.
- **Verified by:** Message inspection (114,050 identical warnings, no other warning types). The Phase 9 reproducibility rerun is to confirm identical metrics with the filter in place.
- **Status:** Resolved (cosmetic)
- **Related files/refs:** `src/forecasting/run.py`

### ISS-012: Random-forest predictions were not bit-reproducible under parallel prediction
- **Date reported:** 2026-10-24
- **Phase / component:** Forecasting reproducibility (`src/forecasting/models.py`)
- **Symptoms:** Two random forests fitted with identical data, `random_state` and `n_jobs = 4` gave predictions differing in 23 of 50 elements, by about 1e-16 (maximum relative difference 2.1e-16). The fitted trees were bit-identical.
- **Reproduction steps:** `tests/test_reproducibility.py` (first draft): fit twice with `n_jobs = 4` and compare `predict` outputs bit for bit.
- **Root cause:** scikit-learn's parallel prediction accumulates per-tree outputs across threads in a non-deterministic order, and floating-point addition is not associative. An earlier claim in `docs/reproducibility.md` that results "do not depend on the number of jobs" was wrong, and has been corrected.
- **Attempted solutions:**
  1. Fit in parallel and predict serially: set `n_jobs = 1` on the fitted model before `predict`.
- **Resolution:** Implemented in `FeatureModel.fit` after the first forecasting run (run A) completed. That run had loaded the old code and was not interrupted. Run A's random-forest forecasts may therefore differ from run B's by about 1e-16 relative; every other model is expected to match exactly.
- **Verified by:** `test_parallel_fit_serial_predict_is_bit_identical` and `test_feature_model_predicts_serially`.
- **Status:** Resolved
- **Related files/refs:** `src/forecasting/models.py`, `tests/test_reproducibility.py`, `docs/reproducibility.md` §3

### ISS-013: Result tables were rounded to 6 significant digits, so the independent verifier failed
- **Date reported:** 2026-10-24
- **Phase / component:** Forecasting outputs (`src/forecasting/run.py`; also the anomaly and EDA table writers)
- **Symptoms:** `src.reporting.verify_results` reported 13 mismatches between `forecast_test_metrics.csv` (run A) and metrics recomputed from the saved predictions, with relative differences of 6e-8 to 3.9e-6. That exceeds the verifier's 1e-6 tolerance.
- **Root cause:** Tables were written with `float_format="%.6g"`, so the stored metrics were lossy. The predictions were stored at full precision and were correct.
- **Attempted solutions:**
  1. Relax the verifier tolerance. Rejected: that would weaken the check.
  2. Write all result tables at full precision, and compute metrics through one shared function, `src.forecasting.run.evaluate`. Run A's metrics were regenerated from its preserved predictions with that function; its original 6-digit table is kept unchanged. **Chosen.**
- **Resolution:**
  - Full-precision writers are now used in the forecasting, anomaly and EDA code.
  - Run A's full-precision table is `reports/runs/forecasting-retrospective-20261023T180644/artifacts/tables/forecast_test_metrics_full_precision.csv`.
  - Every verdict is identical between the 6-digit and full-precision tables.
- **Verified by:** `python -m src.reporting.verify_results --metrics <run A full-precision table> --forecasts-dir <run A forecasts>` gives 14 rows × 7 statistics with 0 problems.
- **Status:** Resolved
- **Related files/refs:** `src/forecasting/run.py`, `src/reporting/verify_results.py`, ISS-012

### ISS-014: Five SARIMA refits in the potato anomaly residual model stopped without convergence
- **Date reported:** 2026-10-24
- **Phase / component:** Anomaly detection (`src/anomaly_detection/run.py` residual walk-forward)
- **Symptoms:** The run manifest counted 5 `ConvergenceWarning`s. The warning tally surfaced them; they were not suppressed.
- **Investigation:** `src/reporting/diagnose_sarima_convergence.py` replays the refit schedule.
  - **Where:** all 5 are potato refits (of 85), at 2018-01-12 and 2020-02-07 (train), 2021-04-02 and 2021-04-30 (validation), and 2022-01-07 (test). Onion and the frozen shock fits all converged.
  - **Cause:** each was a warm-started L-BFGS run that stopped after 1–2 iterations with `warnflag = 2`.
  - **Cold-start check:** refits converge. Three warm fits have a *higher* log-likelihood than the cold optimum; two (2021-04-30, 2022-01-07) are lower by 0.16 and 0.43.
- **Impact:** substituting the converged cold-start parameters changes the residuals by ≤ 0.0042 (log scale) and changes **no** detection at |score| > 3.
- **Resolution:** Results retained and usable. The limitation is documented in `reports/anomaly_analysis.md` §5. No rerun was made to change results.
- **Verified by:** `anomaly_sarima_convergence.csv` and `anomaly_sarima_convergence_impact.json`; the independent verifier reproduced the same 5 warnings.
- **Status:** Accepted limitation (assessed)
- **Related files/refs:** EXP-002

### ISS-015: The robust anomaly score made zero detections for potato (protocol design weakness)
- **Date reported:** 2026-10-24
- **Phase / component:** Anomaly protocol v1.0 (`robust_weekday_score` followed by `causal_standardize`)
- **Symptoms:**
  - The potato robust score made 0 detections at |score| > 3 over 2,111 scored days (9 at 2.5).
  - Precision is undefined; recall is 0 and F1 is 0 by 2TP/(2TP+FP+FN).
  - Its shock recall is low (0.17–0.77).
  - A `RuntimeWarning: All-NaN slice` came from the randomisation median, which is all undefined when there are no detections.
- **Root cause:**
  1. The deviation from the trailing 28-day median absorbs potato's smooth trends: the raw score exceeds |3| on 16% of days.
  2. The protocol's second standardisation uses an expanding *mean and SD*. That is not robust, and is inflated by the extreme Nov–Dec 2016 collapse values (raw score about −18.8), which compresses all later standardised scores (maximum |z| = 2.94).
- **Resolution:**
  - Not changed after seeing results (protocol integrity).
  - Undefined precision is kept as NaN in the tables, the verifier and the report (shown as "—"), and never as 0.
  - Future work: a detrended robust score with robust (median/MAD) standardisation.
- **Status:** Accepted limitation (documented)
- **Related files/refs:** `reports/anomaly_analysis.md` §2, EXP-002
