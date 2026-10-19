# CropCast — Changelog

All notable changes to the CropCast project are recorded here in reverse-chronological order.

**Status labels:** `[Completed]` — verified done. `[Planned]` — intended but not yet done. `[In Progress]` — actively being worked on.

---

## [Unreleased]

### In Progress
- Milestone 1: Dataset feasibility investigation
  - S-4 (ICTD-IITD) anomaly labels directly inspected and assessed — algorithmic, not independent ground truth
  - S-2 (iancovert) commodity list still unconfirmed — HTTP 404 on subdirectory paths; local clone needed
  - OGD API live sampling still pending — requires free API key registration
  - Dataset strategy formalised (DEC-011): real-world data first; synthetic only with documented approval

### Planned
- OGD API key registration and live sampling of resource `9ef84268-d588-465a-a308-a864a43d0070`
- iancovert repository clone to confirm commodity list
- Update `reports/dataset_feasibility.md` with independently calculated statistics
- Researcher approval of updated feasibility report
- Repository directory scaffolding, `requirements.txt`, `README.md`

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
