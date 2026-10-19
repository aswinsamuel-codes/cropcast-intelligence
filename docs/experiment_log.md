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

> No entries yet. Experiment log will be populated during Milestone 3 (Forecasting) and Milestone 4 (Anomaly Detection).
