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

### Actual Completions (as of 2026-10-19, second update)
- Five candidate sources investigated and recorded: OGD/AGMARKNET API, iancovert archive, DoCA/FCA PMS, ICTD-IITD, NHRDF.
- AGMARKNET schema (10 columns) confirmed from multiple independent sources.
- Onion and Potato confirmed present in S-1 (OGD API).
- License confirmed for S-1 (GODL-India — open research use).
- Dataset strategy formalised: real-world data first; synthetic only with documented justification and researcher approval (DEC-011).
- `reports/dataset_feasibility.md` produced (5 sources, comparison table, schema, recommendation).
- **S-2 (iancovert archive) — CLOSED:** GitHub Contents API directly returned the complete list of 12 commodity directories. **Onion is NOT present. Potato is NOT present.** The archive covers exclusively pulses, legumes, and grains (Arhar, Black Gram, Cowpea, Green Gram, Green Peas, Kabuli Chana, Lentil, Maize, Rice, Soyabean, Wheat, White Peas). S-2 is rejected with no further investigation needed. Decision recorded as DEC-012.
- **S-4 (ICTD-IITD) — Potato label inspection complete:**
  - Potato anomaly label schema confirmed: `STARTDATE, ENDDATE, lastMonth, lastYear, SameMonth, MAXMINRATIO, STATENAME, MANDINAME`
  - Potato label earliest STARTDATE: 2016-01-01. File continues beyond 2017-05 (full end date requires Git LFS download).
  - Potato label markets confirmed: Punjab (5 markets), West Bengal (7 markets), Uttar Pradesh (4 markets), NCT of Delhi (Azadpur).
  - Potato states in `Data/Original/Potato/` confirmed: Gujarat, Himachal Pradesh, Madhya Pradesh, NCT of Delhi, Punjab, Uttar Pradesh, West Bengal (7 states).
  - Onion label earliest STARTDATE confirmed: 2016-01-01.
  - **Critical discrepancy noted:** Both label files start at 2016-01-01, not 2011. The paper's 2011–2021 range refers to the price data scope, not the anomaly label scope. This limits anomaly evaluation to ≥2016.
- `docs/research_log.md` updated: RES-002 updated with definitive commodity list and rejection; RES-004 updated with potato label schema, markets, date range, and states.
- `reports/dataset_feasibility.md` updated: S-2 section revised with full commodity list and rejection; S-4 section expanded with confirmed potato coverage; comparison table updated; limitations updated.

### Evidence
- `reports/dataset_feasibility.md` — feasibility report (updated with S-2 closure, S-4 potato confirmation)
- `docs/research_log.md` — RES-001 through RES-005 (RES-002 and RES-004 updated)
- `docs/decision_log.md` — DEC-010, DEC-011, DEC-012
- Direct observations: GitHub Contents API (`https://api.github.com/repos/iancovert/Agmarknet/contents/`) returned the complete 12-directory listing (no Onion, no Potato); ICTD-IITD potato ShowAnomaliesPrice.csv fetched and schema/markets confirmed; ICTD-IITD Potato directory confirmed 7 states via GitHub Contents API

### Deviations from Plan
- Direct OGD API sampling not yet performed — requires API key registration (BLOCKING).
- iancovert commodity list confirmed definitively: Onion and Potato are absent. This is a deviation from the expected use of S-2 as a supplementary source.

### Outstanding Issues
- [ ] **BLOCKING:** Register for data.gov.in API key and execute live OGD API sample for Onion and Potato (resource ID `9ef84268-d588-465a-a308-a864a43d0070`) to calculate actual row counts, date range, missing-value rates, duplicate counts, and date gaps. **Requires researcher to register an account and obtain the key.**
- [ ] **Remaining:** Download full ICTD-IITD anomaly label files via Git LFS to confirm the precise maximum ENDDATE for onion and potato labels, and verify whether label coverage predates 2016.
- [ ] Update `reports/dataset_feasibility.md` Sections 6 and 7 with independently calculated statistics once API sampling is complete.
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
