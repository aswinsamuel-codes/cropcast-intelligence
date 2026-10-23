# Provenance note — anomaly run 1 (`anomaly-20261023T190355Z-a927040a`)

- **Started** from a clean tree at commit `cd56566` (code fingerprint `e7389d24077d…`); **completed** with status `completed` and exit code 0. All 12 artifact checksums matched at verification.
- **`tree_changed_during_run: true`.** `src/reporting/diagnose_sarima_convergence.py` was created at about 00:49 IST while the run was active, so the end fingerprint is `55586692ca81…`. The run never imports that module, and the process had already loaded its code. The executed code was therefore the code at `cd56566`.
- **Warnings counted:**
  - 5 × SARIMA `ConvergenceWarning`, all potato. Located and assessed in `anomaly_sarima_convergence.csv` and `…_impact.json`: no detection changes, residual change ≤ 0.0042.
  - 1 × `RuntimeWarning: All-NaN slice`, from the potato robust score having zero detections in the weak-label window. Its precision is undefined (NaN), not zero.
- **Independent verification:** `python -m src.reporting.verify_anomaly --full` gave 368 checks and 0 problems (2026-10-24).
- **Preserved copies:** `artifacts/` holds copies of the outputs taken after verification, because a later run regenerates the files in `reports/tables`. `anomaly_scores.csv` contains source values and is git-ignored (DEC-022). `anomaly_sarima_convergence*.{csv,json}` were produced by the diagnostic afterwards and are not run outputs.
