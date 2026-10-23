# CropCast — Changelog

All notable changes to the CropCast project are recorded here in reverse-chronological order.

**Status labels:** `[Completed]` — verified done. `[Planned]` — intended but not yet done. `[In Progress]` — actively being worked on.

---

## [Unreleased]

### In Progress
- Phase 0–2 recovery, literature review and dataset freeze (2026-10-23)
  - Project `.venv`, pinned `requirements.txt`, `configs/config.json` with `src/config.py` (DEC-018).
  - Stored M-2 audit regenerated with the current validator: passes, with 2 warnings.
  - `reports/literature_review.md`: 21 references, each verified against its registry record.
  - Frozen dataset v1 via `src/data/dataset.py` (DEC-019), with 13 tests in `tests/test_dataset.py`. The suite now has 64 tests.
  - Peer-market requirements recorded as not applicable (DEC-017).
  - Corrected the unverified CEDA logo-requirement claim in the feasibility report.

### Planned
- Milestone 3: Exploratory Data Analysis (EDA)
  - Modular analysis scripts under `src/analysis/`.
  - Processed dataset assembly module under `src/data/dataset.py`.
  - Descriptive, temporal, missingness, and outlier investigations.
  - Publication-quality visualizations under `reports/figures/`.
  - Detailed academic report at `reports/eda_report.md`.

### Completed
- Milestone 2: Data Acquisition and Preparation — signed off by researcher (2026-10-23)
  - Full historical extraction (2016-01-01 to 2022-12-31) executed via `task-775` across 56 endpoint chunks for Maharashtra Onion and Uttar Pradesh Potato; finished 2026-10-22T21:59Z.
  - Within CEDA rate limits: 92–98s spacing between saved chunks, peak 38 requests in any rolling hour (≤ 40). No run log retained, so absence of 429s/retries is not independently verified.
  - SHA-256 manifest checksums re-verified across all 56 historical and 4 pilot files (0 mismatches).
  - Validation: 0 duplicate keys, 0 nulls, 0 schema violations, 100.0% exact price–quantity date alignment (IoU = 1.000000) for both series.
  - Calendar coverage: 98.67% (2,523 days, 34 missing in 13 gaps) for Maharashtra Onion; 100.00% (2,557 days, 0 gaps) for Uttar Pradesh Potato.
  - Open: 137 UP Potato records with `modal_price` outside `[min_price, max_price]`, confined to 2016-03 – 2017-04; cause unestablished (ISS-002). Previous "volume-weighting" explanation retracted.
  - Reconciliation (RES-011) corrected the onion single-day gap count (6, not 5) and the request-spacing figures.
  - Fixed: `.gitignore` rule `data/` also ignored `src/data/`; anchored to `/data/` (ISS-001).
  - Added `src/data/validate.py`: offline, reproducible M-2 audit (`python -m src.data.validate --output data/raw/m2_validation_audit.json`); regenerated audit passes and matches the earlier ad-hoc audit on every shared field (DEC-016, RES-012).
  - Pipeline validator now reports `modal_price` outside `[min_price, max_price]` as a non-fatal warning (`modal_bounds_warnings`).
  - Test suite: 40 tests passing (16 new in `tests/test_validate.py`, 2 new in `tests/test_ingest_ceda.py`; corrected from "18" on 2026-10-23); `git diff --check` clean. Pre-existing HTTP 500 test found to assert nothing (ISS-006).
- M-2 post-sign-off remediation from the final audit (2026-10-23; RES-013)
  - `src/data/validate.py`: hard failure on manifest entries not `completed` or not `is_valid`, and on empty chunks. New warnings for chunks covering fewer than 90% of their calendar days, zero values, and values beyond 100× of the field median (screening heuristic).
  - `src/data/ingest_ceda.py`:
    - Empty API responses are saved with manifest `status: "empty"` instead of `completed`.
    - Checksum-verified chunks with source-data violations are no longer re-downloaded.
    - Read timeouts and connection errors are retried.
    - A corrupt manifest is now actually backed up before being recreated.
  - ISS-006 fixed: the HTTP 500 backoff test now calls `make_request` and asserts the retry.
  - 51 tests pass: 11 new (6 validator, 5 pipeline) and 2 extended. Against the previous code, 10 of the new tests and the extended corrupt-manifest test fail. The remaining new test guards kept behaviour.
  - Docs: corrected test counts and the `_ceda_audit.py` description; added `docs/environment.md`.
- Milestone 1: Research and Dataset Feasibility (2026-10-23)
  - All 11 acceptance criteria verified and approved by researcher.
  - DEC-015 formally approved: Option A (State-Level Daily Aggregate Forecasting on CEDA Ashoka) for Maharashtra Onion (`state_id: 27`, `commodity_id: 23`) and Uttar Pradesh Potato (`state_id: 9`, `commodity_id: 24`).
  - Proposed historical window: 2016-01-01 to 2022-12-31, subject to bounded pilot validation.
  - CEDA strict rate limit policy (≤40 req/hr) acknowledged and incorporated into pipeline architecture.
  - Raw datasets excluded from Git (`.gitignore` updated and verified).

---

## 2026-10-23

### Added [Completed]
- `reports/_ceda_audit.py` — authenticated CEDA API audit script with response envelope unpacking and composite key alignment. *(Corrected 2026-10-23: an earlier version of this entry also claimed "rate limit diagnostics"; the script contains no rate-limit logic or throttling.)*
- `reports/ceda_onion_price_sample.json`, `reports/ceda_onion_quantity_sample.json` (13 records each) — bounded state-aggregate samples for Maharashtra Onion.
- `reports/ceda_potato_price_sample.json`, `reports/ceda_potato_quantity_sample.json` (15 records each) — bounded state-aggregate samples for Uttar Pradesh Potato.
- `reports/ictd_onion_labels_raw.csv` and `reports/ictd_potato_labels_raw.csv` — raw downloads with original Git conflict markers preserved.
- `reports/ictd_onion_labels.csv` (360 rows) and `reports/ictd_potato_labels.csv` (512 rows) — cleaned working copies of ICTD anomaly labels.
- `reports/_parse_labels.py` — automated audit and validation script verifying bit-level SHA-256 and byte-length match against Git LFS pointer, schema, and statistics.
- `docs/research_log.md` entries RES-006 (CEDA Ashoka Agri-Market Data Portal), RES-007 (`agmarknet` PyPI package & Portal REST API), and RES-008 (CEDA Audit Review, Granularity Verification, and Operational Constraints).
- `docs/decision_log.md` entries DEC-014 (CEDA Ashoka prioritized over OGD and PyPI `agmarknet`) and DEC-015 (Provisional Direction on Data Granularity — Option A State-Level Forecasting).
- `.env.example` — template for configuring local credentials.

### Changed [Completed]
- `reports/dataset_feasibility.md` — comprehensive update with exact recalculated sample values, composite key specifications `(date, commodity_id, census_state_id)`, multi-year coverage findings, CEDA academic attribution requirements, redistribution restriction flagging, and operational rate limits (40 req/hr).
- `reports/_ceda_audit.py` — enhanced to compute alignment on composite key and report exact statistical distributions without hardcoded assumptions.
- `docs/research_log.md` — RES-004 updated with full anomaly label audit; RES-008 added with granularity verification and rate limit findings.
- `docs/milestone_history.md` — Milestone M-1 updated with live audit evidence, operational constraints, DEC-015, and pending approval gates.

### Current State
- Feasibility investigation for all 7 candidate sources complete.
- S-6 (CEDA Ashoka) confirmed functional at the state-aggregate level with 100% price-quantity temporal alignment across 2016–2022 test windows.
- CEDA operational constraints documented: strict 40 requests/hour rate limit and market endpoint latency for large districts (e.g. Nashik).
- S-4 labels validated as weak supervision benchmark (not price time-series).
- S-7 (PyPI package) confirmed unusable due to live CAPTCHA blocking.
- Awaiting researcher decision on data granularity (state aggregate vs market-level) and approval gate sign-off before M-2 scaffolding begins.

---

## 2026-10-19

### Added [Completed]
- `docs/project_charter.md` — project charter initialized with objectives, scope, constraints, deliverables, and approval status.
- `docs/decision_log.md` — decision log initialized with 9 decisions recorded (DEC-001 through DEC-009).
- `docs/milestone_history.md` — milestone history initialized with M-0 through M-5.
- `docs/research_log.md` — research log stub created; to be populated during Milestone 1.
- `docs/experiment_log.md` — experiment log stub created; to be populated during Milestone 3.
- `docs/issue_log.md` — issue log stub created; to be populated as issues arise.
- `docs/meeting_notes.md` — meeting notes initialized with MTG-001 (requirements review).
- `docs/requirements_history.md` — requirements history initialized with RH-001 and RH-002.
- `CHANGELOG.md` — this file.

### Changed [Completed]
- Requirements document refined (RH-002): coverage criterion softened, duplicate handling split, strict time-awareness enforced, 60/20/20 split and walk-forward protocol made explicit, ARIMA eligibility tightened, signal normalization added, evaluation results separated, rolling z-score test corrected.
- Requirements document extended with Requirement 10 (Experiment Provenance and Approval Gate) and Requirement 11 (Engineering Documentation and Research Records).
- Glossary extended with four new terms.

### Current State
- Requirements: drafted and refined (11 requirements). Not yet approved for design phase.
- Dataset feasibility: not yet investigated. Milestone 1 is the next planned work.
- Technical design: not started.
- Implementation: not started.
- Final dataset, modelling approach, and experimental results: not yet confirmed.

---

## 2026-10-19 (continued — Milestone 1)

### Added [In Progress]
- `reports/dataset_feasibility.md` — dataset feasibility report produced (5 sources investigated, schema verified, comparison table, recommendation issued). Direct API verification still pending before report is finalized.
- `docs/research_log.md` — RES-001 through RES-005 populated for all five investigated sources.
- `docs/decision_log.md` — DEC-010 added (preliminary dataset selection: AGMARKNET OGD API as primary source).
- `docs/milestone_history.md` — M-1 updated to In Progress with actual completions, evidence, deviations, and outstanding issues.

### Current State
- Feasibility report produced: 5 sources investigated, AGMARKNET OGD API recommended as primary source.
- Direct API sampling not yet performed: exact row counts, missing-value rates, and duplicate statistics for onion/potato are not yet independently calculated.
- M-1 acceptance criteria: partially met. Blocking items: direct data verification and researcher approval.
- Technical design: not started (blocked on M-1 approval).
- Implementation: not started.
