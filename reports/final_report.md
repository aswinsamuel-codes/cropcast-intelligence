# CropCast: A Data-Driven Framework for Agricultural Commodity Price Forecasting and Market-Relative Anomaly Detection

**Course:** Data Science Ecosystem (DSE), 23CS2024 · **Problem reference:** SIH1647 · **Repository:** github.com/aswinsamuel-codes/cropcast-intelligence · **Date:** October 2026

## Abstract

We study daily state-level wholesale prices and arrivals for Maharashtra onion and Uttar Pradesh potato (2016–2022), using CEDA Agri Market Data processed through a checksum-verified, reproducible pipeline. Exploratory analysis shows that weekly reporting-composition effects dominate daily dynamics, alongside a 2016–2017 source-side reporting regime and partial-reporting days around the 2020 lockdown.

Under a pre-registered, leakage-free protocol, five models were compared with naive and seasonal-naive baselines on one-day-ahead forecasts: linear regression, decision tree, random forest, seasonal ARIMA and exponential smoothing. Every test step used walk-forward refitting, with Diebold–Mariano tests and false-discovery-rate control. For onion, no model differs significantly from the naive forecast. For potato, all five candidates improve on it, the best by about 26% in MAE, but an exploratory breakdown attributes most of this gain to predictable weekly composition effects.

A causal, weekday-aware anomaly screen mainly surfaces data-coverage and composition events. ICTD weak labels cover 59–72% of days and cannot validate it, and synthetic shocks show that the smallest detectable shock grows with the series' volatility. All results were recomputed independently from saved predictions, and two complete runs agree under predefined reproducibility rules.

**Keywords:** agricultural prices; onion; potato; time-series forecasting; walk-forward evaluation; Diebold–Mariano test; anomaly screening; Agmarknet; reproducibility

## 1. Introduction

Onion and potato are staple vegetables in India, and their volatile wholesale prices hurt consumers and producers alike (Madaan et al., 2019; Paul et al., 2016). Daily mandi prices and arrivals are published through Agmarknet by the Directorate of Marketing & Inspection, and CEDA (Ashoka University) redistributes them as state-level daily aggregates.

We ask three questions. How do these series behave? Can standard models forecast the next market day's modal price better than simple baselines under a leakage-free chronological evaluation? And can unusual movements be screened for defensibly without verified ground truth?

The contributions are practical rather than methodological: a checksum-verified pipeline to a frozen dataset; an exploratory analysis exposing composition and reporting effects in the aggregates; a pre-registered comparison of seven forecasting methods with formal significance control; and a causal anomaly screen evaluated separately against weak labels and synthetic shocks. No methodological novelty is claimed.

## 2. Related Work

**Agricultural price studies.** Madaan et al. (2019) forecast Indian onion and potato prices from mandi prices, arrivals and retail prices, and flagged anomalous windows linked to hoarding; their rule-based windows serve here as weak reference labels. Paul et al. (2016) found that ARIMA residuals for monthly Delhi onion prices remained autocorrelated and heteroscedastic, which motivated (E)GARCH models. Shankar et al. (2023) reported gains from decomposition-based hybrid models for onion arrivals and prices. These studies use monthly or mandi-level data, so their accuracy figures are not comparable with this daily state-level setting.

**Methodology.** Simple benchmarks set the bar that any method must clear (Hyndman & Athanasopoulos, 2021), and in large competitions pure machine-learning methods often fail to beat statistical ones (Makridakis et al., 2020). Forecasts should be evaluated on a rolling origin (Tashman, 2000; Bergmeir & Benítez, 2012), with scale-free errors such as MASE (Hyndman & Koehler, 2006). Accuracy differences should be tested allowing for serial correlation (Diebold & Mariano, 1995; Harvey et al., 1997). For anomaly detection, the definition must suit the domain (Chandola et al., 2009), and the median and MAD resist the very outliers being sought (Leys et al., 2013; Rousseeuw & Croux, 1993).

## 3. Data

Daily minimum, maximum and modal prices (INR per quintal) and arrivals (tonnes) for Maharashtra onion and Uttar Pradesh potato, 1 January 2016 to 31 December 2022, were extracted from the CEDA Agri Market Data API. Extraction ran in 56 six-month chunks at under 40 requests per hour, with each file's SHA-256 recorded in a manifest. An offline audit checks every chunk, schema, duplicate key, numeric rule and price–arrival alignment, and passes with two warnings, discussed below.

The frozen dataset (v1) has one row per observed market day, built only from the historical chunks; overlapping pilot files are excluded. All 20,320 values equal the raw files, rebuilding produces identical bytes, and nothing is imputed. Data-quality concerns are marked by flag columns rather than by changing values.

Potato is complete (2,557 of 2,557 days). Onion has 2,523 days: its 34 missing days (1.3%) form 13 gaps of up to 10 days, 20 of them in 2020. Price and arrival dates match exactly in both series.

CEDA permits non-commercial use with credit, but its terms do not clearly allow redistribution, so raw data, processed data and predictions are not published; figures and aggregate statistics are. Each commodity has a single state aggregate, so there are no peer markets: peer-based requirements were formally recorded as not applicable, and "market-relative" refers to the market's own history.

## 4. Exploratory Data Analysis

**Price behaviour.** Both price series are right-skewed, with heavy-tailed daily log returns (excess kurtosis 5.0 for onion, 8.4 for potato). Onion is far more volatile: its daily log-return SD is 0.078 against 0.023 for potato, 16.7% of its day-to-day moves exceed ±10%, and it peaked at ₹7,506 per quintal in December 2019 (Figure 1). Potato rose to ₹3,015 in 2020 before collapsing in December 2020. Dispersion grows with the price level (Spearman ρ between yearly means and SDs: 0.82 for onion, 0.89 for potato), so seasonality is multiplicative; it is stronger for potato (STL seasonal strength 0.42 against 0.24). Log levels give conflicting stationarity results, while log returns are stationary (Dickey & Fuller, 1979; Kwiatkowski et al., 1992).

![Figure 1. Daily modal price with the reported [min, max] band, 2016–2022. Data: CEDA, Ashoka University; original source DMI/Agmarknet.](../figures/fig01_price_series.png)

**Weekday composition effect.** The dominant periodic structure is weekly, not annual. The autocorrelation of daily log returns is −0.32 and −0.30 at lag 1 and +0.31 and +0.38 at lag 7 (onion and potato), against a 95% band of about ±0.04, and weekday differences in returns are highly significant (Kruskal–Wallis, BH-adjusted p < 10⁻⁵⁰). On Sundays arrivals fall to about a third of weekday levels, and the onion price averages 3.7% above its centred weekly mean (Figure 2). The largest onion moves are Sunday spike-and-revert pairs, for example +70% on 3 March 2019 followed by −44% the next day. Our hypothesis is that the state figure averages whichever mandis report each day, so a smaller, different Sunday set shifts the aggregate; mandi counts are not in the data, so this cannot be verified.

![Figure 2. Median arrivals by weekday (left) and mean deviation of the modal price from its centred 7-day mean (right).](../figures/fig12_weekday_composition.png)

**Price–arrival association.** Month-on-month changes in log price and log arrivals move in opposite directions: Spearman ρ = −0.60 for potato (95% block-bootstrap CI [−0.74, −0.34]) and −0.20 for onion [−0.41, −0.05]. This is consistent with supply-driven prices, but it is an association, not proof of cause.

**Data-quality issues.** In 137 potato records (5.4%), the modal price lies outside the reported [min, max] band (ISS-002). The modal's position within the band has a median of 0.07 from the start of the data to April 2017, against 0.50 afterwards, and the shift is abrupt. That points to a change in source reporting rather than in market behaviour. CEDA's methodology page could not be retrieved, so the cause is unresolved, and potato min/max prices are excluded from features. Ten onion days, mostly in March–April 2020 around the start of the national lockdown, have arrivals below 1% of the median (ISS-003). On 8 of them the modal price is a whole number, against 4.6% of all days (Fisher p = 6×10⁻¹⁰), which suggests only one or a few mandis reported. These are treated as coverage anomalies. Figures for both issues are in the EDA report.

## 5. Forecasting Methodology

A written protocol (version 1.1) fixed every modelling choice before any model was fitted. The target is the modal price on the next market day (h = 1). Series are indexed by observed market days, so lags count market days and nothing is imputed.

The feature-based models predict the next log return from price lags 1, 2, 3, 5 and 7 (as log ratios to the current price), 7- and 14-day rolling means and SDs, the origin's day of week and month, the target's day of week, and arrivals at lags 1 and 2. A unit test checks that perturbing future values changes neither the features nor any forecast.

Two baselines, naive and weekly seasonal naive, are compared with five candidates: ordinary least squares, a decision tree, a random forest with 300 trees (Breiman, 2001), seasonal ARIMA (p,1,q)(P,0,Q)₇ on log prices, and Holt–Winters exponential smoothing with weekly seasonality on log prices (Hyndman et al., 2002). They are implemented with scikit-learn (Pedregosa et al., 2011) and statsmodels (Seabold & Perktold, 2010).

Each series is split chronologically 60/20/20, so the test period runs from August 2021 to December 2022. Hyperparameters are chosen on validation MAE; SARIMA orders are first ranked by training-set AIC and the top three compared on validation. Every one of the 505 (onion) and 512 (potato) test forecasts follows a refit on all data before its origin (Tashman, 2000).

MAE is the primary metric, alongside RMSE, MAPE and MASE (Hyndman & Koehler, 2006). Each model is compared with naive using a Diebold–Mariano test with the Harvey–Leybourne–Newbold correction, under one Benjamini–Hochberg adjustment across the 12 comparisons (Diebold & Mariano, 1995; Harvey et al., 1997; Benjamini & Hochberg, 1995). A model "improves on naive" only if its MAE is lower **and** its adjusted p-value is below 0.05.

## 6. Forecasting Results

**Table 1.** Test-set results, generated from the saved results and recomputed independently from the stored predictions. MAE and RMSE are in INR per quintal; Δ MAE is the change relative to naive; DM is the HLN-corrected Diebold–Mariano statistic (negative = lower loss than naive); BH p is adjusted across 12 comparisons. Verdict: Better = lower MAE and BH p < 0.05; Worse = higher MAE and BH p < 0.05; n.s. = no significant difference. Selected settings are in Table A1.

<!-- BEGIN TABLE:forecast_metrics -->
| Series | Model | MAE | RMSE | MAPE % | MASE | Δ MAE | DM | BH p | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| Onion | ETS (Holt–Winters) | 60.04 | 85.58 | 4.01 | 0.836 | -4.3% | -1.52 | 0.174 | n.s. |
| Onion | Seasonal ARIMA | 60.58 | 85.61 | 4.02 | 0.844 | -3.5% | -1.41 | 0.190 | n.s. |
| Onion | Random forest | 61.63 | 87.37 | 4.15 | 0.858 | -1.8% | -0.76 | 0.486 | n.s. |
| Onion | Naive | 62.75 | 88.60 | 4.31 | 0.874 | — | — | — | Baseline |
| Onion | Linear regression | 63.71 | 90.16 | 4.20 | 0.887 | +1.5% | 0.57 | 0.566 | n.s. |
| Onion | Decision tree | 65.36 | 92.51 | 4.40 | 0.910 | +4.2% | 1.52 | 0.174 | n.s. |
| Onion | Seasonal naive (7) | 142.46 | 204.92 | 9.07 | 1.984 | +127.0% | 12.44 | <0.001 | Worse |
| Potato | Random forest | 10.77 | 14.39 | 0.94 | 0.830 | -26.3% | -7.93 | <0.001 | Better |
| Potato | Seasonal ARIMA | 10.97 | 14.75 | 0.96 | 0.845 | -25.0% | -6.87 | <0.001 | Better |
| Potato | ETS (Holt–Winters) | 11.14 | 14.95 | 0.97 | 0.858 | -23.8% | -6.23 | <0.001 | Better |
| Potato | Linear regression | 11.85 | 15.78 | 1.04 | 0.913 | -18.9% | -5.46 | <0.001 | Better |
| Potato | Decision tree | 12.01 | 16.37 | 1.05 | 0.925 | -17.9% | -5.27 | <0.001 | Better |
| Potato | Naive | 14.61 | 19.46 | 1.28 | 1.126 | — | — | — | Baseline |
| Potato | Seasonal naive (7) | 38.75 | 53.45 | 3.42 | 2.986 | +165.1% | 15.51 | <0.001 | Worse |
<!-- END TABLE:forecast_metrics -->

**Pre-specified results.** For onion, no candidate differs significantly from naive, and every candidate's MAE lies within ±5% of it: for next-day Maharashtra onion prices, the last observed price is as accurate as any model tested. For potato, all five candidates improve significantly on naive; the random forest, SARIMA and ETS reduce MAE by about 24–26%, and the gain holds in every test half-year (Table 2). Seasonal naive is far worse than naive for both series, because weekly structure in *returns* does not make the price a week earlier a good forecast of the *level*.

**Table 2.** Test MAE by half-year of the target date (INR per quintal). SN7 = seasonal naive (7); OLS = linear regression; Tree = decision tree; RF = random forest.

<!-- BEGIN TABLE:forecast_halves -->
| Series | Period | n | Naive | SN7 | OLS | Tree | RF | SARIMA | ETS |
|---|---|---|---|---|---|---|---|---|---|
| Onion | 2021-H2 | 140 | 83.9 | 202.5 | 94.5 | 93.6 | 88.4 | 87.8 | 85.9 |
| Onion | 2022-H1 | 181 | 48.9 | 114.9 | 50.4 | 51.4 | 48.5 | 46.4 | 47.0 |
| Onion | 2022-H2 | 184 | 60.2 | 123.9 | 53.4 | 57.7 | 54.1 | 53.9 | 53.2 |
| Potato | 2021-H2 | 147 | 15.9 | 52.4 | 11.9 | 12.8 | 10.4 | 10.7 | 10.9 |
| Potato | 2022-H1 | 181 | 11.9 | 27.3 | 9.6 | 9.4 | 8.7 | 9.0 | 8.9 |
| Potato | 2022-H2 | 184 | 16.2 | 39.1 | 14.0 | 13.9 | 13.1 | 13.2 | 13.5 |
<!-- END TABLE:forecast_halves -->

**Exploratory finding (post hoc, no significance claimed).** A breakdown by target weekday shows where the potato gain comes from. On Sunday and Monday targets, where the composition effect roughly doubles naive errors, the models cut MAE by about half. On Tuesday–Saturday targets the best model's gain is about 8%, and onion models are no better than naive. The forecastable component is therefore mainly the weekly reporting-composition pattern, not general market dynamics. Forecast and residual plots are in the experiment results report.

## 7. Market-Relative Anomaly Screening

An anomaly is a market day whose modal price deviates unusually from what the market's own prior history predicts, allowing for its weekday pattern. Without independent ground truth, this is **exploratory screening**, and no detection accuracy is claimed (Chandola et al., 2009).

Three causal scores are compared, each re-standardised using past values only. The **residual** score is a z-score of one-step seasonal-ARIMA log residuals against the previous 30. The **robust** score is the weekday-adjusted deviation from the trailing 28-day median, scaled by the MAD (Leys et al., 2013). The **composite** is their equally weighted sum. A day is flagged when |score| > 3, a threshold fixed before the analysis.

**Table 3.** Real-data detections at |score| > 3 by data-quality class (onion scored from 29 March 2017, potato from 22 March 2017). Sun/Mon = composition-prone Sunday or Monday; Coverage = arrivals below 10% of the median (ISS-003 type); Other = candidate market events.

<!-- BEGIN TABLE:anomaly_classes -->
| Series | Score | Scored days | Detections | Sun/Mon | Coverage | Other |
|---|---|---|---|---|---|---|
| Onion | Residual | 2077 | 26 (1.25%) | 9 | 1 | 16 |
| Onion | Robust | 2077 | 38 (1.83%) | 9 | 1 | 28 |
| Onion | Composite | 2077 | 23 (1.11%) | 6 | 2 | 15 |
| Potato | Residual | 2111 | 28 (1.33%) | 10 | 5 | 13 |
| Potato | Robust | 2111 | 0 (0.00%) | 0 | 0 | 0 |
| Potato | Composite | 2111 | 26 (1.23%) | 6 | 4 | 16 |
<!-- END TABLE:anomaly_classes -->

Depending on series and score, 26–54% of detections are coverage anomalies or fall on composition-prone Sundays and Mondays, so many "anomalies" in these aggregates are data-quality phenomena. The potato robust score made no detections, because of a design weakness in the pre-registered protocol that is reported rather than corrected after seeing results: its trailing-median deviation absorbs potato's smooth trends, and its second, non-robust standardisation is inflated by the November–December 2016 collapse. Its precision is therefore undefined (shown as "—"), not zero.

**Table 4.** Agreement with the ICTD-IITD weak labels (Madaan et al., 2019): mandi-level rule flags from the same Agmarknet source, **not ground truth**. Label rate = share of evaluated days inside a labelled window; Null precision = median precision over 1,000 circular shifts of the detections; Rand. p = randomisation p-value.

<!-- BEGIN TABLE:anomaly_weak -->
| Series | Score | Days | Label rate | Precision | Recall | F1 | Null precision | Rand. p |
|---|---|---|---|---|---|---|---|---|
| Onion | Residual | 1484 | 0.586 | 0.579 | 0.013 | 0.025 | 0.579 | 0.613 |
| Onion | Robust | 1484 | 0.586 | 0.200 | 0.008 | 0.015 | 0.629 | 0.900 |
| Onion | Composite | 1484 | 0.586 | 0.316 | 0.007 | 0.014 | 0.632 | 0.918 |
| Potato | Residual | 1742 | 0.716 | 0.741 | 0.016 | 0.031 | 0.704 | 0.465 |
| Potato | Robust | 1742 | 0.716 | — | 0.000 | 0.000 | — | — |
| Potato | Composite | 1742 | 0.716 | 0.680 | 0.014 | 0.027 | 0.720 | 0.686 |
<!-- END TABLE:anomaly_weak -->

The weak labels mark 59% (onion) and 72% (potato) of evaluated days as anomalous, and no score beats the circular-shift baseline (randomisation p ≥ 0.46). The labels are therefore **uninformative** here, and agreement with them says nothing about real-world detection accuracy.

**Table 5.** Synthetic one-day shocks injected into the held-out test segment, reported separately from real data. Each cell is mean recall over 5 seeded repeats of 6 shocks, for the residual (Res), robust (Rob) and composite (Com) scores; the last row is the mean false-positive rate on clean days.

<!-- BEGIN TABLE:anomaly_shocks -->
| Shock | Onion Res | Onion Rob | Onion Com | Potato Res | Potato Rob | Potato Com |
|---|---|---|---|---|---|---|
| -50% | 1.00 | 0.40 | 1.00 | 1.00 | 0.77 | 1.00 |
| -30% | 0.97 | 0.10 | 0.87 | 1.00 | 0.50 | 1.00 |
| -20% | 0.73 | 0.07 | 0.53 | 1.00 | 0.27 | 1.00 |
| -10% | 0.10 | 0.03 | 0.07 | 1.00 | 0.27 | 1.00 |
| +10% | 0.10 | 0.00 | 0.03 | 1.00 | 0.17 | 1.00 |
| +20% | 0.53 | 0.17 | 0.53 | 1.00 | 0.20 | 1.00 |
| +30% | 0.87 | 0.03 | 0.67 | 1.00 | 0.40 | 1.00 |
| +50% | 1.00 | 0.30 | 0.97 | 1.00 | 0.50 | 1.00 |
| FPR (clean days) | 0.98% | 0.48% | 0.51% | 0.22% | 0.01% | 0.45% |
<!-- END TABLE:anomaly_shocks -->

For potato, the residual and composite scores flag every shock from ±10%; for onion they need ±30–50%, consistent with onion's roughly 3.4-times higher daily volatility (Figure 3). False-positive rates are about 0.005–1% of clean days. This tests isolated spikes only, not gradual or collective anomalies. Five of the 85 potato residual-model refits stopped without formal convergence; substituting independently converged estimates changes residuals by at most 0.0042 on the log scale and changes no detection.

![Figure 3. Synthetic shock recall by shock magnitude for the three scores (synthetic evaluation).](../figures/fig16_shock_recall.png)

## 8. Reproducibility

All results trace to the frozen dataset (SHA-256 `b5f21e02b681`), which rebuilds byte-identically from the 56 checksum-verified raw files. Each experiment run writes a manifest recording its status and timestamps, the Git commit and whether the tree was clean, a code fingerprint taken at both start and end, the full configuration, the dataset checksum, software versions and the checksum of every output. One command, `python -m src.verify`, re-checks the environment, raw inputs, dataset rebuild, tests, run manifests, independent recomputation of all metrics, report tables, notebooks and Git hygiene.

Both experiments were run twice. Run A, the first forecasting run, predates the run-record system, so its executed code is not recorded; its outputs were preserved and verified. Run B was executed through the notebooks from a clean recorded commit, with the code unchanged throughout. Under rules fixed before the comparison, 13 of 14 test-forecast columns are bit-identical, and the onion random forest differs by at most 2.3×10⁻¹⁶ relative (because run A used parallel prediction; the limit was 10⁻¹²). All metrics agree to within 1.0×10⁻¹⁵, and settings, verdicts and configuration hashes are identical. The SARIMA AIC and validation tables match exactly once run B's values are rounded to the 6 significant digits of run A's stored tables, and both anomaly runs produced exactly equal tables, including all 80 shock runs. Independent recomputation found 0 discrepancies across 14 model rows × 7 statistics and 368 anomaly checks.

The forecasting run's warning tally recorded 73 non-converged SARIMA fits: 52 in the test walk-forward and 21 in validation. Replacing each non-converged test fit with a converged cold-start fit changes SARIMA's test MAE by under 0.003 INR per quintal and leaves every verdict unchanged; the effect of the validation fits on order selection was not assessed.

## 9. Discussion and Limitations

For Maharashtra onion, the last observed price cannot be improved upon for next-day forecasts with these data and models. For Uttar Pradesh potato, standard models improve significantly on naive, mostly by anticipating weekly reporting composition. Applied to state aggregates, anomaly screening mostly surfaces coverage and composition effects, and the available weak labels cannot validate it.

The limitations are these:
1. The series are state aggregates of unknown mandi composition, so the composition and partial-reporting explanations remain hypotheses, and ISS-002 is unexplained because CEDA's aggregation method could not be retrieved.
2. The test period excludes the 2019–2020 spikes, and results cover one-day-ahead forecasts only.
3. There are no peer markets, so the peer-divergence signal envisaged in the charter could not be built.
4. The weak labels are too dense to discriminate, and the pre-registered robust score has a design weakness.
5. Some SARIMA fits stopped without formal convergence; their measured effect on test results is negligible, but their influence on validation-based order selection is untested.
6. Run A predates the run-record system, so its exact executed code is not recorded; its outputs were verified and reproduced by run B from a recorded clean commit.
7. Bit-identical results are demonstrated on one machine only; agreement within numerical tolerance is expected but untested on other hardware.

**Data credit.** CEDA Agri Market Data, Centre for Economic Data and Analysis (CEDA), Ashoka University; original source DMI, Ministry of Agriculture and Farmers Welfare (Agmarknet). Non-commercial academic use.

## 10. Conclusion

CropCast delivers a checksum-verified, reproducible study of daily state-level onion and potato prices under pre-registered, leakage-free protocols. Simple baselines remain hard to beat: onion forecasts gain nothing over naive, and the significant potato gains mostly reflect predictable weekly composition effects. Applied to the aggregates, anomaly screening mainly detects data-quality phenomena. Future work should use mandi-level data with peer markets, to separate composition from price movement and enable peer-divergence signals; extend to longer horizons; develop a detrended, robustly standardised anomaly score; and draw on independently sourced event labels.

## References

- Benjamini, Y., & Hochberg, Y. (1995). Controlling the false discovery rate: A practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society: Series B*, 57(1), 289–300. https://doi.org/10.1111/j.2517-6161.1995.tb02031.x
- Bergmeir, C., & Benítez, J. M. (2012). On the use of cross-validation for time series predictor evaluation. *Information Sciences*, 191, 192–213. https://doi.org/10.1016/j.ins.2011.12.028
- Breiman, L. (2001). Random forests. *Machine Learning*, 45(1), 5–32. https://doi.org/10.1023/A:1010933404324
- Chandola, V., Banerjee, A., & Kumar, V. (2009). Anomaly detection: A survey. *ACM Computing Surveys*, 41(3), 1–58. https://doi.org/10.1145/1541880.1541882
- Dickey, D. A., & Fuller, W. A. (1979). Distribution of the estimators for autoregressive time series with a unit root. *Journal of the American Statistical Association*, 74(366a), 427–431. https://doi.org/10.1080/01621459.1979.10482531
- Diebold, F. X., & Mariano, R. S. (1995). Comparing predictive accuracy. *Journal of Business & Economic Statistics*, 13(3), 253–263. https://doi.org/10.1080/07350015.1995.10524599
- Harvey, D., Leybourne, S., & Newbold, P. (1997). Testing the equality of prediction mean squared errors. *International Journal of Forecasting*, 13(2), 281–291. https://doi.org/10.1016/S0169-2070(96)00719-4
- Hyndman, R. J., & Athanasopoulos, G. (2021). *Forecasting: Principles and practice* (3rd ed.). OTexts. https://otexts.com/fpp3/
- Hyndman, R. J., & Koehler, A. B. (2006). Another look at measures of forecast accuracy. *International Journal of Forecasting*, 22(4), 679–688. https://doi.org/10.1016/j.ijforecast.2006.03.001
- Hyndman, R. J., Koehler, A. B., Snyder, R. D., & Grose, S. (2002). A state space framework for automatic forecasting using exponential smoothing methods. *International Journal of Forecasting*, 18(3), 439–454. https://doi.org/10.1016/S0169-2070(01)00110-8
- Kwiatkowski, D., Phillips, P. C. B., Schmidt, P., & Shin, Y. (1992). Testing the null hypothesis of stationarity against the alternative of a unit root. *Journal of Econometrics*, 54(1–3), 159–178. https://doi.org/10.1016/0304-4076(92)90104-Y
- Leys, C., Ley, C., Klein, O., Bernard, P., & Licata, L. (2013). Detecting outliers: Do not use standard deviation around the mean, use absolute deviation around the median. *Journal of Experimental Social Psychology*, 49(4), 764–766. https://doi.org/10.1016/j.jesp.2013.03.013
- Madaan, L., Sharma, A., Khandelwal, P., Goel, S., Singla, P., & Seth, A. (2019). Price forecasting & anomaly detection for agricultural commodities in India. In *Proceedings of the 2nd ACM SIGCAS Conference on Computing and Sustainable Societies* (pp. 52–64). https://doi.org/10.1145/3314344.3332488
- Makridakis, S., Spiliotis, E., & Assimakopoulos, V. (2020). The M4 Competition: 100,000 time series and 61 forecasting methods. *International Journal of Forecasting*, 36(1), 54–74. https://doi.org/10.1016/j.ijforecast.2019.04.014
- Paul, R. K., Rana, S., & Saxena, R. (2016). Effectiveness of price forecasting techniques for capturing asymmetric volatility for onion in selected markets of Delhi. *The Indian Journal of Agricultural Sciences*, 86(3), 303–309. https://doi.org/10.56093/ijas.v86i3.56843
- Pedregosa, F., Varoquaux, G., Gramfort, A., et al. (2011). Scikit-learn: Machine learning in Python. *Journal of Machine Learning Research*, 12, 2825–2830. https://jmlr.org/papers/v12/pedregosa11a.html
- Rousseeuw, P. J., & Croux, C. (1993). Alternatives to the median absolute deviation. *Journal of the American Statistical Association*, 88(424), 1273–1283. https://doi.org/10.1080/01621459.1993.10476408
- Seabold, S., & Perktold, J. (2010). Statsmodels: Econometric and statistical modeling with Python. In *Proceedings of the 9th Python in Science Conference* (pp. 92–96). https://doi.org/10.25080/Majora-92bf1922-011
- Shankar, S. V., Chandel, A., Gupta, R. K., Sharma, S., Chand, H., Kumar, R., Mishra, N., & Ananthakrishnan, S. (2023). Exploring the dynamics of arrivals and prices volatility in onion (*Allium cepa*) using advanced time series techniques. *Frontiers in Sustainable Food Systems*, 7, 1208898. https://doi.org/10.3389/fsufs.2023.1208898
- Tashman, L. J. (2000). Out-of-sample tests of forecasting accuracy: An analysis and review. *International Journal of Forecasting*, 16(4), 437–450. https://doi.org/10.1016/S0169-2070(00)00065-0

<!-- pagebreak -->

## Appendix A. Selected Settings and Traceability of Key Claims

**Table A1.** Selected model settings (argmin of validation MAE; ₇ marks the weekly seasonal period).

<!-- BEGIN TABLE:forecast_settings -->
| Model | Onion (MH) | Potato (UP) |
|---|---|---|
| Decision tree | max_depth=5, min_samples_leaf=50 | max_depth=5, min_samples_leaf=20 |
| Random forest | max_depth=5, max_features=1.0, min_samples_leaf=5 | max_depth=10, max_features=0.5, min_samples_leaf=5 |
| Seasonal ARIMA | (1,1,1)(1,0,1)₇ | (2,1,2)(1,0,1)₇ |
| ETS (Holt–Winters) | no trend | damped additive trend |
<!-- END TABLE:forecast_settings -->

**Table A2.** Traceability of key claims to source artifacts and verification.

| Claim | Value | Source artifact | Verification |
|---|---|---|---|
| Dataset checksum | b5f21e02b681 (first 12 hex digits) | `data/processed/cropcast_analysis_v1.meta.json` | Rebuilt byte-identically (`src.verify` stage 3) |
| Raw data integrity | 56/56 chunks, 0 hard failures | `data/raw/m2_validation_audit.json` | `src.verify` stage 2 |
| Onion coverage | 2,523 of 2,557 days; 13 gaps | `reports/tables/eda_summary.json` | M-2 audit; `tests/test_dataset.py` |
| Weekly return ACF | 0.31 / 0.38 at lag 7 | `reports/tables/eda_acf.csv` | Generated by `src.analysis.eda` |
| ISS-003 integer prices | 8 of 10 vs 4.6%; p = 6×10⁻¹⁰ | `reports/tables/eda_summary.json` (`integer_modal_share`) | Generated by `src.analysis.eda` |
| Forecast metrics, DM, BH (Tables 1–2) | Generated tables | `reports/tables/forecast_test_metrics.csv`, `forecast_test_breakdown.csv` | `src.reporting.verify_results` (independent recomputation) |
| Model settings | Table A1 | `reports/tables/forecast_test_selection.csv` | Equal to argmin of validation MAE |
| Potato gain on Sun/Mon (exploratory) | About −50% vs about −8% | `reports/tables/forecast_test_breakdown.csv` (`target_weekday`) | Post-hoc; no significance claim |
| Anomaly tables (Tables 3–5) | Generated tables | `reports/tables/anomaly_*.csv` | `src.reporting.verify_anomaly --full` |
| SARIMA convergence | 5 non-converged; ≤ 0.0042 residual change; 0 detection changes | `reports/tables/anomaly_sarima_convergence*.{csv,json}` | `src.reporting.diagnose_sarima_convergence` |
| Run A vs run B agreement | 13/14 forecast columns bit-identical; RF ≤ 2.3×10⁻¹⁶ | `reports/runs/reproducibility_comparison_A_vs_B.json` | `src.reporting.compare_runs` |
| Forecasting convergence | 73 non-converged; test MAE change < 0.003 | `reports/tables/forecast_sarima_convergence*` | `src.reporting.diagnose_forecast_convergence` |
| References | 20 cited | — | Each checked against Crossref, JMLR or OTexts records (`reports/literature_review.md`) |

## Appendix B. Reproduction

```
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m src.verify
```

Full retraining: `.venv/Scripts/python -m src.reporting.notebooks --execute` (about 80 minutes). It needs the CEDA raw data, which is not redistributed (see `data/raw/README.md`).
