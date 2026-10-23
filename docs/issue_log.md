# CropCast — Issue and Resolution Log

Bugs, failed approaches, and unexpected results are recorded here. Failed experiments must not be omitted.

Each entry records: symptoms, reproduction steps, root cause (if established), attempted solutions, and verified resolution.

---

## Entry Template

```
### ISS-NNN: [Short Description]
- **Date reported:** YYYY-MM-DD
- **Phase / component:** [e.g., Data Pipeline, Feature Engineer, Forecaster]
- **Symptoms:** [What was observed]
- **Reproduction steps:** [Minimal steps to reproduce]
- **Root cause:** [Established cause, or "Under investigation"]
- **Attempted solutions:**
  1. [Approach A — outcome]
  2. [Approach B — outcome]
- **Resolution:** [Final fix applied, or "Unresolved"]
- **Verified by:** [test, manual check, or other evidence]
- **Status:** [Open / Resolved / Accepted limitation]
- **Related files/refs:** [code, notebook, report]
```

---

## Entries

### ISS-001: `.gitignore` rule `data/` excluded the `src/data/` source package
- **Date reported:** 2026-10-23
- **Phase / component:** Repository hygiene / Data Pipeline
- **Symptoms:** `git status --ignored` listed `src/data/` as ignored; only `src/__init__.py` would have been committed, omitting `src/data/ingest_ceda.py`.
- **Reproduction steps:** `git check-ignore -v src/data/ingest_ceda.py` → matched `.gitignore: data/`.
- **Root cause:** An unanchored `data/` pattern matches any directory named `data` at any depth.
- **Attempted solutions:**
  1. Anchored the pattern to the repository root (`/data/`) — successful.
- **Resolution:** `.gitignore` now uses `/data/`.
- **Verified by:** `git check-ignore` still matches `data/raw/ceda_manifest.json` and raw chunk files; `src/data/ingest_ceda.py` and `src/data/__init__.py` now show as untracked (committable).
- **Status:** Resolved
- **Related files/refs:** `.gitignore`, `docs/research_log.md` (RES-011)

### ISS-002: UP Potato `modal_price` outside `[min_price, max_price]` in 137 records
- **Date reported:** 2026-10-23
- **Phase / component:** Data Validation
- **Symptoms:** 136 records with `modal_price < min_price` and 1 with `modal_price > max_price` in `potato_uttar_pradesh` prices. Onion has 0 such records.
- **Reproduction steps:** Load all 14 historical price chunks for `potato_uttar_pradesh` and count records violating `min_price <= modal_price <= max_price`.
- **Root cause:** Under investigation. All below-min cases fall within 2016-03-04 – 2017-04-02 (110 in 2016, 26 in 2017); median shortfall 1.46%, max 7.24%. The time confinement points to a source-side aggregation or reporting regime in that period. An earlier "volume-weighted aggregation" explanation was unverified and has been retracted.
- **Attempted solutions:**
  1. None applied. Records are retained unchanged (no deletion, clipping, or imputation).
- **Resolution:** Unresolved. Proposed: carry a quality flag column in the assembled dataset and examine in EDA; optionally ask CEDA about aggregation methodology for 2016–2017.
- **Verified by:** Offline re-verification (RES-011).
- **Status:** Open
- **Related files/refs:** `data/raw/ceda/potato_uttar_pradesh/prices_*.json`, `docs/research_log.md` (RES-010, RES-011), DEC-016

### ISS-003: Near-zero Maharashtra Onion arrivals on four dates in 2020
- **Date reported:** 2026-10-23
- **Phase / component:** Data Validation
- **Symptoms:** `quantity` = 5 (2020-04-24), 3 (2020-04-25), 2 (2020-04-28), 14 (2020-10-26), against a series mean of ~16,323. They sit next to the 2020-04 lockdown gaps and immediately after the 10-day gap ending 2020-10-25.
- **Reproduction steps:** Sort onion quantity records ascending.
- **Root cause:** Under investigation; plausibly partial mandi reporting during disruptions. Not confirmed.
- **Attempted solutions:**
  1. None applied; values retained unchanged.
- **Resolution:** Unresolved; to be characterised in M-3 EDA. Any exclusion or flagging rule must be decided explicitly and logged.
- **Verified by:** Offline re-verification (RES-011).
- **Status:** Open
- **Related files/refs:** `data/raw/ceda/onion_maharashtra/quantities_2020-*.json`

### ISS-004: M-2 validation audit not reproducible from committed code
- **Date reported:** 2026-10-23
- **Phase / component:** Reproducibility / Data Validation
- **Symptoms:** `data/raw/m2_validation_audit.json` (reports 137 potato numeric violations) was produced by a script not in the repository. `historical_extraction_summary.json`, produced by `src/data/ingest_ceda.py`, reports 0 numeric violations for the same data because `validate_records` does not check `min_price <= modal_price <= max_price`. No run log of `task-775` was retained.
- **Reproduction steps:** Compare `numeric_violations` for potato prices across the two JSON files; inspect `CedaIngestionPipeline.validate_records`.
- **Root cause:** Validation gate checks were run ad hoc rather than from a committed module; the pipeline validator lacks the modal-bounds check.
- **Attempted solutions:**
  1. Independent offline re-verification script written outside the repository (RES-011); results agree with the audit file on all counts.
  2. Per DEC-016 (approved): added `src/data/validate.py`, a committed offline audit module with 18 unit tests (`tests/test_validate.py`), and a non-fatal `modal_bounds_warnings` counter in `validate_records`. Warnings do not affect `is_valid`, so they never trigger a re-fetch.
- **Resolution:** `python -m src.data.validate --output data/raw/m2_validation_audit.json` regenerates the audit offline. The previous ad-hoc file is preserved locally as `data/raw/m2_validation_audit.legacy_adhoc.json`. Schema change: the legacy `price_numeric_violations` (137 for potato, modal-bounds cases included) is replaced by `numeric_violations` (hard failures only, 0) and `modal_bounds_warnings` (137).
- **Verified by:** Regenerated audit equals the legacy audit on every shared field (counts, gaps, IoU, match rate, distribution stats); `validate_records` on the full potato price series returns `is_valid=True`, 0 violations, 137 warnings; 40 / 40 tests pass. The run log for `task-775` cannot be recovered, so its 429 / retry history stays unverified.
- **Status:** Resolved
- **Related files/refs:** `src/data/ingest_ceda.py`, `data/raw/m2_validation_audit.json`, `data/raw/historical_extraction_summary.json`

### ISS-005: Pilot chunks overlap historical H1-2021 chunks and use a different file format
- **Date reported:** 2026-10-23
- **Phase / component:** Data Assembly
- **Symptoms:** `*_2021-01-01_2021-01-15.json` pilot files (4 total) are bare JSON lists without the `metadata` envelope, and duplicate dates in the `*_2021-01-01_2021-06-30.json` chunks.
- **Reproduction steps:** Load both files for any series/endpoint and compare records by date.
- **Root cause:** Pilot run preceded the envelope format; full-range run used different chunk boundaries.
- **Attempted solutions:**
  1. Compared all overlapping records — field-for-field identical (0 differences).
- **Resolution:** Dataset assembly must read only the 14 six-month historical chunks per series/endpoint (or deduplicate on the composite key and assert equality). Raw files are left untouched.
- **Verified by:** Offline re-verification (RES-011).
- **Status:** Accepted limitation
- **Related files/refs:** `data/raw/ceda/*/*_2021-01-01_2021-01-15.json`

### ISS-006: `test_http_500_exponential_backoff_and_retry` exercises nothing
- **Date reported:** 2026-10-23
- **Phase / component:** Test suite
- **Symptoms:** The test configures mocks for an HTTP 500 followed by a success but never calls `make_request` and makes no assertions, so it always passes. HTTP 5xx backoff is therefore untested, and earlier test counts overstate coverage by one.
- **Reproduction steps:** Read `tests/test_ingest_ceda.py`, `TestRateLimitingAndRetries.test_http_500_exponential_backoff_and_retry`.
- **Root cause:** Incomplete test body.
- **Attempted solutions:** None yet (outside DEC-016 scope).
- **Resolution:** Unresolved. Fix: call `self.pipeline.make_request(...)` and assert two `urlopen` calls and a backoff `sleep`.
- **Verified by:** —
- **Status:** Open
- **Related files/refs:** `tests/test_ingest_ceda.py`
