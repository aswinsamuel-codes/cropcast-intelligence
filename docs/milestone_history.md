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
| M-0 | Project Setup and Requirements          | Completed   | Pre-development    |
| M-1 | Dataset Feasibility Investigation       | In Progress | Phase 1            |
| M-2 | Data Preparation and EDA                | Planned     | Phase 3            |
| M-3 | Forecasting Models and Evaluation       | Planned     | Phase 5            |
| M-4 | Anomaly Detection Research              | Planned     | Phase 6            |
| M-5 | Final Report and Academic Deliverables  | Planned     | Phase 8            |

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
**M-1: Dataset Feasibility Investigation** — Investigate real agricultural commodity price datasets, inspect actual schemas and records, calculate data-quality statistics, verify historical coverage for onion and potato, check market-arrival and peer-market data availability, and produce `reports/dataset_feasibility.md`. Do not begin model training or generate synthetic data.

---

## M-1: Dataset Feasibility Investigation

**Status:** In Progress

### Planned Scope
- Investigate AGMARKNET, data.gov.in, Department of Consumer Affairs, Price Monitoring System, and secondary sources (Kaggle, GitHub, research publications).
- For each candidate dataset: record name, URL, license, date range, record count, commodities, markets, price fields, units, arrival data, missing values, and accessibility.
- Evaluate onion and potato historical coverage.
- Check whether market-arrival and peer-market data are accessible.
- Identify the most defensible forecasting target and horizon.
- Recommend real, synthetic, or hybrid evaluation with explicit evidence.
- Produce `reports/dataset_feasibility.md`.

### Acceptance Criteria (from Req 1 + Req 11)
- [ ] All candidate sources investigated and recorded.
- [ ] Dataset comparison table produced.
- [ ] Data-quality statistics calculated per dataset.
- [ ] Onion and potato coverage verified.
- [ ] Market-arrival data accessibility confirmed or documented as unavailable.
- [ ] Recommendation (real/synthetic/hybrid) made with explicit evidence.
- [ ] `reports/dataset_feasibility.md` produced and accurate.
- [ ] `docs/research_log.md` updated with each source investigated.
- [ ] `docs/decision_log.md` updated with dataset selection decision.
- [ ] `docs/milestone_history.md` updated at milestone completion.
- [ ] Status summary produced.

### Actual Completions (as of 2026-10-20, third update)

**Completed since last update:**

- **OGD API (S-1) — directly sampled (2026-10-20):**
  - Representative Onion and Potato records retrieved from resource `9ef84268-d588-465a-a308-a864a43d0070`.
  - Files saved: `reports/Onion_api_sample.csv` (369 rows), `reports/Potato_api_sample.csv` (299 rows), single date 20/10/2026.
  - Confirmed schema (10 columns): `state, district, market, commodity, variety, grade, arrival_date, min_price, max_price, modal_price`.
  - **CRITICAL: No `Arrivals (Tonnes)` column in this OGD resource.** This was previously assumed present; it is absent. The portal schema and the OGD API resource schema differ.
  - Onion sample: 213 pure Onion rows + 156 Onion Green across 18 states, 222 distinct markets. 0 nulls, 0 duplicates, 1 suspicious 0.01 placeholder (Punjab/Tarntaran/Patti APMC — variety="Other", grade="Non-FAQ"). Modal price range: 1,800–7,500 INR/quintal.
  - Potato sample: 230 pure Potato rows + 69 Sweet Potato across 17 states, 236 distinct markets. 0 nulls, 0 duplicates, 1 suspicious 0.01 placeholder (Punjab/Tarntaran/Patti APMC — variety="Potato", grade="Local"). Modal price range: 350–7,600 INR/quintal.
  - Grade and Variety columns present (absent from some prior schema descriptions).

- **S-2 (iancovert archive) — DEFINITIVELY CLOSED (2026-10-19):**
  - GitHub API recursive tree returned complete 12-commodity list. Neither Onion nor Potato is present.
  - Archive covers: Arhar, Black Gram, Cowpea, Green Gram, Green Peas, Kabuli Chana, Lentil, Maize, Rice, Soyabean, Wheat, White Peas (2008–2017, ~297 MB total).
  - DEC-012 recorded. S-2 rejected with no further investigation.

- **S-4 (ICTD-IITD) — fully characterised (2026-10-19):**
  - Onion + Potato both confirmed in `Data/Original/` (multiple states each).
  - Anomaly label schema confirmed for both commodities: `STARTDATE, ENDDATE, lastMonth, lastYear, SameMonth, MAXMINRATIO, STATENAME, MANDINAME`.
  - Potato label markets confirmed: Punjab (5), West Bengal (7), UP (4), Delhi (Azadpur) — 17 state+market combos.
  - Label date range: earliest STARTDATE 2016-01-01 for both Onion and Potato.
  - Labels are algorithmic/rule-based (three statistical comparisons), not independently human-verified ground truth.

- **Documentation updated:** `docs/research_log.md` RES-001 updated with full observed schema and quality statistics; RES-002 updated with confirmed commodity list and rejection; DEC-012 and DEC-013 recorded.

### Evidence
- `reports/Onion_api_sample.csv` — 369 rows, directly retrieved from OGD API, 20/10/2026
- `reports/Potato_api_sample.csv` — 299 rows, directly retrieved from OGD API, 20/10/2026
- `docs/research_log.md` — RES-001 through RES-005 (RES-001 and RES-002 updated with directly observed findings)
- `docs/decision_log.md` — DEC-010 through DEC-013
- GitHub API tree inspection (2026-10-19): confirms iancovert archive contains no Onion or Potato
- Python script analysis of CSV samples (2026-10-20): confirms schema, row counts, quality statistics

### Deviations from Plan
- S-2 (iancovert archive) cannot be used as supplementary source — Onion and Potato are absent.
- OGD API resource `9ef84268-d588-465a-a308-a864a43d0070` does not provide arrival volume data. This affects Req 4 AC 5 and Req 6 AC 7 (supply-related features and anomaly signals).
- Historical date-range statistics for the full dataset (multiple years) not yet calculated — the sample is a single day's records only. Full historical coverage requires a multi-date API query.

### Outstanding Issues
- [ ] **RESEARCHER INPUT REQUIRED (arrival data strategy):** The OGD resource has no arrivals column. Options: (a) investigate whether AGMARKNET portal (agmarknet.gov.in) provides a reproducible arrivals data source; (b) use NHRDF for key markets; (c) accept absence of arrival data and restrict experiments accordingly. **This is a scope decision requiring researcher approval before M-1 can close.**
- [ ] **Remaining:** Execute a multi-date historical API query to confirm the actual date range and reporting regularity per market (monthly sampling recommended, 2015–2026). This requires the API key.
- [ ] **Remaining:** Update `reports/dataset_feasibility.md` Sections 5 and 6 to reflect the confirmed OGD schema (no arrivals, 10 columns), sample quality statistics, and revised recommendation.
- [ ] Researcher review and approval of updated feasibility report before proceeding to technical design.

---

## M-2: Data Preparation and EDA

**Status:** Planned — blocked on M-1 approval.

### Planned Scope
- Schema validation and type conversion.
- Date parsing and chronological sorting.
- Exact and conflicting duplicate detection and resolution.
- Missing-value analysis and reporting.
- Descriptive statistics per commodity and market.
- Trend and seasonality decomposition.
- Correlation analysis across peer markets.
- EDA figures: time-series plots, box plots, correlation heatmaps, missingness heatmaps.
- Data dictionary and documented limitations.

### Prerequisite
- M-1 completed and dataset approach locked by researcher approval.

---

## M-3: Forecasting Models and Evaluation

**Status:** Planned — blocked on M-2 completion.

### Planned Scope
- Define forecasting problem (target, horizon, feature set).
- Implement naive and seasonal-naive baselines.
- Implement linear regression and decision-tree regression.
- Implement random forest (if ≥500 training observations).
- Implement ARIMA (if three eligibility criteria met).
- Apply 60/20/20 chronological split and walk-forward evaluation.
- Compute MAE, RMSE, MAPE per model, commodity, and market.
- Produce model-comparison report.

### Prerequisite
- M-2 completed and data pipeline verified.

---

## M-4: Anomaly Detection Research

**Status:** Planned — blocked on M-3 completion.

### Planned Scope
- Compute forecast residuals.
- Compute rolling residual z-scores.
- Compute peer-market divergence signal.
- Normalize both signals, combine into Anomaly_Score.
- Ablation study: residual-only vs residual+peer vs combined.
- Evaluation against ground-truth labels (if available) or synthetic shock injection (separate evaluation).
- Produce anomaly-analysis report.

### Prerequisite
- M-3 completed with at least one validated forecasting model.

---

## M-5: Final Report and Academic Deliverables

**Status:** Planned — blocked on M-4 completion.

### Planned Scope
- Final academic report with verified references, methodology, actual results, limitations, and future scope.
- README with complete reproducibility instructions.
- All figures and tables.
- All documentation files up to date.

### Prerequisite
- M-4 completed and all experiments finalized.
