# CropCast — Anomaly Screening Protocol (M-6)

**Version:** 1.0 · **Fixed on:** 2026-10-23, before any anomaly score or evaluation result was computed · **Dataset:** v1 · **Config:** `configs/config.json` → `anomaly`
**Basis:** Req 6; DEC-017; `reports/eda_report.md` §3, §5, §6; `reports/literature_review.md` §4.

## 1. What is being detected

A **market-relative contextual point anomaly**: a market day whose state-level modal price deviates unusually from what the same market's own prior history predicts, after allowing for that market's weekday pattern.
- No peer markets exist in the approved data (DEC-017). "Market-relative" therefore means relative to the market's own one-step forecast and its own trailing robust baseline.
- **Framing:** no independent, verified ground truth exists. This is **exploratory anomaly screening**, not a validated classifier, and no detection accuracy is claimed.

## 2. Signals (all causal: a score at day t uses only data before t, except y_t itself)

1. **Residual signal (Req 6.1–6.2):**
   - e_t = log y_t − log ŷ_t, where ŷ_t is the one-step forecast of a seasonal ARIMA (period 7) on log prices.
   - The order is the lowest **training-set** AIC order from M-5 (`forecast_sarima_aic.csv`). It is fit on an expanding window from market day 182, refit every 28 origins, with state updates in between.
   - Score: z-score of e_t against the previous 30 residuals.
2. **Robust baseline signal** (substitute for peer divergence, DEC-017):
   - d_t = log y_t − median(log y over the previous 28 market days).
   - Subtract the median d over the previous 52 same-weekday days (the weekday composition offset; EDA §3).
   - Scale by 1.4826 × MAD over the previous 56 market days (Leys et al., 2013; Rousseeuw & Croux, 1993).
3. **Composite (Req 6.4):** the weighted sum (0.5/0.5) of the two signals.
   - **Deviation from Req 6.4 wording:** signals are standardised with the expanding mean and SD of **earlier** values only (minimum 90), not over the whole evaluation window, so no future information enters a score. The composite is re-standardised the same way, so thresholds are comparable across methods.

## 3. Threshold

- A day is flagged when |score| > **3**. That is the "very conservative" cut-off for MAD-based outlier rules discussed by Leys et al. (2013), and it is fixed before seeing results.
- Sensitivity is reported for thresholds 2.5, 3, 3.5, 4 and 5. Daily returns are heavy-tailed (EDA §1), so Gaussian false-positive rates do not apply, and the realised detection rate is reported instead.

## 4. Ablation (Req 6.5, adapted under DEC-017)

Three scores are compared: residual-only, robust-only and composite. Peer configurations do not apply.

## 5. Evaluation, with each part reported separately (Req 6.6–6.7)

1. **Real data:**
   - Detections per method.
   - Each detection is classified as a **coverage anomaly** (arrivals below 10% of the median, or `flag_extreme_arrival`; ISS-003 type), a **band violation** (`flag_modal_outside_bounds`; ISS-002 type), **Sunday/Monday** (composition-prone; EDA §3), or **other**.
   - Data-quality classes are reported apart from candidate market events.
2. **Weak-label agreement:**
   - Reference: ICTD-IITD windows (Madaan et al., 2019) for the same state, in which any of `lastMonth`, `lastYear` or `SameMonth` equals "Anomaly".
   - These are mandi-level, rule-based flags derived from the same Agmarknet source. They are **endogenous weak references, not ground truth**.
   - Precision, recall and F1 (Req 6.6) are reported with the label base rate. A randomisation baseline (1,000 circular shifts of the detection sequence, seeded) tests whether the agreement exceeds chance.
3. **Synthetic shocks (Req 6.7):**
   - One-day multiplicative shocks of ±10, 20, 30 and 50% are injected into the held-out test segment (Aug 2021 – Dec 2022): 6 shocks per run, at least 60 market days apart, 5 seeded repeats per magnitude.
   - Recall is computed on the shocked days. The false-positive rate is computed on clean days, excluding the 7 days after each shock.
   - For feasibility, the residual model's parameters are frozen at the start of the segment, with state updates only.
   - These results are synthetic and are never merged with real-data results.

## 6. Limitations fixed in advance

- **Burn-in:** scores exist only after the residual and robust windows fill (from late 2016). Most of the ISS-002 regime (2016 – Apr 2017) therefore falls before or near the start of scoring.
- **Weekday adjustment:** the composition effect may still produce Sunday/Monday detections. These are labelled, not hidden.
- **Synthetic shocks:** they test sensitivity to isolated spikes only, not to gradual or collective anomalies.
