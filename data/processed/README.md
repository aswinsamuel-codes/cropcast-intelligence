# Processed data (`data/processed/`)

`cropcast_analysis_v1.csv` is the frozen analysis dataset (git-ignored; CEDA redistribution terms are not clear).
`cropcast_analysis_v1.meta.json` is tracked. It records the construction rules, units, the SHA-256 of every source chunk and of the manifest, row counts, the missing-day report, flag counts and the CSV's SHA-256.

Rebuild (offline, deterministic, lossless): `.venv/Scripts/python -m src.data.dataset`.
A rebuild from the same raw files must reproduce the `csv_sha256` in the metadata; `src.data.dataset.load_dataset` refuses a CSV whose checksum does not match.
