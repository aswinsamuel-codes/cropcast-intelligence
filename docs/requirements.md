# Requirements Document

## Introduction

CropCast is a reproducible, research-oriented machine-learning framework for agricultural commodity price forecasting and market-relative anomaly detection in India. The system targets onion and potato prices across Indian mandi markets, using real-world historical data sourced from public government platforms. The project must demonstrate sound data science methodology: dataset auditing, statistical analysis, feature engineering, model evaluation, and anomaly detection research. It is an academic deliverable for the Data Science Ecosystem course (DSE, 23CS2024) responding to SIH1647.

The workflow proceeds in phases: dataset discovery and feasibility, data preparation and EDA, forecasting model development and evaluation, anomaly detection research, and final reporting. No model training or synthetic data generation occurs until real-world data adequacy has been established.

## Glossary

- **CropCast**: The overall system and framework described in this document.
- **Commodity**: An agricultural product being tracked — onion or potato (primary candidates).
- **Mandi**: An agricultural wholesale market in India.
- **Modal_Price**: The most frequently occurring price for a commodity in a market on a given day; the primary forecast target.
- **Market_Day**: A calendar day on which a mandi reports trading activity.
- **Forecast_Horizon**: The number of market days ahead for which a price prediction is made (initially one market day ahead).
- **Forecast_Origin**: The last market day for which data is known at the time of prediction.
- **Residual**: The difference between the actual Modal_Price and the forecasted Modal_Price for a given market day.
- **Anomaly_Score**: A composite numerical signal derived from residuals and peer-market divergence, used to flag unusual price movements.
- **Peer_Market**: Another mandi trading the same commodity in the same time period, used as a reference for divergence calculation.
- **Walk_Forward_Evaluation**: A chronological model-evaluation protocol in which the model is retrained or updated at each step using only past data, with no look-ahead.
- **Dataset_Auditor**: The component responsible for inspecting, profiling, and reporting on candidate datasets.
- **Data_Pipeline**: The component responsible for ingesting, cleaning, transforming, and versioning data.
- **Feature_Engineer**: The component responsible for constructing model-ready features from cleaned data.
- **Forecaster**: The component responsible for training, evaluating, and comparing price-forecasting models.
- **Anomaly_Detector**: The component responsible for computing anomaly scores and evaluating detection performance.
- **Report_Generator**: The component responsible for producing reproducible markdown and figure outputs.
- **Leakage**: The use of information from future time steps as input features during model training or evaluation.
- **Pinned_Dependency**: A Python package version fixed in requirements.txt to ensure reproducibility.
- **Random_Seed**: A fixed integer value passed to all stochastic operations to ensure reproducibility.
- **Decision_Log**: A chronological record of significant project decisions, each with context, alternatives, rationale, and outcome.
- **Experiment_Log**: A structured record of every experiment run, including configuration, metrics, and interpretation.
- **Milestone_History**: A record of planned, in-progress, completed, and blocked milestones with evidence of completion.
- **Configuration_Hash**: A deterministic fingerprint of an experiment's dataset version, random seed, feature set, and hyperparameters, used to enable exact reproduction.

---

## Requirements

### Requirement 1: Dataset Discovery and Feasibility Assessment

**User Story:** As a researcher, I want to systematically investigate publicly available agricultural commodity price datasets, so that I can determine whether real-world data is adequate before committing to any modelling approach.

#### Acceptance Criteria

1. THE Dataset_Auditor SHALL investigate candidate data sources including AGMARKNET, data.gov.in, the Department of Consumer Affairs price monitoring portal, and the Price Monitoring System (fcainfoweb.nic.in).
2. WHEN a candidate dataset is found, THE Dataset_Auditor SHALL record the dataset name, source URL, license, date range, record count, commodities covered, markets covered, price fields, units, arrival data availability, missing-value percentage, accessibility method, and reproducibility notes.
3. THE Dataset_Auditor SHALL evaluate coverage for onion and potato as the primary commodity candidates.
4. WHEN data quality statistics are computed, THE Dataset_Auditor SHALL calculate missing-value counts per column, duplicate-row counts, and date-range continuity gaps for each candidate dataset.
5. THE Dataset_Auditor SHALL produce a dataset comparison table covering all investigated sources.
6. WHEN evaluation is complete, THE Dataset_Auditor SHALL emit a recommendation of real-world data, synthetic data, or hybrid evaluation, accompanied by explicit evidence from the audit.
7. THE Dataset_Auditor SHALL store the feasibility report at `reports/dataset_feasibility.md`.
8. WHEN a candidate dataset does not meet the preferred coverage target (at least 3 years of daily or weekly Modal_Price records for at least one commodity across at least 3 markets), THE Dataset_Auditor SHALL document the specific coverage shortfall, assess whether the available data is sufficient for the proposed experiments given the shortfall, and present the evidence to the researcher for a final feasibility decision before any evaluation mode transition occurs.

---

### Requirement 2: Repository Structure and Reproducibility

**User Story:** As a researcher, I want a well-organised, reproducible repository, so that any reviewer can re-run the entire pipeline from raw data to final reports using a single documented procedure.

#### Acceptance Criteria

1. THE CropCast repository SHALL contain the top-level directories: `configs/`, `data/raw/`, `data/processed/`, `notebooks/`, `src/`, `tests/`, `reports/`, and `figures/`.
2. THE CropCast repository SHALL contain a `requirements.txt` file listing all Python dependencies with pinned versions.
3. THE CropCast repository SHALL contain a `README.md` describing setup, data acquisition steps, and the command sequence to reproduce all results.
4. WHEN any stochastic operation is performed, THE CropCast SHALL use a fixed Random_Seed value loaded from configuration, so that results are reproducible across runs.
5. THE CropCast SHALL load all file paths from configuration or environment variables; hardcoded absolute paths SHALL NOT appear in source files.
6. THE CropCast repository SHALL contain no credentials, API keys, or personally identifiable information in any committed file.
7. THE Data_Pipeline SHALL version raw data files by recording their source URL and retrieval date in a `data/raw/README.md` file.

---

### Requirement 3: Data Preparation and Exploratory Data Analysis

**User Story:** As a researcher, I want to clean and explore the selected dataset thoroughly, so that I understand its structure, quality, and statistical properties before building any model.

#### Acceptance Criteria

1. WHEN raw data is ingested, THE Data_Pipeline SHALL validate the schema by checking for required columns (date, commodity, market, Modal_Price) and raise a structured error for any missing column.
2. WHEN dates are parsed, THE Data_Pipeline SHALL convert all date fields to a consistent ISO 8601 format (YYYY-MM-DD) and report the count of unparseable records.
3. WHEN exact duplicate records are detected (same date, commodity, market, AND identical price values), THE Data_Pipeline SHALL log the count and safely drop the redundant rows. WHEN conflicting duplicate records are detected (same date, commodity, and market but differing price values), THE Data_Pipeline SHALL flag each conflicting group with full details and halt further processing of those rows until the researcher provides an explicit resolution decision; THE Data_Pipeline SHALL NOT automatically resolve conflicting duplicates by retaining the first occurrence.
4. WHEN missing Modal_Price values are identified, THE Data_Pipeline SHALL report the count and percentage per market and commodity, and SHALL NOT impute values without explicit configuration.
5. THE Feature_Engineer SHALL compute descriptive statistics (mean, median, standard deviation, minimum, maximum, 25th and 75th percentile) per commodity and per market.
6. WHEN time-series decomposition is applied, THE Feature_Engineer SHALL decompose the Modal_Price series into trend, seasonal, and residual components using an additive or multiplicative model, determined by coefficient-of-variation analysis.
7. THE Feature_Engineer SHALL compute pairwise Pearson and Spearman correlations between Modal_Price series of Peer_Markets for the same commodity.
8. THE Report_Generator SHALL produce visual EDA outputs including time-series plots, box plots by month, correlation heatmaps, and missing-value heatmaps, stored in `figures/`.

---

### Requirement 4: Forecasting Problem Specification

**User Story:** As a researcher, I want a precisely defined forecasting problem, so that model inputs, outputs, and evaluation boundaries are unambiguous and free of Leakage.

#### Acceptance Criteria

1. THE Forecaster SHALL predict the Modal_Price for the next Market_Day for a selected commodity and market, using only information available at the Forecast_Origin.
2. THE Feature_Engineer SHALL construct lagged Modal_Price features for lags of 1, 2, 3, 5, and 7 market days.
3. THE Feature_Engineer SHALL construct rolling-window statistics (mean and standard deviation) over windows of 7 and 14 market days, calculated using only data up to and including the Forecast_Origin.
4. THE Feature_Engineer SHALL construct calendar features: day-of-week (integer 0–6) and month (integer 1–12) derived from the Forecast_Origin date.
5. WHERE arrival data is available in the selected dataset, THE Feature_Engineer SHALL include lagged market-arrival volume as an additional feature.
6. WHERE Peer_Market price data is available, THE Feature_Engineer SHALL include the most recent available Modal_Price from at least one Peer_Market known at or before the Forecast_Origin as a feature; same-day peer prices that have not yet been reported at the Forecast_Origin SHALL NOT be used.
7. IF a feature value for a required lag or window is unavailable at the Forecast_Origin due to missing data, THEN THE Feature_Engineer SHALL mark the row as invalid and exclude it from training and evaluation.
8. THE Feature_Engineer SHALL produce a feature-availability audit table documenting each feature, its derivation logic, and confirmation that it contains no Leakage.
9. FOR ALL feature rows, every feature value at forecast row index t SHALL be derived exclusively from data with index ≤ t; THE Feature_Engineer SHALL enforce this constraint at construction time and record it in the feature-availability audit table.

---

### Requirement 5: Forecasting Model Development and Evaluation

**User Story:** As a researcher, I want to train and compare multiple forecasting models under a rigorous chronological evaluation protocol, so that I can identify the best-performing approach with statistical credibility.

#### Acceptance Criteria

1. THE Forecaster SHALL implement a naive baseline that predicts the most recent known Modal_Price as the forecast.
2. WHERE the dataset has sufficient length to identify a dominant weekly or annual seasonal period, THE Forecaster SHALL implement a seasonal-naive baseline using the price from the same period in the prior seasonal cycle.
3. THE Forecaster SHALL implement linear regression and decision-tree regression as candidate models.
4. WHERE the dataset contains at least 500 training observations after feature construction, THE Forecaster SHALL implement random-forest regression as an additional candidate model.
5. WHERE the data passes an ADF stationarity test at the 5% significance level after differencing AND the differenced series contains at least 200 observations AND visual inspection of the ACF/PACF patterns supports an ARIMA structure, THE Forecaster SHALL implement an ARIMA model as an additional candidate model.
6. THE Forecaster SHALL split the chronological sequence into training (first 60% of observations), validation (next 20%), and test (final 20%) sets; the validation set SHALL be used for feature selection and hyperparameter tuning only, and the test set SHALL NOT be used during those phases. THE Forecaster SHALL apply Walk_Forward_Evaluation on the test set: at each test step, the model is retrained on all chronological data before that step's Forecast_Origin, with no look-ahead beyond that origin.
7. THE Forecaster SHALL compute MAE, RMSE, and MAPE for every model on the test set; MAPE SHALL be accompanied by a note if any actual values are zero or near-zero.
8. THE Forecaster SHALL report metrics broken down by commodity and by market.
9. THE Report_Generator SHALL store the model-comparison report at `reports/experiment_results.md`, including a ranked table of models by MAE and a residual-plot figure per model.

---

### Requirement 6: Anomaly Detection Research Component

**User Story:** As a researcher, I want to detect unusual price movements using forecast residuals and market-relative signals, so that I can investigate whether data-driven anomaly detection is viable for agricultural commodity markets.

#### Acceptance Criteria

1. WHEN a forecast is produced, THE Anomaly_Detector SHALL compute the Residual as the difference between the actual Modal_Price and the forecasted Modal_Price.
2. THE Anomaly_Detector SHALL compute a z-score for each Residual relative to the rolling distribution of residuals over the prior 30 market days.
3. WHERE Peer_Market data is available, THE Anomaly_Detector SHALL compute a peer-divergence signal as the difference between the target market's Modal_Price and the median Modal_Price of Peer_Markets on the same Market_Day.
4. THE Anomaly_Detector SHALL normalize both the residual z-score and the peer-divergence signal to zero mean and unit variance over the evaluation window before combining them; THE Anomaly_Detector SHALL then compute a composite Anomaly_Score as a weighted sum of the normalized signals with configurable weights.
5. THE Anomaly_Detector SHALL conduct an ablation study comparing residual-only, residual-plus-peer, and combined scoring configurations, reporting the Anomaly_Score distribution for each configuration.
6. WHERE ground-truth anomaly labels exist in the dataset, THE Anomaly_Detector SHALL compute precision, recall, and F1-score at a configurable score threshold using only real-world data; results from synthetic shock evaluation SHALL be reported in a separate table and SHALL NOT be merged with real-world evaluation metrics.
7. IF ground-truth anomaly labels are absent, THEN THE Anomaly_Detector SHALL inject synthetic price shocks of configurable magnitude into a held-out data segment and evaluate detection recall against those injected shocks; these synthetic evaluation results SHALL be reported separately from any real-world anomaly analysis.
8. THE Report_Generator SHALL store the anomaly analysis at `reports/anomaly_analysis.md`, including Anomaly_Score distribution plots, precision-recall curves or shock-detection recall curves, and ablation results.

---

### Requirement 7: Notebook Deliverables

**User Story:** As a researcher, I want structured Jupyter notebooks that narrate each phase of the analysis, so that reviewers can follow the research methodology end-to-end in a readable format.

#### Acceptance Criteria

1. THE CropCast repository SHALL contain notebook `notebooks/01_data_audit.ipynb` covering dataset discovery, schema inspection, and data-quality statistics.
2. THE CropCast repository SHALL contain notebook `notebooks/02_eda.ipynb` covering descriptive statistics, trend/seasonality decomposition, correlation analysis, and visual outputs.
3. THE CropCast repository SHALL contain notebook `notebooks/03_forecasting.ipynb` covering feature construction, model training, Walk_Forward_Evaluation, and metric reporting.
4. THE CropCast repository SHALL contain notebook `notebooks/04_anomaly_analysis.ipynb` covering residual computation, Anomaly_Score construction, ablation study, and evaluation against labels or synthetic shocks.
5. WHEN a notebook is executed from top to bottom with a clean kernel, THE CropCast SHALL produce all figures and report outputs without manual intervention, provided the raw data file is present in `data/raw/`.
6. THE CropCast notebooks SHALL import all reusable logic from `src/` modules rather than duplicating code inline.

---

### Requirement 8: Source Module Structure

**User Story:** As a researcher, I want well-separated source modules, so that each component can be tested and reused independently across notebooks and scripts.

#### Acceptance Criteria

1. THE CropCast repository SHALL contain a `src/data/` module with functions for ingestion, schema validation, duplicate removal, and missing-value reporting.
2. THE CropCast repository SHALL contain a `src/features/` module with functions for lag construction, rolling-window statistics, calendar features, and feature-availability auditing.
3. THE CropCast repository SHALL contain a `src/forecasting/` module with classes or functions for each baseline and candidate model, Walk_Forward_Evaluation, and metric computation.
4. THE CropCast repository SHALL contain a `src/anomaly_detection/` module with functions for residual computation, z-score calculation, peer-divergence computation, Anomaly_Score assembly, and shock injection.
5. THE CropCast repository SHALL contain a `src/evaluation/` module with functions for computing MAE, RMSE, MAPE, precision, recall, and F1-score.
6. WHEN a module function receives an empty DataFrame as input, THE module SHALL raise a descriptive ValueError rather than producing silent incorrect output.

---

### Requirement 9: Testing

**User Story:** As a researcher, I want automated tests for core pipeline logic, so that I can verify correctness after changes and ensure the pipeline does not silently produce wrong results.

#### Acceptance Criteria

1. THE tests SHALL cover the Data_Pipeline schema-validation function with at least one valid schema input and at least one input missing each required column.
2. THE tests SHALL cover the Feature_Engineer lag-construction function and verify that no feature value at row index `t` uses data from any row index greater than `t` (Leakage check).
3. THE tests SHALL cover the rolling-window statistics function with a known input sequence and verify the output values match hand-computed expectations.
4. THE tests SHALL cover the Forecaster metric-computation functions (MAE, RMSE, MAPE) with known input vectors and verify outputs match hand-computed values.
5. THE tests SHALL cover the Anomaly_Detector residual z-score function using a known input residual sequence and a specified rolling window size; the test SHALL verify that z-score values at specific indices match hand-computed expectations for that window, and SHALL verify that each z-score value is computed using only residuals within the rolling window ending at that index (causality check).
6. THE tests SHALL cover the shock-injection function and verify that injected shocks of a specified magnitude appear at the specified indices in the output series.
7. FOR ALL valid non-empty DataFrames produced by the Data_Pipeline cleaning step, the row count of the output SHALL be less than or equal to the row count of the input (no rows are added during cleaning).
8. FOR ALL feature matrices produced by the Feature_Engineer, re-running the Feature_Engineer on the same input SHALL produce an identical output (idempotence property).

---

### Requirement 10: Experiment Provenance and Approval Gate

**User Story:** As a researcher, I want explicit researcher approval before any evaluation mode switch and a complete configuration log for every experiment run, so that I can ensure methodological transparency and reproduce any result exactly.

#### Acceptance Criteria

1. WHEN the Dataset_Auditor completes the feasibility report and the evidence indicates that real-world data may be insufficient, THE CropCast SHALL pause the pipeline and require an explicit researcher approval decision before transitioning to synthetic or hybrid evaluation mode; THE CropCast SHALL NOT automatically proceed to synthetic or hybrid evaluation.
2. WHEN a researcher approves or rejects an evaluation mode transition, THE CropCast SHALL record the decision, the timestamp, and the specific feasibility evidence that prompted the decision in the feasibility report at `reports/dataset_feasibility.md`.
3. WHEN any experiment run is executed, THE CropCast SHALL compute and log a configuration hash derived from the dataset version identifier, the Random_Seed value, the feature set definition, and all model hyperparameters.
4. THE CropCast SHALL store the configuration hash and all associated parameter values in a machine-readable experiment log (e.g., `reports/experiment_log.jsonl`) appended at the end of each run, so that any prior run can be exactly reproduced from its logged entry.
5. IF a researcher attempts to run an experiment without a previously recorded configuration hash and the corresponding parameters are not fully specified in configuration, THEN THE CropCast SHALL raise an error and refuse to proceed rather than using default or inferred values silently.

---

### Requirement 11: Engineering Documentation and Research Records

**User Story:** As a researcher and academic submitter, I want a permanent, traceable documentation system maintained throughout development, so that every significant decision, experiment, dataset finding, and milestone is recorded for academic review, reproducibility, and future reference.

#### Acceptance Criteria

1. THE CropCast repository SHALL contain a `docs/` directory with the following files initialized at project start: `project_charter.md`, `requirements_history.md`, `decision_log.md`, `research_log.md`, `experiment_log.md`, `issue_log.md`, `meeting_notes.md`, and `milestone_history.md`.

2. THE `CHANGELOG.md` at the repository root SHALL record all notable project changes in reverse-chronological order, distinguishing verified completions from planned or in-progress work.

3. WHEN a significant architectural, methodological, or data-source decision is made, THE researcher SHALL record it in `docs/decision_log.md` with: date, context, alternatives considered, rationale, outcome, and approval status.

4. WHEN a dataset source is investigated, THE researcher SHALL record it in `docs/research_log.md` with: source name, URL, retrieval date, schema summary, coverage dates, quality findings, licensing constraints, and selection or rejection rationale.

5. WHEN an experiment is executed, THE researcher SHALL record it in `docs/experiment_log.md` with: objective, hypothesis, dataset version, configuration hash, random seed, evaluation method, metrics, output references, interpretation, and known limitations.

6. WHEN a bug, failed approach, or unexpected result is encountered, THE researcher SHALL record it in `docs/issue_log.md` with: symptoms, reproduction steps, root cause (if established), attempted solutions, and verified resolution. Failed experiments SHALL NOT be omitted.

7. WHEN a milestone is reached, THE researcher SHALL update `docs/milestone_history.md` with: milestone name, planned scope, actual completions, evidence of completion (file references, test results), deviations from plan, and outstanding issues.

8. AT THE END of every milestone, THE researcher SHALL produce a concise status summary containing: what was planned and what was completed, evidence supporting completion, decisions made and rationale, unresolved issues and deviations, documentation files updated, and the next recommended milestone.

9. THE documentation SHALL distinguish verified facts, working hypotheses, assumptions, and proposed work using explicit labels; invented results, fabricated citations, and unverified completion claims SHALL NOT appear in any documentation file.

10. WHEN any subsequent milestone's acceptance criteria are defined, documentation updates for that milestone SHALL be included as explicit acceptance criteria items, not treated as optional.

11. THE CropCast repository SHALL NOT commit credentials, private information, or restricted raw dataset files in the `docs/` directory or anywhere else in the repository.
