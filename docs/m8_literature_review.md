# M-8 Focused Literature Review: Reporting Composition and National Aggregation

**Date:** 2026-10-24
**Status:** Complete for this phase; revised 2026-10-24 after researcher review. The hypotheses (§5) are **proposals**, not a finalised or preregistered protocol. The request plan is in the expansion plan, §11.4.
**Scope limits:** This is a focused review, not a systematic one. No CEDA requests were made for it.

---

## 1. Search methodology

### 1.1 Tools

| Tool | Used for | Limitation |
|---|---|---|
| General web search (Claude Code `WebSearch`; "extended" mode for most queries) | Discovery | Search-engine ranking. No direct access to Scopus, Web of Science or Google Scholar. |
| Crossref REST API (`api.crossref.org/works`) | Checking DOI, authors, venue, volume and pages | Metadata only, not content |
| arXiv abstract pages | Abstracts | Abstract only, unless the full text is listed below |
| Full-text PDFs (downloaded, converted with `pdftotext`) | Bhardwaj et al. (2023); Madaan et al. (2019); the open preprint of Athanasopoulos et al. (2024); the open working-paper version of Qu, Timmermann & Zhu (dated 2023-08-27); CPI Manual (2004) ch. 7 | Read the sections relevant to each claim (data, method, evaluation; the passages cited) |
| Direct page reads | ACROP methodology page; CEDA OpenAPI document; CEDA portal | — |

Published versions of paywalled papers (Springer *Discover Informatics*, *IJF*, *JASA*, *CSDA*) were **not** read. Open preprint or working-paper versions were read where marked P. Where a source is summarised from metadata, an abstract or a search snippet, the matrix says so.

### 1.2 Queries (all run 2026-10-24)

| # | Query | Question | Useful results |
|---|---|---|---|
| Q1 | multi-state India onion potato wholesale price forecasting spatial cross-market Agmarknet deep learning | A, H2 | Bhardwaj et al. 2023; Madaan et al. 2019; several single-market deep-learning studies |
| Q2 | market composition bias aggregated mandi price index number of reporting markets varying forecasting | A | ACROP methodology (the only source naming the problem) |
| Q3 | hierarchical forecast reconciliation agricultural commodity prices states national India | B | No Indian application found |
| Q4 | forecast reconciliation MinT food prices regional national hierarchy wholesale | B | General MinT material; retail and FMCG applications |
| Q5 | CEDA Ashoka Agri Market Data methodology state level national average price computed mandis arrivals weighted | B | No CEDA methodology found |
| Q6 | agricultural market price aggregate changing number of reporting markets composition effect unit value bias | A | Only loosely related (trade-share composition, index-number bias) |
| Q7 | Agmarknet mandi data missing reporting non-random arrivals price reporting gaps study | A | Ma et al. 2019; Jain et al. 2020; administrative under-reporting report |
| Q8 | matched model price index fixed panel versus unbalanced panel composition bias food price index methodology | A | Matched-model and scanner-data index literature |
| Q9 | "Agmarknet" all India average modal price how computed state average arrivals weighted methodology report | B | Mahajan et al. 2026 (snippet); no official method |
| Q10 | forecast reconciliation general linear constraints non-additive weighted average hierarchy Girolimetto Di Fonzo | B | Girolimetto & Di Fonzo 2023; Girolimetto et al. 2025 |
| Q11 | hierarchical forecasting agricultural prices regional reconciliation MinT application commodity prices study | B | No agricultural-price reconciliation study found |
| Q12 | aggregate time series varying cross-section coverage composition change bias forecasting evaluation "balanced panel" constant sample | A, H2 | Qu, Timmermann & Zhu (panel forecast comparison) |
| Q13 | onion potato price India market integration spatial price transmission Lasalgaon Azadpur cointegration study | H2 | Several market-integration studies (snippets only) |
| Q14 | day-of-week effect wholesale agricultural market prices India weekly pattern arrivals Sunday markets closed | A | No weekday-effect study found |
| Q15 | Directorate of Marketing and Inspection Agmarknet "national average" OR "all India" modal price computation state wise average price trend report onion | B | No official DMI method; aggregator sites use their own rules |
| Q16 | Crossref bibliographic searches: Qu & Timmermann panel comparison; Girolimetto non-linear; CPI Manual 2020; Mahajan 2026 | — | DOIs confirmed |

Q1–Q4 are the preliminary searches recorded in the plan's §3, run earlier the same day. Their results were re-examined here, and L1 was then read in full.

**Coverage caveat:** "No study found" in this document always means *not found by Q1–Q16 with the tools above*. It is **not** evidence that no such study exists.

---

## 2. Source matrix

Verification levels:
- **F** = full text read (at least the sections supporting the claims made);
- **P** = open preprint or working-paper version read, not the published version;
- **A** = abstract only (arXiv page or Crossref abstract);
- **D** = official documentation read directly;
- **I** = industry or news page read directly (not peer-reviewed);
- **M** = bibliographic metadata confirmed via Crossref only, with no content examined;
- **S** = search-engine snippet only.

A claim in the matrix is only as strong as its level. Claims at M or S are leads for follow-up, not established support.

| ID | Source | Ver. | Question and data | Method and evaluation | Relevance to CropCast | Overlap and limitations |
|---|---|---|---|---|---|---|
| L1 | Bhardwaj, Pawar, Bhat, Deepanshu, Enaganti, Sagar, Narahari (2023). *An innovative deep learning based approach for accurate agricultural crop price prediction.* arXiv:2304.09761 | F | Mandi-level daily Agmarknet prices and arrivals; tomato (557 mandis) and potato (676 mandis); 2014–2018; plus weather and soil data | CNN + GNN (GraphSAGE). Edges link mandis within 200 km. Horizons 4–30 days. MAE, RMSE, CoV, R², Pearson. Compared only with PECAD. No naive baseline, no significance tests. | Closest spatial/cross-market precedent for H2. Reports that 46% of price entries are missing. | Imputes missing days (spline, then linear interpolation), so evaluation targets may include imputed values. Removes all Sundays, stating mandis are closed then; our pilot found ~24.5 Maharashtra onion mandis reporting on Sundays. No state or national aggregation, no composition analysis. arXiv preprint (v1, 15 Apr 2023); no peer-reviewed version identified in this review. |
| L2 | Madaan, Sharma, Khandelwal, Goel, Singla, Seth (2019). *Price forecasting & anomaly detection for agricultural commodities in India.* Proc. 2nd ACM SIGCAS Conf. on Computing and Sustainable Societies (COMPASS '19), pp. 52–64. doi:10.1145/3314344.3332488 | F | Onion and potato; selected mandis and retail centres with little missing data; Agmarknet mandi data ("almost 11 years") plus retail prices from 30 district centres | ARIMA, SARIMA, multivariate regression and LSTM; 30-day forecasts; RMSE only. Anomaly classes come from newspaper reports. Lead–lag graphs between source and terminal mandis. | Precedent for combined forecasting and anomaly work, and for cross-market lead–lag (H2) | Restricts to low-missingness series rather than modelling missingness. No aggregation or composition analysis, no significance tests. |
| L3 | Ma, Nowocin, Marathe, Chen (2019). *An interpretable produce price forecasting system for small and marginal farmers in India…* ICTD 2019; arXiv:1812.05173 | A | Agmarknet, over a thousand markets, "extremely sparse" | Collaborative-filtering imputation; tree-based classifier | Confirms widespread missingness at mandi level | Imputes rather than measures reporting. No aggregation. |
| L4 | Jain, Marvaniya, Godbole, Munigala (2020). *A framework for crop price forecasting in emerging economies by analyzing the quality of time-series data.* arXiv:2009.04171 | A | Tomato and maize, 14 markets in India | Model selection using data-quality features | Data quality treated as an input to forecasting | Single markets; reporting composition of aggregates not addressed |
| L5 | ACROP AI, *How ACROP AI collects and calculates mandi prices*, acrop.app/methodology (no date; mentions an October 2026 method change; read 2026-10-24) | I | Agmarknet via data.gov.in | Area price = median of per-mandi modal prices; each mandi counted once (varieties combined first); minimum mandi counts; flags for low reporting | Names the problem directly: movements "partly reflect who reported" and the figure is "not a fixed-market price index" | Industry documentation, not peer-reviewed. Describes the problem but does not quantify it or study forecasting. Uses a different aggregate (median) from CEDA (mean of rows, per our pilot). |
| L6 | Mahajan, Muley, Fegade (2026). *Forecasting agricultural commodity prices using machine learning models.* Discover Informatics 1. doi:10.1007/s44564-026-00015-0 | M + S (full text blocked by the publisher sign-in redirect) | Maharashtra mandi-level Agmarknet, 9 commodities, monthly | According to the snippet: monthly mean of modal prices with equal weight per valid mandi observation; one-step machine-learning forecasts | Shows that unweighted pooling of varying mandi sets is common practice | Full text not read. Monthly, single state, no composition analysis (per snippet). |
| L7 | Hyndman, Ahmed, Athanasopoulos, Shang (2011). *Optimal combination forecasts for hierarchical time series.* Comput. Stat. Data Anal. 55(9), 2579–2589. doi:10.1016/j.csda.2011.03.006 | M (content as described in L9) | Methodological | Combination-based reconciliation for hierarchies defined by aggregation (sums) | Foundation for H3 | Paper itself not read. CEDA prices are averages, not sums. |
| L8 | Wickramasuriya, Athanasopoulos, Hyndman (2019). *Optimal forecast reconciliation for hierarchical and grouped time series through trace minimization.* J. Am. Stat. Assoc. 114(526), 804–819. doi:10.1080/01621459.2018.1448825 | M (content as described in L9) | Methodological | MinT reconciliation | Candidate H3 method | Paper itself not read. Not applied to Indian crop prices in any source found. |
| L9 | Athanasopoulos, Hyndman, Kourentzes, Panagiotelis (2024). *Forecast reconciliation: A review.* Int. J. Forecast. 40(2), 430–456. doi:10.1016/j.ijforecast.2023.10.010 | P (preprint dated 11 Dec 2023; sections read) | Review | Describes coherence as satisfying linear constraints, a generalisation beyond aggregation. Reports Hubrich (2005): bottom-up euro-area inflation forecasts suffered increased bias when shocks hit components similarly. | Context for H3; supports the descriptions of L7 and L8 | Published version not compared with the preprint |
| L10 | Girolimetto & Di Fonzo (2024; online 21 Dec 2023). *Point and probabilistic forecast reconciliation for general linearly constrained multiple time series.* Stat. Methods Appl. 33, 581–607. doi:10.1007/s10260-023-00738-6 | A (Crossref abstract) | Methodological | Projection-based reconciliation for any linear constraints, not only hierarchies | Applies to a national price that is a **known-weight** mean of state prices | Weights must be known. CEDA's apparent weights (row counts) are random and unknown at forecast time. |
| L11 | Girolimetto, Panagiotelis, Di Fonzo, Li (2025). *Forecast reconciliation with non-linear constraints.* arXiv:2510.21249 | A | Methodological; demography and economics data | Projection onto a non-linear constraint surface (ratio variables) | Closest method for a price that is a ratio (sum of row prices ÷ row count) | Preprint. The abstract mentions ratios, not averages. Not applied to agricultural prices. |
| L12 | Qu, Timmermann, Zhu (2024). *Comparing forecasting performance with panel data.* Int. J. Forecast. 40(3), 918–941. doi:10.1016/j.ijforecast.2023.08.001 | P (working paper dated 27 Aug 2023; abstract, introduction and inference sections read) | Methodological | Panel Diebold–Mariano tests averaged over units and time, allowing cross-sectional dependence. Their simulations find that **many existing tests** over-reject under temporal or cross-sectional dependence. Inference with fewer than about 5 clusters is very restrictive. | Pooled test across states for H2 | Few states give little power; published version not compared |
| L13 | ILO, IMF, OECD, Eurostat, UNECE, World Bank (2004). *Consumer Price Index Manual: Theory and Practice*, ch. 7 "Adjusting for quality change". Successor edition: *Consumer Price Index Manual: Concepts and Methods* (2020), doi:10.5089/9781484354841.069 (M only). | F (2004 ch. 7, opening sections) | Methodological | Compare prices of the same matched items across periods; problems arise from missing, new and changing items | Established basis for the matched-mandi aggregate (H1) | The matched ("both-periods") comparison is **established index-number practice**, not a CropCast idea. The 2020 edition's wording was not checked. |
| L14 | Matched-model and unbalanced-panel price-index literature (NBER chapters; scanner-data panel indices, PMC6404774; BLS new-vehicle index) | S | Methodological | Matched-model bias from dropped and imputed items; composition shifts bias matched indices | Confounders for H1 (§4) | Snippets only |
| L15 | CEDA OpenAPI document (embedded in `api.ceda.ashoka.edu.in/documentation/`) and portal `agmarknet.ceda.ashoka.edu.in` | D | Official documentation | `state_id: 0` = "all India". `district_id` "will fetch data at the district level". No aggregation method stated. | Defines the endpoints | The pilot found the district-level description inaccurate: it returns mandi rows (RES-016). No methodology published. |
| L16 | Indian market-integration studies (e.g. ICAR *Indian J. Agric. Sci.* potato markets 2015–2024; onion cointegration studies including Lasalgaon and Azadpur) | S | Mandi-level price integration | Cointegration and Granger causality | Supports cross-market information for H2 | Snippets only; descriptive, not forecast evaluations |
| L17 | *Sentinel Assam* report on market committees not updating Agmarknet | S (page not opened) | News | — | Administrative evidence that reporting is incomplete and varies by institution, a possible reason for non-random reporting | News source, not research |

---

## 3. Comparison matrix

| Category | Item | Basis |
|---|---|---|
| **1. Established prior work** | Mandi-level forecasting on Agmarknet with ML, deep learning and graph models | L1, L2, L3, L4 |
| | Cross-market and spatial information (lead–lag, GNN, cointegration) | L1, L2, L16 |
| | Combined forecasting and anomaly work on Indian onion and potato | L2 |
| | Heavy, uneven mandi-level missingness, usually handled by imputation or by dropping sparse mandis | L1 (46% missing), L3, L4 |
| | Matched-model and fixed-sample comparison as the standard remedy for composition change in price indices | L13, L14 |
| | Reconciliation for summing hierarchies (MinT), general linear constraints, and non-linear (ratio) constraints | L7–L11 |
| | Panel tests for comparing forecasts across many series | L12 |
| **2. Evidence for a possible gap** | No source examined measures how the **changing set of reporting mandis** moves **aggregate** (state or national) price series, or how much apparent **forecast skill** on such aggregates comes from predictable composition changes | Searches Q2, Q6, Q7, Q8, Q12, Q14. L5 names the problem without quantifying it. |
| | Our pilot shows the CEDA state series is an unweighted mean of mandi rows (Maharashtra onion, 2022 Q1), so composition is mechanically part of the forecast target. Mandi counts drop on Saturdays and Sundays. | RES-016 |
| | No application of reconciliation to Indian crop prices was found | Q3, Q4, Q11 |
| **3. Unresolved questions** | Does the row-mean rule hold for potato, other states and earlier years? (ISS-002 suggests a 2016–2017 regime.) | Needs mandi-level data |
| | What is CEDA's national rule: a mean over all India's rows, a weighted mean of state means, or something else? | L15 gives none; pilot ratios are inconclusive |
| | How much of the v1 potato gain over naive is composition? | Needs H1 |
| | Are reporting gaps informative (e.g., mandis skip days when prices are extreme)? | Cannot be tested without mandi-level data; even then only partially, because absence is not explained |
| | Is cross-state information useful at state-aggregate level once composition is controlled? | H2 |
| **4. Claims not currently justified** | "Novel algorithm" or "first to study X" | Focused search only (§1.2 caveat) |
| | "Real-time forecasting" | Latest CEDA record 2025-10-30 (RES-016) |
| | Any national forecast or reconciliation result | National rule unverified |
| | "Arrivals are a valid proxy for composition" | Never tested; now unnecessary, since counts are observable |
| | "The potato gain is a composition artefact" | Only a mechanism is shown; the effect size is unmeasured |
| | Generalising the Maharashtra-onion row-mean rule to all CEDA series | One state, one crop, one quarter |

---

## 4. Strongest defensible research gap (candidate, not a novelty claim)

**Established vs possible contribution.** Comparing prices only for units present in both periods (the matched-model, or "both-days", comparison) is an **established price-index method** (L13). CropCast does not propose it as new. CropCast's *possible* contribution is empirical: measuring how much forecast performance against naive on CEDA's mandi-average series changes when composition change is removed this way. That contribution is unconfirmed until H1 is tested, and its novelty is unestablished beyond the search scope in §1.2.

> Published Indian crop-price forecasting work examined here either forecasts individual mandis, often after imputing missing days, or uses averages over whichever mandis report, without measuring how changes in that set affect the series and the forecast evaluation. CEDA's state series appears to be an unweighted mean over reporting mandi rows, and the number of reporting mandis varies systematically by weekday. **Separating within-mandi price change from reporting-composition change, using the established matched-model approach, and measuring how forecast skill against naive differs between the published aggregate and a composition-controlled aggregate** is a specific, testable contribution not found in the sources examined.

- **What is not new:** the matched-model idea (L13) and the problem statement (L5). The possible contribution is the empirical measurement and its forecast-evaluation consequence for Indian mandi aggregates.
- **Confounders and limits of a fixed-mandi or matched-mandi comparison:**
  1. **Selection.** Consistently reporting mandis may be larger, more urban or more stable, so the panel aggregate measures a different market population. Price levels are therefore not comparable; changes are.
  2. **Panel drift over 10 years.** Mandis open, close and change reporting habits. A single fixed panel shrinks; a chained, matched-pair index avoids this but compounds small errors.
  3. **Leakage.** Choosing the panel by reporting over the full period uses future information. Membership must be fixed from training data only.
  4. **Sparse days.** A strict fixed panel may have few or no members on Sundays. Matched pairs (t−1 to t) still exist, but with higher variance.
  5. **Duplicate rows.** Up to 3 price rows per mandi-day with no variety field. Within-mandi row averaging changes variety mix and weights.
  6. **Non-random gaps.** If a mandi skips days because prices are extreme, both aggregates are biased in unknown ways. This can be described but not corrected.
  7. **A different target.** A composition-controlled series is a different forecast target. Showing that models gain less on it does not make the published-series gain "wrong". It changes its interpretation.
- **National coherence (H3)** is a weaker candidate. Methods exist (L10, L11), the national rule is unknown, and if it is a row-count-weighted mean the weights are random. H3 should stay conditional.

---

## 5. Proposed hypotheses and evaluation design

**Status:** H1a, H1b, H2 and H3 are **proposed hypotheses for researcher review**. They are not a finalised or preregistered protocol. A protocol v2.0 document would be written, approved and frozen before any confirmatory data is examined. Every numeric threshold below is **provisional** (§5.6).

### 5.1 Data periods and blinding
- **Development:** 2016-01-01 to 2022-12-31, the same 60/20/20 chronological split as v1. The v1 test results for Maharashtra onion and Uttar Pradesh potato are already known, so H1 on this period is **exploratory, not confirmatory**.
- **Proposed confirmatory out-of-time test:** 2023-01-01 to 2025-10-30, evaluated **once**, after protocol v2.0 is frozen and approved.
- **Audit of prior contact with 2023-01-01 to 2025-10-30** (checked against `reports/pilot_m8/request_log.json` and `src/analysis/pilot_m8.py`):
  - **Maharashtra onion and Uttar Pradesh potato:** no data from this period has been retrieved. Untouched.
  - **Karnataka onion and West Bengal potato (state level):** retrieved in the pilot. Only these were computed: row counts, date ranges, coverage and gap lengths, missing days by weekday, price–quantity date overlap, zero/null counts and modal-outside-band counts. No price levels, returns, volatility or forecasts were computed or viewed.
  - **Decisions informed by that contact:**
    - the end date 2025-10-30;
    - the observation that some gaps are source-wide;
    - listing these two states as having data.

    These concern data availability, not model, feature or threshold choices.
  - **Conclusion:** for Maharashtra and Uttar Pradesh the period can serve as a **confirmatory** test. For Karnataka and West Bengal it should be called a **held-out evaluation period with coverage inspected**: availability was seen, outcomes were not.
  - **Untouched future period:** none exists yet, because CEDA returned no data after 2025-10-30. If such data appears, it would be a genuinely untouched future test and should be reserved, not used for development.
- The two approved verification requests (national onion, January 2022; Uttar Pradesh potato, 2022) lie in the development period and do not touch the confirmatory period.

### 5.2 Common definitions
- **Target:** the price on the next market day with a price row (horizon h = 1, as in v1). A secondary horizon h = 7 may be pre-registered. Models predict log returns; metrics are on the price scale.
- **Published aggregate A_t:** CEDA's state `modal_price` (verified as the unweighted row mean only for Maharashtra onion, 2022 Q1).
- **Composition-controlled aggregate M_t (matched-mandi chained index):**
  - p̄_{i,t} = mean of mandi i's price rows on day t.
  - Δlog M_t = mean over mandis that report on both the previous market day and day t of (log p̄_{i,t} − log p̄_{i,t−1}).
  - M_t = A at the start × exp(cumulative sum).
  - No imputation. Days where fewer than k matched mandis exist are flagged; k is fixed in protocol v2.0; proposed k = 5 (provisional, §5.6).
- **Composition term:** C_t = Δlog A_t − Δlog M_t.

### 5.3 Missing data and special cases
- **Missing reports:** no row means "unobserved". Targets are never imputed. Feature windows use only observed values up to the origin.
- **Non-trading days:** zero arrivals and missing arrivals cannot be told apart (no zeros occur). Neither is filled with zero. Missing-quantity indicators may be features.
- **Repeated mandi-day rows:** averaged within the mandi-day for M_t. For A_t, CEDA's rule is reproduced as published. Sensitivity analysis: keep only mandi-days with one row.
- **Panel membership:** matched pairs are recomputed daily from observed data only. If a fixed-panel variant is reported, its members are those reporting on at least 80% (provisional, §5.6) of training-period market days, fixed before validation. Entries and exits are logged.

### 5.4 Hypotheses

- **H1a (descriptive, composition):**
  - Claim: the composition term C_t has a non-zero mean that differs by weekday.
  - Test: Kruskal–Wallis across weekdays, plus per-weekday sign tests; BH-adjusted across series. A block-bootstrap CI (7-day blocks) is reported for the share of Var(Δlog A_t) attributable to C_t.
  - Practical threshold: a weekday mean |C| ≥ 1% per day (provisional, §5.6).
- **H1b (forecasting, composition):**
  - Claim: the relative MAE gain of the pre-specified best v1 model over naive is larger on A than on M.
  - Statistic: D = (1 − MAE_model/MAE_naive)_A − (1 − MAE_model/MAE_naive)_M. Moving-block bootstrap CI over test days (block 7).
  - Within-series significance: DM with the HLN correction, BH-adjusted.
  - Supported if the CI for D excludes 0 **and** D ≥ 5 percentage points (provisional threshold, §5.6).
- **H2 (cross-state information):**
  - Claim: a pooled model using lagged prices from other states of the same crop beats (i) naive and (ii) the best per-state v1 model refit on identical observations.
  - Tests: DM-HLN per state, BH across states, plus a panel test (L12). Effect sizes reported.
  - Leakage control: other states' values enter only if dated before the forecast origin.
- **H3 (national coherence; conditional):**
  - Run only if CEDA's national rule is verified.
  - Claim: reconciling state and national forecasts under the verified rule (L10 if the weights are known; L11 if they form a ratio) improves coherence without worsening national or state MAE by more than 2% relative to base forecasts (provisional tolerance, §5.6).
  - Tests: equivalence-style comparison with block-bootstrap CIs against the 2% margin.
  - Weights for the forecast day come only from lagged information.
  - If the rule is not verified, H3 is dropped, not approximated.

### 5.5 Multiple comparisons and dependence (limitations)

| Family | Comparisons (if run on Maharashtra onion and Uttar Pradesh potato) | Adjustment | Dependence concern |
|---|---|---|---|
| H1a | 2 series × (1 Kruskal–Wallis + 7 weekday sign tests) = 16 | BH within the family | Weekday tests within a series share one series. BH is guaranteed under independence or positive regression dependence (PRDS), which two-sided tests on correlated statistics may not satisfy. Benjamini–Yekutieli (valid under any dependence) is reported as a sensitivity check. |
| H1b | 2 bootstrap intervals for D, plus 2 DM tests per aggregate | BH across the 2 series | Little to adjust with 2 tests. The bootstrap uses moving blocks of 7 days to respect weekly dependence. |
| H2 | k states × 2 baselines | BH across states; panel test only if k ≥ 5 | States share common shocks. L12 shows many panel tests over-reject under dependence and that inference with fewer than about 5 clusters is very restrictive. |
| H3 | conditional | — | — |

**Diebold–Mariano limitations:**
- With h = 1, the HLN-corrected statistic uses a variance with no autocovariance terms (h − 1 = 0). The weekly structure found in EDA (RES-015) may leave loss differentials serially correlated.
- Proposed check: also report a HAC (Newey–West) variance with a pre-specified 7-lag truncation as a sensitivity analysis.
- DM compares forecasts, not models. When one model nests another and models are re-estimated recursively, standard DM asymptotics may not apply. This is a known issue whose references have not yet been checked in this review; results are described as forecast comparisons only.

**Significance vs importance:** a BH-significant result is not called important unless it also meets the practical threshold for its hypothesis. Effect sizes with confidence intervals are always reported.

### 5.6 Provisional researcher decisions (no empirical or literature basis yet)

| Item | Proposed value | Status and rationale |
|---|---|---|
| H1b practical threshold | D ≥ 5 percentage points | **Provisional.** Analyst placeholder: about one fifth of the v1 potato gain over naive (26.3%), large enough to change how that gain is interpreted. Not derived from data or literature. The researcher should set it before protocol v2.0 is frozen. |
| H3 accuracy tolerance | ≤ 2% MAE worsening | **Provisional.** Analyst placeholder with no empirical basis. |
| H1a practical threshold | weekday mean of the composition term ≥ 1% per day | **Provisional.** Analyst placeholder. |
| Minimum matched mandis per day | k = 5 | **Provisional.** Mirrors ACROP's minimum mandi count for national figures (L5); not validated for CEDA. |
| Fixed-panel membership | ≥ 80% of training-period market days | **Provisional.** Analyst placeholder. |
| HAC truncation lag | 7 | **Provisional.** Chosen to match the weekly cycle (RES-015). |

### 5.7 Statistical and procedural rules
- **Metrics:** MAE (primary), RMSE and MASE.
- **Significance:** α = 0.05 after BH adjustment within each hypothesis family (§5.5), with Benjamini–Yekutieli as a sensitivity check.
- **Significance vs practical:** both are reported. A result is described as a practical improvement only if it meets the pre-stated threshold.
- **No retuning:** model grids are the v1 grids. No grid changes, threshold changes or target redefinitions after the confirmatory period is examined.

---

## 6. Sources cited (stable identifiers)

- **L1** — arXiv:2304.09761 — https://arxiv.org/abs/2304.09761
- **L2** — doi:10.1145/3314344.3332488 — PDF: https://www.cse.iitd.ac.in/~parags/papers/conference/2019/pfadaci-compass19.pdf
- **L3** — arXiv:1812.05173 — https://arxiv.org/abs/1812.05173
- **L4** — arXiv:2009.04171 — https://arxiv.org/abs/2009.04171
- **L5** — https://acrop.app/methodology
- **L6** — doi:10.1007/s44564-026-00015-0
- **L7** — doi:10.1016/j.csda.2011.03.006
- **L8** — doi:10.1080/01621459.2018.1448825
- **L9** — doi:10.1016/j.ijforecast.2023.10.010 — preprint: https://robjhyndman.com/papers/hf_review.pdf
- **L10** — doi:10.1007/s10260-023-00738-6 — preprint: https://arxiv.org/abs/2305.05330
- **L11** — arXiv:2510.21249 — https://arxiv.org/abs/2510.21249
- **L12** — doi:10.1016/j.ijforecast.2023.08.001 — working paper: https://rady.ucsd.edu/_files/faculty-research/timmermann/Panel_DM.pdf
- **L13** — https://webapps.ilo.org/CPI/doc/ch7.pdf (2004 Manual, ch. 7); 2020 edition doi:10.5089/9781484354841.069
- **L14** — https://pmc.ncbi.nlm.nih.gov/articles/PMC6404774/ ; https://www.bls.gov/osmr/research-papers/2019/pdf/ec190040.pdf
- **L15** — https://api.ceda.ashoka.edu.in/documentation/ ; https://agmarknet.ceda.ashoka.edu.in/
- **L16** — https://epubs.icar.org.in/index.php/IJAgS/article/view/169134 (others: snippets only)
- **L17** — https://www.sentinelassam.com/topheadlines/assam-marketing-board-pulled-up-for-not-updating-data-on-agmarknet-portal
