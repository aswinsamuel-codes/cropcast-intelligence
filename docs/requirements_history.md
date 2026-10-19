# CropCast — Requirements History

Changes to the requirements document are recorded here in reverse-chronological order.

---

## RH-002: Requirements Refinements and Requirement 11 Added
- **Date:** 2026-10-19
- **Changed by:** Researcher instruction
- **Summary of changes:**
  - Req 1 AC 8: Hard coverage rejection gate replaced with preferred target + shortfall assessment + researcher decision.
  - Req 3 AC 3: Single duplicate rule replaced with separate handling for exact vs conflicting duplicates.
  - Req 4 AC 6: Peer-market features restricted to prices known at or before Forecast_Origin (same-day peer prices prohibited).
  - Req 4 AC 9: Added explicit index-level leakage enforcement constraint.
  - Req 5 AC 5: ARIMA eligibility expanded from ADF test alone to three criteria (ADF + ≥200 obs + ACF/PACF support).
  - Req 5 AC 6: Chronological split made explicit as 60/20/20; walk-forward evaluation protocol defined step-by-step.
  - Req 6 AC 4: Both signals normalized before combining into Anomaly_Score.
  - Req 6 AC 6–7: Synthetic shock results separated from real-world evaluation results.
  - Req 9 AC 5: Rolling z-score test corrected to verify index-specific hand-computed values and causality, not global distribution.
  - Req 10: New requirement added — Experiment Provenance and Approval Gate.
  - Req 11: New requirement added — Engineering Documentation and Research Records.
  - Glossary: Four terms added (Decision_Log, Experiment_Log, Milestone_History, Configuration_Hash).
- **Rationale:** Researcher-directed refinements to improve scientific defensibility and methodological rigour.
- **Approval status:** Confirmed by researcher.

---

## RH-001: Initial Requirements Document Created
- **Date:** 2026-10-19
- **Changed by:** Initial spec creation
- **Summary:** Requirements document created with 9 requirements (Req 1–9) covering dataset feasibility, repository structure, data preparation, forecasting problem specification, model evaluation, anomaly detection, notebook deliverables, source module structure, and testing. Glossary established with 19 terms.
- **Approval status:** Draft — approved as starting point, subject to refinement.
