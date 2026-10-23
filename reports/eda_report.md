# CropCast — Exploratory Data Analysis (M-3)

**Date:** 2026-10-23 · **Dataset:** v1 (`v1:b5f21e02b681`, DEC-019) · **Code:** `src/analysis/eda.py` · **Outputs:** `reports/tables/eda_*.csv`, `reports/tables/eda_summary.json`, `figures/fig01–fig12`

Reproduce with `.venv/Scripts/python -m src.analysis.eda`. Every number below is taken from the saved outputs. Labels used: **[Observed]** for measurements, **[Hypothesis]** for explanations not verifiable from these data, and **[Protocol]** for consequences for modelling.

Data credit: CEDA Agri Market Data, Centre for Economic Data and Analysis (CEDA), Ashoka University; original source DMI, Ministry of Agriculture and Farmers Welfare (Agmarknet). Prices are in INR per quintal; arrivals are in tonnes (RES-008).

## 1. Coverage and data quality

**[Observed]**
- **Maharashtra onion:** 2,523 of 2,557 calendar days are observed. The 34 missing days form 13 gaps: six single days, three 2-day, two 3-day, one 6-day (2020-04-08..13) and one 10-day gap (2020-10-16..25), listed in `eda_gaps_onion_maharashtra.csv` and shown in Figure 3. 20 of the 34 missing days fall in 2020. Missing days are spread across weekdays (Fri 7, Sun 7, Sat 6, Mon 5, Thu 5, Wed 3, Tue 1).
- **Uttar Pradesh potato:** all 2,557 days are observed.
- No duplicates, nulls, non-finite or negative values were found (M-2 audit).

**Table 1. Descriptive statistics** (from `eda_descriptive_stats.csv`; prices in INR/quintal, arrivals in tonnes)

| Series | Variable | Mean | Median | SD | Min | Q25 | Q75 | Max | Skew |
|---|---|---|---|---|---|---|---|---|---|
| Onion | Modal price | 1,388.3 | 1,079.3 | 963.2 | 406.2 | 710.0 | 1,755.6 | 7,506.5 | 2.14 |
| Onion | Arrivals | 16,323 | 15,664 | 9,002 | 2 | 9,069 | 22,739 | 45,648 | 0.34 |
| Onion | Daily log return | 0.000 | 0.001 | 0.078 | −0.584 | −0.040 | 0.039 | 0.533 | −0.12 |
| Potato | Modal price | 1,016.9 | 952.1 | 493.5 | 433.6 | 646.3 | 1,230.3 | 3,015.2 | 1.51 |
| Potato | Arrivals | 15,364 | 14,683 | 8,594 | 442 | 9,251 | 19,920 | 113,475 | 2.20 |
| Potato | Daily log return | 0.000 | 0.000 | 0.023 | −0.204 | −0.010 | 0.011 | 0.172 | 0.01 |

Both price series are right-skewed: the potato mean is 7% above its median and the onion mean 29% above. Daily log returns are heavy-tailed, with excess kurtosis 5.0 for onion and 8.4 for potato (Figure 11).

## 2. Price behaviour

**[Observed]**
- **Trend and spikes (Figure 1; Table 2):**
  - Onion's annual mean modal price ranges from 742 (2016) to 1,904 (2019). Its largest spike reached 7,506 in December 2019, and the within-year coefficient of variation reached 0.88 in 2019.
  - Potato ranged from an annual mean of 487 (2017, CV 0.06) to 1,799 (2020). Its 2020 surge peaked at 3,015 and collapsed in December 2020.
- **Seasonality (Figures 4, 5):**
  - The decomposition model was chosen by the Req 3.6 rule: across years, the standard deviation of monthly prices rises with their mean (Spearman 0.82 for onion, 0.89 for potato), so both series use a multiplicative model (STL on log monthly means).
  - Potato has the stronger annual seasonality (STL seasonal strength 0.42 vs 0.24 for onion). Its seasonal peak is in August and trough in February.
  - Onion's seasonal pattern is less regular: it peaks in November and troughs in April. Its median modal price by month runs from 693 (May) to 2,115 (November).
- **Stationarity (`eda_stationarity.csv`):**
  - Log price levels give conflicting results (ADF p = 0.012 for onion and 0.023 for potato, while KPSS rejects stationarity with p ≤ 0.01).
  - Daily log returns are stationary by both tests (ADF p < 0.001; KPSS p ≥ 0.10).
- **Volatility (Figure 7):**
  - Onion is far more volatile: the daily log-return SD is 0.078 against 0.023 for potato, and 16.7% of onion day-to-day moves exceed ±10% against 0.5% for potato.
  - Variance differs significantly across years for both series (Brown–Forsythe p < 0.001).
- **Largest moves (`eda_extreme_moves.csv`):** these are one-day spike-and-revert pairs, for example 2019-03-03 (+70%) followed by 2019-03-04 (−44%), and 2016-01-24 (+53%) followed by 2016-01-25 (−35%). Both spike days are Sundays.

**Table 2. Annual summary of modal price** (from `eda_annual_summary.csv`)

| Year | Onion mean | Onion min–max | Onion CV | Potato mean | Potato min–max | Potato CV |
|---|---|---|---|---|---|---|
| 2016 | 742 | 455–1,686 | 0.23 | 998 | 448–1,523 | 0.35 |
| 2017 | 1,230 | 418–3,335 | 0.67 | 487 | 434–610 | 0.06 |
| 2018 | 1,047 | 480–3,031 | 0.50 | 949 | 457–1,260 | 0.30 |
| 2019 | 1,904 | 406–7,506 | 0.88 | 762 | 529–1,278 | 0.22 |
| 2020 | 1,784 | 573–4,571 | 0.59 | 1,799 | 971–3,015 | 0.34 |
| 2021 | 1,737 | 827–3,441 | 0.34 | 945 | 645–1,445 | 0.19 |
| 2022 | 1,299 | 760–2,288 | 0.30 | 1,176 | 763–1,637 | 0.24 |

## 3. Weekly structure and the weekday composition effect

**[Observed]** (Figures 6 and 12; `eda_acf.csv`, `eda_weekday_profile.csv`)
- **Autocorrelation of daily log returns:**
  - Lag 1: −0.32 (onion) and −0.30 (potato).
  - Lag 7: +0.31 and +0.38; lag 14: +0.26 and +0.30.
  - The 95% band is about ±0.04.
- **Weekday differences:** returns differ across weekdays (Kruskal–Wallis H = 254 for onion and 564 for potato; Benjamini–Hochberg-adjusted p < 10⁻⁵⁰).
- **Sunday:** median arrivals collapse on Sundays, to 6,348 t for onion and 7,544 t for potato, against roughly 15,000–21,000 t on other days.
  - Onion's Sunday modal price averages +3.7% above its centred 7-day mean; potato's averages −1.5%.
  - The mean absolute return is highest on Sundays and Mondays, the days into and out of the low-arrival day.
- **Annual autocorrelation:** autocorrelation of log levels at lag 365 market days is weak (0.19 for onion, 0.07 for potato).

**[Hypothesis]** The state series is an aggregate over the mandis that report each day. On Sundays far fewer mandis trade, so the daily figure reflects a different and smaller set of markets. That shift in the reporting mix, rather than any change in market prices, would produce the weekly pattern and the Sunday spike-and-revert moves. Mandi-level reporting counts are not in the data, so this cannot be verified here.

**[Protocol]**
- The dominant seasonal period for the seasonal-naive baseline is **weekly (7 market days)**, not annual (Req 5.2).
- Day-of-week is a required feature (Req 4.4).
- The anomaly detector must condition on weekday, or one-day composition swings will dominate the detections (Section 6).

## 4. Price–arrival relationship

**[Observed]** Monthly means, 84 months (Figure 8). Correlations of levels are distorted by shared trends, so the inference uses month-on-month changes, with 95% intervals from a moving-block bootstrap (block 6 months, 2,000 replicates, seeded).
- **Potato:** Spearman ρ between changes in log price and log arrivals is **−0.60 [−0.74, −0.34]**. Lagged correlations are −0.56 when arrivals lead by one month and −0.31 at two months.
- **Onion:** ρ = **−0.20 [−0.41, −0.05]**. Lagged correlations are near zero (−0.04, 0.00, 0.01 at lags 1–3).
- **Cross-commodity:** the onion–potato correlation of monthly log modal prices is 0.16 (Figure 9). These are different markets, not peers (DEC-017).

**[Interpretation]**
- These are associations in observational data and do not establish that arrivals cause prices.
- The negative sign is consistent with supply-driven price movements, especially for potato.
- The one-month-lead association for potato may reflect persistence in arrival changes rather than prices responding to arrivals.

**[Protocol]** Lagged arrivals are included as a feature (Req 4.5). Their incremental value is tested empirically and not assumed.

## 5. ISS-002 — Potato modal prices outside [min, max]

**[Observed]** (Figure 10; `eda_summary.json` → `iss002`)
- The modal price's position within the band, (modal − min)/(max − min), has a median of **0.07** for potato between 2016-03-04 and 2017-04-02, against **0.50** in all other periods. Onion stays near 0.61 throughout.
- The low-position regime is already present when the data begins in January 2016. It ends abruptly around April 2017, after which the potato position is stable near 0.5.
- The 137 modal-below-minimum days are the extreme tail of this regime. Monthly counts peak in May 2016 (28) and April 2016 (23).
- The relative band width (max/min) is similar in and out of the regime (medians 1.09 and 1.13).

**[Assessment]**
- The abrupt and lasting shift points to a **change in source reporting or aggregation** around April 2017, not to market behaviour.
- CEDA's methodology documentation could not be retrieved (HTTP 404, RES-014), so the mechanism stays **unresolved**.
- No values are changed. The rows keep `flag_modal_outside_bounds`.

**[Protocol]**
- `modal_price` is the forecast target throughout and is used as reported.
- Potato `min_price`/`max_price` are not used as features: their relationship to the modal price changes across the regime.
- The 2016-03 – 2017-04 regime falls inside the training period (Section 7), so it cannot contaminate test metrics.

## 6. ISS-003 — Near-zero onion arrivals

**[Observed]** (`eda_iss003_extreme_arrivals.csv`, Figure 2)
- Ten onion days have arrivals below 1/100 of the series median (2–150 t): 2020-03-22, 2020-04-21/22/24/25/28/29, 2020-10-26, 2020-11-14 and 2021-05-01.
- On 8 of these 10 days, the modal price is a whole number, against **4.6%** of all onion days (Fisher exact p = 6×10⁻¹⁰). The min and max prices on those days are also round values.
- Modal prices on these days are not extreme relative to the prior 14 days. For example, 2020-04-28 had a modal of 1,000 against a prior median of 1,014.

**[Assessment]**
- **[Hypothesis]** A state mean over many mandis is rarely a whole number. Whole-number prices together with near-zero arrivals therefore suggest that **only one or a few mandis reported** on those days.
- Seven of the ten dates (22 March, and 21–29 April 2020) fall in the weeks around the start of India's nationwide COVID-19 restrictions. A 21-day national lockdown was announced on 24 March 2020, in force from 25 March to 14 April (INGSA COVID-19 Policy-Making Tracker, citing PIB release 1607995; the PIB page itself returned HTTP 403). Whether restrictions were still in force on 21–29 April 2020 was not verified for this report. 22 March 2020 is reported in secondary sources as a nationwide "Janata Curfew".
- **[Protocol]** These are treated as **coverage anomalies**, not as market events. They are kept in the data and flagged. The anomaly study reports them separately from price anomalies.

## 7. Implications for the forecasting protocol (M-4)

1. **Target:** next-market-day modal price on market-day sequences. Onion has 34 calendar-day gaps (1.3%). Lags are defined in market days, so no imputation is needed (Req 4).
2. **Models in log space:** returns are stationary, the series are skewed, and the seasonal pattern is multiplicative. Errors are reported in INR on the original scale.
3. **Baselines:** naive (last observed price) and weekly seasonal naive (7 market days earlier), per Sections 2–3.
4. **ARIMA:** eligible under Req 5.5. Log returns pass ADF at 5% with more than 2,000 observations, and the ACF shows short-run (lag 1) and weekly (lags 7 and 14) structure. A seasonal ARIMA with period 7 is therefore justified.
5. **Split:** a chronological 60/20/20 split by market day gives these periods:
   - **Onion:** train 2016-01-01..2020-03-02, validation 2020-03-03..2021-08-13, test 2021-08-14..2022-12-31.
   - **Potato:** train 2016-01-01..2020-03-13, validation 2020-03-14..2021-08-06, test 2021-08-07..2022-12-31.
   - The ISS-002 regime and the 2019 onion spike fall in training.
   - Validation contains the COVID-19 period, the potato 2020 surge and collapse, and the ISS-003 days, so tuning happens on an unusually volatile period.
   - The test period contains neither the ISS-002 regime nor the 2019/2020 spikes. Test results describe a calmer period and must not be generalised to spike episodes.
6. **Anomaly scoring** must condition on weekday or work on weekday-adjusted residuals, and must report coverage anomalies (ISS-003) separately.

## Figures

- Figure 1 `fig01_price_series.png`: daily modal price with the [min, max] band.
- Figure 2 `fig02_arrival_series.png`: daily arrivals (log scale), with the flagged near-zero days marked.
- Figure 3 `fig03_missingness_heatmap.png`: observed and missing days by year and day of year.
- Figure 4 `fig04_monthly_boxplots.png`: modal price by calendar month.
- Figure 5 `fig05_stl_decomposition.png`: STL decomposition of log monthly means.
- Figure 6 `fig06_acf_*.png`: ACF of daily log returns and of log levels.
- Figure 7 `fig07_rolling_volatility.png`: rolling 30-day volatility.
- Figure 8 `fig08_price_arrival_monthly_changes.png`: monthly changes in price against monthly changes in arrivals.
- Figure 9 `fig09_correlation_heatmap.png`: Spearman correlation of monthly log levels.
- Figure 10 `fig10_modal_position_iss002.png`: position of the modal price within the [min, max] band.
- Figure 11 `fig11_return_distributions.png`: distributions of daily log returns.
- Figure 12 `fig12_weekday_composition.png`: weekday arrivals and price deviations.

## Limitations

- These are state aggregates of unknown mandi composition. The weekday and ISS-003 explanations are hypotheses consistent with the evidence, not verified facts.
- Monthly price–arrival analysis has only 84 observations. The block-bootstrap intervals assume dependence of roughly six months or less.
- CEDA's aggregation method is undocumented, which leaves ISS-002 unresolved.
