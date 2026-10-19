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
- **Date accessed:** 2026-10-19 (initial); direct file tree inspection 2026-10-19
- **URL:** https://github.com/icc2115/Agmarknet
- **Source type:** Secondary archive of government data (originally from AGMARKNET/DMI)
- **Data owner:** Archive by Ian Covert; underlying data from Government of India (GODL-India applies)
- **License / Terms of use:** No explicit repository license file present (verified by inspection). Underlying data: GODL-India. Redistribution of bulk files not recommended — document retrieval procedure only.
- **Date range:** 2008 – June 2017 (~9.5 years). Stated in README; not independently verified by row-level inspection.
- **Record count:** ~4,000,000 across 12 food products (stated in README)
- **Commodities covered:** 12 food products. README does not list them explicitly. Direct file tree navigation via GitHub returned HTTP 404 for `/Potato` and `/Onion` subdirectory paths, indicating those directories do not exist at the repository root. **Onion and Potato presence is UNCONFIRMED.** The repository README mentions "rice, maize, soybean" as examples but does not enumerate all 12. Full commodity list requires cloning the repository and inspecting CSV file names or a commodity column.
- **Markets covered:** Subset of AGMARKNET (collected 2008–2017); exact count not documented
- **Price fields available:** Min Price (Rs./Quintal), Max Price (Rs./Quintal), Modal Price (Rs./Quintal) — confirmed in README
- **Units and currency:** INR per quintal
- **Arrival / supply data:** Yes — `Arrivals (Tonnes)` field stated in README
- **Schema summary (from README, not independently row-verified):** State Name, District Name, Market Name, Commodity, Variety, Group, Arrivals (Tonnes), Min Price (Rs./Quintal), Max Price (Rs./Quintal), Modal Price (Rs./Quintal), Reported Date
- **Missing values:** Not calculated. No per-commodity quality statistics provided in repository.
- **Duplicate records:** Not calculated. Data was collected day-by-day via automated scraper — minor artefacts possible.
- **Accessibility method:** Direct GitHub repository access. CSV files organised per-crop per-year. No API key required. Repository is publicly accessible.
- **Reproducibility:** Static archive. Not updated since June 2017. Cannot be extended beyond that date from this source.
- **Quality findings:** (a) Onion/Potato directory paths return 404 — commodity list must be confirmed by cloning. (b) Archive is frozen at June 2017. (c) Scraper-collected — potential for missed dates. (d) No explicit license for the archive; GODL-India applies to underlying data. (e) File sizes and per-commodity row counts are unknown without local inspection.
- **Selection / rejection rationale:** Role changed to backup/supplementary pending commodity confirmation. If onion and potato are confirmed present, the 2008–2017 period provides a useful pre-assembled historical segment. Cannot replace S-1 for post-2017 data. Must not be committed to the project repository as bulk data.
- **Outstanding verification task:** Clone or browse repository to confirm commodity list and verify onion/potato file existence.
- **Status:** Supplementary (2008–2017) — BLOCKED on commodity confirmation via direct file inspection

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
- **Outstanding verification task:** Inspect full date range of label files; confirm Git LFS download procedure; obtain full commodity list for potato label files.
- **Status:** Confirmed as research reference for anomaly methodology — labels are algorithmic, not independent ground truth; limitations documented

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
