# CropCast — Runtime Environment

The data pipeline, audit and tests use only the Python standard library. There are no third-party dependencies, so no `requirements.txt` is needed yet.

- **Python:** 3.11 (tested with 3.11.9 on Windows 11, 2026-10-23). No other versions have been tested.
- **Working directory:** run every command from the repository root, so that `src` is importable and the default `data/raw/...` paths resolve.
- **Credentials:** copy `.env.example` to `.env` and set `CEDA_API_KEY`. Only live extraction (`src.data.ingest_ceda`) and `reports/_ceda_audit.py` need it; tests and the offline audit do not.

## Commands

| Purpose | Command | Network |
|---|---|---|
| Run tests | `python -m unittest discover -s tests` | No |
| Offline M-2 audit (stdout) | `python -m src.data.validate` | No |
| Regenerate stored audit | `python -m src.data.validate --output data/raw/m2_validation_audit.json` | No |
| Historical extraction | `python -m src.data.ingest_ceda --all-approved --start-date 2016-01-01 --end-date 2022-12-31 --chunk-months 6` | Yes — CEDA, ≤ 40 req/hr |
| ICTD label audit | `python reports/_parse_labels.py` | No (needs git-ignored label CSVs) |
| CEDA sample audit | `python reports/_ceda_audit.py` | Yes — live CEDA requests, no throttling |

Raw data under `data/` and the `.env` file are git-ignored and must never be committed.
