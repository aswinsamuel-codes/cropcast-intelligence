# M-8 Proposal: Multi-State ("National") Expansion

**Status:** Proposed. The feasibility pilot (§10) and the focused literature review (§11; `docs/m8_literature_review.md`) are complete. Broader retrieval and all implementation await researcher approval.
**Date:** 2026-10-24
**Prepared by:** project management pass after M-7 sign-off. Sections 1–9 are the original proposal. Where §10 or §11 differs from them, the later section supersedes. §10.5 is superseded by §11.4.

---

## 1. Goal

Move CropCast from two state series (Maharashtra onion, Uttar Pradesh potato) to a multi-state study. The aims are:

1. Real state-level data for the main producing states of each crop, plus the national aggregate.
2. A forecasting method that uses information across states, tested under the same rigour as v1.
3. Forecasts of genuinely upcoming prices, if CEDA has data after 2022.

All v1 results stay as they are. M-8 builds a new dataset version (v2) and a new protocol version; nothing in v1 is rerun or overwritten.

## 2. Why not synthetic data for the other states

The idea was to generate the other states synthetically from the Maharashtra and Uttar Pradesh series. This plan does not do that, for three reasons:

- A model trained and tested on states made from Maharashtra and Uttar Pradesh only relearns those two series. Its accuracy would say nothing about other states.
- Presenting such series as "national" results would misrepresent the data to examiners.
- The charter requires explicit approval before any switch from real to synthetic evaluation.

Synthetic data is still useful in one role: as a **test bench with known truth**. Planted shocks and planted reporting effects show whether each method recovers what we know is there. Every synthetic file and figure would be labelled "Synthetic test data — not market prices" and kept out of the real results.

## 3. Literature check: what is and isn't new

A short search was done on 2026-10-24 (three web searches, one abstract read). It is not a systematic review; a proper search must precede any novelty claim in the report.

| Idea | Prior work found | Status |
|---|---|---|
| Spatial/cross-market forecasting of Indian crop prices | Bhardwaj et al. (2023), arXiv:2304.09761: graph neural networks for potato and tomato, up to 30 days ahead. Several multi-market LSTM studies. | **Exists.** Cannot be claimed as new. |
| Forecasting plus anomaly detection on Agmarknet | ICTD-IITD, COMPASS 2019 (already cited). | **Exists.** |
| Correcting for the changing set of reporting mandis in state averages | Only an industry methodology note (ACROP) describing the problem. No academic forecasting study found. | **Possible gap.** |
| Hierarchical reconciliation (states → national) for Indian crop prices | General methods (Hyndman et al. 2011; MinT) and retail applications. No Indian crop-price application found. | **Possible gap.** |

## 4. Proposed method contribution

**Composition-aware, cross-state forecasting**, built on the v1 finding that most of the potato gain comes from Sunday/Monday shifts in the state average.

1. **Composition signal.** CEDA's state aggregates do not report how many mandis contributed each day. The proxy is arrivals relative to their usual level for that weekday, which we already have. Whether it is a good proxy is tested, not assumed.
2. **Pooled cross-state model.** One model trained on all states of a crop, with lagged prices from other states (for example, Maharashtra onion leading Delhi onion).
3. **Coherent national forecast.** State forecasts are combined into a national forecast and compared with forecasting the national series directly. Prices are averages, not sums, so the combination needs arrival weights. Whether CEDA's national series is arrival-weighted must be checked first.

Each part is compared against the naive forecast and the best v1 models under the v1 testing rules (Diebold–Mariano with the HLN correction, BH adjustment). If a part does not beat them, it is reported as a negative result.

## 5. Data plan and CEDA request budget

Current pipeline: one request per endpoint (prices, quantities) per 6-month chunk, spaced 95 s apart: at most 38 requests in any rolling hour (3600 ÷ 95 ≈ 37.9), under CEDA's 40-per-hour limit. All times in this document are (requests − 1) × 95 s, plus response time.

**Candidate states.** Census codes must be verified against `/agmarknet/geographies` before use.

| Crop | Candidates |
|---|---|
| Onion | Maharashtra (have), Karnataka, Madhya Pradesh, Gujarat, Rajasthan; NCT of Delhi as a consumer market |
| Potato | Uttar Pradesh (have), West Bengal, Bihar, Gujarat, Punjab, Madhya Pradesh |
| Both | National aggregate (`state_id: 0`) |

**Budget.** Assumes 2016–2025 (20 chunks × 2 endpoints = 40 requests per new series) and the 2023–2025 extension of the two existing series (24 requests).

| Option | Series | Requests | Download time at 95 s spacing |
|---|---|---|---|
| A: core | 4 onion + 4 potato states + 2 national | ≈ 426 | ≈ 11.5 h |
| B: lean | 3 onion + 3 potato states + 2 national | ≈ 346 | ≈ 9.5 h |
| C: pilot first | 1 onion + 1 potato state, 2023–2025 only, plus 2 metadata calls | ≈ 26 | ≈ 45 min |

The download can resume after an interruption: verified chunks are kept, and empty ranges are recorded as `empty`. If CEDA has no data after 2022, the budget falls by about 30%, and "upcoming price" forecasting is not possible from CEDA.

## 6. "Real-time" forecasting

This is possible only if CEDA updates its data regularly. The pilot (option C) checks the latest available date. If the data is current:

- a command fetches the newest days within the rate limit and forecasts the next market day for each state;
- the dashboard shows those forecasts with the date of the latest data and the model's tested accuracy;
- forecasts are shown as estimates with uncertainty ranges, never as guaranteed prices.

If CEDA lags by weeks or months, the honest label is "latest-data forecast", not real-time.

## 7. Phases

| Phase | Work | Needs approval |
|---|---|---|
| 8.0 | Charter amendment, protocol v2.0 (pre-registered before any v2 test data is seen) | Yes: scope change |
| 8.1 | Pilot fetch (option C): verify IDs, check latest date | Yes: CEDA requests |
| 8.2 | Full fetch (option A or B), validation, dataset v2 freeze | Yes: CEDA requests |
| 8.3 | Generalise the pipeline to any state and crop from configuration; synthetic test bench | No |
| 8.4 | v1 models on all states; composition-aware and cross-state models; national reconciliation | No |
| 8.5 | Fresh out-of-time test on 2023–2025 (if available); report, dashboard, verification | No |

## 8. Risks

| Risk | Effect | Mitigation |
|---|---|---|
| CEDA has no data after 2022 | No upcoming-price forecasts; smaller dataset | Pilot first (option C) |
| Smaller states have many gaps | Some series unusable | Coverage threshold set in protocol v2.0 before modelling |
| The arrivals proxy does not track composition | Method part 1 fails | Report as a negative result; parts 2 and 3 are independent |
| Similar published work turns up | Novelty claim lost | Systematic search before writing any claim |
| Rate-limit or API changes | Slower fetch | Existing throttling, resume and retry logic |
| CEDA licence | Cannot share daily data | Same as v1: only aggregates committed or shown (DEC-022) |

## 9. Decisions needed

1. Approve the scope change: multi-state data, a new method, and a live forecast dashboard.
2. Approve CEDA requests: the pilot (option C) now, and the full fetch (option A or B) after the pilot.
3. Choose the states, or accept the candidates above.
4. Confirm that synthetic data is used only as a labelled test bench, not as stand-in states.
5. Deadline: the date the faculty review needs results by, which decides between option A and option B.

---

## 10. Pilot Outcome (2026-10-24) and Revised Proposal

### 10.1 What was done
- **Approval:** a pilot of about 26 requests, conditionally approved. 20 were used, all HTTP 200, with no retries or 429s.
- **Requests:**
  - 1 geography list;
  - 12 requests for Karnataka onion and West Bengal potato, 2023–2025, in 12-month chunks;
  - 4 national 2022 requests (prices and arrivals for both crops);
  - 1 national 2026 freshness probe;
  - 2 mandi-level requests for Maharashtra onion, January–March 2022.
- **Records:** `reports/pilot_m8/request_log.json`, `reports/pilot_m8/pilot_summary.json`, RES-016, and `reports/dataset_feasibility.md` §6.
- **Planned but not done:** the market-list request and the separate market-level fetch, because the district request already returned mandi rows. Option C as written (§5) was otherwise followed.

### 10.2 Findings that change the plan
| Plan item | Pilot evidence | Revision |
|---|---|---|
| Real-time forecasting (§6) | Latest record is 2025-10-30; the 2026 request returned no data; the update process is undocumented | Drop "real-time". Use "forecasting from the latest available data", which can be tested out-of-time on 2023 – 2025-10. |
| Composition signal from arrivals (§4.1) | Mandi-level rows with `market_id` are available; mandi counts per day are directly observable | Use observed mandi counts. No proxy is needed. |
| How state prices are built | State modal, min and max are the unweighted mean of mandi rows; state arrivals are the sum of mandi quantities (90/90 days, Maharashtra onion, 2022 Q1) | The composition effect is mechanical and measurable. A **fixed-panel state price** (the same mandis every day) can be built and compared with the published series. |
| National forecast (§4.3) | National series exists (`state_id: 0`); state arrivals never exceed national; the price rule is unknown | Keep provisional. Never sum prices. Verify the rule first (see 10.4). |
| Candidate states | All 10 codes exist; Karnataka onion and West Bengal potato have data for 2023–2025 | Coverage for 2016–2022 and for the other 8 states remains unverified. |
| Data quality | Shared gaps in 2023-12, 2024-06/07 and 2024-12; up to 3 price rows per mandi-day with no variety field; no zero quantities | Coverage rules and duplicate-row handling must be fixed in protocol v2.0 before modelling. |

### 10.3 Revised method candidates (not implemented)
1. **Composition-adjusted target.** Compare the published state mean with a fixed-panel mean over mandis that report consistently. Test whether forecast gains on the published series disappear on the fixed-panel series. This directly tests the v1 explanation of the potato gain.
2. **Composition-aware forecasting.** Use the observed daily mandi count, or the set of mandis expected to report tomorrow, as a feature. This is only usable if the count is known before the forecast is made: the count for the target day is not known in advance. Only lagged counts and weekday patterns are legitimate inputs.
3. **Pooled cross-state model** (unchanged).
4. **National aggregation.** Only after 10.4 confirms the rule.

**Hypotheses to pre-register in protocol v2.0, before any test data is examined:**
- **H1:** the naive-relative MAE gain on the published state series is larger than on the fixed-panel series.
- **H2:** adding lagged mandi-count features reduces MAE relative to the best v1 model.
- **Testing rules:** Diebold–Mariano with the HLN correction on identical observations; BH adjustment across states; effect sizes reported alongside p-values.

### 10.4 Open verification items
- **National rule.** Does national modal equal the unweighted mean of all Indian mandi rows? This needs mandi-level prices from every reporting state for one crop and one month: up to about 36 requests (states with no mandis return empty). Adding quantities, to check that national arrivals are a sum, doubles that.
- **Generality.** Does the unweighted-mean rule hold for other states, potato, and the 2016–2017 period? (ISS-002 suggests the rule may have changed in 2017.) About 2 requests per check.
- **Large-state chunks.** Is a 12-month mandi-level request feasible for large states, such as Uttar Pradesh with 71 districts? Not tested.

### 10.5 Revised request estimates (superseded by §11.4; kept for the record)
Mandi-level data replaces state-level data: it gives the state series and the mandi counts in the same number of requests. Costs assume 12-month chunks from 2016-01-01 to 2025-10-30, so 10 chunks × 2 endpoints = 20 requests per state-crop. They double if large states need 6-month chunks.

| Option | Contents | Requests | Time at 95 s spacing |
|---|---|---|---|
| Stage 1 | National-rule check (one crop-month, about 36), generality checks (about 4), and mandi-level Maharashtra onion and Uttar Pradesh potato (40) | ≈ 80 | ≈ 2.2 h |
| Stage 2 | 4 new states (2 onion, 2 potato), mandi-level | ≈ 80 (≤ 160) | ≈ 2.2–4.3 h |
| Full candidate list | All 10 candidate states, mandi-level | ≈ 200 (≤ 400) | ≈ 5.4–10.8 h |

**Recommendation:** approve Stage 1 only, then decide on Stage 2 from its results.

### 10.6 Follow-up literature search (before any novelty claim)
- **Topics:**
  - composition (panel-change) bias in unweighted market averages;
  - fixed-panel versus chained price indices in agricultural statistics;
  - reconciliation of averaged (non-additive) hierarchies;
  - graph and spatial models on Agmarknet.
- **Sources:** Crossref, Google Scholar, RePEc and arXiv, plus the citations of Bhardwaj et al. (2023) and Madaan et al. (2019).
- **Recording:** every search string and every closest study goes in the research log.

---

## 11. Literature Review Outcome and Minimum-Request Verification Plan (2026-10-24)

The full review, source matrix, comparison matrix and hypotheses are in `docs/m8_literature_review.md` (RES-017). No CEDA requests were made in this phase.

### 11.1 Established by the pilot vs unverified

| Established (RES-016) | Unverified |
|---|---|
| Latest record 2025-10-30; no 2026 national data | CEDA's update schedule |
| `district_id` requests return mandi rows | Whether this holds for every state, crop and year |
| Maharashtra onion state modal/min/max = unweighted row mean; arrivals = mandi sum (2022 Q1, 90/90 days) | The same rule for potato, other states and 2016–2017 |
| Weekday drop in reporting mandis (Sunday ~24.5 vs weekday ~41–46) | The size of the composition effect on forecasts |
| National series exists; state arrivals never exceed national (2022) | The national price rule |
| Coverage of Karnataka onion and West Bengal potato, 2023–2025 | The other 8 candidate states; all 2016–2022 new-state coverage |

### 11.2 Reporting-composition measurement (proposed)
- **What it measures:** the matched-mandi chained index M_t and the composition term C_t = Δlog A_t − Δlog M_t. Both are computed from observed mandi rows only, with no proxy and no imputation.
- **What it cannot measure:**
  - why a mandi did not report;
  - trades that were never recorded;
  - variety mix within a mandi-day.
- **Possible bias:** the selection, panel-drift and non-random-gap biases listed in review §4.

### 11.3 National aggregation question
- **The question:** is the CEDA national price (a) the unweighted mean over all India's mandi rows, (b) a weighted mean of state values, or (c) something else?
- **Evidence needed:** mandi-level rows for every reporting state for one crop and one period, then a direct reconstruction test as in RES-016.
- **Until then:** H3 and every national forecast stay out of scope. State prices are never summed.

### 11.4 Is further retrieval justified? Proposed minimum request list (not approved)

**Justification:**
- H1, the strongest candidate gap, cannot be tested on the existing state-level data. It needs mandi-level rows for the series already studied: Maharashtra onion and Uttar Pradesh potato.
- Those same rows also test whether the row-mean rule generalises. We already hold their state series for 2016–2022, so this needs **no extra requests**.
- Prices alone suffice for H1. Quantities are optional.

| Priority | Group | Request(s) | Count | Information gained | Stop rule |
|---|---|---|---|---|---|
| P1 | Q-B1 national rule, cheap probe | `prices`, onion, `state_id: 0`, `district_id` = all 640 district IDs, 2022-01-01..2022-01-31 | 1 | If it returns all-India mandi rows, a single request tests the national rule against the 2022 national series already held. If refused or empty, the national rule stays unresolved at a cost of 1 request. | Stop Q-B after 1 request. Any fallback (≤ 36 state-by-state requests) needs separate approval. |
| P1 | Q-A1 chunk-size check | `prices`, Uttar Pradesh potato, `state_id: 9`, all 71 district IDs, 2022-01-01..2022-12-31 | 1 | Whether a 12-month mandi-level request works for the largest state. It also tests the row-mean rule on potato against the held v1 state series. | If it times out or fails, stop and report; 6-month chunks would double Q-A2. |
| P2 | Q-A2 Maharashtra onion, mandi-level prices | `prices`, `state_id: 27`, all 35 district IDs, one request per calendar year 2016–2025 (2025 ends 2025-10-30) | 10 | H1 development data for 2016–2022, the row-mean rule across all years (including the ISS-002 period, checked against held data), and confirmatory 2023–2025 data | Stop on any 429 or failure |
| P2 | Q-A3 Uttar Pradesh potato, mandi-level prices | `prices`, `state_id: 9`, 71 district IDs, years 2016–2025 except 2022 (already fetched in Q-A1) | 9 | As Q-A2, for potato, including the ISS-002 regime 2016-03 to 2017-04 | As above |
| P3 (optional) | Q-A4 quantities | Same as Q-A2 and Q-A3 for `quantities` | 20 | Arrivals per mandi: the composition–arrival link and the arrivals-sum rule across years. Not required for H1. | Approve separately |
| P3 (optional) | Q-F freshness re-check | `prices`, onion, `state_id: 0`, 2025-10-31..request date | 1 | Whether newer data has appeared. Do this only shortly before the final report. | — |
| Deferred | Q-C cross-state (H2) | Mandi-level prices for 2 onion and 2 potato candidate states, 2016–2025 | ≈ 40 | H2 data | Only after H1 results and a separate approval |

**Summary:**
- **Requested for approval:** P1 + P2 = **21 requests**: (21 − 1) × 95 s ≈ 32 minutes plus response time (3–6 s each in the pilot), so about 32–35 minutes. At most 38 requests in any rolling hour, under CEDA's 40 per hour.
- **Researcher decision (2026-10-24):** only the two P1 requests are authorised, after the documentation commit. The 19 P2 requests and all P3 requests are **not approved**.
- **Optional extras:** P3, 21 more.
- **Cost:** no money (CEDA access is free for non-commercial research).
- **Storage:** all raw rows go to git-ignored `data/raw/`. Only aggregates and metadata are committed (DEC-019, DEC-022). Runs use the pilot's capped client: no automatic retries, a stop on HTTP 429, and the overall 26-request pilot cap. Each run is limited to the requests approved for it.

### 11.5 Risks specific to this plan
| Risk | Mitigation |
|---|---|
| The all-India `district_id` probe is refused or times out | It costs 1 request. The national rule stays unresolved. |
| 12-month mandi-level chunks fail for Uttar Pradesh | Checked first (Q-A1). Stop and re-plan. |
| The row-mean rule fails in some years | This is a finding. The H1 definitions use only mandi rows, so they do not depend on the rule. |
| Bias from the confirmatory period | Protocol v2.0 is frozen and approved before 2023–2025 Maharashtra or Uttar Pradesh data is examined. Retrieval itself is fine; any analysis beyond coverage counts waits. |
| CEDA's terms on derived data are unclear | Same conservative handling as v1 |
