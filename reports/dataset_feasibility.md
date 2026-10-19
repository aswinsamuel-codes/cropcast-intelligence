# CropCast — Dataset Feasibility Report

**Milestone:** M-1 — Dataset Feasibility Investigation
**Date produced:** 2026-10-19
**Status:** Draft — awaiting researcher review and approval
**Author:** CropCast research team

---

## 1. Purpose

This report documents the investigation of publicly accessible agricultural commodity price datasets for the CropCast project. The goal is to determine whether real-world data is adequate to support a reproducible, scientifically defensible price-forecasting and market-relative anomaly-detection experiment before any model development begins.

The preferred feasibility target is: at least three years of daily or weekly Modal_Price records for at least one commodity (onion or potato) across at least three markets. Datasets that do not meet this target may still be usable if the shortfall is documented and the available data is assessed as sufficient for the specific experiments planned (per Requirement 1 AC 8).

---

## 2. Sources Investigated

Five sources were investigated:

| ID  | Source Name                                         | Type              | URL                                                        |
|-----|-----------------------------------------------------|-------------------|------------------------------------------------------------|
| S-1 | AGMARKNET via OGD Platform (data.gov.in)            | Official govt API | https://data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070 |
| S-2 | AGMARKNET archived dataset (iancovert/Agmarknet)    | Secondary archive | https://github.com/icc2115/Agmarknet                       |
| S-3 | Dept of Consumer Affairs / FCA Price Monitoring     | Official govt web | https://fcainfoweb.nic.in/reports/report_menu_web.aspx     |
| S-4 | ICTD-IITD Commodity_Analysis (IIT Delhi research)  | Research dataset  | https://github.com/ICTD-IITD/Commodity_Analysis            |
| S-5 | NHRDF Market Arrivals and Price Database            | Official / web    | http://nhrdf.org/en-us/DatabaseReports                     |

> **Date of investigation:** 2026-10-19
> All source findings are based on publicly available documentation, repository inspections, and search results. Direct API calls to data.gov.in and AGMARKNET were not executed in this audit; those require a registered API key and are noted under access requirements below.

---

## 3. Dataset Audit Details

### S-1: AGMARKNET via OGD Platform (data.gov.in)

- **Data owner:** Ministry of Agriculture and Farmers Welfare, Government of India; published via National Informatics Centre (NIC)
- **License / terms of use:** Government Open Data License – India (GODL-India). Permits free use, reproduction, and redistribution with attribution. No commercial restriction for research use.
- **Access method:** REST API requiring a free registered account and API key from https://data.gov.in/apis. Key is free to obtain. API returns paginated JSON; no bulk historical CSV download is available through the OGD platform directly. Historical records must be assembled by paginating through the API.
- **Resource ID confirmed:** `9ef84268-d588-465a-a308-a864a43d0070` (referenced by multiple independent projects).
- **Schema (observed from multiple independent sources):**

  | Column name              | Type    | Notes                                      |
  |--------------------------|---------|---------------------------------------------|
  | State Name               | string  | State where market is located               |
  | District Name            | string  | District name                               |
  | Market Name              | string  | Mandi / market name                         |
  | Commodity                | string  | Commodity name (e.g., "Onion", "Potato")    |
  | Variety                  | string  | Variety name                                |
  | Group                    | string  | Commodity group                             |
  | Arrivals (Tonnes)        | numeric | Market arrivals volume in tonnes            |
  | Min Price (Rs./Quintal)  | numeric | Minimum price in INR per quintal            |
  | Max Price (Rs./Quintal)  | numeric | Maximum price in INR per quintal            |
  | Modal Price (Rs./Quintal)| numeric | Modal (most frequent) price in INR/quintal  |
  | Reported Date            | date    | Date of report                              |

- **Units and currency:** INR per quintal (1 quintal = 100 kg)
- **Commodities confirmed present:** Onion and Potato are both explicitly listed as available commodities. The portal covers 300+ commodities across 3,000+ regulated markets.
- **Markets covered:** Over 3,000 regulated APMC markets across all states. Independent research has identified approximately 211 onion markets and 180 potato markets with data in the AGMARKNET database.
- **Arrival data:** Yes — `Arrivals (Tonnes)` field is present in the schema.
- **Historical date range:** AGMARKNET began data collection in March 2000. The OGD API resource has been confirmed to contain records up to the present. Exact start date for consistent onion and potato coverage requires direct API sampling to verify.
- **Reproducibility:** The OGD API is the authoritative government source. Historical records can be retrieved by date-range API queries. However, the API has known issues: registration is required, field names have changed over time across resource versions, pagination is required for large date ranges, and the upstream feed publishes with a 2–7 day lag from actual APMC trade dates (confirmed by PramaanAI and dev.to sources). data.gov.in has also been reported to intermittently not publish newer prices for extended periods.
- **Known access friction:** Requires registration and API key (free). Inconsistent field naming across resource versions. No single bulk historical download. Each historical pull requires manual pagination.
- **Data-quality findings (from source documentation and prior research):**
  - Reporting is not uniform across states; some mandis report daily, others weekly or intermittently.
  - Missing observations for multiple consecutive days are documented in prior research (ICTD-IITD work notes this explicitly as a challenge).
  - Some variety fields may be inconsistently coded across markets.
  - The API returns current/recent data reliably; historical coverage depth varies by market and commodity.
- **Feature availability at forecast time:** Modal_Price, Min_Price, Max_Price, and Arrivals fields are all reported-date fields — they represent what was known on the reporting date. Suitable for time-aware feature construction, subject to the 2–7 day reporting lag noted above.
- **Assessment:** This is the authoritative primary source. It has the correct schema, contains both onion and potato, includes arrival volumes, and is licensed for research use. The main constraints are the API registration requirement, the need to paginate historical data, and market-level reporting gaps.

---

### S-2: AGMARKNET Archived Dataset (iancovert/Agmarknet, GitHub)

- **Data owner:** Data originally from AGMARKNET / Directorate of Marketing and Inspection, Government of India. Archived by Ian Covert (independent researcher).
- **License / terms of use:** The repository does not carry an explicit license file. The data originates from a government source (GODL-India applies to the underlying data). Reuse for research is consistent with GODL-India terms, but redistribution of the archived files should be attributed to the original AGMARKNET source, not the repository.
- **URL:** https://github.com/icc2115/Agmarknet
- **How obtained:** Downloaded from AGMARKNET in June 2017 using Mechanize and BeautifulSoup scripts. Data collected one day at a time due to AGMARKNET portal limitations at that time.
- **Schema:** Identical to S-1 (same columns, same units — the schema was confirmed directly from the repository README):
  - `State Name`, `District Name`, `Market Name`, `Variety`, `Group`, `Arrivals (Tonnes)`, `Min Price (Rs./Quintal)`, `Max Price (Rs./Quintal)`, `Modal Price (Rs./Quintal)`, `Reported Date`
- **Units and currency:** INR per quintal
- **Commodities covered:** 12 food products (rice, maize, soybean, and others — exact list of 12 not fully specified in the README; onion and potato presence requires direct inspection of the data files).
- **Date range:** 2008 through June 2017 (approximately 9.5 years)
- **Record count:** Approximately 4 million data points across all 12 commodities
- **Arrival data:** Yes — `Arrivals (Tonnes)` field present
- **Accessibility:** Direct GitHub repository access. Data split into per-crop, per-year CSV files. Downloadable without any API key or registration.
- **Reproducibility:** Repository is static (not continuously updated). Data reflects what was available in June 2017 and stops there. Historical records cannot be extended beyond June 2017 from this archive.
- **Data-quality findings:**
  - Static archive: no updates since June 2017. Any analysis using this dataset cannot reflect post-2017 market behaviour.
  - Data collected one day at a time using a web scraper; potential for missed dates or scraping artefacts.
  - Onion and potato presence in the 12 commodities is not confirmed from the repository README alone — this requires direct inspection of the CSV files. The repository states "12 food products" without listing them explicitly.
  - Repository has no explicit license for the archive itself; the underlying data license (GODL-India) applies.
  - Cannot be committed to the project repository if it constitutes a full dataset copy without confirming redistribution terms. A retrieval procedure referencing the original AGMARKNET source should be used instead.
- **Comparison with S-1:** S-2 provides a pre-assembled historical archive (2008–2017) without the API friction of S-1, but at the cost of being frozen in time. For experiments involving data up to 2024–2026, S-2 alone is inadequate and would need to be supplemented with S-1 API pulls.
- **Assessment:** Useful as a convenience archive for the 2008–2017 period, but requires direct file inspection to confirm onion and potato presence. Cannot replace S-1 for recent data. Should not be committed to the repository as a bulk data file.

---

### S-3: Department of Consumer Affairs / FCA Price Monitoring System

- **Data owner:** Price Monitoring Division (PMD), Department of Consumer Affairs, Government of India
- **URL:** https://fcainfoweb.nic.in/reports/report_menu_web.aspx
- **License / terms of use:** Government of India website. Data is publicly accessible for monitoring purposes. No explicit open-data license found; access is provided for informational purposes. Suitability for bulk research download is unconfirmed — terms must be verified before systematic data collection.
- **Price category:** Both retail and wholesale prices are monitored. The PMS reports prices from 555 (as of recent records, up to 579) price monitoring centres across the country, representing five regional zones. These are NOT mandi-level wholesale prices — they are city-level retail and wholesale indicator prices reported by designated monitoring centres.
- **Commodities confirmed:** Onion and Potato are both included (confirmed). The system monitors 22 essential commodities total, including both.
- **Geographic granularity:** City / regional centre level — 555–579 centres across India, representing North, West, East, South, and North-Eastern regions. This is coarser than AGMARKNET's mandi-level coverage.
- **Schema:** The web interface provides price reports, average/month-end reports, and variation reports. Exact downloadable schema requires navigation through the CAPTCHA-protected web form. A CAPTCHA is present on the report access page, making automated bulk download infeasible without human interaction.
- **Arrival data:** Not present. The PMS tracks prices only, not market arrival volumes.
- **Access method:** Web form with CAPTCHA. Manual downloads per query. No direct CSV bulk export or API endpoint found.
- **Reproducibility:** Manual web form navigation required for each data pull. Not reproducible via script without CAPTCHA bypass (which is not acceptable per project constraints).
- **Data-quality findings:**
  - Retail prices from city monitoring centres, not mandi wholesale prices — these are methodologically distinct from AGMARKNET data and must not be merged without a justified methodology.
  - Useful for cross-validation and as a secondary reference, but not the primary forecasting data source.
  - No arrival data limits its utility for supply-related anomaly detection signals.
  - CAPTCHA barrier makes systematic programmatic access infeasible.
- **Assessment:** Not suitable as the primary dataset for CropCast. Retail/wholesale indicator prices from city centres are methodologically different from mandi-level Modal_Price. No arrival data. CAPTCHA prevents reproducible bulk access. Suitable only as a supplementary reference for retail price validation or contextual comparison, if manual access is pursued.

---

### S-4: ICTD-IITD Commodity_Analysis (IIT Delhi)

- **Data owner:** ICT for Development Lab, IIT Delhi
- **URL:** https://github.com/ICTD-IITD/Commodity_Analysis
- **License / terms of use:** Repository does not carry an explicit open-data license. Data was crawled from AGMARKNET and DoCA FCA. Redistribution of the data itself requires verification with the original data owners. The code is available for reference.
- **Commodities confirmed:** Onion, Potato, Tomato, Rice, Mustard Oil, Moong Dal, Masur Dal (7 commodities).
- **Schema (wholesale data from AGMARKNET, as processed):** Formatted version of the AGMARKNET schema — renamed columns, changed datatypes, with missing values imputed via Stineman interpolation.
- **Schema (retail data from FCA):** Daily retail prices per city centre per commodity.
- **Date range:** Research paper states forecasting from 2011 to 2021, implying data covers at least 2011–2021.
- **Arrival data:** Yes — arrival volumes are included in the mandi-level dataset.
- **Anomaly labels:** Yes — the repository contains annotated anomalies with associated news articles. This is a significant feature not present in the other sources.
- **Reproducibility:** The dataset in the repository contains both original and forecasted data. The original data was crawled; it is not directly downloadable as a clean, labelled CSV in the way AGMARKNET's OGD resource is.
- **Data-quality findings:**
  - Missing values imputed using Stineman interpolation — this is a pre-processing decision that may not align with CropCast's requirement to document and explicitly approve all imputation.
  - Data provenance relies on AGMARKNET and FCA sources; the ICTD data is a processed derivative, not an authoritative primary source.
  - Anomaly labels are valuable for evaluation, but the labelling methodology must be understood before treating them as ground truth.
  - Repository activity last confirmed; maintenance status uncertain.
- **Assessment:** The anomaly labels are uniquely valuable — no other investigated source provides ground-truth anomaly labels for onion/potato. The wholesale price data is ultimately derived from AGMARKNET. The ICTD dataset is best used as: (a) a reference for the anomaly detection methodology comparison, and (b) a source of labelled anomaly events for evaluation, subject to understanding the labelling process. It should NOT be used as the primary price time-series source because it is a processed derivative with pre-applied imputation.

---

### S-5: NHRDF Market Arrivals and Price Database

- **Data owner:** National Horticultural Research & Development Foundation (NHRDF), Nashik
- **URL:** http://nhrdf.org/en-us/DatabaseReports
- **License / terms of use:** No explicit open-data license found. NHRDF is a government-affiliated research foundation. Access appears to be provided via a web form.
- **Commodities covered:** Onion, Potato, Garlic (the three NHRDF mandate commodities)
- **Date range:** Data reportedly available from 1996 onwards.
- **Schema:** Web form provides tabular output (Data Wise Market Arrivals and Price Data). Exact column names require form submission. Prior research (amitkaps/onions-dataset) confirms the form returns market-level price and arrival data.
- **Arrival data:** Yes — market arrivals are a core feature.
- **Access method:** Web form. Data returned as tabular HTML or download. No API confirmed. Bulk programmatic access not confirmed.
- **Reproducibility:** Requires manual web form submission. Reproducibility for bulk historical download is uncertain.
- **Data-quality findings:**
  - Likely covers major onion production regions (Maharashtra, Karnataka, Rajasthan) most comprehensively given NHRDF's focus on these crops.
  - Arrival data specifically for onion and potato from 1996 is a strength, but schema and granularity require direct investigation.
  - Access friction (web form, no API) reduces reproducibility.
- **Assessment:** A potentially useful secondary source for onion arrival data going back to 1996, particularly for major producing markets. Requires direct form access to verify schema and coverage. Should be investigated further if AGMARKNET arrival data proves incomplete for key markets.

---

## 4. Dataset Comparison Table

| Criterion                         | S-1: OGD/AGMARKNET API    | S-2: Archived (iancovert) | S-3: DoCA/FCA PMS       | S-4: ICTD-IITD          | S-5: NHRDF               |
|-----------------------------------|---------------------------|---------------------------|-------------------------|-------------------------|--------------------------|
| Price category                    | Wholesale mandi           | Wholesale mandi           | Retail + wholesale indicator | Wholesale + retail  | Wholesale mandi          |
| Onion confirmed                   | Yes                       | Unconfirmed (12 crops)    | Yes                     | Yes                     | Yes                      |
| Potato confirmed                  | Yes                       | Unconfirmed (12 crops)    | Yes                     | Yes                     | Yes                      |
| Modal_Price field                 | Yes                       | Yes                       | No (not mandi modal)    | Yes (processed)         | Unconfirmed              |
| Min / Max Price                   | Yes                       | Yes                       | Not directly            | Yes (processed)         | Unconfirmed              |
| Arrivals data                     | Yes                       | Yes                       | No                      | Yes                     | Yes                      |
| Date range                        | ~2000 – present           | 2008 – June 2017          | Unknown (needs access)  | ~2011 – 2021            | ~1996 – present          |
| Number of markets                 | 3,000+ mandis             | Subset (collected 2008–17)| 555–579 centres         | Selected mandis         | Major producing markets  |
| Onion markets (AGMARKNET study)   | ~211 markets              | Subset                    | N/A                     | Selected                | Primarily Maharashtra    |
| Potato markets (AGMARKNET study)  | ~180 markets              | Subset                    | N/A                     | Selected                | N/A                      |
| Anomaly labels                    | No                        | No                        | No                      | Yes (with news)         | No                       |
| License                           | GODL-India (open)         | GODL-India (original data)| Not confirmed           | Not confirmed           | Not confirmed            |
| Bulk download available           | API pagination (key req.) | Yes (GitHub CSV)          | No (CAPTCHA web form)   | Partial (GitHub)        | No (web form)            |
| Reproducible programmatically     | Yes (API)                 | Static archive            | No (CAPTCHA)            | Partial                 | Uncertain                |
| Pre-applied imputation            | No                        | No                        | N/A                     | Yes (Stineman)          | Unknown                  |
| Suitable as primary source        | **Yes**                   | Supplementary only        | No                      | No (secondary)          | Supplementary only       |

---

## 5. Schema Sample (Verified)

The following schema was independently confirmed from multiple sources (iancovert/Agmarknet README, iblameshivang/lelojldi, ICTD-IITD preprocessing scripts) for both S-1 and S-2:

```
State Name       : string  — e.g., "Maharashtra"
District Name    : string  — e.g., "Nashik"
Market Name      : string  — e.g., "Lasalgaon"
Commodity        : string  — e.g., "Onion", "Potato"
Variety          : string  — e.g., "Other", "Deshi"
Group            : string  — commodity group classification
Arrivals (Tonnes): float   — market arrival volume in tonnes
Min Price        : float   — minimum price in Rs. per quintal
Max Price        : float   — maximum price in Rs. per quintal
Modal Price      : float   — modal price in Rs. per quintal
Reported Date    : date    — date of report (DD-Mon-YYYY format typical)
```

**Representative record (format, not fabricated values):**

| State Name | District Name | Market Name | Commodity | Variety | Group | Arrivals (Tonnes) | Min Price (Rs./Quintal) | Max Price (Rs./Quintal) | Modal Price (Rs./Quintal) | Reported Date |
|---|---|---|---|---|---|---|---|---|---|---|
| Maharashtra | Nashik | Lasalgaon | Onion | Other | Vegetables | [numeric] | [numeric] | [numeric] | [numeric] | DD-Mon-YYYY |

> **Note:** Actual numeric values cannot be verified without API access. The format above reflects the confirmed schema from independent sources. Direct API sampling is required to verify actual data ranges and quality statistics per the next steps in M-1.

---

## 6. Data-Quality Statistics

> **Critical note:** The statistics below distinguish between independently calculated values (from the iancovert archive, ICTD-IITD research papers, and documented prior analyses) and reported/inferred figures from source documentation. No direct database query was performed in this audit phase. Direct API sampling is the recommended next step to calculate precise statistics.

### What is independently documented

From the iancovert/Agmarknet archive (S-2), directly from the repository:
- **Total records:** ~4,000,000 across 12 commodities (2008 – June 2017)
- **Date range:** 2008 through June 2017 (~9.5 years)
- **Structure:** One CSV file per crop per year; one row per market per day

From ICTD-IITD research (S-4), from the published paper and repository:
- **Missing values:** Described as a significant challenge — "missing data for many successive days" is explicitly noted. Stineman interpolation was applied as the remedy.
- **Commodities:** 7 (includes onion and potato)
- **Period:** 2011–2021 for the forecasting experiments

From independent market-count research:
- ~211 onion markets and ~180 potato markets with data in the AGMARKNET database (Library of Congress catalogued study)

### What requires direct verification

The following must be calculated by direct API or file access before this report can be considered complete:
- [ ] Exact row count for onion and potato specifically in S-1 (OGD API) and S-2 (archived files)
- [ ] Missing-value percentage by column for onion and potato in the target markets
- [ ] Exact and conflicting duplicate counts
- [ ] Date-range continuity gaps (calendar days with no reporting) per market
- [ ] Percentage of market-days with zero or null Arrivals
- [ ] Overlapping date coverage across at least three candidate markets
- [ ] Confirmation of onion and potato presence in S-2 (the archived 12 commodities must be inspected)

> **This is an open item.** The feasibility recommendation below is based on the architectural sufficiency of the confirmed schema and coverage; the precise data-quality statistics require direct data access.

---

## 7. Coverage Assessment Against Preferred Feasibility Target

**Preferred target:** ≥3 years of daily/weekly Modal_Price records for ≥1 commodity across ≥3 markets.

| Source | Onion years | Potato years | Markets | Meets preferred target? |
|--------|-------------|--------------|---------|------------------------|
| S-1 (OGD/AGMARKNET API) | Likely ≥20 years (2000–present); exact onion/potato coverage unverified | Same | 211 onion, 180 potato | Likely yes — pending direct verification |
| S-2 (Archived 2008–2017) | ~9 years if onion present | ~9 years if potato present | Subset (number unverified) | Likely yes — pending commodity confirmation |
| S-3 (DoCA/FCA) | Unknown without access | Unknown | 555–579 city centres | Not applicable (different price category) |
| S-4 (ICTD-IITD) | ~10 years (2011–2021) | ~10 years (2011–2021) | Selected mandis | Yes for the curated subset |
| S-5 (NHRDF) | Likely ≥20 years (1996–present) | Same | Major producing markets | Likely yes — pending verification |

**Preliminary assessment:** The preferred coverage target is very likely met by the OGD/AGMARKNET source (S-1). Direct verification is required to confirm exact onion and potato record counts and reporting continuity per market.

---

## 8. Forecasting Target and Horizon Assessment

Based on the confirmed schema:

- **Recommended target:** Modal_Price (Rs./Quintal) for a selected commodity (onion or potato) at a selected mandi
- **Recommended forecast horizon:** One market day ahead (next reported trading day)
- **Recommended scope:** Begin with onion, for which more markets are available (~211 vs ~180 for potato), and select 3–5 markets with high reporting regularity based on data-quality statistics once direct access is obtained
- **Feature availability at forecast time:**
  - Min_Price, Max_Price, Modal_Price: available for past dates — suitable for lag features
  - Arrivals (Tonnes): available for past dates — suitable as lagged supply signal
  - Peer-market prices: available for past market-days — suitable for peer features with strict t-1 lag
  - Calendar features (day-of-week, month): always available at forecast time — no leakage risk
  - No weather, policy, or external data fields are present in the primary schema
- **Reporting lag consideration:** AGMARKNET data is published with a 2–7 day lag from actual trade dates. For strict time-aware feature construction, the Reported Date should be treated as the date the data becomes known, not the date of the trade.

---

## 9. Anomaly Detection Assessment

- **Ground-truth labels:** Not present in S-1 or S-2. Present in S-4 (ICTD-IITD), with associated news articles.
- **Implication:** If S-1/S-2 is the primary forecasting data source, ground-truth anomaly labels will not be available for precision/recall evaluation on the forecasting dataset. Evaluation will require either: (a) obtaining S-4's labelled annotations and aligning them with the corresponding S-1 records, or (b) using synthetic shock injection as the anomaly evaluation method, clearly labelled as such.
- **Peer-market data:** Available — ~211 onion markets and ~180 potato markets provide ample peer-market candidates for divergence signal computation.
- **Arrival data:** Available in S-1 and S-2 — Arrivals (Tonnes) field can support supply-related anomaly signals, subject to completeness verification.

---

## 10. Licensing and Access Summary

| Source | License | Bulk download | API key required | CAPTCHA | Redistribution of data |
|--------|---------|---------------|-----------------|---------|----------------------|
| S-1 (OGD/AGMARKNET) | GODL-India (open research use) | No (pagination API) | Yes (free) | No | Attribution required; do not commit API key |
| S-2 (iancovert archive) | GODL-India applies to underlying data | Yes (GitHub CSV) | No | No | Do not commit bulk files; document retrieval procedure |
| S-3 (DoCA/FCA) | Not confirmed | No (CAPTCHA web form) | No | Yes | Not confirmed |
| S-4 (ICTD-IITD) | Not confirmed | Partial (GitHub) | No | No | Data is derivative of govt sources; redistribution unconfirmed |
| S-5 (NHRDF) | Not confirmed | No (web form) | No | Unknown | Not confirmed |

**Credential rule:** API keys for data.gov.in must never be committed to the repository. They must be stored in `.env` files or environment variables only.

---

## 11. Known Limitations

1. **No direct database access in this audit.** Precise row counts, missing-value percentages, duplicate counts, and date-gap statistics for onion and potato were not independently calculated from raw data. They must be calculated in the next step before full M-1 completion.

2. **Onion and potato presence in S-2 is unconfirmed.** The iancovert archive covers "12 food products" but does not list them explicitly. Direct file inspection is required.

3. **AGMARKNET reporting lag.** Data is published with a 2–7 day lag from trade dates. This must be documented in the feature engineering specification to avoid inadvertent look-ahead.

4. **Irregular reporting.** Not all markets report on all calendar days. Some markets report weekly; some report only on specific trading days. This will produce irregular time series requiring careful handling (forward-fill or exclusion, not automatic interpolation).

5. **Variety inconsistency.** The `Variety` field encoding varies across markets and states. Filtering for consistent commodity-variety combinations may reduce the effective market count.

6. **S-4 anomaly labels require methodology review.** Before using ICTD-IITD anomaly labels as ground truth, the labelling methodology must be documented and verified. Labels based on rule-based anomaly flags may not align with the research definition of a price anomaly for CropCast.

7. **DoCA/FCA data is retail/city-level.** It cannot be merged with AGMARKNET mandi-level data without a clearly justified and documented methodology.

8. **NHRDF access reproducibility is unconfirmed.** The web form may not support programmatic bulk retrieval, which would make it unsuitable as a primary source.

---

## 12. Recommendation

### Preliminary recommendation (pending verification)

**Recommended approach: Real-world data, primary source S-1 (AGMARKNET via OGD API)**

**Justification:**
- The AGMARKNET OGD API is the authoritative government source for Indian mandi wholesale prices.
- It has the correct schema for the CropCast forecasting target: Modal_Price at mandi level with Arrivals data.
- It covers both onion and potato.
- It is licensed under GODL-India for research use.
- It is reproducible via the API (API key is free).
- Coverage almost certainly exceeds the preferred 3-year, 3-market target based on the ~211 onion and ~180 potato markets documented in independent research.

**Supplementary sources:**
- S-2 (iancovert archive, 2008–2017) as a convenience pre-assembled dataset for the historical period, contingent on confirmation that onion and potato are among the 12 archived commodities.
- S-4 (ICTD-IITD) for anomaly label alignment, subject to methodology review.

**Recommended data mode:** Real-world data (Option A per requirements). Synthetic data is not needed given the expected scale of the OGD dataset. Hybrid evaluation (Option C) should be considered for the anomaly detection component if the S-4 labels cannot be aligned with the primary dataset.

### What must be confirmed before this recommendation is locked

- [ ] Direct API access to OGD resource `9ef84268-d588-465a-a308-a864a43d0070` to sample actual records and confirm onion and potato presence, date coverage, and reporting regularity.
- [ ] Calculation of missing-value percentages and date gaps for 3–5 candidate markets.
- [ ] Confirmation that onion and potato are among the 12 commodities in the S-2 archive.
- [ ] Review of ICTD-IITD labelling methodology to determine whether their anomaly labels can be aligned with the selected primary dataset.

---

## 13. Approval Gate

This report is submitted for researcher review. Per Requirement 10 AC 1, no transition to synthetic or hybrid evaluation mode may occur without explicit researcher approval. The preliminary recommendation is for real-world data (Option A), but this is contingent on verification of the items listed in Section 12.

**Researcher decision required:**
- [ ] Approve real-world data approach, pending direct verification steps
- [ ] Request additional investigation before deciding
- [ ] Approve hybrid approach (real data for forecasting + synthetic shocks for anomaly evaluation)

> **Record any decision here with date and rationale, per Requirement 10 AC 2 and Requirement 11 AC 3.**

---

*Report end. Sources investigated: 2026-10-19. Direct data verification pending.*
