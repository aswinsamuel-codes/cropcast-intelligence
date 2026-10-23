# CropCast — Runtime Environment

- **Python:** 3.11 (tested with 3.11.9 on Windows 11, 2026-10-23). No other versions have been tested.
- **Virtual environment:** use a project-local `.venv` (git-ignored). On the development machine the `python` on PATH belongs to an unrelated tool's virtual environment, so always call `.venv/Scripts/python` (Windows) or `.venv/bin/python` (POSIX) explicitly.
- **Dependencies:** pinned in `requirements.txt` (numpy, pandas, scipy, statsmodels, scikit-learn, matplotlib, python-docx, nbformat/nbclient/ipykernel). Ingestion, validation and their tests need only the standard library.
- **Configuration:** all paths, the random seed and experiment parameters are in `configs/config.json` (override with the `CROPCAST_CONFIG` environment variable). Run every command from the repository root.
- **Credentials:** copy `.env.example` to `.env` and set `CEDA_API_KEY`. Only live extraction (`src.data.ingest_ceda`) and `reports/_ceda_audit.py` need it.

## Setup

```
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
```

## Commands

| Purpose | Command | Network |
|---|---|---|
| Run tests | `.venv/Scripts/python -m unittest discover -s tests` | No |
| Offline M-2 audit (stdout) | `.venv/Scripts/python -m src.data.validate` | No |
| Regenerate stored audit | `.venv/Scripts/python -m src.data.validate --output data/raw/m2_validation_audit.json` | No |
| Build frozen analysis dataset | `.venv/Scripts/python -m src.data.dataset` | No |
| Historical extraction | `.venv/Scripts/python -m src.data.ingest_ceda --all-approved --start-date 2016-01-01 --end-date 2022-12-31 --chunk-months 6` | Yes — CEDA, ≤ 40 req/hr |
| ICTD label audit | `.venv/Scripts/python reports/_parse_labels.py` | No (needs git-ignored label CSVs) |
| CEDA sample audit | `.venv/Scripts/python reports/_ceda_audit.py` | Yes — live CEDA requests, no throttling |

Raw and processed data under `data/` and the `.env` file are git-ignored and must never be committed.
