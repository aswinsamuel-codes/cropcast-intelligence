# CropCast — Forecasting Protocol (M-4)

**Version:** 1.1 · **Fixed on:** 2026-10-23, before any model was fitted or any validation/test result was seen (v1.1 adds the validation refit cadence in §4) · **Dataset:** v1 (`v1:b5f21e02b681`)
**Basis:** `docs/requirements.md` Req 4, 5 and 10; `reports/eda_report.md` §7; `reports/literature_review.md`.

Any later change to this protocol must be recorded as a new version with a decision-log entry. Results produced under an earlier version are kept, not overwritten.

## 1. Forecast target and horizon

- **Target:** the modal price (INR/quintal) on the **next market day** for each series (Req 4.1). The horizon is h = 1 market day.
  - For potato a market day is always the next calendar day.
  - For onion, 34 calendar days (1.3%) are missing, so the next market day can be up to 11 calendar days later. These cases are reported, not removed.
- **Forecast origin t:** the last observed market day. Everything observed on day t (prices and arrivals) is assumed known at the origin; the forecast is issued after day t's data is published.

## 2. Frequency and missing data

- Series are indexed by **market day**, the sequence of observed dates. Lags and windows count market days (Req 4.2–4.3). **Nothing is imputed** (Req 3.4).
- Rows whose required lags or windows reach before the first observation are marked invalid and excluded (Req 4.7). These are the first 14 market days of each series.
- Flagged rows (ISS-002, ISS-003) stay in the data and are reported separately in the error analysis. They are not removed from evaluation.

## 3. Models and inputs

| Model | Type | Inputs | Rationale |
|---|---|---|---|
| Naive | Baseline | y_t | Req 5.1; FPP3 §5.2 |
| Seasonal naive (7) | Baseline | y_{t+1−7} | Req 5.2. The EDA found weekly structure dominant (return ACF at lag 7 is 0.31/0.38) and annual ACF weak |
| Linear regression (OLS) | Feature-based | Feature set F | Req 5.3 |
| Decision tree | Feature-based | Feature set F | Req 5.3 |
| Random forest | Feature-based | Feature set F | Req 5.4 (≥ 500 training rows); Breiman (2001) |
| Seasonal ARIMA (period 7) on log price | Univariate | log y | Req 5.5 eligibility met (EDA §7.4) |
| ETS (Holt–Winters, weekly seasonality) on log price | Univariate | log y | Standard statistical benchmark (Hyndman et al., 2002; M4) |

Not included:
- **Drift baseline:** the mean daily log return is about 0, so drift is indistinguishable from naive at h = 1.
- **XGBoost or other boosting:** not required by Req 5. The random forest covers tree ensembles, and boosting would only be added if the RF result shows that a tree ensemble adds value (DEC-018).
- **Peer-market features:** not available (DEC-017).

### Feature set F (Req 4.2–4.5)

Constructed at origin t from data with market-day index ≤ t. Here y is the modal price and q is arrivals.
- Lags y_{t}, y_{t−1}, y_{t−2}, y_{t−4}, y_{t−6}. These are lags 1, 2, 3, 5, 7 relative to the target y_{t+1}.
- Rolling mean and standard deviation of y over the last 7 and 14 market days, ending at t inclusive.
- Day of week (0–6) and month (1–12) of the **forecast origin date** (Req 4.4).
- Day of week of the **target date**. The target date is known at the origin for potato. For onion it is taken as the next calendar day after t, because whether a day will be missing is not known in advance.
- Arrivals q_t and q_{t−1} (Req 4.5).

**Model-input transformation** (fit-free, so it cannot leak): the feature-based models predict the **next log return** r_{t+1} = log y_{t+1} − log y_t, with the forecast ŷ_{t+1} = y_t · exp(r̂_{t+1}). Price features enter as log ratios to y_t; rolling SDs as SD divided by y_t; arrivals as log(1 + q). The reasons:
1. Levels are non-stationary and potato test prices exceed the training range, which trees cannot extrapolate.
2. Returns are stationary (EDA §2).

Potato min/max prices are **not** used: their relationship to the modal changes across the ISS-002 regime.

## 4. Chronological split

60/20/20 by market day within each series (Req 5.6). No random splitting.

| Series | Train | Validation | Test |
|---|---|---|---|
| Onion | 2016-01-01 – 2020-03-02 | 2020-03-03 – 2021-08-13 | 2021-08-14 – 2022-12-31 |
| Potato | 2016-01-01 – 2020-03-13 | 2020-03-14 – 2021-08-06 | 2021-08-07 – 2022-12-31 |

- **Validation:** used only for hyperparameter and order selection. Validation uses the same walk-forward procedure as test, with training data restricted to dates before each validation origin. *(v1.1, fixed 2026-10-23 before any fit: during validation tuning only, models are refit every 7 steps (`validation_refit_every = 7`). Between refits, feature models apply the last fitted model to current features, and univariate models update their state. This keeps the grid search feasible (about 12,000 random-forest fits at every-step refit). It introduces no look-ahead. DEC-020.)*
- **Test:** used once, after every configuration is fixed.
- **Walk-forward on test (Req 5.6):** at each test origin, the model is refit on all rows whose **target** date is ≤ the origin date, so no target after the origin is used.
  - The refit frequency is a configuration parameter, `refit_every`, defaulting to 1 (refit every step).
  - Between refits, the univariate models update their state with each new observation using fixed parameters. This is not look-ahead, because parameters are estimated only from data before the refit origin.
  - If ARIMA refitting at every step proves computationally infeasible, the value used is recorded, with its runtime evidence, as a protocol deviation.

## 5. Hyperparameter selection (validation only)

The grids are fixed in `configs/config.json`; the selection criterion is **validation MAE**.
- **Decision tree:** `max_depth` ∈ {3, 5, 8}, `min_samples_leaf` ∈ {5, 20, 50}.
- **Random forest:** 300 trees; `max_depth` ∈ {5, 10, None}, `min_samples_leaf` ∈ {5, 20}, `max_features` ∈ {0.5, 1.0}.
- **Seasonal ARIMA:** orders (p, 1, q)(P, 0, Q)_7 with p, q ∈ {0, 1, 2} and P, Q ∈ {0, 1}, ranked by **AIC on the training set**. The three best AIC orders are compared on validation MAE, and the best is chosen.
- **ETS:** additive seasonality (period 7) on log prices, with trend ∈ {none, additive damped}, selected on validation MAE.
- **OLS:** no hyperparameters.
- **Seeds:** all randomness (tree models) uses `random_seed` from the config.

## 6. Metrics and comparison

- **Metrics:** MAE (primary), RMSE and MAPE on the test set, in INR per quintal (Req 5.7).
  - MAPE is reliable because the minimum observed modal price is 406, far from zero; the report states the minimum test actual value.
  - MASE (Hyndman & Koehler, 2006) is also reported, scaled by the in-sample naive MAE on the training set, to compare across series.
- **Breakdown (Req 5.8):** results by series (commodity and market), and in the error analysis by test half-year, by weekday, and for flagged versus unflagged rows.
- **Significance:** each candidate is compared with the naive forecast using the Diebold–Mariano test with the Harvey–Leybourne–Newbold small-sample correction (h = 1, absolute-error loss), two-sided. All model × series comparisons share one Benjamini–Hochberg FDR adjustment at q = 0.05.
- **Claim rule:** a model is described as *improving on the naive baseline* only if its test MAE is lower **and** its BH-adjusted DM p-value is below 0.05. Otherwise the result is reported as "no significant difference" or "worse". All models are reported, whatever their result. No metric or period is selected after seeing test results.

## 7. Leakage controls

1. Features are computed by shift-and-roll operations on the market-day sequence, using only indices ≤ t. A unit test perturbs future values and checks that features are unchanged (Req 9.2).
2. Training rows at each origin are restricted to target dates ≤ the origin.
3. No scaler, imputer or feature selector is fit on data outside the training window. OLS and trees need no scaling, and the log-ratio transformation has no parameters.
4. Validation and test periods never feed hyperparameter choices from the test set.
5. Rolling statistics in the anomaly study (M-6) use only prior observations.

## 8. Reproducibility and provenance (Req 10)

- **Configuration hash:** before a run, a SHA-256 is computed over the dataset version ID, the seed, the feature-set definition and all model hyperparameters.
- **Run log:** each run appends its configuration, hash, software versions, timings and metrics to `reports/experiment_log.jsonl`.
- **Fail-closed:** a run whose model parameters are not fully specified in the config raises an error (Req 10.5).
- **Saved outputs:** predictions are saved per model, series and split to `reports/forecasts/`, with actuals and dates. Metrics are recomputed from the saved predictions in Phase 9.

## 9. Known limitations fixed in advance

- The test period (Aug 2021 – Dec 2022) excludes the 2019/2020 spikes and the ISS-002 regime. Results describe that period only.
- At h = 1 with strong persistence, the naive forecast is expected to be hard to beat. The protocol treats "no improvement" as a valid finding.
