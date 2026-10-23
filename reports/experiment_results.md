# CropCast — Forecasting Experiment Results (M-5)

**Protocol:** `docs/forecasting_protocol.md` v1.1 (fixed before any fit) · **Dataset:** v1 · **Runs:** `reports/runs/` (see `docs/experiment_log.md`)
**Tables below are generated from the saved results** by `python -m src.reporting.report_tables --report reports/experiment_results.md`, and are checked by `python -m src.verify`.

Data credit: CEDA Agri Market Data, Centre for Economic Data and Analysis (CEDA), Ashoka University; original source DMI/Agmarknet.

## 1. Ranked test results (Req 5.9)

Test period: onion 2021-08-14 – 2022-12-31 (505 one-step forecasts); potato 2021-08-07 – 2022-12-31 (512). Every test step refits on all data before its origin.

How to read the table:
- Rows are ranked by MAE within each series, in INR per quintal.
- MASE is scaled by the in-sample naive MAE on the training period.
- **DM** is the Diebold–Mariano statistic with the Harvey–Leybourne–Newbold correction (absolute-error loss) against naive; a negative value means lower loss than naive.
- **BH p** is the Benjamini–Hochberg-adjusted p-value across all 12 comparisons.
- MAPE is stable: the lowest test actual value is 759.5 INR/quintal (onion) and 763.4 (potato).

**Table 1.** Test-set comparison with the naive baseline.

<!-- BEGIN TABLE:forecast_metrics -->
<!-- END TABLE:forecast_metrics -->

## 2. Stability across the test period

**Table 2.** Test MAE by half-year of the target date.

<!-- BEGIN TABLE:forecast_halves -->
<!-- END TABLE:forecast_halves -->

## 3. Residuals

![Figure 13a. Onion: test residuals for every model.](../figures/fig13_residuals_onion_maharashtra.png)

![Figure 13b. Potato: test residuals for every model.](../figures/fig13_residuals_potato_uttar_pradesh.png)

![Figure 14. Test-period one-step forecasts: actual, naive and the lowest-MAE non-naive model.](../figures/fig14_test_forecasts.png)

## 4. Findings

1. **Onion:** no candidate model differs significantly from the naive forecast after BH adjustment, and all five candidates are within ±5% of its MAE (−4.3% to +4.2%). For next-day Maharashtra onion prices the last observed price is as good as any model tested.
2. **Potato:** all five candidates improve significantly on naive. The best (random forest, SARIMA and ETS) reduce MAE by about 24–26%, and the gain holds in each test half-year.
3. **Seasonal naive** (7 market days) is far worse than naive for both series. Weekly autocorrelation in *returns* does not make a week-old *level* a good forecast.
4. **Where the potato gain comes from (exploratory, post-hoc; not part of the pre-registered claims; see EXP-001):**
   - Most of the improvement is on Sunday and Monday targets, where naive errors double.
   - On Tuesday–Saturday targets the best model's gain falls to about 8%.
   - The models largely anticipate the weekly reporting-composition pattern found in the EDA, rather than general market dynamics.
5. **Ensemble gains** (random forest versus OLS) are modest, consistent with the M4 finding that complex ML methods rarely dominate simpler statistical ones (Makridakis et al., 2020).

## 5. Limitations

- **Test period:** the test period is calm relative to 2019/2020. Spike episodes are untested out of sample.
- **Horizon:** results are for h = 1 only.
- **Peer markets:** none are available (DEC-017), which limits the feature set.
- **SARIMA residuals:** the training-set Ljung–Box test at lag 14 rejects whiteness for the top potato order (p = 0.014). Some structure is left unmodelled.
