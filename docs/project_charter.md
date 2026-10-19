# CropCast — Project Charter

**Status:** Active
**Version:** 1.0
**Date Initialized:** 2026-10-19
**Course:** Data Science Ecosystem (DSE), 23CS2024
**Problem Reference:** Smart India Hackathon 2024 — SIH1647

---

## 1. Project Summary

CropCast is a reproducible, research-oriented machine-learning framework for agricultural commodity price forecasting and market-relative anomaly detection in India. It is an academic project submitted under the Data Science Ecosystem course (23CS2024) in response to SIH1647.

The system targets onion and potato wholesale prices across Indian mandi markets, using real-world historical data from public government sources. The project must demonstrate sound data science methodology — dataset auditing, statistical analysis, feature engineering, model evaluation, and anomaly detection research — before any modelling work begins.

---

## 2. Objectives

1. Determine whether adequate real-world agricultural price data exists for the proposed experiments (Milestone 1).
2. Build a cleaned, reproducible data pipeline with documented quality characteristics.
3. Define and evaluate multiple price-forecasting models under a strictly chronological, leakage-free evaluation protocol.
4. Investigate whether forecast residuals and peer-market divergence signals can flag unusual price movements (anomaly detection research component).
5. Produce all academic deliverables: feasibility report, EDA, model-comparison report, anomaly-analysis report, and final research paper.

---

## 3. Scope

**In scope:**
- Dataset discovery and feasibility auditing (AGMARKNET, data.gov.in, DoCA, PMS, secondary sources)
- Data preparation, cleaning, and exploratory data analysis
- Forecasting model development and chronological evaluation (naive baseline through random forest / ARIMA)
- Market-relative anomaly detection research (ablation study)
- Jupyter notebook deliverables and modular Python source code
- Academic documentation and research records

**Out of scope (at this stage):**
- Web dashboard or frontend application
- Real-time or production deployment
- Commodities other than onion and potato (unless evidence strongly favours a substitution)
- Any model training or synthetic data generation before dataset feasibility is confirmed

---

## 4. Constraints

- No model training or synthetic data generation may begin until Milestone 1 (dataset feasibility) is reviewed and the data approach is approved.
- All features must be constructed without future information (strict leakage prevention).
- Evaluation mode may not switch from real-world to synthetic or hybrid without explicit researcher approval based on feasibility evidence.
- No credentials, API keys, or restricted raw data may be committed to the repository.
- All file paths must be loaded from configuration; no hardcoded absolute paths.
- All stochastic operations must use a fixed, configurable random seed.

---

## 5. Deliverables

| ID  | Deliverable                        | Phase        | Status    |
|-----|------------------------------------|--------------|-----------|
| D-A | Dataset Feasibility Report         | Milestone 1  | Planned   |
| D-B | Cleaned Data Pipeline + EDA Report | Milestone 2  | Planned   |
| D-C | Forecasting Model Comparison Report| Milestone 3  | Planned   |
| D-D | Anomaly Detection Analysis Report  | Milestone 4  | Planned   |
| D-E | Final Academic Report              | Milestone 5  | Planned   |
| D-F | README with Reproducibility Guide  | All phases   | Planned   |

---

## 6. Team and Roles

> [Team composition and roles to be recorded here when confirmed.]

---

## 7. Approval and Review

| Action                              | Status      | Date       |
|-------------------------------------|-------------|------------|
| Requirements drafted                | Verified    | 2026-10-19 |
| Requirements refinements applied    | Verified    | 2026-10-19 |
| Documentation system established    | Verified    | 2026-10-19 |
| Dataset feasibility approved        | Pending     | —          |
| Technical design approved           | Pending     | —          |
| Data approach locked                | Pending     | —          |

---

## 8. Notes

- This charter reflects the project state as of 2026-10-19.
- The final dataset, modelling approach, and experimental results are not yet confirmed.
- All status labels in this document refer to verified actions only. Planned work is labelled "Planned" and must not be described as complete.
