# Raw data provenance (`data/raw/`)

Raw files in this directory are **not committed**: CEDA's terms permit non-commercial
research use with attribution but do not clearly grant redistribution of the data.
Re-create them with the ingestion command below and a free CEDA API key.

| Item | Value |
|---|---|
| Source | CEDA Agri Market Data API — `https://api.ceda.ashoka.edu.in/v1` (`/agmarknet/prices`, `/agmarknet/quantities`) |
| Original source | Directorate of Marketing & Inspection (DMI), Ministry of Agriculture and Farmers Welfare (Agmarknet) |
| Attribution | Centre for Economic Data and Analysis (CEDA), Ashoka University |
| Series | Maharashtra Onion (`commodity_id=23`, `state_id=27`); Uttar Pradesh Potato (`commodity_id=24`, `state_id=9`) |
| Window | 2016-01-01 to 2022-12-31, 14 six-month chunks per series and endpoint (56 files) |
| Retrieval | Historical chunks: 2026-10-22 20:32Z – 21:59Z (manifest `fetched_at`). Pilot chunks (`*_2021-01-01_2021-01-15.json`, 4 files): 2026-10-22 20:11Z |
| Integrity | SHA-256 per file in `ceda_manifest.json`; offline audit in `m2_validation_audit.json` |

Pilot chunks overlap the H1-2021 historical chunks and are excluded from dataset assembly (ISS-005).

Re-create (≈56 requests at ≤ 40/hour, about 90 minutes):

```
python -m src.data.ingest_ceda --all-approved --start-date 2016-01-01 --end-date 2022-12-31 --chunk-months 6
python -m src.data.validate --output data/raw/m2_validation_audit.json
```
