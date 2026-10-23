# CropCast — Research Log

Dataset sources and research findings are recorded here in chronological order.

Each entry records: source name, URL, retrieval date, schema summary, coverage dates, quality findings, licensing constraints, and selection or rejection rationale.

---

## Entry Template

```
### RES-NNN: [Source Name]
- **Date accessed:** YYYY-MM-DD
- **URL:** [direct link]
- **Source type:** Official government / Secondary / Research publication / Other
- **Data owner:** [organization]
- **License / Terms of use:** [summary]
- **Date range:** [start date] to [end date]
- **Record count:** [approximate or exact]
- **Commodities covered:** [list]
- **Markets covered:** [count and description]
- **Price fields available:** [Min_Price, Max_Price, Modal_Price, other]
- **Units and currency:** [e.g., INR per quintal]
- **Arrival / supply data:** [available / not available / partial]
- **Schema summary:** [column names and types as observed]
- **Missing values:** [percentage or count per key column]
- **Duplicate records:** [count or description]
- **Accessibility method:** [CSV download / API / web form / other]
- **Reproducibility:** [can historical records be re-obtained reliably?]
- **Quality findings:** [notable issues observed]
- **Selection / rejection rationale:** [why selected or rejected]
- **Status:** [Under investigation / Selected / Rejected / Pending review]
```

---

## Entries

### RES-001: AGMARKNET via OGD Platform (data.gov.in)
- **Date accessed:** 2026-10-19 (initial investigation); sample retrieved 2026-10-20
- **URL:** https://data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070
- **Source type:** Official government — Ministry of Agriculture and Farmers Welfare, NIC
- **Data owner:** Government of India
- **License / Terms of use:** Government Open Data License – India (GODL-India). Free for research use with attribution. API key required (free registration at https://data.gov.in/apis).
- **Date range:** ~March 2000 – present. Sample retrieved on 20/10/2026.
- **Record count:** Not independently calculated for the full historical dataset — API returns paginated results; total count requires iterating all pages. Single-day sample retrieved: 369 rows for Onion (incl. Onion Green), 299 rows for Potato (incl. Sweet Potato).

**Confirmed schema (directly observed from retrieved CSV samples):**

| Column        | Type   | Notes                                         |
|---------------|--------|-----------------------------------------------|
| state         | string | State name                                    |
| district      | string | District name                                 |
| market        | string | Market/mandi name                             |
| commodity     | string | Commodity name ("Onion", "Onion Green", "Potato", "Sweet Potato") |
| variety       | string | Variety name (e.g., "Bellary", "Nasik", "Red Nanital", "Other", "FAQ") |
| grade         | string | Grade (e.g., "FAQ", "Local", "Grade A", "Medium") |
| arrival_date  | string | Date in DD/MM/YYYY format                     |
| min_price     | string | Minimum price (INR/quintal)                   |
| max_price     | string | Maximum price (INR/quintal)                   |
| modal_price   | string | Modal price (INR/quintal)                     |

**CRITICAL FINDING — No arrivals column:** The resource `9ef84268-d588-465a-a308-a864a43d0070` does NOT contain a market arrivals (volume) field. The schema is price-only. This differs from the AGMARKNET portal schema (`Arrivals (Tonnes)` is present in the portal's downloadable/scrapable format but is absent from this OGD API resource.

**Sample data-quality statistics (independently calculated from 20/10/2026 sample):**

Onion sample (369 rows, single date 20/10/2026):
- Commodity values: "Onion" (213 rows), "Onion Green" (156 rows)
- Distinct states: 18 (Andhra Pradesh, Assam, Bihar, Chandigarh, Gujarat, Haryana, Himachal Pradesh, Keralam, Madhya Pradesh, Maharashtra, Punjab, Rajasthan, Tamil Nadu, Telangana, Tripura, Uttar Pradesh, Uttarakhand, West Bengal)
- Distinct state+market combinations: 222
- Null/empty modal_price: 0
- Suspicious modal_price (value = 0.01): 1 (Punjab/Tarntaran/Patti APMC, commodity=Onion, variety=Other, grade=Non-FAQ — probable data-entry placeholder)
- Exact duplicates (same state+district+market+commodity+variety+date): 0
- Conflicting duplicates (same natural key, differing prices): 0
- Onion (excl. Onion Green) modal_price range: 1,800 – 7,500 INR/quintal

Potato sample (299 rows, single date 20/10/2026):
- Commodity values: "Potato" (230 rows), "Sweet Potato" (69 rows)
- Distinct states: 17
- Distinct state+market combinations: 236
- Null/empty modal_price: 0
- Suspicious modal_price (value = 0.01): 1 (Punjab/Tarntaran/Patti APMC, commodity=Potato, variety=Potato, grade=Local — same market as Onion anomaly, probable placeholder row)
- Exact duplicates: 0
- Conflicting duplicates: 0
- Potato modal_price range: 350 – 7,600 INR/quintal

**Single-date sample limitation:** These statistics are from a single date (20/10/2026). They confirm the schema, commodity presence, geographic breadth, and absence of nulls/duplicates on that date. They cannot be used to assess historical coverage, multi-year reporting continuity, date gaps, or year-on-year completeness. A multi-date historical query is required for those assessments.

**Schema discrepancy with prior assumptions:**
- The OGD resource schema has 10 columns, not the 11-column AGMARKNET portal schema. It has `grade` (not in the AGMARKNET portal schema) and lacks `Arrivals (Tonnes)` and `Group`.
- The `arrival_date` field name is different from the portal's `Reported Date`.
- The commodity column contains both "Onion" and "Onion Green" as separate entries — filtering is required.

**Access and reproducibility:**
- API key required (free account at data.gov.in). Confirmed: unauthenticated requests return `{"error": "Key not authorised"}`.
- Historical queries require date-range filtering via API parameters. Single-date sample only retrieved in this investigation.
- The `datagovindia` Python library (`pip install datagovindia`) provides a programmatic interface.
- Known publication lag: 2–7 days from APMC trade dates.
- Mandi Price API (mandi-api.vercel.app) noted data.gov.in had not published prices newer than 24 Sept 2026 as of late October 2026 — intermittent publication gaps are a confirmed issue.

- **Quality findings summary:** No nulls, no duplicates in single-day sample. One suspicious 0.01 placeholder value (Punjab/Patti APMC, consistent across Onion and Potato). Commodity column mixes target commodity with related varieties (Onion Green, Sweet Potato) — must filter. No arrivals field in this OGD resource.
- **Selection / rejection rationale:** Retained as primary source for price data. Arrival data must be sought from an alternative source (AGMARKNET portal direct access, NHRDF, or documented as unavailable).
- **Status:** Selected (primary, price data only) — arrival data gap documented; historical range requires further API sampling

---

### RES-002: AGMARKNET Archived Dataset (iancovert/Agmarknet, GitHub)
- **Date accessed:** 2026-10-19 (initial); GitHub API directory inspection completed 2026-10-19
- **URL:** https://github.com/iancovert/Agmarknet (note: correct user is `iancovert`, not `icc2115`)
- **Source type:** Secondary archive of government data (originally from AGMARKNET/DMI)
- **Data owner:** Archive by Ian Covert; underlying data from Government of India (GODL-India applies)
- **License / Terms of use:** No explicit repository license file present (verified by inspection). Underlying data: GODL-India. Redistribution of bulk files not recommended.
- **Date range:** 2008 – June 2017 (~9.5 years). Stated in README.
- **Record count:** ~4,000,000 across 12 food products (stated in README)

**Complete commodity list (definitively confirmed by GitHub API directory listing of repository root — 2026-10-19):**

The GitHub Contents API (`https://api.github.com/repos/iancovert/Agmarknet/contents/`) returned the following 12 top-level commodity directories plus a README:
1. Arhar (Tur-Red Gram)
2. Black Gram (Urd Beans)
3. Cowpea (Lobia-Karamani)
4. Green Gram (Moong)
5. Green Peas
6. Kabuli Chana (Chickpeas-White)
7. Lentil (Masur)
8. Maize
9. Rice
10. Soyabean
11. Wheat
12. White Peas

**FINDING: Onion is NOT present. Potato is NOT present.** The archive covers exclusively pulses, legumes, and grains. The earlier HTTP 404 results for `/Onion` and `/Potato` are confirmed to be correct — no such directories exist and no such commodity data was collected by the archive creator.

- **Markets covered:** Subset of AGMARKNET (collected 2008–2017); exact count not documented in README
- **Price fields available:** Min Price (Rs./Quintal), Max Price (Rs./Quintal), Modal Price (Rs./Quintal)
- **Units and currency:** INR per quintal
- **Arrival / supply data:** Yes — `Arrivals (Tonnes)` field stated in README
- **Schema summary (from README):** State Name, District Name, Market Name, Commodity, Variety, Group, Arrivals (Tonnes), Min Price (Rs./Quintal), Max Price (Rs./Quintal), Modal Price (Rs./Quintal), Reported Date
- **Missing values:** Not calculated.
- **Duplicate records:** Not calculated.
- **Accessibility method:** Direct GitHub repository access. CSV files organised per-crop per-year. No API key required.
- **Reproducibility:** Static archive. Not updated since June 2017.
- **Quality findings:** (a) Onion and Potato are definitively ABSENT from this archive — confirmed by complete directory listing. (b) Archive covers exclusively pulses, legumes, and grains. (c) Frozen at June 2017. (d) No explicit license for the archive; GODL-India applies to underlying data.
- **Selection / rejection rationale:** **REJECTED for CropCast primary or supplementary use.** Onion and Potato are not present in the archive. This source has no value for the CropCast commodity scope. No further investigation needed.
- **Status:** ❌ REJECTED — Onion and Potato definitively absent from the archive (confirmed by GitHub API directory inspection 2026-10-19)

---

### RES-003: Department of Consumer Affairs / FCA Price Monitoring System
- **Date accessed:** 2026-10-19
- **URL:** https://fcainfoweb.nic.in/reports/report_menu_web.aspx
- **Source type:** Official government — Price Monitoring Division, Dept of Consumer Affairs
- **Data owner:** Government of India
- **License / Terms of use:** Not explicitly confirmed as open data. Publicly accessible for informational use. Bulk research download terms unconfirmed.
- **Date range:** Unknown — requires manual access to determine historical depth
- **Record count:** Not determined
- **Commodities covered:** 22 essential commodities including Onion and Potato (confirmed)
- **Markets covered:** 555–579 city-level price monitoring centres (not mandi-level)
- **Price fields available:** Retail prices and wholesale indicator prices — not mandi-level Modal_Price
- **Units and currency:** INR per unit (exact units require access)
- **Arrival / supply data:** Not available
- **Schema summary:** Not confirmed — CAPTCHA prevents automated schema inspection
- **Missing values:** Not calculated
- **Duplicate records:** Not calculated
- **Accessibility method:** Web form with CAPTCHA. Manual access only.
- **Reproducibility:** Not reproducible programmatically (CAPTCHA barrier).
- **Quality findings:** City-level retail/wholesale indicator prices — methodologically distinct from mandi-level data. No arrival data. CAPTCHA prevents bulk programmatic access.
- **Selection / rejection rationale:** Rejected as primary source. Price category (retail/city-level) is methodologically distinct from mandi wholesale Modal_Price. No arrival data. CAPTCHA prevents reproducible access. May be used as supplementary retail price reference if manually accessed.
- **Status:** Rejected (primary use) — may serve as supplementary retail reference only

---

### RES-004: ICTD-IITD Commodity_Analysis (IIT Delhi)
- **Date accessed:** 2026-10-19 (initial); direct repository inspection 2026-10-19
- **URL:** https://github.com/ICTD-IITD/Commodity_Analysis
- **Source type:** Research dataset — ICT for Development Lab, IIT Delhi
- **Data owner:** IIT Delhi (data derived from AGMARKNET and DoCA FCA)
- **License / Terms of use:** No explicit open-data license on repository (confirmed by inspection). Code available for reference. Data redistribution terms unconfirmed. Must not be used as a redistribution source.
- **Date range:** ~2011 – 2021 (from research paper; scripts reference 2011–2021 forecasting range)
- **Record count:** Not specified
- **Commodities covered (directly observed):** Onion ✓, Potato ✓, Tomato, Rice, Mustard Oil, Moong Dal, Masur Dal — confirmed by browsing `Data/Original/` directory tree
- **Markets covered (directly observed):**
  - Onion: Karnataka (Bangalore, Belgaum, Davangere, Hubli/Amaragol), Maharashtra (Lasalgaon), NCT of Delhi (Azadpur), Uttar Pradesh (multiple: Auraiya, Azamgarh, Bahraich, Barabanki, Basti, Fatehpur, Gazipur, Gonda, Jalaun, Kannauj, Kanpur, Lakhimpur, Lucknow, Mirzapur, Pukhrayan)
  - Potato: Gujarat, Himachal Pradesh, Madhya Pradesh, NCT of Delhi, Punjab, Uttar Pradesh, West Bengal — confirmed by browsing `Data/Original/Potato/` directory tree
- **Price fields available:** Wholesale mandi prices (Modal_Price, from AGMARKNET), retail city prices (from DoCA FCA) — both processed
- **Units and currency:** INR per quintal (wholesale); units for retail unconfirmed
- **Arrival / supply data:** Yes — arrival volumes included; confirmed by `Arrival.csv` files in NormalOrAnomalous/Combined
- **Schema summary:** Processed/renamed version of AGMARKNET schema. Pre-processing includes Stineman interpolation for missing values.

**Anomaly label structure (directly observed from `Data/PlottingData/ONION/NormalOrAnomalous/Combined/ShowAnomaliesPrice.csv`):**

The label file was directly fetched. The schema is:
```
STARTDATE, ENDDATE, lastMonth, lastYear, SameMonth, MAXMINRATIO, STATENAME, MANDINAME
```
Each row represents a time window for a specific mandi. The `lastMonth`, `lastYear`, and `SameMonth` columns carry either `"Anomaly"` or `"Normal"` (or blank). The `MAXMINRATIO` is a numeric price ratio used as a supplementary signal.

Sample records directly observed (partial):
```
2016-01-01,2016-02-13,,,Anomaly,1.99,KARNATAKA,BANGALORE
2016-01-01,2016-02-13,,,Anomaly,1.76,UTTAR PRADESH,JALAUN
2016-02-15,2016-03-29,Anomaly,,Anomaly,4.21,KARNATAKA,DAVANGERE
2017-07-23,2017-09-04,Anomaly,Normal,Normal,3.37,UTTAR PRADESH,GAZIPUR
```

**Anomaly labelling methodology (inferred from observed schema and published paper):**
Labels are derived algorithmically from three rule-based comparisons:
- `SameMonth`: price in the current window compared to the same month across other mandis
- `lastMonth`: price compared to previous month's values in peer mandis
- `lastYear`: price compared to same period in the prior year

These are **rule-based algorithmic flags**, not independently human-verified ground-truth labels. The `MAXMINRATIO` provides a price volatility measure. A `Combined` label exists but requires further inspection to understand how the three signals are merged.

**Critical assessment of label quality:**
- Labels are derived from the same AGMARKNET price data — they are **endogenous labels** (derived from the data being modelled, not from an independent external source such as news events or regulatory reports).
- The associated news feed provides some external corroboration, but the news-to-anomaly linkage is also algorithmically generated.
- These labels define anomalies as statistically unusual price windows relative to peer mandis and prior periods — this is closer to a statistical anomaly flag than a verified ground-truth event label.
- Per the ICTD-IITD published paper (COMPASS 2019), the research explicitly covers onion and potato forecasting and anomaly detection. The paper's stated motivation includes identifying "hoarding of stock by traders" — a causal claim beyond what the labels themselves can prove.
- Coverage for onion labels: windows from 2016 through at least 2019 observed in the sample. Full date range requires complete file inspection.

**Compatibility with CropCast:**
- The onion markets in ICTD-IITD (Lasalgaon/Maharashtra, Bangalore/Karnataka, Azadpur/Delhi, multiple UP markets) overlap directly with major AGMARKNET-reporting mandis, so temporal alignment with S-1 primary data is feasible.
- Labels are at the window level (STARTDATE–ENDDATE per mandi), not at the daily record level — alignment with daily Modal_Price records requires a join on mandi name and date range.
- The labelling methodology is transparent and documented (three rule-based criteria), which is a strength for academic use — limitations can be stated explicitly.

- **Missing values:** Pre-imputed using Stineman interpolation. Original missing-value statistics not preserved separately.
- **Duplicate records:** Not documented.
- **Accessibility method:** GitHub repository — data files available via raw URLs and Git LFS (confirmed: ShowAnomaliesPrice.csv is stored in Git LFS — a Git LFS pointer was returned alongside the actual content in a merge-conflict format in the raw file, indicating the repository has both LFS and non-LFS versions of some files).
- **Reproducibility:** Partial — processed derivative, original raw data not re-creatable from this repository alone.
- **Quality findings:**
  - Onion and Potato both confirmed present with per-state market directories.
  - Anomaly labels are algorithmic (rule-based), not independently human-verified ground truth.
  - Labels are at window granularity, requiring date-range join with daily AGMARKNET records.
  - Git LFS is used for some data files — full download requires Git LFS support.
  - No explicit open-data license; research use is consistent with academic norms but redistribution is not confirmed.
- **Selection / rejection rationale:** Confirmed as a valid research reference for anomaly label methodology. Not suitable as primary price data source. Suitable for: (a) comparing CropCast anomaly detection approach against ICTD-IITD methodology, (b) using the window-level labels as weak supervision signals with clearly documented limitations, (c) aligning specific mandi-period labels with S-1 primary data for evaluation — subject to documented methodology caveats.

**Potato anomaly label inspection (direct GitHub raw URL fetch — 2026-10-19):**

File: `Data/PlottingData/POTATO/NormalOrAnomalous/Combined/ShowAnomaliesPrice.csv`

Confirmed schema: `STARTDATE, ENDDATE, lastMonth, lastYear, SameMonth, MAXMINRATIO, STATENAME, MANDINAME`

The file is stored under Git LFS (a merge-conflict format header was present alongside the actual content: `<<<<<<< HEAD` / LFS pointer / `=======` / actual CSV data). The CSV content was retrievable directly despite the LFS pointer ambiguity.

Earliest observed STARTDATE in potato labels: **2016-01-01**
Latest visible label in truncated content: window starting 2017-05 (file continues beyond this — full date range to 2021 is inferred from the paper's stated 2011–2021 scope, but requires full download to confirm precisely).

Markets confirmed in potato anomaly labels (from direct observation):
- Punjab: Zira, Malerkotla, Sangrur, Ajnala, Barnala
- West Bengal: Uluberia, Sheoraphuly, Katwa, Kalyani, Durgapur, Bishnupur (Bankura), Islampur
- Uttar Pradesh: Basti, Faizabad, Lucknow, Lakhimpur
- NCT of Delhi: Azadpur

States in `Data/Original/Potato/` (confirmed by GitHub Contents API):
1. Gujarat
2. Himachal Pradesh
3. Madhya Pradesh
4. NCT of Delhi
5. Punjab
6. Uttar Pradesh
7. West Bengal

Onion anomaly label date range (direct observation from file):
- Earliest STARTDATE: **2016-01-01** (confirmed — first row: Karnataka/Bangalore and Uttar Pradesh/Jalaun)
- Latest observed in truncated content: 2017-11-xx (file continues beyond this)
- Full range: 2016–2021 (inferred from paper scope; requires full file download to confirm last date)

Note: Both onion and potato label files appear to START at 2016-01-01, not at 2011 as implied by the paper's stated scope. The paper's 2011–2021 range may refer to the price training data, not the anomaly label coverage. This discrepancy requires confirmation.

- **Outstanding verification task:** Completed on 2026-10-23. Full label files recovered, conflict markers audited, and complete statistics calculated.
- **Status:** Confirmed as research reference for anomaly methodology — weak-supervision algorithmic labels; full date range (2016-01-01 to 2022-01-03) and bit-level provenance definitively confirmed.

**Definitive Label Validation Findings (audited 2026-10-23):**
- **Conflict Marker Analysis:** Raw files downloaded from `raw.githubusercontent.com` contain Git merge conflict markers (`<<<<<<< HEAD`, `=======`, `>>>>>>> 6ac9248b3ef33a88bcb4b748e11d3743f40f9979`). Upstream git history shows an author checked in an unresolved merge conflict on 2022-01-23 between an LFS pointer block and raw CSV text from commit `6ac9248b3e`.
- **Bit-level Provenance Verification:**
  - Onion: LFS pointer declared `oid sha256:fa424b7466a41fa1372650f1025fb99353cb61d93a6356a8e6852aaf7bc936fe` and `size 30460`. The extracted CSV section is exactly 30,460 bytes and produces the identical SHA256 hash.
  - Potato: LFS pointer declared `oid sha256:ecad6c98a80619fb96c1fe16d28d12d42920ed76e730aee8f50701f27d2941dd` and `size 41732`. The extracted CSV section is exactly 41,732 bytes and produces the identical SHA256 hash.
  - The extracted data is 100% complete, uncorrupted, and matches the authoritative Git LFS object.
- **Onion Labels (`reports/ictd_onion_labels.csv`):**
  - Total data rows: 360 (excluding header).
  - Schema: `STARTDATE, ENDDATE, lastMonth, lastYear, SameMonth, MAXMINRATIO, STATENAME, MANDINAME`
  - STARTDATE range: 2016-01-01 to 2021-11-21; ENDDATE range: 2016-02-13 to 2022-01-03 (43–44 day sliding windows).
  - Missing fields: `lastMonth` 6 (1.7%), `lastYear` 32 (8.9%), all others 0.
  - Exact duplicates: 0; Natural key duplicates: 0.
  - Markets: 18 mandis in 4 states (Karnataka: 4, Maharashtra: 1 [Lasalgaon], NCT of Delhi: 1 [Azadpur], Uttar Pradesh: 12).
  - Label counts: `lastMonth` (122 Anomaly, 232 Normal); `lastYear` (172 Anomaly, 156 Normal); `SameMonth` (148 Anomaly, 212 Normal).
  - Anomaly rows: 360/360 (100% — source file is an anomaly-filtered view).
- **Potato Labels (`reports/ictd_potato_labels.csv`):**
  - Total data rows: 512 (excluding header).
  - Schema: identical to Onion.
  - STARTDATE range: 2016-01-01 to 2021-11-21; ENDDATE range: 2016-02-13 to 2022-01-03.
  - Missing fields: `lastMonth` 7 (1.4%), `lastYear` 75 (14.6%), all others 0.
  - Exact duplicates: 0; Natural key duplicates: 0.
  - Markets: 17 mandis in 4 states (NCT of Delhi: 1 [Azadpur], Punjab: 5, Uttar Pradesh: 4, West Bengal: 7).
  - Label counts: `lastMonth` (250 Anomaly, 255 Normal); `lastYear` (297 Anomaly, 140 Normal); `SameMonth` (165 Anomaly, 347 Normal).
  - Anomaly rows: 512/512 (100% — source file is an anomaly-filtered view).
- **Crucial Methodological Distinction:** These label files must NOT be treated as price observations (they are sliding-window event tags) and must NOT be treated as independent ground truth (they are heuristic algorithmic rules derived from AGMARKNET prices).

---

### RES-005: NHRDF Market Arrivals and Price Database
- **Date accessed:** 2026-10-19
- **URL:** http://nhrdf.org/en-us/DatabaseReports
- **Source type:** Official / government-affiliated research foundation
- **Data owner:** National Horticultural Research & Development Foundation (NHRDF), Nashik
- **License / Terms of use:** Not confirmed. Government-affiliated; likely government data terms apply.
- **Date range:** ~1996 – present (reported)
- **Record count:** Not determined
- **Commodities covered:** Onion, Potato, Garlic (NHRDF mandate crops)
- **Markets covered:** Major onion/potato producing markets — likely Maharashtra-focused but broader coverage unconfirmed
- **Price fields available:** Unconfirmed — requires form access. Prior research confirms price and arrival data are available.
- **Units and currency:** Unconfirmed
- **Arrival / supply data:** Yes — arrivals are a core feature
- **Schema summary:** Not confirmed — web form output only
- **Missing values:** Not calculated
- **Duplicate records:** Not calculated
- **Accessibility method:** Web form. No API. Bulk download reproducibility uncertain.
- **Reproducibility:** Uncertain. Manual web form submissions required.
- **Quality findings:** Potentially valuable for onion-specific arrival data going back to 1996. Access constraints reduce reproducibility. Requires direct form access to verify schema and coverage.
- **Selection / rejection rationale:** Not selected as primary source due to reproducibility uncertainty. Should be revisited if AGMARKNET arrival data is incomplete for key onion-producing markets.
- **Status:** Under investigation — revisit if AGMARKNET arrival data proves insufficient

---

### RES-006: CEDA Agri-Market Data Portal (Ashoka University)
- **Date accessed:** 2026-10-23
- **URL:**
  - Base URL: https://api.ceda.ashoka.edu.in/v1
  - Documentation: https://api.ceda.ashoka.edu.in/documentation/
  - Portal: https://ceda.ashoka.edu.in/
- **Source type:** Academic Research Data Portal — Centre for Economic Data and Analysis (CEDA), Ashoka University
- **Data owner:** CEDA, Ashoka University; underlying data sourced from AGMARKNET / Ministry of Agriculture and Farmers Welfare, Government of India
- **License / Terms of use:** Free for non-commercial research, academic analysis, and application development. Mandatory citation required: *"CEDA Agri Market Data (CEDA-AMD), Centre for Economic Data & Analysis, Ashoka University"*. Underlying government data governed by GODL-India.
- **Date range:** Stated as 2000 – present in platform documentation and OpenAPI query examples (~25 years). Actual date boundaries and continuity for Onion and Potato specifically remain to be confirmed via live authenticated sampling.
- **Record count:** Stated platform scope covers 300+ commodities across 2,700+ mandis. Specific record counts and reporting regularity for Onion and Potato to be calculated from authenticated query results.
- **Commodities covered:** Onion (Commodity ID: 23), Potato (Commodity ID: 24), and 300+ other agricultural commodities.
- **Markets covered:** 2,700+ regulated APMC mandis mapped to Census of India state and district codes (platform-wide).
- **Price fields available:**
  - `POST /agmarknet/prices` returns `date`, `commodity_id`, `census_state_id`, `census_district_id`, `market_id`, `min_price`, `max_price`, `modal_price`.
- **Units and currency:** INR per quintal (prices); dates in YYYY-MM-DD.
- **Arrival / supply data:** **YES (Confirmed).**
  - Dedicated endpoint `POST /agmarknet/quantities` returns `date`, `commodity_id`, `census_state_id`, `census_district_id`, `market_id`, `quantity`.
  - Units: Tonnes.
  - Shares exact composite key with price endpoint, enabling straightforward deterministic joining.
- **Schema summary:** Clean normalized JSON schema adhering to OpenAPI 3.0 specification.
- **Missing values / Duplicates:** Normalized and harmonized by CEDA from AGMARKNET raw feeds; census boundary mapping applied.
- **Accessibility method:** REST API with Bearer token authentication (`Authorization: Bearer <token>`). Free registration via web form (`https://api.ceda.ashoka.edu.in/`) using email + OTP verification.
- **Reproducibility:** Highly reproducible via standardized REST API endpoints.
- **Quality findings (Authenticated Live Audit 2026-10-23):**
  - **Response Envelope:** CEDA `/v1` endpoints wrap all successful responses in an outer container: `{"output": {"type": "success", "message": "Data exists", "data": [...]}}`. Applications must unpack `response["output"]["data"]`.
  - **Commodity Verification:** `GET /agmarknet/commodities` returned 453 commodities. Target IDs definitively confirmed:
    - Onion: `commodity_id = 23`
    - Potato: `commodity_id = 24`
    - Onion Green: `commodity_id = 358`
    - Sweet Potato: `commodity_id = 152`
  - **Geography Verification:** `GET /agmarknet/geographies` returned 640 districts across 36 states/UTs mapped to official Census codes.
  - **Live Price Sampling (2021-01-01 to 2021-01-15):**
    - Onion (Maharashtra, `state_id: 27`): 13 daily price records retrieved.
    - Potato (Uttar Pradesh, `state_id: 9`): 15 daily price records retrieved.
    - Fields: `date` (ISO-8601 string, e.g., `'2021-01-01T00:00:00.000Z'`), `commodity_id`, `census_state_id`, `min_price`, `max_price`, `modal_price` (INR/quintal).
  - **Live Arrival Quantity Sampling (2021-01-01 to 2021-01-15):**
    - Onion (Maharashtra, `state_id: 27`): 13 daily arrival records retrieved.
    - Potato (Uttar Pradesh, `state_id: 9`): 15 daily arrival records retrieved.
    - Fields: `date`, `commodity_id`, `census_state_id`, `quantity` (Tonnes).
  - **Price vs. Arrival Alignment:**
    - Onion: 13 / 13 trading days matched (100.0% date alignment).
    - Potato: 15 / 15 trading days matched (100.0% date alignment).
  - **Audit Sample Files Saved:**
    - `reports/ceda_onion_price_sample.json` (13 records)
    - `reports/ceda_onion_quantity_sample.json` (13 records)
    - `reports/ceda_potato_price_sample.json` (15 records)
    - `reports/ceda_potato_quantity_sample.json` (15 records)
  - **Remaining Uncertainties:**
    - Unfiltered district/market queries (e.g. querying a district without market IDs) can experience backend join latency or timeouts on CEDA's database; queries should be executed per state or with explicit market IDs.
    - Long multi-year historical spans must be queried via bounded date chunks to prevent timeout.
- **Selection / rejection rationale:** **Selected as Primary Candidate Source.** Confirmed live retrieval of both wholesale prices and market arrival volumes with 100% temporal alignment.
- **Status:** Candidate Primary Source — Authenticated live sampling verified; full historical range ingestion pending researcher approval.

---

### RES-007: `agmarknet` PyPI Package & AGMARKNET Portal REST API
- **Date accessed:** 2026-10-23
- **URL:**
  - PyPI: https://pypi.org/project/agmarknet/
  - Portal REST API Base: https://api.agmarknet.gov.in/v1
  - Live Filters Endpoint: https://api.agmarknet.gov.in/v1/daily-price-arrival/filters
  - Live Report Endpoint: https://api.agmarknet.gov.in/v1/daily-price-arrival/report
- **Source type:** Unofficial third-party Python wrapper around internal government web portal API.
- **Data owner:** Package by Manojkumar Patil (MIT license); underlying portal managed by DMI / NIC.
- **License / Terms of use:** Package is MIT licensed. The underlying endpoint is the internal API for `agmarknet.gov.in`.
- **Date range:** **2021-01-01 to present only.**
  - Direct live query to `/v1/daily-price-arrival/filters` returned server-enforced `range_data`: `from_date: 2021-01-01`, `to_date: 2026-10-22` (current day).
  - **The API does NOT contain historical records prior to 2021.**
- **Record count:** 4,178 mandis and 604 commodities declared in filter metadata.
- **Commodities covered:** Onion (ID 23), Potato (ID 24), Onion Green (ID 305), Sweet Potato (ID 124).
- **Price and Arrival fields:** Stated schema includes `min_price`, `max_price`, `model_price`, `arrival_qty`.
- **Accessibility method:** Reverse-engineered HTTP POST requests with spoofed browser headers.
- **Fatal Quality / Operational Blockers (Confirmed by Source Code & Live Network Tests):**
  1. **CAPTCHA Barrier:** Live POST requests to `/daily-price-arrival/report` fail with `HTTP 400 Bad Request: {"detail":"Captcha key and captcha value are required.","code":"TOKEN_OR_CAPTCHA_REQUIRED"}`.
  2. **Zero CAPTCHA Logic:** Inspection of package source code (`session.py`, `client.py`, `models.py`) reveals no token generation or CAPTCHA solving functionality. The package cannot execute downloads against the current live portal.
  3. **Broken Project Metadata:** The declared project repository `https://github.com/agmarknet/agmarknet` returns `HTTP 404 Not Found`.
  4. **Insufficient Historical Depth:** Restricted to $\le 5$ years (2021–present); cannot provide long-term training baselines.
- **Selection / rejection rationale:** **REJECTED.** Unofficial, unmaintained wrapper blocked by live portal CAPTCHA protection and restricted to post-2021 records.
- **Status:** ❌ REJECTED — Blocked by CAPTCHA and truncated historical coverage (≥2021 only).

---

### RES-008: CEDA Audit Review, Granularity Verification, and Operational Constraints
- **Date accessed:** 2026-10-23
- **Audited files:**
  - `reports/_ceda_audit.py`
  - `reports/ceda_onion_price_sample.json` (13 records)
  - `reports/ceda_onion_quantity_sample.json` (13 records)
  - `reports/ceda_potato_price_sample.json` (15 records)
  - `reports/ceda_potato_quantity_sample.json` (15 records)
- **Granularity Verification (Task 1 & 2):**
  - **Result:** The four saved JSON samples contain **state-level daily aggregates**, NOT individual market records.
  - **Schema fields present:**
    - Prices: `date` (ISO-8601), `commodity_id`, `census_state_id`, `min_price`, `max_price`, `modal_price`
    - Quantities: `date` (ISO-8601), `commodity_id`, `census_state_id`, `quantity`
    - Fields NOT present: `district_id`, `census_district_id`, `market_id`, `market_name`
  - **Reason:** In CEDA's OpenAPI specification, omitting `district_id` and `market_id` returns state-level aggregated data. Prices are arithmetic means across reporting mandis in the state (non-integer floats with up to 15 decimal places); quantity is the state-wide total arrivals in Tonnes.
- **Join Key & Alignment Recalculation (Task 2 & 3):**
  - **Strongest Common Key:** Composite key `(date, commodity_id, census_state_id)`.
  - **Duplicate keys:** 0 in all four files (all dates are unique per commodity/state).
  - **Unmatched keys:** 0 across both price and quantity sets.
  - **Alignment:** 13/13 (100.0%) for Onion in Maharashtra; 15/15 (100.0%) for Potato in UP.
  - **Interpretation:** Confirms 100% temporal synchronization at the state aggregate level. This does NOT demonstrate market-level alignment.
- **Correction of Previously Reported Sample Statistics (Task 5):**
  - An inconsistency was detected between previously drafted ranges and actual values in the saved JSON files:
    - Onion Modal Price: Actual is min 2,054.18, max 2,832.40, mean 2,328.33 INR/qtl (previously reported 1,847–2,639).
    - Onion Min Price: Actual is min 633.33, max 1,950.00 INR/qtl.
    - Onion Max Price: Actual is min 2,626.62, max 3,366.67 INR/qtl.
    - Onion Quantity: Actual is min 394.00, max 19,907.00, mean 7,705.15 Tonnes (previously reported 9,332.9–25,626.8).
    - Potato Modal Price: Actual is min 872.33, max 1,074.93, mean 987.07 INR/qtl (previously reported 887–1,073).
    - Potato Quantity: Actual is min 5,957.45, max 20,593.52, mean 17,003.59 Tonnes (previously reported 5,160.8–11,811.2).
  - Feasibility report updated with verified numbers directly calculated from local artifacts.
- **Multi-Year Sampling Across Evaluation Horizon (Task 4):**
  - Bounded 7-day January windows (Jan 1–7) tested across multiple historical years:
    - 2016: 7 price records, 7 quantity records (100% aligned, modal range 1,234.8–1,432.7 INR/qtl, qty 6,486–33,262 T).
    - 2018: 7 price records, 7 quantity records (100% aligned, modal range 2,699.2–3,031.2 INR/qtl, qty 6,355–26,260 T).
    - 2020: 7 price records, 7 quantity records (100% aligned, modal range 3,314.8–3,833.7 INR/qtl, qty 6,079–22,983 T).
    - 2022: 7 price records, 7 quantity records (100% aligned, modal range 1,706.8–1,989.0 INR/qtl, qty 2,324–35,333 T).
  - Verified that synchronized price and arrival records exist across the entire ICTD evaluation period (2016–2022).
  - However, continuous day-by-day reporting across all dates cannot be inferred without full ingestion.
- **Server Rate Limits Discovered (Operational Finding):**
  - Server headers returned: `RateLimit-Policy: 40;w=3600`, `RateLimit-Limit: 40`, `RateLimit-Remaining: 0`, `Retry-After: 1831`.
  - CEDA strictly enforces **40 requests per hour**. Exceeding this quota triggers `HTTP 429 Too Many Requests` with a 1-hour reset window.
  - Rate limit was verified live: client stopped safely upon receiving 429; wait requirement of 1,831 seconds (~30.5 minutes) recorded without circumventing the limit.
  - Any ingestion pipeline must be metered, throttle requests, and maximize date span per query.
- **Market-Level Endpoint Query Latency (Operational Finding):**
  - `POST /agmarknet/markets` on Ludhiana (district 41, Punjab) returned market records in 0.69 seconds.
  - `POST /agmarknet/markets` on Nashik (district 516, Maharashtra) timed out (>30 seconds) on CEDA's database.
  - Market discovery for high-volume production districts cannot be queried on-the-fly without static market ID mappings or longer timeouts.
- **Academic Licensing & Attribution Terms (Task 4):**
  - Free for non-commercial academic research.
  - Mandatory citation: *"CEDA Agri Market Data (CEDA-AMD), [date range]. Centre for Economic Data & Analysis, Ashoka University"*.
  - Visualizations must display the CEDA logo and credit text.
  - **Redistribution Restriction Flagged:** CEDA terms grant non-commercial usage but do not explicitly grant public redistribution rights for raw data files. Committing raw CEDA sample datasets to a public repository is flagged as an unresolved legal/licensing question. Project governance rule (DEC-008, Req 10 AC 2) applies: raw bulk datasets must not be committed to Git; ingestion must be pipeline-driven.
- **Decision Taken:** DEC-015 approved by researcher (Option A: State-Level Daily Aggregate Forecasting on CEDA Ashoka).
- **Status:** Primary Research Source Approved — State-aggregate sample verified; Milestone M-1 closed; Milestone M-2 initialized.

---

### RES-009: CEDA Ashoka Ingestion Pipeline Implementation and Bounded Pilot Results
- **Date accessed / implemented:** 2026-10-23
- **Pipeline module:** `src/data/ingest_ceda.py`
- **Unit test suite:** `tests/test_ingest_ceda.py` (13 automated tests passing)
- **Manifest and summary artifacts:** `data/raw/ceda_manifest.json`, `data/raw/pilot_validation_summary.json` (git-ignored)
- **Pipeline Architecture and Technical Guarantees:**
  1. **Authentication:** Safe environment-based authentication via `CEDA_API_KEY` in `os.environ` or local `.env` (git-ignored). Zero credential logging or exposure in stdout, stderr, or manifest files.
  2. **Rate Limit Compliance:** Enforces $\le 40$ requests/hour policy (`MIN_REQUEST_INTERVAL_SECONDS = 90.0` conservative inter-request spacing). Explicitly inspects `HTTPError 429` responses for `Retry-After` and `RateLimit-Reset` headers; implements bounded waiting and safe quota preservation without crashing or circumventing limits.
  3. **Date Chunking & Pagination:** Splits multi-year queries into configurable calendar chunks (e.g. 1 to 6 months) to avoid server-side timeouts on large joins.
  4. **Checkpointing & Resumption:** Atomic manifest persistence at `data/raw/ceda_manifest.json`. Tracks chunk ID, endpoint, date boundaries, record counts, file paths, and SHA-256 checksums. Re-running the pipeline checks existing chunks and skips redundant API calls.
  5. **Envelope & Schema Validation:** Validates CEDA's outer response envelope (`response["output"]["data"]`). Enforces ISO-8601 date parsing, strict commodity and state ID matching, non-negative prices and quantities, logical price constraints (`min_price <= max_price`), and zero duplicate composite keys `(date, commodity_id, census_state_id)`.
  6. **Price-Arrival Key Alignment:** Computes deterministic inner-join alignment between wholesale prices and arrival quantities by `(date, commodity_id, census_state_id)`.
  7. **Repository Hygiene:** All raw JSON responses, parquet files, and manifest metadata are strictly saved under `data/raw/`, verified as excluded by `.gitignore`.
- **Bounded Pilot Results (Date Span: 2021-01-01 to 2021-01-15):**
  - **Candidate Series 1: Maharashtra Onion (`commodity_id: 23`, `census_state_id: 27`)**
    - Prices: 13 records across 13 reporting observation dates (Jan 7 and Jan 8 are absent calendar dates in the API response; the source provides no metadata explaining why these dates lack observations). Modal price: min 2,054.18, max 2,832.40, mean 2,328.33 INR/quintal. Min price: 633.33 to 1,950.00; Max price: 2,626.62 to 3,366.67 INR/quintal.
    - Quantities: 13 records. Statewide total arrivals: min 394.00, max 19,907.00, mean 7,705.15 Tonnes.
    - Data Quality: 0 duplicate composite keys, 0 null fields, 0 numeric violations, 0 schema errors (`is_valid: true`).
    - Price-Quantity Alignment: 13 / 13 (100.0% aligned). Zero price-only or quantity-only dates.
  - **Candidate Series 2: Uttar Pradesh Potato (`commodity_id: 24`, `census_state_id: 9`)**
    - Prices: 15 records across 15 consecutive calendar days (0 missing dates). Modal price: min 872.33, max 1,074.93, mean 987.07 INR/quintal.
    - Quantities: 15 records. Statewide total arrivals: min 5,957.45, max 20,593.52, mean 17,003.59 Tonnes.
    - Data Quality: 0 duplicate composite keys, 0 null fields, 0 numeric violations, 0 schema errors (`is_valid: true`).
    - Price-Quantity Alignment: 15 / 15 (100.0% aligned). Zero price-only or quantity-only dates.
- **State Aggregate Semantics Verified:**
  - Prices are confirmed to represent state arithmetic means across reporting mandis (float precision).
  - Quantities are state aggregate total arrivals in Tonnes.
  - No sub-state mandi metadata is present when omitting `district_id` and `market_id`, confirming clean state-level aggregate semantics.
- **Operational Status & Approval Gate:**
  - Pipeline design and bounded pilot validation are complete and verified.
  - Full historical extraction (2016–2022) was authorized and executed under task-775.

---

### RES-010: CEDA Ashoka Full Historical Extraction (2016–2022) and M-2 Validation Gate Findings
- **Date executed:** 2026-10-23
- **Extraction Task:** `task-775` (Command: `python -m src.data.ingest_ceda --all-approved --start-date 2016-01-01 --end-date 2022-12-31 --chunk-months 6`)
- **Historical Scope:** 2016-01-01 through 2022-12-31 (7 calendar years = 2,557 calendar days, including leap years 2016 and 2020)
- **Approved Series Evaluated:**
  1. Maharashtra Onion (`commodity_id: 23`, `census_state_id: 27`)
  2. Uttar Pradesh Potato (`commodity_id: 24`, `census_state_id: 9`)
- **Rate-Limiting & Quota Execution Audit:**
  - Total requests dispatched: 56 requests (14 six-month chunks $\times$ 2 endpoints $\times$ 2 series).
  - Rate-limit spacing: ~~90.4s to 93.5s per request~~ *(corrected in RES-011: 92.4s to 97.6s between consecutive manifest `fetched_at` timestamps).*
  - Quota compliance: ~~Maximum hourly request rate $\approx 37.89$ req/hour~~ *(corrected in RES-011: at most 38 requests in any rolling 60-minute window)*, within CEDA's 40 req/hour limit (`RateLimit-Policy: 40;w=3600`).
  - Network & API errors: **0 HTTP 429 rate limit triggers, 0 server retries, 0 connection drops, 0 API error envelopes** *(not independently verifiable: no run log was retained; see RES-011).*
  - Checkpoint integrity: All 56 raw JSON files written atomically via temporary files and cataloged in `data/raw/ceda_manifest.json`.
- **M-2 Validation Gate Audit Results:**
  - **Chunk & File Integrity:**
    - Expected historical chunks: 56 / 56 found and validated.
    - Missing local raw files: 0.
    - SHA-256 bit-level checksum mismatches: **0 mismatches** (recomputed SHA-256 matches manifest 100%).
    - JSON parsing / schema decoding failures: 0.
  - **Candidate Series 1: Maharashtra Onion (`commodity_id: 23`, `census_state_id: 27`)**
    - First observed date: `2016-01-01` | Last observed date: `2022-12-31`.
    - Price observations: 2,523 records across 2,523 unique dates.
    - Arrival observations: 2,523 records across 2,523 unique dates.
    - Duplicate composite keys `(date, commodity_id, census_state_id)`: 0.
    - Null values in required fields: 0.
    - Numeric validity: 100% non-negative; `min_price <= modal_price <= max_price` strictly satisfied for all 2,523 price records (0 violations).
    - Price distribution (INR/quintal): Min = 406.16, Max = 7,506.45, Mean = 1,388.29.
    - Quantity distribution (Tonnes): Min = 2.00, Max = 45,648.00, Mean = 16,323.07.
    - Calendar coverage: 2,523 / 2,557 calendar days (**98.67% temporal coverage**).
    - Missing observation dates: 34 calendar days (1.33%).
    - Consecutive gap structure: Exactly 13 gaps.
      - 10-day gap: 2020-10-16 to 2020-10-25 (maximum gap length).
      - 6-day gap: 2020-04-08 to 2020-04-13 (coinciding with initial national COVID-19 lockdown disruptions).
      - 3-day gaps: 2 (2017-01-20 to 2017-01-22; 2019-05-17 to 2019-05-19).
      - 2-day gaps: 3 (2016-09-04 to 2016-09-05; 2021-01-07 to 2021-01-08; 2021-03-17 to 2021-03-18).
      - 1-day isolated missing dates: 6 *(corrected from 5 in RES-011)* (2017-02-19, 2017-02-24, 2020-04-20, 2020-04-23, 2020-04-27, 2020-05-02).
    - Price–Quantity Key Alignment:
      - $|D_{\text{price}}| = 2,523$, $|D_{\text{quantity}}| = 2,523$, $|D_{\text{price}} \cap D_{\text{quantity}}| = 2,523$.
      - Intersection-over-Union (IoU): **1.000000** (100.0%).
      - Price-observation match rate: **1.000000** (100.0%).
      - Unmatched dates: 0 price-only dates, 0 quantity-only dates.
  - **Candidate Series 2: Uttar Pradesh Potato (`commodity_id: 24`, `census_state_id: 9`)**
    - First observed date: `2016-01-01` | Last observed date: `2022-12-31`.
    - Price observations: 2,557 records across 2,557 unique dates.
    - Arrival observations: 2,557 records across 2,557 unique dates.
    - Duplicate composite keys `(date, commodity_id, census_state_id)`: 0.
    - Null values in required fields: 0.
    - Numeric validity: 100% non-negative; `min_price <= max_price` strictly satisfied for all 2,557 records (0 violations).
    - Price distribution (INR/quintal): Min = 433.56, Max = 3,015.18, Mean = 1,016.85.
    - Quantity distribution (Tonnes): Min = 442.00, Max = 113,475.30, Mean = 15,363.75.
    - Calendar coverage: 2,557 / 2,557 calendar days (**100.00% complete daily coverage**).
    - Missing observation dates: 0 calendar days (0.00%).
    - Consecutive gap structure: 0 gaps. Complete continuous daily time series across 7 full years.
    - Price–Quantity Key Alignment:
      - $|D_{\text{price}}| = 2,557$, $|D_{\text{quantity}}| = 2,557$, $|D_{\text{price}} \cap D_{\text{quantity}}| = 2,557$.
      - Intersection-over-Union (IoU): **1.000000** (100.0%).
      - Price-observation match rate: **1.000000** (100.0%).
      - Unmatched dates: 0 price-only dates, 0 quantity-only dates.
    - **Empirical State-Aggregate Price Ordering Finding:**
      - In Uttar Pradesh Potato, 137 records (5.36%) exhibit an aggregated `modal_price` outside the arithmetic mean `[min_price, max_price]` (136 records have `modal_price < min_price`, 1 record has `modal_price > max_price`).
      - ~~This is mathematically explained by multi-mandi aggregation dynamics: ...volume-weighted modal price aggregation...~~ *Retracted in RES-011: this explanation is unverified, conflicts with the arithmetic-mean semantics recorded in RES-009, and does not account for the violations being confined to 2016-03-04 – 2017-04-02. Root cause is open (ISS-002).*
      - All prices remain strictly non-negative and `min_price <= max_price` is satisfied across 100% of observations.
- **Automated Test Suite & Git Hygiene Verification:**
  - `python -m unittest discover -s tests -v`: 22 / 22 tests passing in 0.056s.
  - `git diff --check`: 0 errors.
  - Git exclusion: `data/` and all raw JSON / manifest files verified as excluded by `.gitignore`. *(RES-011: the unanchored `data/` rule also excluded `src/data/`; fixed — see ISS-001.)*
- **Status:** ~~Milestone M-2 Validation Gate PASSED.~~ Superseded by RES-011: validation checks re-run and reconciled; gate sign-off pending researcher approval.

---

### RES-011: Independent Re-verification and Reconciliation of M-2 Extraction (task-775)
- **Date:** 2026-10-23
- **Purpose:** Handover reconciliation. Confirm the actual state of `task-775` and independently re-check every RES-010 claim against the raw files, without any CEDA API requests.
- **Method:** Offline read-only script (not committed; see ISS-004) that recomputes SHA-256 per chunk against `data/raw/ceda_manifest.json`, checks envelope metadata, exact record key sets, ID consistency, date format and chunk bounds, duplicates, nulls, non-numeric / non-finite / negative / zero values, `min ≤ modal ≤ max`, calendar gaps, price–quantity date alignment, pilot-chunk overlap, and request spacing from manifest `fetched_at` timestamps.
- **Extraction task state:** Completed. All 56 historical chunk files are present; manifest last updated `2026-10-22T21:59:11Z` (last chunk `potato_uttar_pradesh/quantities_2022-07-01_2022-12-31`). No Python process was running at inspection time. `historical_extraction_summary.json` was written at completion, so the run exited normally. No further API requests were made during this reconciliation.
- **Confirmed (matches RES-010):**
  - 56 / 56 historical chunks + 4 pilot chunks; every manifest entry `status: completed`, `is_valid: true`; 0 orphan files; 0 SHA-256 mismatches; 0 metadata or record-count mismatches.
  - Every record has exactly the expected key set; IDs match the series; all dates are `YYYY-MM-DDT00:00:00.000Z` and fall inside their chunk window.
  - 0 duplicate dates, 0 nulls, 0 non-numeric / non-finite values, 0 negative values, 0 zero values, 0 cases of `min_price > max_price`, 0 cases of `min_price == max_price`.
  - Onion: 2,523 price / 2,523 quantity dates, 34 missing calendar days in 13 gaps (max 10 days), IoU = 1.0; `min ≤ modal ≤ max` holds for all records.
  - Potato: 2,557 / 2,557 dates, 0 missing days, IoU = 1.0.
  - Modal-price and quantity min / max / mean match RES-010.
- **Corrections to RES-010:**
  1. Onion single-day gaps: **6**, not 5 (gap-length histogram: 1-day ×6, 2-day ×3, 3-day ×2, 6-day ×1, 10-day ×1 = 34 days).
  2. Request spacing: **92.4s – 97.6s** between consecutive `fetched_at` timestamps (these are post-response save times, not send times); peak **38 requests in any rolling 60-minute window** (< 40). The previously stated 90.4–93.5s range could not be reproduced.
  3. "0 HTTP 429 / 0 retries / 0 connection drops": **unverifiable** — no execution log was retained and the manifest does not record retries. The evidence is consistent with a clean run (uniform spacing, no gaps longer than ~98s) but does not prove it.
  4. Potato `modal_price` outside `[min_price, max_price]`: count confirmed (136 below `min_price`, 1 above `max_price`, total 137 = 5.36%), but the "volume-weighting" explanation is **retracted**. New evidence: all 136 below-min cases fall between **2016-03-04 and 2017-04-02** (110 in 2016, 26 in 2017; none from 2017-04-03 to 2022-12-31). Relative shortfall below `min_price`: median 1.46%, max 7.24%. The single above-max case is 2016-10-20 (min 1163.75, max 1265.38, modal 1302.47). The time-confined pattern suggests a source-side aggregation or reporting regime in that period rather than a general property of the data; cause unestablished (ISS-002).
  5. `.gitignore` rule `data/` silently excluded `src/data/` (the ingestion package). Fixed by anchoring to `/data/` (ISS-001).
- **New findings:**
  - Onion near-zero arrivals: quantity = 2, 3, 5 on 2020-04-28, 2020-04-25, 2020-04-24 (COVID-19 lockdown period) and 14 on 2020-10-26 (the day after the 10-day gap). Retained unchanged; to be treated in EDA as possible partial-reporting days (ISS-003).
  - Onion missing days by year: 2016: 2, 2017: 5, 2019: 3, 2020: 20, 2021: 4, 2018 and 2022: 0.
  - Pilot chunks (`*_2021-01-01_2021-01-15.json`) are stored as bare JSON lists without the `metadata` envelope used by historical chunks, and overlap the H1-2021 historical chunks. Every overlapping pilot record (onion 13 + potato 15 per endpoint, 56 in total) is field-for-field identical to the corresponding historical record. Dataset assembly must exclude pilot chunks to avoid duplicate dates (ISS-005).
  - `CedaIngestionPipeline.validate_records` does not check `min_price ≤ modal_price ≤ max_price`, so `historical_extraction_summary.json` reports 0 numeric violations for potato while `m2_validation_audit.json` reports 137. `m2_validation_audit.json` was produced by a script not present in the repository (ISS-004).
- **Tests & hygiene:** `python -m unittest discover -s tests`: 22 / 22 OK (0.064s). `git diff --check`: clean. `data/`, `.env`, `.kiro/` and restricted sample files confirmed git-ignored; `src/data/` now tracked as intended. No credentials found in untracked source files.
- **Status:** M-2 data acquisition complete and validated, with the open data-quality items above. **Awaiting researcher sign-off before M-3.**

---

### RES-012: Reproducible M-2 Validation Audit (DEC-016 Option 2)
- **Date:** 2026-10-23
- **Purpose:** Make the M-2 validation audit reproducible from committed code (ISS-004) and flag modal-bounds cases inside the pipeline validator.
- **Changes:**
  - `src/data/validate.py`: offline, read-only audit. For each approved series it checks expected chunks against the manifest, SHA-256 checksums, record counts, exact key sets, IDs, date format and chunk bounds, duplicates, nulls, non-numeric / non-finite / negative values, and `min_price > max_price` (all hard failures, exit code 1). It also checks that supplementary chunks such as the pilot agree with historical records (hard failure if not). It reports `modal_price` outside `[min_price, max_price]` as a warning, plus calendar gaps, price–quantity IoU and match rate, distribution statistics, the five smallest arrivals, and request spacing from manifest timestamps. No network access.
  - `src/data/ingest_ceda.py`: `ValidationSummary` gains `modal_bounds_warnings` and `warnings`. These never change `is_valid`, so chunks with flagged records are never re-fetched.
  - Tests: 16 new tests *(corrected from 18 in RES-013)* in `tests/test_validate.py` (synthetic fixtures only) and 2 in `tests/test_ingest_ceda.py`. A null-value test exposed a crash in the first draft of the statistics code (it computed on unvalidated values); fixed before the real-data run.
- **Real-data run:** `python -m src.data.validate --output data/raw/m2_validation_audit.json` → `passed: true`, exit 0, 56 / 56 chunks, 0 hard failures, 1 warning (`potato_uttar_pradesh: 137 records with modal_price outside [min_price, max_price]`). Pilot chunks: 0 mismatches. Request timing: 92.4–97.6s spacing, peak 38 per rolling hour.
- **Agreement with prior audit:** Every field shared with the legacy ad-hoc audit (kept locally as `data/raw/m2_validation_audit.legacy_adhoc.json`) is identical, including the 13 onion gap intervals. Every RES-011 figure is reproduced.
- **Tests & hygiene:** 40 / 40 tests pass; `git diff --check` clean. ISS-006 notes that one pre-existing test asserts nothing.
- **Status:** ISS-004 resolved. **M-2 signed off by researcher on 2026-10-23.** M-3 not started; it awaits an explicit start instruction.

---

### RES-013: Final M-2 Audit and Approved Remediation
- **Date:** 2026-10-23
- **Final audit (read-only):** Verdict PASS WITH ISSUES.
  - The acquired data was re-verified file by file: 56 / 56 historical chunks, checksums, schemas, 0 conflicting duplicates (pilot overlaps are exact), and alignment IoU = 1.0 for both series.
  - Synthetic probes showed the validators accepted empty, truncated and failed chunks (ISS-007), and the pipeline had the four defects in ISS-008. Documentation errors are listed in ISS-009.
  - GitHub was unreachable (`Could not resolve host: github.com`), so the remote state was not verified; the local ref `origin/main` = `3879282`.
- **Remediation (researcher-approved items 1–4):**
  1. `src/data/validate.py`: hard failures for manifest entries not `completed` or not `is_valid`, and for empty expected chunks. Warnings for chunks with records on < 90% of their calendar days, zero values, and values beyond 100× of the field median.
  2. `src/data/ingest_ceda.py`:
     - Empty responses get `status: "empty"`.
     - Checksum-verified chunks with source-data violations are kept rather than re-downloaded.
     - `TimeoutError` / `ConnectionError` are retried.
     - A corrupt manifest is backed up before recreation.
  3. Documentation corrections (ISS-009) and `docs/environment.md`.
  4. ISS-006 test completed.
- **Tests:**
  - Command: `python -m unittest discover -s tests`. Result: 51 run, 0 failures, 0 errors, 0 skipped.
  - New: 6 validator and 5 pipeline tests; 2 existing tests extended.
  - Against a scratch copy of the previous code, 10 of the 11 new tests and the extended corrupt-manifest test fail. The remaining new test guards kept behaviour.
- **Real-data run:** `python -m src.data.validate` (stdout only; stored `data/raw/m2_validation_audit.json` not regenerated) gives `passed: true`, exit 0, 0 hard failures. Warnings: 137 UP Potato modal-bounds records (ISS-002, unchanged) and 10 Maharashtra Onion arrival values beyond 100× of the median (ISS-003). No manifest-status, empty-chunk or low-coverage findings; the lowest historical chunk coverage is 172 / 182 days (94.5%). Every metric field also present in the stored audit is unchanged.
- **Not verified:** pushes to GitHub (network unavailable); the `task-775` run log (never retained).
- **Status:** Remediation complete and uncommitted. M-3 not started.

---

### RES-014: Literature Review, CEDA Source Documentation, and Dataset Freeze
- **Date:** 2026-10-23
- **Literature review:** `reports/literature_review.md`. 21 references, each verified against its registry record (Crossref by DOI, the JMLR page, or the OTexts pages). Published findings and CropCast hypotheses are labelled separately.
- **CEDA terms (republishing guidelines, accessed 2026-10-23):**
  - Visualisations may be reproduced with the credit "Centre for Economic Data and Analysis (CEDA), Ashoka University"; use is non-commercial.
  - **No logo requirement is stated.** The earlier claim in the feasibility report has been corrected.
  - Terms for redistributing derived data are ambiguous (CC BY-ND link vs "adapted"), so raw and processed data stay uncommitted.
- **ISS-002 source check:** CEDA's Agri Market methodology README returned HTTP 404, the API documentation page shows no methodology text, and the CEDA tool page gives no aggregation rule. The cause stays **unresolved**: no documented explanation exists for modal prices below the state minimum in 2016-03 – 2017-04.
- **ICTD-IITD labels:** the source paper is confirmed as Madaan et al. (2019), ACM COMPASS, doi:10.1145/3314344.3332488. Local label files hold 360 onion windows (25 in Maharashtra) and 512 potato windows (97 in Uttar Pradesh), dated 2016-01-01 to 2022-01-03. They are treated as weak, endogenous references (DEC-017).
- **Dataset v1:** built and frozen (DEC-019). Onion: 2,523 rows, 34 missing days (1.33%). Potato: 2,557 rows, 0 missing.
- **Status:** Phase 2 complete; prerequisites for M-3 EDA satisfied.
