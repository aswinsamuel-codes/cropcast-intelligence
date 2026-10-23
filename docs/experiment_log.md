# CropCast — Experiment Log

Every experiment run is recorded here with full configuration and results.

Each entry records: objective, hypothesis, dataset version, configuration hash, random seed, evaluation method, metrics, output references, interpretation, and known limitations.

---

## Entry Template

```
### EXP-NNN: [Short Experiment Name]
- **Date:** YYYY-MM-DD
- **Phase:** [Forecasting / Anomaly Detection / Other]
- **Objective:** [What this experiment is testing]
- **Hypothesis:** [Expected outcome and why]
- **Dataset version:** [identifier or hash of raw data file used]
- **Configuration hash:** [hash of full experiment config]
- **Random seed:** [value used]
- **Feature set:** [list of features used]
- **Model / method:** [name and hyperparameters]
- **Evaluation method:** [walk-forward / held-out / synthetic shocks]
- **Split:** [train / validation / test date ranges or percentages]
- **Metrics:**
  - MAE: [value]
  - RMSE: [value]
  - MAPE: [value or N/A with reason]
  - Other: [precision, recall, F1 if applicable]
- **Output files:** [figures, reports, predictions produced]
- **Interpretation:** [what the results mean]
- **Limitations:** [caveats, data issues, scope restrictions]
- **Status:** [Completed / Failed / Inconclusive]
```

---

## Entries



### EXP-001: Forecasting comparison, run A (pre-registered protocol v1.1)
- **Date:** 2026-10-23 18:06Z – 18:55Z (UTC)
- **Phase:** Forecasting (M-5)
- **Objective:** Compare five candidate models with the naive and seasonal-naive baselines for the next-market-day modal price.
- **Hypothesis (stated in the protocol before results):** at h = 1 the naive forecast is hard to beat, and "no improvement" is a valid outcome.
- **Dataset version:** `v1:b5f21e02b681` · **Random seed:** 20261023 · **Configuration hashes:** per model in `reports/experiment_log.jsonl` (72 records: 58 validation, 14 test)
- **Feature set:**
  - Price lags 1, 2, 3, 5 and 7; rolling mean and SD over 7 and 14 market days; day of week and month of the origin; day of week of the target; arrivals at lags 1 and 2.
  - Inputs enter as log ratios; the target is the next log return.
- **Evaluation method:**
  - 60/20/20 chronological split.
  - Validation walk-forward with refits every 7 steps, used for selection (by validation MAE).
  - Test walk-forward with refits at every step (Req 5.6).
  - DM test with the HLN correction (absolute loss) against naive, with one BH adjustment across all 12 comparisons.
- **Run record:** `reports/runs/forecasting-retrospective-20261023T180644/` (RETROSPECTIVE manifest: the code was uncommitted at run time, and `run.py` was edited on disk during the run without affecting it).
- **Independent verification:**
  - `src.reporting.verify_results` on the full-precision regeneration: 14 rows × 7 statistics, 0 problems.
  - Selected configuration equals the argmin of validation MAE in every family.
  - Test targets match the protocol split exactly.
- **Metrics (test; MAE in INR/quintal; full precision in the run folder):**

| Series | Model | MAE | vs naive | DM (HLN) | BH p | Verdict |
|---|---|---|---|---|---|---|
| Onion | ETS (no trend) | 60.04 | −4.3% | −1.52 | 0.174 | no significant difference |
| Onion | SARIMA(1,1,1)(1,0,1)₇ | 60.58 | −3.5% | −1.41 | 0.190 | no significant difference |
| Onion | Random forest | 61.63 | −1.8% | −0.76 | 0.486 | no significant difference |
| Onion | Naive | 62.75 | — | — | — | baseline |
| Onion | Linear regression | 63.71 | +1.5% | 0.57 | 0.566 | no significant difference |
| Onion | Decision tree | 65.36 | +4.2% | 1.52 | 0.174 | no significant difference |
| Onion | Seasonal naive (7) | 142.46 | +127.0% | 12.44 | 2.1e-30 | significantly worse |
| Potato | Random forest | 10.77 | −26.3% | −7.93 | 5.5e-14 | improves on naive |
| Potato | SARIMA(2,1,2)(1,0,1)₇ | 10.97 | −25.0% | −6.87 | 5.6e-11 | improves on naive |
| Potato | ETS (damped additive trend) | 11.14 | −23.8% | −6.23 | 2.3e-09 | improves on naive |
| Potato | Linear regression | 11.85 | −18.9% | −5.46 | 1.5e-07 | improves on naive |
| Potato | Decision tree | 12.01 | −17.9% | −5.27 | 3.5e-07 | improves on naive |
| Potato | Naive | 14.61 | — | — | — | baseline |
| Potato | Seasonal naive (7) | 38.75 | +165.1% | 15.51 | 1.1e-43 | significantly worse |

  The selected SARIMA orders were (1,1,1)(1,0,1)₇ for onion (the third-ranked AIC order, chosen on validation MAE) and (2,1,2)(1,0,1)₇ for potato (the top-ranked AIC order). The selected ETS was no trend for onion and a damped additive trend for potato. Source: `selected_params` in the metrics table. *(Corrected 2026-10-24: the first draft of this entry misstated the onion SARIMA order and the potato ETS trend; the final report uses generated tables.)*
- **Interpretation:**
  - **Onion:** no model differs significantly from naive.
  - **Potato:** all five candidates improve on naive.
  - **Seasonal naive:** much worse than naive for both series. The weekly *return* autocorrelation does not make the price from 7 market days earlier a good level forecast.
- **Exploratory, post-hoc analysis (not pre-registered; unadjusted p-values):**
  - The potato gains are concentrated on Sunday and Monday targets: random forest MAE is −47% (Sunday) and −50% (Monday) relative to naive, against −5.5% to −15% on Tuesday–Saturday.
  - On Tuesday–Saturday targets only, potato RF is −8.4% versus naive (DM −3.66, p = 3e-4), SARIMA −6.4% (p = 0.04) and ETS −5.8% (p = 0.07).
  - On Tuesday–Saturday targets, onion models are 0.3–3.1% *worse* than naive.
  - **Interpretation:** most of the potato improvement comes from anticipating the weekly reporting-composition pattern (EDA §3), not general market dynamics.
  - The potato gains hold in all three test half-years (−19% to −35% for RF).
- **Limitations:**
  - The test period (Aug 2021 – Dec 2022) excludes the 2019/2020 spikes.
  - The SARIMA residual Ljung–Box test at lag 14 on training data gives p = 0.014 for the top potato order, so some residual autocorrelation remains.
  - Random-forest predictions in this run used parallel prediction (ISS-012, ~1e-16 nondeterminism).
  - The SARIMA/ETS warning counts were not captured for this run.
- **Status:** Completed (verified)

### EXP-002: Anomaly screening, run 1 (pre-registered protocol v1.0)
- **Date:** 2026-10-23 19:03Z – 19:28Z (UTC)
- **Phase:** Anomaly detection (M-6)
- **Objective:** Screen both series for market-relative contextual point anomalies, and evaluate the screen against weak labels and synthetic shocks, reported separately.
- **Hypothesis:** none on accuracy. This is screening, not a validated detector, and there is no independent ground truth.
- **Dataset version:** `v1:b5f21e02b681` · **Random seed:** 20261023 · **Run:** `reports/runs/anomaly-20261023T190355Z-a927040a/` (clean start at `cd56566`; one unrelated file was created during the run, see its PROVENANCE_NOTE)
- **Configuration:**
  - Residual SARIMA uses the top training-AIC order: (0,1,2)(1,0,1)₇ for onion, (2,1,2)(1,0,1)₇ for potato.
  - z-score window 30; robust windows 28/52/56; causal standardisation with a minimum of 90 prior values; threshold 3.
- **Independent verification:** `verify_anomaly --full`, 368 checks, 0 problems. It covers scores, burn-in, detections at 5 thresholds, weak-label metrics, SARIMA residuals, and all 80 shock runs (positions, recall and FPR).
- **Results (verified; tables in `reports/anomaly_analysis.md`):**
  - **Detections at |score| > 3:** onion 26 (residual), 38 (robust), 23 (composite); potato 28, **0**, 26. Between 26% and 54% of detections are coverage anomalies or Sunday/Monday days.
  - **Weak labels:** ICTD windows cover 59% (onion) and 72% (potato) of evaluated days. No method's precision exceeds the circular-shift baseline (p = 0.46–0.92), and recall is 0–1.6%. The labels are uninformative here.
  - **Synthetic shocks:**
    - Potato: residual and composite recall is 1.00 at every magnitude from ±10%.
    - Onion: residual recall is 0.10 at ±10% and 1.00 at ±50%.
    - Robust recall is 0–0.77.
    - False-positive rate on clean days is 0.005–1%.
- **Limitations:**
  - The potato robust score is silent, because of trend contamination and non-robust re-standardisation (ISS-015).
  - 5 SARIMA fits stopped abnormally; the impact is assessed as negligible (ISS-014).
  - The scoring window starts in March 2017, so the ISS-002 regime is almost entirely unscored.
- **Status:** Completed (verified, with documented limitations)
