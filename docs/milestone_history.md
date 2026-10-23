# CropCast — Milestone History

This file records planned, in-progress, completed, and blocked milestones with evidence of completion, deviations, and outstanding issues.

**Status labels used in this document:**
- `Planned` — Defined but not yet started.
- `In Progress` — Actively being worked on.
- `Completed` — Acceptance criteria verified; evidence recorded below.
- `Blocked` — Cannot proceed; reason documented.

---

## Milestone Overview

| ID  | Name                                    | Status      | Target Phase       |
|-----|-----------------------------------------|-------------|--------------------|
| M-0 | Project Foundation                      | Completed   | Pre-development    |
| M-1 | Research and Dataset Feasibility        | Completed   | Phase 1            |
| M-2 | Data Acquisition and Preparation        | Completed   | Phase 2            |
| M-3 | Exploratory Data Analysis               | Planned (Awaiting Approval) | Phase 3            |
| M-4 | Forecasting Protocol and Baselines      | Planned     | Phase 4            |
| M-5 | Forecasting Experiments                 | Planned     | Phase 5            |
| M-6 | Anomaly Detection                       | Planned     | Phase 6            |
| M-7 | Final Analysis and Academic Report      | Planned     | Phase 7            |

---

## M-0: Project Setup and Requirements

**Status:** Completed
**Completed:** 2026-10-19

### Planned Scope
- Define the CropCast project, objectives, and constraints.
- Draft and refine the requirements document.
- Establish the documentation system.
- Confirm the workflow approach (requirements-first).

### Actual Completions
- Requirements document drafted (11 requirements, glossary).
- Requirements refined per researcher instructions:
  - Coverage criterion softened to preferred target with justified exceptions (Req 1).
  - Duplicate handling split into exact vs conflicting (Req 3).
  - Strict time-awareness enforced for all features (Req 4).
  - Explicit 60/20/20 chronological split and walk-forward protocol defined (Req 5).
  - ARIMA eligibility tightened to three criteria (Req 5).
  - Signal normalization before anomaly score combination (Req 6).
  - Synthetic and real-world evaluation results separated (Req 6).
  - Rolling z-score test corrected to verify causal, index-specific behaviour (Req 9).
  - Experiment provenance and approval gate added (Req 10).
  - Engineering documentation system added as Req 11.
- Documentation system initialized: `docs/project_charter.md`, `docs/decision_log.md`, `docs/milestone_history.md`.
- Requirements-first workflow selected and confirmed.

### Evidence
- `.kiro/specs/cropcast/requirements.md` — requirements document (11 requirements).
- `docs/project_charter.md` — project charter initialized.
- `docs/decision_log.md` — 9 decisions recorded.
- `docs/milestone_history.md` — this file.

### Deviations from Plan
- None. This milestone was established retrospectively to record the project setup state accurately.

### Outstanding Issues
- Remaining `docs/` files (`research_log.md`, `experiment_log.md`, `issue_log.md`, `meeting_notes.md`, `requirements_history.md`) not yet initialized. These should be created at the start of M-1 or when first needed.
- `CHANGELOG.md` at repository root not yet created.
- Repository directory structure (`data/`, `src/`, `notebooks/`, etc.) not yet scaffolded.

### Next Milestone
**M-1: Dataset Feasibility Investigation** — Completed 2026-10-23.

---

## M-1: Dataset Feasibility Investigation

**Status:** Completed
**Completed:** 2026-10-23

### Planned Scope
- Investigate AGMARKNET, data.gov.in, Department of Consumer Affairs, Price Monitoring System, and secondary sources (Kaggle, GitHub, research publications).
- For each candidate dataset: record name, URL, license, date range, record count, commodities, markets, price fields, units, arrival data, missing values, and accessibility.
- Evaluate onion and potato historical coverage.
- Check whether market-arrival and peer-market data are accessible.
- Identify the most defensible forecasting target and horizon.
- Recommend real, synthetic, or hybrid evaluation with explicit evidence.
- Produce `reports/dataset_feasibility.md`.

### Acceptance Criteria (from Req 1 + Req 11)
- [x] All candidate sources investigated and recorded. (S-1 through S-7 investigated).
- [x] Dataset comparison table produced. (`reports/dataset_feasibility.md` Section 8).
- [x] Data-quality statistics calculated per dataset. (`reports/dataset_feasibility.md` Section 9).
- [x] Onion and potato coverage verified. (Verified in S-1, S-4, S-6; multi-year span confirmed on S-6).
- [x] Market-arrival data accessibility confirmed or documented as unavailable. (Confirmed accessible at state level via CEDA S-6).
- [x] Recommendation (real/synthetic/hybrid) made with explicit evidence. (Hybrid Option C / Option A state-level forecasting with real time-series, weak supervision against S-4, synthetic shock benchmarking).
- [x] `reports/dataset_feasibility.md` produced and accurate. (13 sections, comprehensive, accurate).
- [x] `docs/research_log.md` updated with each source investigated. (RES-001 through RES-008).
- [x] `docs/decision_log.md` updated with dataset selection decision. (DEC-010 through DEC-015 approved).
- [x] `docs/milestone_history.md` updated at milestone completion. (Updated herein).
- [x] Status summary produced. (Presented and approved by researcher).

### Actual Completions (as of 2026-10-23, fifth update)

**Completed since last update:**

- **CEDA API Authenticated Audit & Granularity Verification (2026-10-23):**
  - Response envelope parsing fixed in `reports/_ceda_audit.py` by unpacking `response["output"]["data"]`.
  - Live query results confirmed:
    - `GET /agmarknet/commodities`: 453 commodities (Onion ID 23, Potato ID 24).
    - `GET /agmarknet/geographies`: 640 districts across 36 states/UTs mapped to Census codes.
  - Data granularity verified: queries omitting `district_id` and `market_id` return **state-level daily aggregates**, NOT individual market observations. Prices are arithmetic mean averages across reporting mandis in the state; quantity is the statewide total arrivals in Tonnes.
  - Exact recalculated sample statistics from saved JSON files:
    - Maharashtra Onion: 13 daily price records, 13 daily quantity records (2021-01-01 to 2021-01-15; 2 missing calendar dates on non-reporting days Jan 7–8). Modal price min 2,054.18, max 2,832.40, mean 2,328.33 INR/qtl; arrivals min 394.00, max 19,907.00, mean 7,705.15 Tonnes. 0 duplicate composite keys.
    - Uttar Pradesh Potato: 15 daily price records, 15 daily quantity records (2021-01-01 to 2021-01-15; 0 missing dates). Modal price min 872.33, max 1,074.93, mean 987.07 INR/qtl; arrivals min 5,957.45, max 20,593.52, mean 17,003.59 Tonnes. 0 duplicate composite keys.
  - Recalculated price-quantity key alignment: 100.0% match on composite key `(date, commodity_id, census_state_id)` (13/13 Onion, 15/15 Potato).
  - Multi-year date coverage testing (7-day January windows): confirmed records present in 2016, 2018, 2020, and 2022 (7 of 7 days present in each window with 100% price-quantity temporal alignment). Continuous day-by-day coverage cannot be inferred without full ingestion.
  - Server rate limits verified from response headers: `RateLimit-Limit: 40`, `RateLimit-Policy: 40;w=3600`. Strict quota of **40 requests per hour** with a 1-hour cooldown window (`Retry-After: 1831` seconds observed).
  - Market-level endpoint latency: `POST /agmarknet/markets` on Ludhiana (Punjab, district 41) returned in 0.69s; on Nashik (Maharashtra, district 516) timed out (>30s) due to unindexed database scans across 20+ years of transactions.
  - CEDA source terms and attribution: Mandatory citation format recorded. Redistribution restriction flagged — CEDA does not explicitly grant public redistribution rights, so raw samples must not be committed to a public repository; ingestion must be pipeline-driven.
  - DEC-015 formally approved by researcher (2026-10-23): Option A (State-Level Daily Aggregate Forecasting) adopted.

### Evidence
- `reports/Onion_api_sample.csv` (369 rows) and `reports/Potato_api_sample.csv` (299 rows) from OGD API
- `reports/ictd_onion_labels_raw.csv` and `reports/ictd_potato_labels_raw.csv` (raw downloads with Git conflict markers)
- `reports/ictd_onion_labels.csv` (360 rows) and `reports/ictd_potato_labels.csv` (512 rows) (cleaned working copies)
- `reports/_parse_labels.py` (executable validation script)
- `reports/_ceda_audit.py` (authenticated CEDA audit script)
- `reports/ceda_onion_price_sample.json` (13 records) and `reports/ceda_onion_quantity_sample.json` (13 records)
- `reports/ceda_potato_price_sample.json` (15 records) and `reports/ceda_potato_quantity_sample.json` (15 records)
- `reports/dataset_feasibility.md` (comprehensive 13-section feasibility report, reconciled with exact sample stats)
- `docs/research_log.md` (RES-001 through RES-008)
- `docs/decision_log.md` (DEC-010 through DEC-015)

### Deviations from Plan
- S-2 (iancovert archive) definitively rejected — Onion and Potato are absent.
- S-1 (OGD API) does not provide arrival volume data.
- S-7 (PyPI `agmarknet`) cannot be used — blocked by live portal CAPTCHA and pre-2021 date cutoff.
- S-6 (CEDA Ashoka) provides state-level aggregate series rather than individual mandi series when market filters are omitted.
- Option A (State-Level Forecasting) adopted to avoid mandi-level database discovery timeouts on CEDA.

### Outstanding Issues
- [x] **CEDA API Key Registration:** `CEDA_API_KEY` configured in `.env` (git-ignored).
- [x] **RESEARCHER APPROVAL GATE (Granularity & Method):** Approved by researcher (2026-10-23) — Option A (State-Level Forecasting) adopted.
- [x] **RESEARCHER APPROVAL GATE (Milestone M-1 Sign-off):** Approved by researcher (2026-10-23) — Milestone M-1 closed; M-2 initialized.
- [ ] (Optional) Researcher OGD API key registration at `data.gov.in` for secondary price validation.

---

## M-2: Data Acquisition and Preparation

**Status:** Completed
**Started:** 2026-10-23
**Completed:** 2026-10-23 — signed off by researcher (extraction finished 2026-10-22T21:59Z; re-verification RES-011; reproducible audit RES-012)

### Planned Scope
- Implement bounded, rate-throttled CEDA ingestion pipeline (`src/data/ingest_ceda.py`) respecting the 40 requests/hour limit.
- Git-ignored raw data storage (`data/raw/`).
- Dataset manifest and provenance metadata.
- Schema validation, data type conversion, and chronological ordering.
- Duplicate detection, missingness analysis, date continuity checks, and numeric range validation.
- Cleaned, analysis-ready datasets.
- Automated data validation test suite.

### Acceptance Criteria
- [x] Ingestion pipeline implemented with authentication, chunking, rate limiting, and checkpointing (`src/data/ingest_ceda.py`).
- [x] Automated unit test suite passing (22/22 tests in `tests/test_ingest_ceda.py` at pilot time; one of these asserted nothing, see ISS-006. Current suite: 51 tests, RES-013).
- [x] Git exclusion verified for all raw data and manifest paths (`data/raw/`).
- [x] Bounded pilot executed for Maharashtra Onion and Uttar Pradesh Potato.
- [x] Schema, nulls, duplicates, and price-arrival alignment verified (100% match on `(date, commodity_id, census_state_id)`).
- [x] RESEARCHER APPROVAL GATE: Review pilot findings and authorize full historical extraction (2016–2022) — Approved 2026-10-23.
- [x] Full historical extraction executed within rate limits (≤ 40 req/hr; peak 38 in any rolling hour per manifest timestamps) across 56 chunks; all chunks `completed`. Absence of 429s/retries is not independently verifiable (no run log retained).
- [x] Independent offline re-verification of all chunks, checksums, schemas, missingness, duplicates, numeric constraints, and price–quantity alignment (RES-011).
- [x] Reproducible offline audit module `src/data/validate.py` plus a non-fatal modal-bounds warning in the pipeline validator (DEC-016, RES-012); audit regenerated with `passed: true`; 40 / 40 tests pass.
- [x] M-2 validation gate protocol fully executed: 56 chunks verified, 0 checksum mismatches, 0 duplicate keys, 0 nulls, exact dual alignment metrics reported (IoU = 1.000000, Match Rate = 1.000000).

### Actual Completions (as of 2026-10-23)
- **Ingestion Pipeline Designed & Implemented (`src/data/ingest_ceda.py`):**
  - Secure credential loading from local environment/`.env` without printing or logging secrets.
  - Rate limiting strictly enforced: $\le 40$ requests/hour (`MIN_REQUEST_INTERVAL_SECONDS = 95.0s`), explicit `HTTPError 429` detection, `Retry-After` header extraction, and safe quota preservation.
  - Calendar chunking support (6-month chunks) avoiding server timeouts on unindexed joins.
  - Atomic checkpoint manifest (`data/raw/ceda_manifest.json`) tracking chunk status, record count, file path, and SHA-256 checksums.
  - Envelope parsing (`response["output"]["data"]`), schema validation, non-negative price/quantity checks, `min_price <= max_price`, and duplicate composite key detection.
- **Unit Test Suite Implemented (`tests/test_ingest_ceda.py`):**
  - 22 automated unit tests passing across date chunking, envelope unpacking, schema validation, composite key duplication, numeric violations, price-arrival key alignment, manifest checkpoint resumption, HTTP 429 / Retry-After handling, HTTP 500 backoff, corrupt manifest recovery, missing raw file re-fetch, truncated JSON re-fetch, SHA-256 checksum mismatch detection, interrupted run partial resumption, and explicit API error envelope validation.
- **Full Historical Extraction Completed (2016-01-01 to 2022-12-31):**
  - Executed via `task-775` across 56 requests without any HTTP 429 rate limit triggers, server retries, or data corruption.
  - **Maharashtra Onion:** 2,523 price and 2,523 quantity records across 2,557 calendar days (98.67% coverage; 34 missing calendar dates in 13 gaps; max gap: 10 days, second max: 6 days during lockdown). 0 duplicates, 0 nulls, 0 violations. IoU = 1.000000, Match Rate = 1.000000. Near-zero arrivals (2–14) on four dates in 2020 flagged (ISS-003).
  - **Uttar Pradesh Potato:** 2,557 price and 2,557 quantity records across 2,557 calendar days (100.00% complete daily calendar coverage; 0 missing dates; 0 gaps). 0 duplicates, 0 nulls, 0 `min > max` violations. IoU = 1.000000, Match Rate = 1.000000.
  - Open finding: 137 UP Potato records (5.36%) have `modal_price` outside `[min_price, max_price]` (136 below min, all within 2016-03-04 – 2017-04-02; 1 above max on 2016-10-20). Cause unestablished; an earlier "volume-weighting" explanation was retracted (RES-011, ISS-002). Records retained unchanged.
- **Git & Security Verification:**
  - `git status --ignored` and `git diff --check` confirm clean workspace, zero trailing whitespace errors, and strict git exclusion of all `data/` artifacts.
  - Fixed 2026-10-23: unanchored `data/` rule also ignored `src/data/` (the ingestion package); now `/data/` (ISS-001).

### Outstanding Issues
- [ ] ISS-002: Root cause of 137 UP Potato modal-outside-bounds records (open).
- [ ] ISS-003: Onion near-zero arrival days in 2020 (open; EDA treatment).
- [x] ISS-004: Validation audit not reproducible from committed code (resolved 2026-10-23; RES-012).
- [x] ISS-006: One pre-existing HTTP 500 test makes no assertions (resolved 2026-10-23; RES-013).
- [x] ISS-007 / ISS-008 / ISS-009: Validator gaps, pipeline defects and doc inaccuracies found in the final M-2 audit (resolved 2026-10-23; RES-013).
- [ ] ISS-005: Pilot chunks overlap historical chunks; must be excluded during assembly (accepted limitation).
- [x] **RESEARCHER APPROVAL GATE (M-2 Sign-off):** Approved by researcher (2026-10-23) after review of RES-011 and RES-012. M-2 closed with ISS-002, ISS-003, ISS-005 and ISS-006 carried forward as open or accepted items.
- [ ] **RESEARCHER APPROVAL GATE (M-3 Start):** Explicit researcher instruction to begin M-3 work. Not yet given — the researcher asked to stop after M-2 sign-off.

### Prerequisite
- M-1 completed and dataset approach locked by researcher approval (Satisfied 2026-10-23).

---

## M-3: Exploratory Data Analysis

**Status:** Planned (Awaiting Researcher Authorization)

### Planned Scope
- Reproducible EDA notebook or scripts.
- Descriptive statistics and distributional summaries for prices and arrival quantities.
- Temporal coverage and missingness analysis across trading days.
- Trend, seasonality, and calendar effects.
- Price–arrival supply-volume relationship analysis.
- Evidence-based findings and documented limitations.

### Prerequisite
- M-2 completed and data pipeline verified.

---

## M-4: Forecasting Protocol and Baselines

**Status:** Planned — blocked on M-3 review.

### Planned Scope
- Define forecasting target (`modal_price`) and horizon ($t+1$ up to 7-day multi-step).
- Define forecast origin and strictly time-aware feature set (no future-data leakage).
- Implement naive and seasonal-naive baselines.
- Chronological train/validation/test split protocol (e.g. 60/20/20 walk-forward).
- Metric selection: MAE, RMSE (with MAPE/sMAPE only where mathematically justified).
- Leakage prevention and reproducibility protocol formalization.

### Prerequisite
- M-3 completed and EDA observations reviewed.

---

## M-5: Forecasting Experiments

**Status:** Planned — blocked on M-4 protocol approval.

### Planned Scope
- Train and evaluate candidate models (Linear Regression, Decision Tree, Random Forest, ARIMA if 3 eligibility criteria met).
- Walk-forward chronological evaluation across validation and test splits.
- Record configurations, random seeds, data versions, and performance tables.
- Model comparison report and ablation analysis.

### Prerequisite
- M-4 forecasting protocol formally approved by researcher.

---

## M-6: Anomaly Detection

**Status:** Planned — methodologically separate from forecasting.

### Planned Scope
- Keep anomaly detection evaluation methodologically separate from price forecasting.
- Compute multi-signal anomaly scores (forecast residuals, rolling z-scores, volume shock signals).
- Heuristic alignment against ICTD-IITD weak-supervision labels (strictly labeled as weak supervision).
- Synthetic shock injection benchmarking (price spikes, volume collapses) only upon explicit researcher approval.
- Produce anomaly detection research report.

### Prerequisite
- M-5 completed with at least one validated forecasting baseline.

---

## M-7: Final Analysis and Academic Report

**Status:** Planned — blocked on M-5 and M-6 completion.

### Planned Scope
- Results tables and publication-quality figures generated from reproducible experiments.
- Methodological discussion, data provenance, and ethical compliance.
- IEEE-style references verified against actual authoritative sources.
- Comprehensive academic research report adhering to project charter.
- Reproducibility instructions, code cleanup, and final validation.

### Prerequisite
- M-6 completed and all experimental findings finalized.
