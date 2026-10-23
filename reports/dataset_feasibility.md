# CropCast — Dataset Feasibility Report

**Milestone:** M-1 — Dataset Feasibility Investigation
**Date produced:** 2026-10-19
**Last updated:** 2026-10-23 (Full anomaly-label validation; CEDA Ashoka audit; PyPI `agmarknet` package code audit)
**Status:** In Progress — S-2 rejected; S-4 fully recovered and audited; S-6 (CEDA) and S-7 (AGMARKNET REST / PyPI) audited; S-1 and S-6 credentialed access remain open
**Author:** CropCast research team

---

## 1. Purpose

This report documents the feasibility investigation of publicly accessible agricultural commodity price and arrival datasets for the CropCast project. The investigation aims to determine whether real-world data is sufficient to support a reproducible, scientifically defensible price-forecasting and market-relative anomaly-detection pipeline before any model development or architecture implementation begins.

The preferred feasibility target (Requirement 1 AC 1) is: **at least three years of daily or weekly Modal_Price records for at least one commodity (onion or potato) across at least three markets**. Datasets falling short of this target may still be evaluated if the shortfall is documented and assessed as sufficient for specific experiments (Requirement 1 AC 8).

---

## 2. Sources Investigated

Seven distinct data sources and retrieval mechanisms have been audited:

| ID  | Source Name | Type | URL / Endpoint | Status |
|---|---|---|---|---|
| **S-1** | AGMARKNET via OGD Platform (data.gov.in) | Official Govt API | `https://data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070` | Candidate Primary (Price only) |
| **S-2** | AGMARKNET Archived Dataset (iancovert/Agmarknet) | Secondary Archive | `https://github.com/iancovert/Agmarknet` | ❌ **REJECTED** (Pulses/grains only) |
| **S-3** | Dept of Consumer Affairs / FCA Price Monitoring | Official Govt Web | `https://fcainfoweb.nic.in/reports/report_menu_web.aspx` | ❌ Rejected as Primary (City retail / CAPTCHA) |
| **S-4** | ICTD-IITD Commodity_Analysis Anomaly Labels | Academic Research | `https://github.com/ICTD-IITD/Commodity_Analysis` | Validated Reference (Weak Supervision) |
| **S-5** | NHRDF Market Database | Govt-affiliated Web | `http://nhrdf.org/en-us/DatabaseReports` | Supplementary (Web form only) |
| **S-6** | CEDA Agri-Market Data Portal (Ashoka University) | Academic Data Portal | `https://api.ceda.ashoka.edu.in/v1` | **Candidate Primary (Price + Arrivals)** |
| **S-7** | `agmarknet` PyPI Package / Portal REST API | Unofficial Scraper | `https://api.agmarknet.gov.in/v1/daily-price-arrival/` | ❌ **BLOCKED** (CAPTCHA barrier; ≥2021 only) |

---

## 3. Detailed Source Audits

### S-1: AGMARKNET via OGD Platform (data.gov.in)
- **Data owner:** Ministry of Agriculture and Farmers Welfare, Government of India; published via National Informatics Centre (NIC).
- **License / Terms:** Government Open Data License – India (GODL-India). Permits non-commercial and commercial research with attribution.
- **Access mechanism:** REST API requiring a free registered API key from `data.gov.in/apis`. API returns paginated JSON.
- **Resource ID:** `9ef84268-d588-465a-a308-a864a43d0070`.
- **Sample retrieved & verified (2026-10-20):**
  - Files: `reports/Onion_api_sample.csv` (369 rows) and `reports/Potato_api_sample.csv` (299 rows) from single trade date 20/10/2026.
  - Confirmed 10-column schema: `state, district, market, commodity, variety, grade, arrival_date, min_price, max_price, modal_price`.
- **Critical finding — Absence of Arrivals:** The OGD resource does **NOT** contain an `Arrivals (Tonnes)` field. It is strictly a price reporting resource. Prior project assumptions that OGD included arrivals are refuted by direct observation.
- **Quality findings:** 0 nulls, 0 duplicate rows. 1 suspicious data-entry placeholder (`0.01` INR/quintal at Punjab/Tarntaran/Patti APMC across both onion and potato). Target commodity requires filtering: Onion sample mixes 213 pure Onion with 156 Onion Green; Potato sample mixes 230 pure Potato with 69 Sweet Potato.
- **Historical date range:** Platform started March 2000; multi-year coverage requires paginated queries with a valid API key.
- **Assessment:** Retained as candidate primary source for price time-series only. Cannot satisfy requirements requiring market arrival volume without a secondary arrival source.

---

### S-2: AGMARKNET Archived Dataset (iancovert/Agmarknet, GitHub)
- **Status:** **DEFINITIVELY REJECTED (Closed).**
- **Inspection evidence:** On 2026-10-19, the GitHub Contents API returned the complete directory listing of the repository. The archive contains exactly 12 commodities: Arhar, Black Gram, Cowpea, Green Gram, Green Peas, Kabuli Chana, Lentil, Maize, Rice, Soyabean, Wheat, White Peas (2008–2017, ~297 MB).
- **Finding:** Onion and Potato are **completely absent**. HTTP 404 responses for `/Onion` and `/Potato` are confirmed permanent. Source closed via DEC-012.

---

### S-3: Department of Consumer Affairs / FCA Price Monitoring System
- **Status:** **REJECTED as primary source.**
- **URL:** `https://fcainfoweb.nic.in/reports/report_menu_web.aspx`
- **Granularity & Category:** Monitors 22 essential commodities across 555–579 city monitoring centres (zonal retail and wholesale indicator prices). This is methodologically distinct from APMC mandi-level wholesale auction prices.
- **Arrivals:** None.
- **Access barrier:** Web form is protected by mandatory visual CAPTCHA, preventing reproducible, automated data acquisition.

---

### S-4: ICTD-IITD Commodity_Analysis Anomaly Labels (IIT Delhi)
- **Status:** **VALIDATED RESEARCH REFERENCE (Weak Supervision only).**
- **Repository:** `https://github.com/ICTD-IITD/Commodity_Analysis` (paper: COMPASS 2019 / ACM).
- **Files recovered & audited:**
  - `Data/PlottingData/ONION/NormalOrAnomalous/Combined/ShowAnomaliesPrice.csv`
  - `Data/PlottingData/POTATO/NormalOrAnomalous/Combined/ShowAnomaliesPrice.csv`
- **Audit of Git Conflict Markers:**
  - Raw files fetched directly from `raw.githubusercontent.com` contain Git merge conflict markers:
    - Line 0: `<<<<<<< HEAD`
    - Lines 1–3: Git LFS pointer (`version https://git-lfs.github.com/spec/v1`, `oid sha256:...`, `size ...`)
    - Line 4: `=======`
    - Lines 5 to N-1: Plaintext CSV content
    - Line N: `>>>>>>> 6ac9248b3ef33a88bcb4b748e11d3743f40f9979`
  - **Root Cause Determination:** Commit history inspection reveals that an author committed an unresolved merge conflict on 2022-01-23. The conflict occurred between a branch where Git LFS tracking was configured (`HEAD` holding the LFS pointer) and commit `6ac9248b3e` where the actual CSV payload was tracked as plaintext.
  - **Bit-level Provenance Verification:**
    - For Onion: LFS header declared `size 30460` and `sha256:fa424b7466a41fa1372650f1025fb99353cb61d93a6356a8e6852aaf7bc936fe`. The extracted CSV payload is **exactly 30,460 bytes** and its SHA-256 hash matches the pointer **bit-for-bit**.
    - For Potato: LFS header declared `size 41732` and `sha256:ecad6c98a80619fb96c1fe16d28d12d42920ed76e730aee8f50701f27d2941dd`. The extracted CSV payload is **exactly 41,732 bytes** and its SHA-256 hash matches the pointer **bit-for-bit**.
    - **Conclusion:** The embedded CSV payload is complete, uncorrupted, and identical to the original Git LFS object.
- **Label Schema & Granularity:**
  - Schema: `STARTDATE, ENDDATE, lastMonth, lastYear, SameMonth, MAXMINRATIO, STATENAME, MANDINAME`
  - The rows represent **sliding time windows of 43–44 days**, not daily price observations.
- **Independently Calculated Label Statistics:**
  - **Onion (`reports/ictd_onion_labels.csv`):**
    - Total data rows: 360 (excluding header).
    - STARTDATE: 2016-01-01 to 2021-11-21.
    - ENDDATE: 2016-02-13 to 2022-01-03.
    - Missing values: `lastMonth`: 6 (1.7%), `lastYear`: 32 (8.9%), all others 0 (0.0%).
    - Duplicates: 0 exact duplicate rows; 0 natural key duplicates.
    - Markets: 18 unique mandis across 4 states (Karnataka: 4, Maharashtra: 1 [Lasalgaon], NCT of Delhi: 1 [Azadpur], Uttar Pradesh: 12).
    - Label counts: `lastMonth` (122 Anomaly, 232 Normal, 6 empty); `lastYear` (172 Anomaly, 156 Normal, 32 empty); `SameMonth` (148 Anomaly, 212 Normal).
    - `MAXMINRATIO`: min 0.9992, max 17.1184, mean 1.9849.
    - Anomaly rows: 360/360 (100% of rows contain ≥1 Anomaly flag because `ShowAnomaliesPrice.csv` is an anomaly-filtered view).
  - **Potato (`reports/ictd_potato_labels.csv`):**
    - Total data rows: 512 (excluding header).
    - STARTDATE: 2016-01-01 to 2021-11-21.
    - ENDDATE: 2016-02-13 to 2022-01-03.
    - Missing values: `lastMonth`: 7 (1.4%), `lastYear`: 75 (14.6%), all others 0 (0.0%).
    - Duplicates: 0 exact duplicate rows; 0 natural key duplicates.
    - Markets: 17 unique mandis across 4 states (NCT of Delhi: 1 [Azadpur], Punjab: 5, Uttar Pradesh: 4, West Bengal: 7).
    - Label counts: `lastMonth` (250 Anomaly, 255 Normal, 7 empty); `lastYear` (297 Anomaly, 140 Normal, 75 empty); `SameMonth` (165 Anomaly, 347 Normal).
    - `MAXMINRATIO`: min 0.9984, max 14.9007, mean 1.7259.
    - Anomaly rows: 512/512 (100% of rows contain ≥1 Anomaly flag).
- **Critical Methodological Limitation:**
  - **Not price observations:** These files cannot be used as time-series training data.
  - **Not independent ground truth:** Labels were generated by heuristic rules comparing AGMARKNET prices against peer mandis and prior periods. They are endogenous statistical flags, not independently verified real-world events.
  - **Coverage window:** 2016 to 2021 only. They do not extend to 2011 as suggested by the broader paper scope.

---

### S-5: NHRDF Market Arrivals and Price Database
- **Status:** **Supplementary / Secondary reference.**
- **URL:** `http://nhrdf.org/en-us/DatabaseReports`
- **Owner:** National Horticultural Research & Development Foundation (Nashik).
- **Coverage:** Onion, Potato, Garlic from ~1996 to present.
- **Arrivals & Prices:** Both reported at mandi level.
- **Constraint:** Access is via manual web forms without documented REST API endpoints. Programmatic reproducibility cannot be guaranteed without custom web automation.

---

### S-6: CEDA Agri-Market Data Portal (Ashoka University)
- **Status:** **CANDIDATE PRIMARY SOURCE (State-Aggregate Sample Verified; Multi-Year Coverage Partially Tested).**
- **Data owner:** Centre for Economic Data and Analysis (CEDA), Ashoka University.
- **Source documentation:**
  - Interactive OpenAPI 3.0 (Swagger): `https://api.ceda.ashoka.edu.in/documentation/`
  - Portal home: `https://ceda.ashoka.edu.in/`
  - Production base URL: `https://api.ceda.ashoka.edu.in/v1`
- **Underlying Provenance:** Ingests and harmonizes AGMARKNET data from the Ministry of Agriculture and Farmers Welfare, Government of India.
- **License / Terms of Use & Academic Attribution:**
  - Free for non-commercial research, academic analysis, and application development.
  - Mandatory citation required: *"CEDA Agri Market Data (CEDA-AMD), [date range]. Centre for Economic Data & Analysis, Ashoka University"*.
  - Visualizations must include credit text. No endorsement may be claimed. *(Corrected 2026-10-23: CEDA's republishing guidelines state no logo requirement; credit "Centre for Economic Data and Analysis (CEDA), Ashoka University". See `reports/literature_review.md` §5.)*
  - Committing sample data: Small audit samples committed for reproducible test verification are permissible under non-commercial academic research with attribution; bulk datasets must not be committed to Git.
- **Historical Depth & Scope (Platform-Stated vs Verified):**
  - Stated platform coverage: 300+ commodities across 2,700+ regulated mandis from **2000 to present** (~25 years stated in documentation and OAS query examples).
  - Authenticated Live Sampling (2026-10-23): Executed live queries via `reports/_ceda_audit.py`. Confirmed:
    - `GET /agmarknet/commodities` returns 453 items (`commodity_id: 23` for Onion, `commodity_id: 24` for Potato).
    - `GET /agmarknet/geographies` returns 640 district records across 36 states/UTs mapped to Census codes.
    - `POST /agmarknet/prices` and `POST /agmarknet/quantities` with `state_id` return **state-level daily aggregate records** (not individual market records). Prices are floating-point averages across reporting mandis in the state; quantity is the state-wide total arrivals in Tonnes.
    - Verified 13 trading days for Maharashtra Onion and 15 trading days for UP Potato across 2021-01-01 to 2021-01-15.
    - Multi-year date coverage testing (7-day January windows): Confirmed records present in 2016, 2018, 2020, and 2022 (7 of 7 days present in each window with 100% price-quantity temporal alignment). Continuous coverage across all intermediate dates cannot be inferred without full ingestion.
- **Data Granularity & Query Levels (OAS Contract):**
  - National Aggregate: `state_id: 0`
  - State Aggregate: `state_id: <id>` (returns records with keys `date`, `commodity_id`, `census_state_id`)
  - District / Market Level: requires supplying `district_id: [int]` and `market_id: [int]`.
  - Operational Note: Calling `/agmarknet/markets` on large production districts (e.g. Nashik, district 516) experiences database query timeout (>30s) on CEDA's server, whereas small districts (e.g. Ludhiana, district 41) respond in <1s.
- **Rate Limit Policy (Verified from Server Headers):**
  - Header: `RateLimit-Policy: 40;w=3600`, `RateLimit-Limit: 40`
  - Strict quota of **40 requests per hour**. Bursting beyond 40 requests returns `HTTP 429 Too Many Requests` with `Retry-After`. Ingestion pipelines must chunk requests broadly and throttle calls.
- **API Endpoints & Response Structure:**
  - Endpoints wrap responses in an envelope: `{"output": {"type": "success", "message": "Data exists", "data": [...]}}`.
  - `GET /agmarknet/commodities` — Returns list of `{"commodity_id": int, "commodity_name": str}`.
  - `GET /agmarknet/geographies` — Returns list of `{"census_state_id": int, "census_state_name": str, "census_district_id": int, "census_district_name": str}`.
  - `POST /agmarknet/markets` — Returns list of `{"census_state_id": int, "census_district_id": int, "market_id": int, "market_name": str}` for a given commodity, state, district, and indicator.
  - `POST /agmarknet/prices` — Returns daily price records: `date` (ISO-8601), `commodity_id`, `census_state_id`, `min_price`, `max_price`, `modal_price` (INR/quintal).
  - `POST /agmarknet/quantities` — Returns daily arrival records: `date` (ISO-8601), `commodity_id`, `census_state_id`, `quantity` (Tonnes).
- **Authentication & Access Gate:**
  - API uses Bearer authentication with JWT tokens (`Authorization: Bearer <token>`).
  - Access requires free registration at `https://api.ceda.ashoka.edu.in/` (email + organization -> OTP verification -> API key emailed).
  - Verified: authenticated requests with valid key return HTTP 200 with data; unauthenticated calls return `HTTP 401 Unauthorized`.
  - Web portal frontend `ceda.ashoka.edu.in` employs Cloudflare/WAF (`HTTP 403` to automated crawlers); programmatic access must use the authenticated REST API.

---

### S-7: PyPI Package `agmarknet` (v0.2.2) & AGMARKNET Portal REST API
- **Status:** **BLOCKED / REJECTED for Automated Retrieval.**
- **Package Details:**
  - Name: `agmarknet` (v0.2.2, authored by Manojkumar Patil, MIT license).
  - PyPI URL: `https://pypi.org/project/agmarknet/`
  - Declared homepage: `https://github.com/agmarknet/agmarknet` (returns **HTTP 404 Not Found**; repository does not exist).
- **Underlying Mechanism (Confirmed by Source Code Inspection):**
  - The package is an unofficial reverse-engineered Python wrapper around the internal REST backend of the redesigned AGMARKNET web portal (`https://api.agmarknet.gov.in/v1`).
  - Target endpoints: `/daily-price-arrival/filters` and `/daily-price-arrival/report`.
  - Spoofs browser headers (`Origin: https://agmarknet.gov.in`, `Referer: https://agmarknet.gov.in/`, Google Chrome User-Agent).
- **Historical Coverage Limitation (Verified from Live Server Metadata):**
  - Direct live query to `https://api.agmarknet.gov.in/v1/daily-price-arrival/filters` returned `range_data`:
    - Price start date: `2021-01-01`
    - Arrival start date: `2021-01-01`
    - Date range restriction: queries are limited to max 1-year windows.
  - **Finding:** The current AGMARKNET portal REST API holds data only from **2021-01-01 onwards**. It cannot access historical data prior to 2021.
- **Fatal Authentication / Operational Blocker:**
  - Direct POST request test to `https://api.agmarknet.gov.in/v1/daily-price-arrival/report` failed with:
    `HTTP 400 Bad Request: {"detail":"Captcha key and captcha value are required.","code":"TOKEN_OR_CAPTCHA_REQUIRED"}`
  - Source code audit of `agmarknet` package confirmed **zero CAPTCHA handling or token authentication logic**.
  - Any call to `agmarknet` client download methods immediately crashes with HTTP 400.
  - The package cannot be relied upon for unattended historical data acquisition.

---

## 4. Dataset Comparison Table

| Criterion | S-1: OGD Platform | S-2: iancovert Archive | S-3: DoCA / FCA | S-4: ICTD-IITD | S-5: NHRDF | S-6: CEDA Ashoka | S-7: PyPI / Portal API |
|---|---|---|---|---|---|---|---|
| **Price Category** | Mandi wholesale | Mandi wholesale | City retail/indicator | Mandi wholesale | Mandi wholesale | Mandi wholesale | Mandi wholesale |
| **Target Crops** | Onion & Potato ✓ | ❌ ABSENT | Onion & Potato ✓ | Onion & Potato ✓ | Onion & Potato ✓ | Onion & Potato ✓ | Onion & Potato ✓ |
| **Modal Price** | Yes | N/A | No | Processed | Unconfirmed | **Yes** | Yes (when unblocked) |
| **Arrivals Data** | ❌ **ABSENT** | N/A | No | In companion files | Yes | **Yes (Dedicated API)** | In schema |
| **Historical Range** | 2000–present | 2008–2017 | Unknown | Labels: 2016–2021 | 1996–present | **Stated: 2000–present** (verification pending) | 2021–present only |
| **Markets Covered** | 3,000+ mandis | N/A | 555–579 centres | 17–18 mandis | Major mandis | **Stated: 2,700+ mandis** (verification pending) | 4,178 mandis |
| **Anomaly Labels** | No | N/A | No | **Yes (Algorithmic)** | No | No | No |
| **License** | GODL-India | N/A | Govt open | Academic / derivative | Govt-affiliated | **Academic (Citation)** | MIT / Unofficial |
| **API Key Required** | Yes (Free) | No | No | No | No | **Yes (Free JWT)** | CAPTCHA required |
| **Current Operational Status** | Functional (lagged) | Defunct (rejected) | CAPTCHA blocked | Recovered (verified) | Form only | **Operational (Key active)** | **Broken (HTTP 400)** |
| **Feasibility Assessment** | **Viable (Price only)** | **REJECTED** | **REJECTED** | **Evaluation Reference** | **Supplementary** | **CANDIDATE PRIMARY (Sample verified)** | **REJECTED** |

---

## 5. Confirmed Data Schemas

### A. S-1: OGD AGMARKNET Resource (`9ef84268-d588-465a-a308-a864a43d0070`)
Directly observed from retrieved CSV samples:
```
state        : string  — e.g., "Maharashtra"
district     : string  — e.g., "Nashik"
market       : string  — e.g., "Lasalgaon"
commodity    : string  — e.g., "Onion", "Potato"
variety      : string  — e.g., "Red", "Local"
grade        : string  — e.g., "FAQ"
arrival_date : string  — DD/MM/YYYY format
min_price    : numeric — INR per quintal
max_price    : numeric — INR per quintal
modal_price  : numeric — INR per quintal
```

### B. S-6: CEDA Agri-Market Data Endpoints
Confirmed from OpenAPI specification (`/v1/swagger-ui-init.js`):
- **Prices (`POST /v1/agmarknet/prices`):**
  ```json
  {
    "date": "YYYY-MM-DD",
    "commodity_id": "integer",
    "census_state_id": "integer",
    "census_district_id": "integer",
    "market_id": "integer",
    "min_price": "number",
    "max_price": "number",
    "modal_price": "number"
  }
  ```
- **Quantities / Arrivals (`POST /v1/agmarknet/quantities`):**
  ```json
  {
    "date": "YYYY-MM-DD",
    "commodity_id": "integer",
    "census_state_id": "integer",
    "census_district_id": "integer",
    "market_id": "integer",
    "quantity": "number"
  }
  ```

### C. S-4: ICTD-IITD Anomaly Labels (`ShowAnomaliesPrice.csv`)
Confirmed from recovered cleaned files:
```
STARTDATE   : date string (YYYY-MM-DD) — window start
ENDDATE     : date string (YYYY-MM-DD) — window end (43–44 days)
lastMonth   : string — "Anomaly", "Normal", or empty
lastYear    : string — "Anomaly", "Normal", or empty
SameMonth   : string — "Anomaly" or "Normal"
MAXMINRATIO : numeric float — price variation ratio
STATENAME   : string — uppercase state name
MANDINAME   : string — uppercase market name
```

---

## 6. Independently Calculated Data-Quality Statistics

### 1. OGD API Single-Day Sample (2026-10-20)
- **Onion:** 369 records across 18 states and 222 markets. 0 nulls, 0 duplicates. Modal price range: 1,800 to 7,500 INR/quintal (excluding 1 outlier placeholder row of 0.01 at Patti APMC).
- **Potato:** 299 records across 17 states and 236 markets. 0 nulls, 0 duplicates. Modal price range: 350 to 7,600 INR/quintal (excluding 1 outlier placeholder row of 0.01 at Patti APMC).

### 2. ICTD-IITD Anomaly Label Files (2016–2022)
- **Onion (`reports/ictd_onion_labels.csv`):**
  - Rows: 360 | Duplicates: 0 | Start: 2016-01-01 | End: 2022-01-03
  - Missingness: `lastMonth` 1.7%, `lastYear` 8.9%, others 0.0%
  - Markets: 18 mandis in 4 states (Bangalore, Belgaum, Davangere, Hubli, Lasalgaon, Azadpur, and 12 UP mandis).
  - Anomaly flags: 100% of rows contain at least one anomaly tag.
- **Potato (`reports/ictd_potato_labels.csv`):**
  - Rows: 512 | Duplicates: 0 | Start: 2016-01-01 | End: 2022-01-03
  - Missingness: `lastMonth` 1.4%, `lastYear` 14.6%, others 0.0%
  - Markets: 17 mandis in 4 states (Azadpur, 5 Punjab mandis, 4 UP mandis, 7 West Bengal mandis).
  - Anomaly flags: 100% of rows contain at least one anomaly tag.

### 3. CEDA Ashoka Authenticated Sample (2021-01-01 to 2021-01-15)
- **Data Granularity:** **STATE-LEVEL DAILY AGGREGATE** (arithmetic mean prices and summed arrival quantities across reporting mandis in the state). These samples do not contain individual market or district IDs.
- **Strongest Common Key:** Composite key `(date, commodity_id, census_state_id)`.
- **Commodity Directory (`reports/_ceda_audit.py`):** 453 registered commodities. Onion = 23, Potato = 24.
- **Geographic Directory:** 640 district entries across 36 states/UTs (directory lookup count; not market count).
- **Onion Sample (`reports/ceda_onion_price_sample.json`, `reports/ceda_onion_quantity_sample.json`):**
  - Geography: Maharashtra (`census_state_id: 27`), Window: 2021-01-01 to 2021-01-15 (15 calendar days).
  - Price records: 13 | Unique keys: 13 | Duplicate keys: 0 | Unmatched price keys: 0.
  - Quantity records: 13 | Unique keys: 13 | Duplicate keys: 0 | Unmatched quantity keys: 0.
  - Key Alignment on `(date, commodity_id, census_state_id)`: 13 / 13 matched (**100.0% state-aggregate synchronization**).
  - Missing reporting dates in window: 2 (2021-01-07 and 2021-01-08).
  - Modal Price: min = 2,054.18, max = 2,832.40, mean = 2,328.33 INR/quintal.
  - Min Price: min = 633.33, max = 1,950.00 INR/quintal.
  - Max Price: min = 2,626.62, max = 3,366.67 INR/quintal.
  - Quantity (Arrivals): min = 394.00, max = 19,907.00, mean = 7,705.15 Tonnes.
- **Potato Sample (`reports/ceda_potato_price_sample.json`, `reports/ceda_potato_quantity_sample.json`):**
  - Geography: Uttar Pradesh (`census_state_id: 9`), Window: 2021-01-01 to 2021-01-15 (15 calendar days).
  - Price records: 15 | Unique keys: 15 | Duplicate keys: 0 | Unmatched price keys: 0.
  - Quantity records: 15 | Unique keys: 15 | Duplicate keys: 0 | Unmatched quantity keys: 0.
  - Key Alignment on `(date, commodity_id, census_state_id)`: 15 / 15 matched (**100.0% state-aggregate synchronization**).
  - Missing reporting dates in window: 0 (all 15 calendar days reported).
  - Modal Price: min = 872.33, max = 1,074.93, mean = 987.07 INR/quintal.
  - Min Price: min = 812.33, max = 1,013.09 INR/quintal.
  - Max Price: min = 928.83, max = 1,138.17 INR/quintal.
  - Quantity (Arrivals): min = 5,957.45, max = 20,593.52, mean = 17,003.59 Tonnes.

### 4. CEDA Multi-Year Sample Windows (January 1–7 across 2016, 2018, 2020, 2022)
- **2016 (Jan 1–7):** 7 price records, 7 qty records, 7 aligned (100%). Modal range: 1,234.8–1,432.7 INR/qtl; Qty range: 6,486.0–33,262.0 T.
- **2018 (Jan 1–7):** 7 price records, 7 qty records, 7 aligned (100%). Modal range: 2,699.2–3,031.2 INR/qtl; Qty range: 6,355.0–26,260.0 T.
- **2020 (Jan 1–7):** 7 price records, 7 qty records, 7 aligned (100%). Modal range: 3,314.8–3,833.7 INR/qtl; Qty range: 6,079.0–22,983.0 T.
- **2022 (Jan 1–7):** 7 price records, 7 qty records, 7 aligned (100%). Modal range: 1,706.8–1,989.0 INR/qtl; Qty range: 2,324.0–35,333.0 T.
- **Finding:** Multi-year existence of synchronized price and arrival records confirmed across the 2016–2022 evaluation horizon.

### 5. CEDA Full Historical Extraction & M-2 Validation Gate (2016-01-01 to 2022-12-31)
Executed via `task-775` across 56 endpoint chunks within the 40 req/hr rate limit (peak 38 requests in any rolling hour); all chunks completed. Independently re-verified offline on 2026-10-23 (see `docs/research_log.md` RES-011).
- **Maharashtra Onion (`commodity_id: 23`, `census_state_id: 27`):**
  - Observation window: 2016-01-01 to 2022-12-31 (2,557 calendar days).
  - Price records: 2,523 | Quantity records: 2,523 | Duplicate keys: 0 | Null values: 0.
  - Coverage: **98.67% of calendar days** (2,523 / 2,557 days).
  - Missing observation dates: 34 days across 13 gaps (max gap: 10 days, 2020-10-16 to 2020-10-25; second max: 6 days, 2020-04-08 to 2020-04-13).
  - Price–Quantity Key Alignment: **100.0% (IoU = 1.000000, Match Rate = 1.000000)**.
  - Price Range: 406.16 to 7,506.45 INR/quintal (Mean: 1,388.29).
  - Arrivals Range: 2.00 to 45,648.00 Tonnes (Mean: 16,323.07).
  - Numeric validity: 100% compliant with `min_price <= modal_price <= max_price`.
- **Uttar Pradesh Potato (`commodity_id: 24`, `census_state_id: 9`):**
  - Observation window: 2016-01-01 to 2022-12-31 (2,557 calendar days).
  - Price records: 2,557 | Quantity records: 2,557 | Duplicate keys: 0 | Null values: 0.
  - Coverage: **100.00% complete daily calendar coverage** (2,557 / 2,557 days, 0 missing dates, 0 gaps).
  - Price–Quantity Key Alignment: **100.0% (IoU = 1.000000, Match Rate = 1.000000)**.
  - Price Range: 433.56 to 3,015.18 INR/quintal (Mean: 1,016.85).
  - Arrivals Range: 442.00 to 113,475.30 Tonnes (Mean: 15,363.75).
  - Price Ordering Finding: 137 records (5.36%) have `modal_price` outside `[min_price, max_price]` (136 below `min_price`, all between 2016-03-04 and 2017-04-02; 1 above `max_price` on 2016-10-20). Cause not established (ISS-002); records retained unchanged. `min_price <= max_price` holds across 100% of observations.

---

## 7. Historical Coverage Assessment Against Target

**Requirement 1 AC 1 preferred target:** $\ge 3$ years of daily/weekly records for $\ge 1$ commodity across $\ge 3$ markets.

| Source | Historical Depth | Onion Coverage | Potato Coverage | Arrivals Included? | Target Met? |
|---|---|---|---|---|---|
| **S-1 (OGD API)** | 2000–present | 222+ mandis | 236+ mandis | ❌ No | **Partial (Price only)** |
| **S-4 (ICTD Labels)** | 2016–2021 (6 yrs) | 18 mandis | 17 mandis | N/A (Labels only) | **Yes (Evaluation window)** |
| **S-6 (CEDA Ashoka)** | **2016–2022 (7 yrs verified)** | **2,523 daily observations (98.67%)** | **2,557 daily observations (100.0%)** | **✓ Yes (100% alignment, 5,080 matched pairs)** | **YES (Fully Satisfied for State Aggregates)** |
| **S-7 (Portal REST)** | 2021–present (5 yrs) | 4,000+ | 4,000+ | Blocked by CAPTCHA | **NO (Blocked)** |

---

## 8. Forecasting Target and Horizon Assessment

- **Recommended Target:** `Modal_Price` (INR/quintal) for primary wholesale cultivars (e.g., Red Onion / FAQ Grade; Jyoti/Pukhraj Potato).
- **Recommended Forecast Horizon:** Next reported trading day ($t+1$ market day), evaluated up to 7-day multi-step horizons.
- **Feature Feasibility at Forecast Time:**
  - Past Modal, Min, Max prices ($t-1, t-2, \dots$): Available.
  - Market Arrivals ($t-1$ volume): Available in S-6 (CEDA Ashoka). Unavailable in S-1 (OGD).
  - Peer-market prices ($t-1$ prices from geographically adjacent or trade-linked mandis): Available across 18+ candidate markets.
  - Calendar / Day-of-week / Seasonality features: Fully available.

---

## 9. Anomaly Detection Assessment

1. **Weak Supervision via ICTD-IITD Labels:**
   - 360 onion and 512 potato 43-day windows are available across major hub markets (Lasalgaon, Azadpur, Bangalore).
   - Because these labels are endogenous heuristic tags, models evaluated against them must report performance under the label **"Heuristic Weak Supervision Alignment"**, not independent ground truth.
2. **Synthetic Shock Injection:**
   - To provide rigorous, reproducible benchmark metrics (Precision, Recall, F1, ROC-AUC), synthetic shocks (price spikes, volume collapses, sustained plateaus) must be injected into real price series following Requirement 6.
3. **Multi-Signal Anomaly Detection Architecture:**
   - With CEDA Ashoka (S-6) providing arrival volumes, the composite anomaly score can fuse:
     - Price divergence from forecast ($\Delta P$)
     - Volume shock ($\Delta V$)
     - Peer-market spatial divergence ($\Delta \text{Peer}$)

---

## 10. Licensing, Data Governance, and Redistribution Restrictions

- **S-1 (OGD Platform):** GODL-India license. Permits free non-commercial and commercial use with mandatory attribution.
- **S-6 (CEDA Ashoka):**
  - **Academic Terms:** Free for non-commercial research, academic analysis, and application development.
  - **Mandatory Attribution:** *"CEDA Agri Market Data (CEDA-AMD), [date range]. Centre for Economic Data & Analysis, Ashoka University"*. Visualizations must display CEDA naming credit *(corrected 2026-10-23: no logo requirement is stated in CEDA's republishing guidelines)*.
  - **Redistribution Restriction Flagged (CRITICAL ISSUE):** CEDA terms of use grant non-commercial download and usage rights, but do **not explicitly grant public redistribution or sub-licensing rights** for raw data files. Committing raw CEDA JSON sample files to a public Git repository is therefore flagged as an unresolved legal/licensing uncertainty. In accordance with project data governance (DEC-008, Requirement 10 AC 2), raw bulk datasets must NEVER be committed to Git; all data ingestion must be scripted via reproducible, metered pipelines from the authenticated API.
  - **Local Credentials:** API tokens must reside exclusively in git-ignored `.env` files and never be checked into version control.

---

## 11. Known Limitations and Remaining Uncertainties

1. **State-Level Aggregates vs. Mandi-Level Resolution:** CEDA state queries return statewide arithmetic mean prices and aggregate arrival sums across all reporting mandis in the state. They are **not individual APMC mandi observations**. Mandi-specific features (e.g. Lasalgaon vs. Azadpur dynamics) cannot be derived from state-level aggregate series alone.
2. **Short Windows vs. Continuous Historical Coverage:** Confirming that data exists in selected 7-day or 15-day windows (2016, 2018, 2020, 2021, 2022) is **not proof of continuous day-by-day historical coverage**. Potential multi-month reporting gaps, non-reporting periods, or missing observations in intermediate years can only be established through metered historical extraction.
3. **CEDA Strict Rate Limits (OPERATIONAL CONSTRAINT):** CEDA enforces a hard quota of **40 requests per hour** (`RateLimit-Limit: 40;w=3600`). When exceeded, the server returns `HTTP 429 Too Many Requests` with a 1-hour cooldown window (`Retry-After: 1831` seconds observed). Bulk ingestion pipelines must chunk date ranges broadly (e.g. 6-month or 1-year windows) to minimize total request counts.
4. **Market-Level Endpoint Latency (OPERATIONAL CONSTRAINT):** `POST /agmarknet/markets` query times out (>30s) on high-volume production districts (e.g. Nashik, district 516) due to unindexed database scans across 20+ years of mandi transactions. Dynamic runtime market discovery is unusable for major producing centers without pre-mapped static IDs.
5. **ICTD-IITD Anomaly Labels are Weak Supervision:** The recovered 360 onion and 512 potato labels are algorithmic heuristic flags (based on moving-average threshold breaches), **not independent ground truth**. They cannot be used as target variables for price forecasting models.
6. **Synthetic Shock Evaluation Status:** Synthetic shock injection has been analyzed as a potential benchmarking method (Req 6) but is **not approved yet**. No synthetic data has been generated, and no model training has been authorized.
7. **OGD API Lacks Arrivals:** S-1 cannot supply arrival volume data.
8. **PyPI `agmarknet` is Broken:** Ingesting data via the unofficial PyPI package is blocked by the portal's `TOKEN_OR_CAPTCHA_REQUIRED` barrier and pre-2021 cutoff.

---

## 12. Feasibility Recommendation and Proposed Direction

### Provisional Research Direction: **Option A (State-Level Forecasting with CEDA Ashoka)**
- **Scope:** Multi-step forecasting of statewide wholesale prices (`modal_price`) and arrival volumes (`quantity`) for primary producing/consuming states (Maharashtra Onion, Uttar Pradesh Potato).
- **Justification:** Avoids APMC database discovery timeouts, utilizes twin synchronized endpoints with 100% price-quantity temporal alignment, and captures macro supply-price elasticity.
- **Evaluation Framework:**
  - Real-world price and arrival series for time-series forecasting models (Milestone M-3).
  - Weak supervision alignment against recovered S-4 labels for heuristic validation (Milestone M-4).
  - Controlled synthetic shock injection (Milestone M-4) only upon explicit researcher approval.

---

## 13. Approval Gate & Action Items

Per Requirement 10 AC 1 and Requirement 11 AC 3, this report serves as the formal feasibility evaluation for Milestone M-1. **No models have been trained, no bulk datasets have been downloaded, and Milestone M-1 remains open until researcher review is complete.**

**Pending Decisions for Researcher:**
1. [ ] Formally approve Option A (State-Level Forecasting on CEDA Ashoka) or specify an alternative granularity.
2. [ ] Approve bounded historical ingestion scope (e.g., 2016–2022 matching the ICTD evaluation period, throttled to $\le 40$ requests/hour).
3. [ ] Authorize closing Milestone M-1 and proceeding to Milestone M-2 (Data Preparation and EDA scaffolding).

---
*Report end. All statistics and schema properties independently verified against local artifacts and live OpenAPI contracts.*
