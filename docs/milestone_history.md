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

### Actual Completions (as of 2026-10-19, updated)
- Five candidate sources investigated and recorded: OGD/AGMARKNET API, iancovert archive, DoCA/FCA PMS, ICTD-IITD, NHRDF.
- AGMARKNET schema (10 columns) confirmed from multiple independent sources.
- Onion and Potato confirmed present in S-1 (OGD API).
- License confirmed for S-1 (GODL-India — open research use).
- Dataset strategy formalised: real-world data first; synthetic only with documented justification and researcher approval (DEC-011).
- `reports/dataset_feasibility.md` produced (5 sources, comparison table, schema, recommendation).
- **S-2 (iancovert archive) — direct inspection result:** GitHub subdirectory navigation returned HTTP 404 for `/Onion` and `/Potato` paths. Commodity list in the archive remains UNCONFIRMED. Repository README confirms schema and date range but does not list the 12 crops. Local clone required to inspect CSV file names.
- **S-4 (ICTD-IITD) — direct inspection result:**
  - Onion and Potato directories confirmed present in `Data/Original/` (directly observed).
  - Onion markets: Karnataka (Bangalore, Belgaum, Davangere, Hubli/Amaragol), Maharashtra (Lasalgaon), NCT of Delhi (Azadpur), multiple UP mandis.
  - Potato states: Gujarat, Himachal Pradesh, Madhya Pradesh, NCT of Delhi, Punjab, Uttar Pradesh, West Bengal.
  - Anomaly label CSV directly fetched (`ShowAnomaliesPrice.csv` for Onion). Schema confirmed: `STARTDATE, ENDDATE, lastMonth, lastYear, SameMonth, MAXMINRATIO, STATENAME, MANDINAME`.
  - Labels are **algorithmic/rule-based** (three statistical comparisons against peer mandis and prior periods), not independently human-verified ground truth.
  - Labels cover windows from at least 2016 through 2019 in the observed sample; full date range requires complete file inspection.
  - Some files stored in Git LFS — download requires Git LFS support.
  - Data is a processed derivative with pre-applied Stineman interpolation; not suitable as primary price source.
- **OGD API (S-1):** Direct live API call not yet executed — requires free API key registration at data.gov.in. The `datagovindia` Python library provides a programmatic interface; row counts and date-range statistics must be calculated via API sampling.
- `docs/research_log.md` updated: RES-002 updated with direct inspection findings; RES-004 updated with confirmed commodity list, market names, anomaly label schema, label structure analysis, and compatibility assessment.
- `docs/decision_log.md` updated: DEC-011 added (dataset strategy formalised).

### Evidence
- `reports/dataset_feasibility.md` — feasibility report (5 sources)
- `docs/research_log.md` — RES-001 through RES-005 (RES-002 and RES-004 updated with direct inspection findings)
- `docs/decision_log.md` — DEC-010, DEC-011
- Direct observations: ICTD-IITD repository file trees browsed; `ShowAnomaliesPrice.csv` fetched and schema inspected; iancovert `/Onion` and `/Potato` paths returned 404

### Deviations from Plan
- Direct OGD API sampling not yet performed — requires API key registration. This remains a blocking item.
- iancovert commodity list not confirmed by direct file inspection — HTTP 404 on directory paths; local clone needed.

### Outstanding Issues
- [ ] **BLOCKING:** Register for data.gov.in API key and execute live OGD API sample for Onion and Potato (resource ID `9ef84268-d588-465a-a308-a864a43d0070`) to calculate actual row counts, date range, missing-value rates, duplicate counts, and date gaps.
- [ ] **BLOCKING:** Clone or browse iancovert/Agmarknet to confirm commodity list (onion and potato presence).
- [ ] Update `reports/dataset_feasibility.md` Sections 5 and 6 with independently calculated statistics once API sampling is complete.
- [ ] Inspect full date range of ICTD-IITD anomaly label files (potato labels not yet inspected).
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
