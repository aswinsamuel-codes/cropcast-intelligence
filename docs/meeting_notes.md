# CropCast — Meeting and Review Notes

Significant reviews, feedback sessions, and milestone sign-off discussions are recorded here.

---

## Entry Template

```
### MTG-NNN: [Topic / Review Name]
- **Date:** YYYY-MM-DD
- **Participants:** [roles or names]
- **Purpose:** [milestone review / feedback / planning / other]
- **Key discussion points:**
  - [Point 1]
  - [Point 2]
- **Decisions made:** [reference DEC-NNN entries where applicable]
- **Action items:**
  - [ ] [Action] — [owner] — [due date]
- **Next review:** [planned date or trigger]
```

---

## Notes

### MTG-001: Requirements Review and Refinement
- **Date:** 2026-10-19
- **Participants:** Researcher
- **Purpose:** Review initial requirements draft and apply scientific rigor refinements.
- **Key discussion points:**
  - Coverage criterion softened from hard rejection to preferred target with justified exceptions.
  - Duplicate handling split into exact vs conflicting categories.
  - Strict time-awareness enforced for all features to prevent leakage.
  - Chronological split and walk-forward protocol made explicit (60/20/20).
  - ARIMA eligibility tightened to three criteria.
  - Signal normalization before anomaly score combination.
  - Synthetic and real-world evaluation results separated.
  - Rolling z-score test corrected.
  - Experiment provenance and approval gate added (Req 10).
  - Engineering documentation system added as Req 11.
- **Decisions made:** See DEC-004 through DEC-009.
- **Action items:**
  - [x] Apply all refinements to requirements document — Completed 2026-10-19.
  - [x] Initialize docs/ directory — Completed 2026-10-19.
  - [ ] Begin Milestone 1: Dataset Feasibility Investigation.
- **Next review:** After `reports/dataset_feasibility.md` is produced and reviewed.
