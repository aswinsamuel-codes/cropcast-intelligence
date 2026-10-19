# CropCast — Decision Log

Significant architectural, methodological, and data-source decisions are recorded here in chronological order.

Each entry records: date, context, alternatives considered, rationale, outcome, and approval status.

---

## Decision Template

```
### DEC-NNN: [Short Title]
- **Date:** YYYY-MM-DD
- **Context:** [What situation or question prompted this decision]
- **Alternatives considered:**
  1. [Option A]
  2. [Option B]
- **Rationale:** [Why the chosen option was selected]
- **Outcome:** [The decision made]
- **Approval status:** [Approved by / Pending / Rejected]
- **Related files/refs:** [Links to requirements, reports, or code if applicable]
```

---

## Decisions

### DEC-001: Requirements-First Workflow Selected
- **Date:** 2026-10-19
- **Context:** When creating the CropCast spec, the workflow approach had to be chosen: start from requirements or start from technical design.
- **Alternatives considered:**
  1. Requirements-first: document business/research needs before technical design.
  2. Design-first: document technical architecture first, then derive requirements.
- **Rationale:** The project starts from a research brief (SIH1647) with defined objectives but no fixed technical implementation. Documenting requirements first ensures the modelling choices remain grounded in the research goals.
- **Outcome:** Requirements-first workflow adopted. Requirements document created and refined before any design or implementation work.
- **Approval status:** Approved (researcher confirmed).
- **Related files/refs:** `.kiro/specs/cropcast/requirements.md`

---

### DEC-002: Onion and Potato as Primary Commodity Candidates
- **Date:** 2026-10-19
- **Context:** The project brief specifies onion and potato as initial commodity candidates but allows substitution if another commodity has substantially better data quality.
- **Alternatives considered:**
  1. Onion and potato (as specified in brief).
  2. Another commodity with better data availability (to be determined by feasibility audit).
- **Rationale:** Following the brief's guidance. Substitution requires explicit evidence from the dataset feasibility audit and documented justification before any change is made.
- **Outcome:** Onion and potato adopted as primary targets for Milestone 1 investigation. Subject to revision after feasibility audit.
- **Approval status:** Approved (per project brief).
- **Related files/refs:** `reports/dataset_feasibility.md` (planned)

---

### DEC-003: No Model Training Before Dataset Feasibility Confirmed
- **Date:** 2026-10-19
- **Context:** The project brief explicitly states that model training and synthetic data generation must not begin until real-world data adequacy has been established.
- **Alternatives considered:**
  1. Proceed with model development in parallel with data investigation.
  2. Block all model development until feasibility is confirmed and reviewed.
- **Rationale:** Starting models on unvalidated data risks wasted effort and scientifically unsound results. The feasibility gate ensures the modelling scope is appropriate for the actual available data.
- **Outcome:** Hard stop enforced: no model training or synthetic data generation until Milestone 1 is reviewed and the data approach is explicitly approved.
- **Approval status:** Approved (per project brief and requirements).
- **Related files/refs:** `requirements.md` Req 1 AC 8, Req 10 AC 1

---

### DEC-004: Coverage Criterion Treated as Preferred Target, Not Hard Rejection
- **Date:** 2026-10-19
- **Context:** Initial requirements used a hard threshold (≥3 years, ≥3 markets) as an automatic rejection gate. This was revised during requirements refinement.
- **Alternatives considered:**
  1. Hard threshold: automatically reject datasets below the coverage target.
  2. Preferred target: document shortfalls, assess sufficiency, present evidence to researcher for final decision.
- **Rationale:** A hard threshold could unnecessarily eliminate datasets that are adequate for the specific experiments planned. The researcher is better positioned to judge adequacy once the evidence is documented.
- **Outcome:** Three-year, three-market coverage remains the preferred feasibility target. Shortfalls are documented and assessed; the researcher makes the final call.
- **Approval status:** Approved (researcher confirmed during requirements refinement).
- **Related files/refs:** `requirements.md` Req 1 AC 8

---

### DEC-005: Conflicting Duplicates Require Researcher Resolution
- **Date:** 2026-10-19
- **Context:** Initial requirements automatically retained the first record when duplicate keys with differing prices were found. This was revised.
- **Alternatives considered:**
  1. Retain first occurrence automatically.
  2. Flag conflicting duplicates and halt processing pending researcher resolution.
- **Rationale:** Automatically selecting the first record when prices conflict could silently introduce incorrect values. The researcher must decide the correct resolution strategy for each source.
- **Outcome:** Exact duplicates (same prices) are safely dropped. Conflicting duplicates are flagged with full details and processing halts until an explicit resolution decision is provided.
- **Approval status:** Approved (researcher confirmed during requirements refinement).
- **Related files/refs:** `requirements.md` Req 3 AC 3

---

### DEC-006: Strict Time-Awareness Enforced for All Features
- **Date:** 2026-10-19
- **Context:** Peer-market features initially allowed same-day prices, which could constitute leakage if those prices are not yet reported at the forecast origin.
- **Alternatives considered:**
  1. Allow same-day peer prices (simpler, but risks leakage).
  2. Use only prices known at or before the forecast origin for all features, including peer markets.
- **Rationale:** Using same-day peer data that is not yet available at forecast time is a form of look-ahead leakage. Strict time-awareness is required for scientifically valid evaluation.
- **Outcome:** All features must use only data with index ≤ forecast origin t. Peer-market features use the most recent available price known at or before the forecast origin.
- **Approval status:** Approved (researcher confirmed during requirements refinement).
- **Related files/refs:** `requirements.md` Req 4 AC 6, AC 9

---

### DEC-007: ARIMA Selection Requires Three Criteria
- **Date:** 2026-10-19
- **Context:** Initial requirements selected ARIMA solely based on an ADF stationarity test. This was identified as insufficient.
- **Alternatives considered:**
  1. ADF test alone as the ARIMA eligibility criterion.
  2. ADF test + series length (≥200 observations after differencing) + ACF/PACF visual support.
- **Rationale:** An ADF test alone does not confirm that an ARIMA model is appropriate. Series length and autocorrelation structure must also support it.
- **Outcome:** ARIMA is implemented only when all three criteria are met: ADF stationarity at 5% after differencing, ≥200 observations, and ACF/PACF patterns consistent with an ARIMA structure.
- **Approval status:** Approved (researcher confirmed during requirements refinement).
- **Related files/refs:** `requirements.md` Req 5 AC 5

---

### DEC-008: Evaluation Mode Transition Requires Explicit Approval
- **Date:** 2026-10-19
- **Context:** The system needed a safeguard against automatically switching to synthetic or hybrid evaluation without the researcher reviewing the evidence.
- **Alternatives considered:**
  1. Automatic transition based on coverage thresholds.
  2. Pause and require explicit researcher approval based on feasibility report evidence.
- **Rationale:** Automatic transitions risk premature or unjustified abandonment of real-world data. A documented approval gate ensures methodological transparency.
- **Outcome:** Requirement 10 added: pipeline pauses when feasibility evidence suggests data may be insufficient, and requires explicit researcher approval before any mode transition. Decision is logged with timestamp and evidence.
- **Approval status:** Approved (researcher confirmed during requirements refinement).
- **Related files/refs:** `requirements.md` Req 10

---

### DEC-009: Engineering Documentation System Established
- **Date:** 2026-10-19
- **Context:** The project needed a permanent, traceable record for academic submission, research review, and reproducibility. Documentation was not previously formalized as a requirement.
- **Alternatives considered:**
  1. Ad-hoc notes scattered across notebooks and README.
  2. Structured docs/ directory with defined files for each record type, maintained throughout development.
- **Rationale:** Academic projects require traceable records of decisions, experiments, and findings. A structured system established early prevents incomplete retrospective documentation.
- **Outcome:** Requirement 11 added. `docs/` directory initialized with project charter, decision log, and milestone history. Remaining docs files to be initialized as work progresses.
- **Approval status:** Approved (researcher confirmed).
- **Related files/refs:** `requirements.md` Req 11, `docs/project_charter.md`, `docs/milestone_history.md`

---

### DEC-010: AGMARKNET OGD API Selected as Primary Dataset Source (Preliminary)
- **Date:** 2026-10-19
- **Context:** M-1 dataset investigation identified five candidate sources. A recommendation must be made before proceeding to technical design or model development.
- **Alternatives considered:**
  1. AGMARKNET via OGD API (S-1): authoritative, licensed, mandi-level, includes arrivals, requires API key.
  2. iancovert/Agmarknet archive (S-2): pre-assembled, no key, but frozen at June 2017.
  3. DoCA/FCA PMS (S-3): retail/city-level, CAPTCHA barrier, no arrivals.
  4. ICTD-IITD Commodity_Analysis (S-4): processed derivative, has anomaly labels, not authoritative.
  5. NHRDF (S-5): onion/potato specialist, web form only, reproducibility uncertain.
- **Rationale:** S-1 is the authoritative national source with the correct schema (Modal_Price, Arrivals), confirmed onion and potato coverage, open license for research use, and programmatic access via free API. The other sources are either methodologically incompatible (S-3), derived/processed (S-4), access-constrained (S-5), or date-limited (S-2).
- **Outcome:** AGMARKNET via OGD API (S-1) recommended as primary dataset. S-2 as supplementary historical archive (2008–2017), pending commodity confirmation. S-4 as secondary reference for anomaly labels. Decision is preliminary — locked after researcher approval of feasibility report.
- **Approval status:** Pending researcher review of `reports/dataset_feasibility.md`.
- **Related files/refs:** `reports/dataset_feasibility.md`, `docs/research_log.md` RES-001 through RES-005

---

### DEC-011: Dataset Strategy Formalised — Real-World Data First, Synthetic as Last Resort
- **Date:** 2026-10-19
- **Context:** Following conditional approval of the preliminary recommendation (DEC-010), the researcher formalised the data strategy for M-1 and all subsequent phases.
- **Alternatives considered:**
  1. Proceed with synthetic data now to unblock model development.
  2. Pursue real-world data exhaustively first; synthetic only if real data is demonstrably insufficient.
  3. Hybrid from the start (real data for forecasting, synthetic shocks for anomaly detection).
- **Rationale:** Real-world data is the scientifically correct choice for an academic forecasting project. Switching to synthetic data prematurely would undermine the credibility of all performance claims. The hybrid option remains available for the anomaly detection component but should not be assumed until real data coverage is confirmed.
- **Outcome:**
  - Primary: AGMARKNET / data.gov.in mandi-price data.
  - Backup: iancovert historical archive (2008–2017), subject to commodity confirmation and licensing verification.
  - Research reference: ICTD-IITD dataset, subject to anomaly label verification and compatibility check.
  - Alternative: DoCA/FCA price data if mandi-level sources prove unsuitable (methodological justification required).
  - Synthetic data: permitted only after: (a) documenting why real-data options failed, (b) identifying precisely which research requirements cannot be met, (c) proposing a documented synthetic design with explicit assumptions, (d) obtaining researcher approval, and (e) recording the decision here.
  - Synthetic results must always be labelled separately and never presented as real-world forecasting performance.
  - M-1 remains In Progress until all verification tasks are complete and acceptance criteria are met.
- **Approval status:** Approved by researcher (2026-10-19).
- **Related files/refs:** `reports/dataset_feasibility.md`, `docs/research_log.md`, `requirements.md` Req 10

---

### DEC-012: iancovert/Agmarknet Archive Rejected — Onion and Potato Absent
- **Date:** 2026-10-19
- **Context:** S-2 (iancovert/Agmarknet archive) was previously listed as a supplementary source pending direct commodity confirmation, because the README mentioned "12 food products" without listing them. A direct GitHub Contents API call was made to enumerate the repository's root-level directories.
- **Evidence:** GitHub Contents API (`https://api.github.com/repos/iancovert/Agmarknet/contents/`) returned exactly 12 commodity directories + README:
  Arhar (Tur-Red Gram), Black Gram (Urd Beans), Cowpea (Lobia-Karamani), Green Gram (Moong), Green Peas, Kabuli Chana (Chickpeas-White), Lentil (Masur), Maize, Rice, Soyabean, Wheat, White Peas.
  No Onion directory. No Potato directory. The archive was independently confirmed to cover exclusively pulses, legumes, and cereal grains.
- **Alternatives considered:**
  1. Mark as "needs further confirmation" and proceed to clone the repository locally.
  2. Accept the GitHub Contents API listing as definitive — it returns every root-level object in the repository; absence of Onion and Potato directories is conclusive.
- **Rationale:** The GitHub Contents API is authoritative for the repository's file structure. There are no alternative locations in this repository where commodity data could be stored without appearing in this listing (all CSV files are in top-level commodity directories as stated in the README). Cloning would confirm the same result at additional cost and time with no expected new information.
- **Outcome:** S-2 is **closed and rejected** as a data source for CropCast. The previous "BLOCKED on commodity confirmation" status is resolved. No further investigation of this source is needed or warranted.
- **Approval status:** Independent finding — no researcher approval required (factual determination, not a policy choice).
- **Related files/refs:** `reports/dataset_feasibility.md` Section 3 (S-2), `docs/research_log.md` RES-002
