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

---

### DEC-012: iancovert/Agmarknet Archive Rejected — Onion and Potato Absent
- **Date:** 2026-10-19
- **Context:** The iancovert/Agmarknet archive (S-2) was listed as a supplementary backup source. Direct inspection of the repository via the GitHub API was required to confirm commodity coverage.
- **Evidence:** GitHub Contents API (`https://api.github.com/repos/iancovert/Agmarknet/git/trees/master?recursive=1`) returned the complete file tree (truncated=false). The 12 commodity directories are: Arhar (Tur-Red Gram), Black Gram (Urd Beans), Cowpea (Lobia-Karamani), Green Gram (Moong), Green Peas, Kabuli Chana (Chickpeas-White), Lentil (Masur), Maize, Rice, Soyabean, Wheat, White Peas. Year coverage: 2008–2017. Total size: ~297 MB. Neither "Onion" nor "Potato" appears in any directory or file name.
- **Outcome:** S-2 rejected as a data source for CropCast. No supplementary archive is available for the 2008–2017 period for onion and potato.
- **Approval status:** Decision is factual (commodity absence confirmed by direct inspection). No researcher approval required.
- **Related files/refs:** `docs/research_log.md` RES-002

---

### DEC-013: OGD API Resource Lacks Arrivals Column — Arrival Data Strategy Required
- **Date:** 2026-10-20
- **Context:** The OGD API resource `9ef84268-d588-465a-a308-a864a43d0070` was sampled directly. The retrieved CSV schema contains only 10 columns: state, district, market, commodity, variety, grade, arrival_date, min_price, max_price, modal_price. There is no arrivals (volume) column.
- **Evidence:** Onion and Potato CSV samples retrieved 20/10/2026 (369 and 299 rows respectively). Python analysis confirmed 10-column schema with no arrivals field. This differs from the AGMARKNET portal's downloadable schema which includes `Arrivals (Tonnes)`.
- **Alternatives considered:**
  1. Accept the OGD resource as-is, proceed without arrival data.
  2. Investigate whether the AGMARKNET portal itself (agmarknet.gov.in, not the OGD resource) provides arrivals data that can be accessed reproducibly.
  3. Use NHRDF as a supplementary arrivals source for key onion/potato markets.
  4. Document arrival data as unavailable from the primary source and restrict the anomaly detection experiment accordingly.
- **Outcome:** Decision pending researcher input. The OGD resource is still the primary price source. Arrival data availability from the AGMARKNET portal (separate from the OGD API) requires further investigation. If arrivals are unavailable, the supply-related anomaly signal (Req 6 AC 7, Req 4 AC 5) cannot be computed and must be documented as an unmet criterion.
- **Approval status:** Pending — researcher input required on arrival data strategy (see M-1 blocker below).
- **Related files/refs:** `reports/Onion_api_sample.csv`, `reports/Potato_api_sample.csv`, `docs/research_log.md` RES-001, `requirements.md` Req 4 AC 5, Req 6 AC 7

---

### DEC-014: Candidate Primary Dataset Selection — CEDA Ashoka Prioritized over OGD and PyPI `agmarknet` for Price + Arrival Volume
- **Date:** 2026-10-23
- **Context:** Following DEC-013 (OGD resource lacked arrival volumes), CEDA Ashoka (S-6) and the `agmarknet` PyPI package (S-7) were investigated to identify a viable source providing both prices and market arrivals across multi-year historical spans. Additionally, the recovered ICTD-IITD anomaly label files (S-4) were audited to establish their status.
- **Evidence:**
  1. **CEDA Ashoka (S-6):** Directly inspects the OpenAPI 3.0 specification (`https://api.ceda.ashoka.edu.in/documentation/`). Provides twin REST endpoints: `POST /agmarknet/prices` and `POST /agmarknet/quantities` sharing identical composite keys. Stated platform scope covers 2000 to present (~25 years) across 300+ commodities (Onion ID 23, Potato ID 24) and 2,700+ mandis mapped to Census boundaries. Requires free registration (email + OTP) to obtain a Bearer JWT API token. Resolves the arrival data absence of S-1 subject to live authenticated verification.
  2. **PyPI Package `agmarknet` (S-7):** Source code inspection confirms it is an unofficial reverse-engineered wrapper around the internal web portal API (`api.agmarknet.gov.in/v1`). Live server metadata confirms it is hard-restricted to records starting 2021-01-01 onwards. Furthermore, live POST queries fail with `HTTP 400: TOKEN_OR_CAPTCHA_REQUIRED`; the library contains zero CAPTCHA handling logic, and its declared GitHub repository is a dead link (HTTP 404).
  3. **ICTD-IITD Labels (S-4):** Anomaly label CSVs were recovered from raw files containing merge conflict markers. Bit-level SHA-256 and byte-length verification confirms the CSV sections match the Git LFS pointer exactly (30,460 bytes for onion, 41,732 bytes for potato). Clean copies have 360 onion and 512 potato rows spanning 2016-01-01 to 2022-01-03 across 17–18 mandis. Confirmed as heuristic weak-supervision labels, not independent ground truth.
- **Alternatives considered:**
  1. Retain OGD API (S-1) alone and abandon arrival volume features.
  2. Attempt to bypass AGMARKNET portal CAPTCHA via scraping (rejected per project constraints).
  3. Adopt CEDA Ashoka (S-6) as primary dataset for combined prices and arrivals, supplemented by OGD (S-1) for cross-verification.
- **Outcome:**
  - Prioritize CEDA Ashoka (S-6) as the primary candidate source for both price forecasting and supply-related anomaly detection, subject to live authenticated verification of historical coverage and arrival alignment once CEDA_API_KEY is supplied.
  - Reject PyPI `agmarknet` (S-7) for automated ingestion due to fatal CAPTCHA blocking and date restriction ($\ge 2021$ only).
  - Adopt Hybrid Evaluation (Option C): Real-world price/arrival time-series, weak supervision against recovered S-4 labels, and synthetic shock injection for objective benchmark metrics.
- **Approval status:** Pending — requires researcher registration of free CEDA API key and formal approval of updated feasibility report.
- **Related files/refs:** `reports/dataset_feasibility.md`, `docs/research_log.md` (RES-004, RES-006, RES-007), `reports/ictd_onion_labels.csv`, `reports/ictd_potato_labels.csv`, `reports/_parse_labels.py`

---

### DEC-015: Primary Research Direction Formally Approved — Option A (State-Level Forecasting on CEDA Ashoka)
- **Date:** 2026-10-23
- **Context:** Following authenticated live audit and schema inspection of CEDA Ashoka (S-6), the returned series were verified as state-level daily aggregates (arithmetic mean prices across reporting mandis in the state, and statewide total arrival volumes in Tonnes). Attempts to perform runtime market discovery via `POST /agmarknet/markets` on high-volume production districts (e.g. Nashik, district 516) resulted in backend database query timeouts (>30 seconds) on CEDA's server, whereas state-level queries respond reliably in 1–2 seconds with 100% price-quantity temporal alignment.
- **Evidence:**
  1. Saved JSON samples confirm schema: `(date, commodity_id, census_state_id, min_price, max_price, modal_price)` and `(date, commodity_id, census_state_id, quantity)`.
  2. 100% temporal alignment on composite key `(date, commodity_id, census_state_id)` for Maharashtra Onion (13/13 trading days) and Uttar Pradesh Potato (15/15 calendar days).
  3. Multi-year verification confirms synchronized records exist across 2016, 2018, 2020, 2022.
  4. CEDA enforces a strict rate limit of 40 requests/hour (`RateLimit-Policy: 40;w=3600`).
- **Alternatives considered:**
  1. Option A (State-Level Forecasting): Model state-level aggregate prices and arrival volumes for primary producing/consuming states (Maharashtra Onion, Uttar Pradesh Potato).
  2. Option B (Dual-Track Hybrid): Use OGD API for mandi-level prices and CEDA for state-level arrivals.
  3. Option C (Static Pre-Mapped Market Extraction): Undertake offline extraction of specific market IDs if static mappings become available.
- **Outcome:**
  - Adopt **Option A (State-Level Forecasting)** as the approved primary research direction for CropCast.
  - Candidate series: Maharashtra Onion (`state_id: 27`, `commodity_id: 23`) and Uttar Pradesh Potato (`state_id: 9`, `commodity_id: 24`).
  - Historical extraction window approved: `2016-01-01` to `2022-12-31` (7 years), subject to rate throttling ($\le 40$ requests/hour) and bounded pilot validation.
  - Raw datasets must remain in local Git-ignored storage (`data/raw/`); no raw data committed to Git.
- **Approval status:** **Approved by researcher (2026-10-23).** Researcher confirmed Option A, candidate series, historical window (2016–2022), rate limit compliance, and authorized closing Milestone M-1.
- **Related files/refs:** `reports/dataset_feasibility.md`, `docs/research_log.md` (RES-008), `reports/_ceda_audit.py`

---

### DEC-016: M-2 Sign-off Conditions and Data-Quality Handling
- **Date:** 2026-10-23
- **Context:** Independent re-verification (RES-011) confirmed that the `task-775` extraction is complete and internally consistent, but surfaced open items: 137 UP Potato records with `modal_price` outside `[min_price, max_price]` (ISS-002), near-zero onion arrival days in 2020 (ISS-003), a validation audit that cannot be regenerated from committed code (ISS-004), and overlapping pilot chunks (ISS-005).
- **Evidence:** `docs/research_log.md` RES-011; `docs/issue_log.md` ISS-001 to ISS-005.
- **Alternatives considered:**
  1. Sign off M-2 as-is and handle every open item inside M-3.
  2. Before sign-off, add a committed validation module (`src/data/validate.py` + tests) that regenerates `m2_validation_audit.json` offline, and add a modal-bounds warning flag to the pipeline validator.
  3. Exclude or correct the 137 potato records (rejected: violates the no-silent-deletion rule and the cause is unknown).
- **Outcome:**
  - Option 2, then sign off M-2.
  - Retain all raw records unchanged; carry explicit quality flags (`modal_outside_bounds`, low-arrival candidates) into the assembled dataset rather than deleting or imputing.
  - Assemble datasets from the 14 six-month historical chunks only; exclude pilot chunks.
- **Approval status:** **Option 2 approved by researcher (2026-10-23).** Implemented the same day: `src/data/validate.py` (offline audit, `python -m src.data.validate --output data/raw/m2_validation_audit.json`) and a non-fatal `modal_bounds_warnings` counter in `CedaIngestionPipeline.validate_records` (RES-012). **M-2 signed off by researcher on 2026-10-23.** The quality-flag and pilot-exclusion points above take effect at dataset assembly (M-3).
- **Related files/refs:** `src/data/ingest_ceda.py`, `data/raw/m2_validation_audit.json`, `docs/issue_log.md`

---

### DEC-017: Peer-Market Requirements Not Applicable; "Market-Relative" Redefined for State Aggregates
- **Date:** 2026-10-23
- **Context:** Under DEC-015 (Option A, approved), each commodity has exactly one series: a state-level aggregate (Maharashtra onion; Uttar Pradesh potato). Req 3.7 (peer-market correlations), Req 4.6 (peer-price feature) and Req 6.3–6.5 (peer-divergence signal, residual-plus-peer ablation) assume several peer markets for the same commodity.
- **Alternatives considered:**
  1. Acquire more states per commodity from CEDA to act as peers. Rejected for this phase: it is a new extraction (≈ 56+ requests per added series), a scope change beyond the approved series, and DEC-015 approved exactly two series.
  2. Use the other commodity as a "peer". Rejected: onion and potato are different markets, so their divergence is not a market-relative signal.
  3. Mark the peer components as not applicable and define the anomaly relative to the market's own expected behaviour. **Chosen.**
- **Outcome:**
  - Peer-market requirements are recorded as not applicable, with this reason.
  - The anomaly signal is "market-relative" in the sense of relative to the same market's one-step forecast (residual z-score, Req 6.1–6.2) and to its own trailing robust baseline (rolling median/MAD).
  - The Req 6.5 ablation compares residual-only, robust-baseline-only and combined scores.
  - Adding peer states is listed as future work.
- **Approval status:** Decided under the researcher's 2026-10-23 end-to-end authorisation ("change the approved research scope substantially [only after] documenting the reason and consequences"). Consequence: the anomaly study cannot test peer divergence, which the charter names as a signal of interest.
- **Related files/refs:** `docs/requirements.md` (Req 3.7, 4.6, 6.3–6.5), DEC-015, `reports/literature_review.md` §4

### DEC-018: Project Virtual Environment and Pinned Dependencies
- **Date:** 2026-10-23
- **Context:** The `python` on PATH is an unrelated tool's virtual environment ("hermes-agent") with no analysis packages. Installing into it would change another tool's environment.
- **Outcome:** Created a git-ignored project `.venv` from the base Python 3.11.9 and pinned the dependencies in `requirements.txt` (Req 2.2). statsmodels covers ARIMA and decomposition; scikit-learn covers linear regression, decision tree and random forest. XGBoost was not added: Req 5 does not require it, and Phase 5 will decide whether a further tree ensemble is justified by the random forest results.
- **Approval status:** Engineering decision under end-to-end authorisation.
- **Related files/refs:** `requirements.txt`, `docs/environment.md`

### DEC-019: Analysis Dataset v1 Freeze Rules
- **Date:** 2026-10-23
- **Outcome:** `data/processed/cropcast_analysis_v1.csv` is built only from the 56 checksum-verified historical chunks; pilot chunks are excluded.
  - One row per observed market day; prices and arrivals joined one-to-one.
  - No imputation and no value changes; full-precision values (all 20,320 numeric values verified equal to the raw JSON).
  - Flag columns `flag_modal_outside_bounds` (ISS-002; 137 potato rows) and `flag_extreme_arrival` (ISS-003; 10 onion rows).
  - Deterministic output: CSV SHA-256 `b5f21e02b681c7887af340ba6e5d22ec9b3847bfd171da8e7ba3ffc24152b773`, identical across rebuilds. The dataset version ID used in experiment hashes is `v1:b5f21e02b681`.
- **Approval status:** Engineering decision under end-to-end authorisation.
- **Related files/refs:** `src/data/dataset.py`, `data/processed/cropcast_analysis_v1.meta.json`, `tests/test_dataset.py`

### DEC-020: Forecasting Protocol v1.1 — Validation Refit Cadence
- **Date:** 2026-10-23 (fixed before any model was fitted)
- **Context:** Req 5.6 requires walk-forward evaluation on the test set with retraining at each step. Applying the same every-step refit to the validation grid would take about 12,000 random-forest fits plus SARIMA refits, beyond the machine's practical budget (7.3 GB RAM, about 0.8 GB free).
- **Alternatives considered:**
  1. Every-step refits in validation too (infeasible).
  2. A smaller grid (weakens tuning).
  3. Refit every 7 origins during validation only, keeping every-step refits on test. **Chosen.**
- **Outcome:** `validation_refit_every = 7` and `test_refit_every = 1` in `configs/config.json` (`docs/forecasting_protocol.md` §4).
  - Between refits, feature models apply the last fitted model to current features, and univariate models update their state with fixed parameters.
  - No look-ahead is possible either way: `tests/test_features.py` checks forecasts are unchanged when future values are perturbed, for refit 1 and 7.
- **Approval status:** Engineering decision under end-to-end authorisation, recorded before results.
- **Related files/refs:** `docs/forecasting_protocol.md`, `src/forecasting/run.py`, `src/forecasting/models.py`

### DEC-021: Anomaly Protocol v1.0 — Causal Standardisation and Fixed Threshold
- **Date:** 2026-10-23 (fixed before any anomaly score was computed)
- **Context:** Req 6.4 standardises signals "over the evaluation window" before combining them. Statistics over the whole window would let later data influence earlier scores.
- **Outcome:**
  - Signals are standardised with the expanding mean and SD of earlier values only (minimum 90), and the composite is re-standardised the same way.
  - The threshold is |score| > 3, the conservative MAD-rule cut-off discussed by Leys et al. (2013), with sensitivity reported for 2.5–5.
  - Shock-evaluation residual parameters are frozen at the start of the test segment, for computational feasibility.
  - Full protocol: `docs/anomaly_protocol.md`.
- **Approval status:** Engineering decision under end-to-end authorisation, recorded before results.
- **Related files/refs:** `docs/anomaly_protocol.md`, `src/anomaly_detection/`

### DEC-022: Derived Files Containing Source Values Are Not Committed
- **Date:** 2026-10-24
- **Context:** Several generated files embed CEDA source values:
  - test predictions (`reports/forecasts/test_*.csv`, with daily actual and origin prices);
  - run copies of those predictions;
  - `reports/tables/anomaly_scores.csv` (the full daily price and arrival series).
  CEDA's terms do not clearly permit redistribution (DEC-019, RES-014).
- **Outcome:**
  - These files are git-ignored and stay local, like the dataset.
  - Committed results are aggregate metrics, model configurations, small event tables, figures (with CEDA credit) and run manifests. Manifests still record the SHA-256 of the ignored files, so the local copies can be verified.
  - A fresh user regenerates them from the documented pipeline after obtaining CEDA access.
- **Approval status:** Decided under end-to-end authorisation (conservative licensing choice).
- **Related files/refs:** `.gitignore`, `docs/reproducibility.md`

### DEC-023: M-8 Pilot Scope and Provisional Findings
- **Date:** 2026-10-24
- **Context:** The researcher conditionally approved a CEDA pilot of about 26 requests to test multi-state feasibility. Bulk retrieval, dataset selection and any scope change were explicitly withheld.
- **Outcome:**
  - The pilot was run with a separate client that has a hard request cap and no automatic retries. It used 20 requests (RES-016).
  - Project scope is unchanged. Dataset v1 and all v1 results are untouched.
  - **Provisional pending approval:**
    - The "real-time" goal is reworded as "forecasting from the latest available CEDA data" (latest record 2025-10-30).
    - The reporting-composition component would use observed mandi counts from mandi-level rows instead of an arrivals proxy.
    - The national component stays provisional until the national aggregation rule is verified.
  - No models were trained and no synthetic data was generated.
- **Approval status:** pilot conditionally approved by the researcher. Broader retrieval and all M-8 implementation **await researcher approval**.
- **Related files/refs:** RES-016, `docs/m8_national_expansion_plan.md`, `reports/dataset_feasibility.md` §6
