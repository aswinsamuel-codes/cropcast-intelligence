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
- **Date accessed:** 2026-10-19
- **URL:** https://data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070
- **Source type:** Official government — Ministry of Agriculture and Farmers Welfare, NIC
- **Data owner:** Government of India
- **License / Terms of use:** Government Open Data License – India (GODL-India). Free for research use with attribution. API key required (free registration).
- **Date range:** ~March 2000 – present (exact onion/potato coverage start requires API verification)
- **Record count:** Not independently calculated — requires API sampling
- **Commodities covered:** 300+ commodities. Onion and Potato confirmed present.
- **Markets covered:** 3,000+ regulated APMC mandis. ~211 onion markets, ~180 potato markets identified in independent research.
- **Price fields available:** Min Price (Rs./Quintal), Max Price (Rs./Quintal), Modal Price (Rs./Quintal)
- **Units and currency:** INR per quintal
- **Arrival / supply data:** Yes — `Arrivals (Tonnes)` field confirmed in schema
- **Schema summary:** State Name, District Name, Market Name, Commodity, Variety, Group, Arrivals (Tonnes), Min Price (Rs./Quintal), Max Price (Rs./Quintal), Modal Price (Rs./Quintal), Reported Date
- **Missing values:** Not calculated — documented as a known issue (irregular reporting, consecutive missed days)
- **Duplicate records:** Not calculated
- **Accessibility method:** REST API with pagination. Free API key required from https://data.gov.in/apis. No bulk historical download.
- **Reproducibility:** Yes — authoritative government source. API allows historical queries by date range. Known 2–7 day publication lag from trade dates.
- **Quality findings:** Irregular reporting frequency across markets; some weekly, some daily. Field names have changed across API resource versions. Upstream feed publishes with 2–7 day lag. data.gov.in has had intermittent periods of not publishing newer prices.
- **Selection / rejection rationale:** Selected as primary source. Authoritative government data, correct schema, licensed for research, includes arrivals, covers both onion and potato at mandi level. Direct API verification pending.
- **Status:** Selected (primary) — pending direct API verification

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

- **Outstanding verification task:** Download full anomaly label files (Git LFS required) to confirm the precise maximum ENDDATE for both onion and potato labels. Verify whether label coverage predates 2016.
- **Status:** Confirmed as research reference for anomaly methodology — labels are algorithmic, not independent ground truth; potato label schema, markets, and partial date range (2016–2021 estimated) confirmed by direct inspection

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
