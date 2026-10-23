"""
CropCast M-2 Raw Data Validation Audit
======================================
Regenerates the M-2 validation gate audit entirely offline from the local
CEDA manifest and raw chunk files. Never makes network requests and never
modifies raw data.

Hard failures (exit code 1):
- Missing expected chunk files or manifest entries; SHA-256 mismatches.
- Schema problems: wrong key set, wrong IDs, bad dates, dates outside the chunk.
- Duplicate dates, nulls, non-numeric / non-finite / negative values, min_price > max_price.
- Supplementary chunks (e.g. the pilot) whose records disagree with the historical chunks.

Warnings (reported, exit code unaffected):
- modal_price outside [min_price, max_price] (ISS-002).

Usage:
    python -m src.data.validate --output data/raw/m2_validation_audit.json
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.data.ingest_ceda import APPROVED_COMMODITIES, APPROVED_STATES, generate_date_chunks

SERIES_SPECS: List[Tuple[str, int, int]] = [
    ("onion_maharashtra", APPROVED_COMMODITIES["onion"], APPROVED_STATES["maharashtra"]),
    ("potato_uttar_pradesh", APPROVED_COMMODITIES["potato"], APPROVED_STATES["uttar_pradesh"]),
]
ENDPOINTS = ("prices", "quantities")
KEY_FIELDS = {"date", "commodity_id", "census_state_id"}
VALUE_FIELDS = {
    "prices": ("min_price", "max_price", "modal_price"),
    "quantities": ("quantity",),
}
DATE_SUFFIX = "T00:00:00.000Z"
SCHEMA_COUNTERS = ("schema_keyset", "id_mismatch", "bad_date_format", "date_outside_chunk")


def load_chunk_records(path: Path) -> List[Dict[str, Any]]:
    """Return records from a chunk file stored either as an envelope `{metadata, data}` or a bare list."""
    with open(path, "r", encoding="utf-8") as f:
        doc = json.load(f)
    if isinstance(doc, dict):
        return doc["data"]
    if isinstance(doc, list):
        return doc
    raise ValueError(f"Unrecognised chunk format in {path}")


def _numeric(value: Any) -> Optional[float]:
    """Return a finite, non-negative float, or None for null / non-numeric / non-finite / negative values."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        return None
    return float(value)


def find_gaps(missing: List[datetime.date]) -> List[Tuple[str, str, int]]:
    """Group sorted missing dates into consecutive runs `(first, last, length)`."""
    runs: List[List[datetime.date]] = []
    for d in missing:
        if runs and (d - runs[-1][-1]).days == 1:
            runs[-1].append(d)
        else:
            runs.append([d])
    return [(r[0].isoformat(), r[-1].isoformat(), len(r)) for r in runs]


def _check_record(
    rec: Dict[str, Any],
    endpoint: str,
    commodity_id: int,
    state_id: int,
    from_date: str,
    to_date: str,
    counts: Counter,
) -> Optional[datetime.date]:
    """Apply per-record schema and numeric checks; return the record's date if parseable."""
    if set(rec) != KEY_FIELDS | set(VALUE_FIELDS[endpoint]):
        counts["schema_keyset"] += 1
    if rec.get("commodity_id") != commodity_id or rec.get("census_state_id") != state_id:
        counts["id_mismatch"] += 1

    raw_date = rec.get("date")
    if not isinstance(raw_date, str) or not raw_date.endswith(DATE_SUFFIX):
        counts["bad_date_format"] += 1
    try:
        day = datetime.date.fromisoformat(str(raw_date)[:10])
    except ValueError:
        counts["bad_date_format"] += 1
        return None
    if not (from_date <= day.isoformat() <= to_date):
        counts["date_outside_chunk"] += 1

    values: Dict[str, float] = {}
    for k in VALUE_FIELDS[endpoint]:
        v = rec.get(k)
        if v is None:
            counts["null"] += 1
        elif isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
            counts["non_numeric"] += 1
        elif v < 0:
            counts["negative"] += 1
        else:
            values[k] = float(v)
    if endpoint == "prices" and len(values) == 3:
        if values["min_price"] > values["max_price"]:
            counts["min_gt_max"] += 1
    return day


def audit_series(
    series_id: str,
    commodity_id: int,
    state_id: int,
    manifest: Dict[str, Any],
    raw_dir: Path,
    chunks: List[Tuple[str, str]],
    start_date: str,
    end_date: str,
) -> Dict[str, Any]:
    """Audit one series. `chunks` are the expected historical (from, to) windows."""
    manifest_chunks = {c["chunk_id"]: c for c in manifest.get("series", {}).get(series_id, {}).get("chunks", [])}
    expected_ids = {f"{ep}_{a}_{b}" for ep in ENDPOINTS for a, b in chunks}

    missing_files: List[str] = []
    checksum_failures: List[str] = []
    schema_failures: List[str] = []
    counts: Counter = Counter()
    duplicates = {ep: 0 for ep in ENDPOINTS}
    records: Dict[str, Dict[datetime.date, Dict[str, Any]]] = {ep: {} for ep in ENDPOINTS}

    for ep in ENDPOINTS:
        for a, b in chunks:
            chunk_id = f"{ep}_{a}_{b}"
            path = raw_dir / series_id / f"{chunk_id}.json"
            entry = manifest_chunks.get(chunk_id)
            if entry is None or not path.exists():
                missing_files.append(f"{series_id}/{chunk_id}")
                continue
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != entry.get("sha256"):
                checksum_failures.append(f"{series_id}/{chunk_id}")
            try:
                recs = load_chunk_records(path)
            except (ValueError, KeyError) as e:
                schema_failures.append(f"{series_id}/{chunk_id}: {e}")
                continue
            if entry.get("record_count") != len(recs):
                schema_failures.append(f"{series_id}/{chunk_id}: manifest record_count != file")
            before = sum(counts[k] for k in SCHEMA_COUNTERS)
            for rec in recs:
                day = _check_record(rec, ep, commodity_id, state_id, a, b, counts)
                if day is None:
                    continue
                if day in records[ep]:
                    duplicates[ep] += 1
                records[ep][day] = rec
            if sum(counts[k] for k in SCHEMA_COUNTERS) > before:
                schema_failures.append(f"{series_id}/{chunk_id}: record-level schema failures")

    # Supplementary chunks (e.g. pilot) must agree with historical records on every overlapping date
    supplementary_mismatches: List[str] = []
    for chunk_id, entry in sorted(manifest_chunks.items()):
        if chunk_id in expected_ids:
            continue
        ep = entry["endpoint"]
        path = raw_dir / series_id / f"{chunk_id}.json"
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != entry.get("sha256"):
            checksum_failures.append(f"{series_id}/{chunk_id}")
            continue
        for rec in load_chunk_records(path):
            day = datetime.date.fromisoformat(rec["date"][:10])
            if records[ep].get(day) != rec:
                supplementary_mismatches.append(f"{series_id}/{chunk_id}: {day.isoformat()}")

    prices, quantities = records["prices"], records["quantities"]
    start = datetime.date.fromisoformat(start_date)
    end = datetime.date.fromisoformat(end_date)
    calendar = [start + datetime.timedelta(days=i) for i in range((end - start).days + 1)]
    missing_price = [d for d in calendar if d not in prices]
    missing_qty = [d for d in calendar if d not in quantities]
    price_gaps = find_gaps(missing_price)
    qty_gaps = find_gaps(missing_qty)

    common = set(prices) & set(quantities)
    union = set(prices) | set(quantities)

    # Statistics and bounds checks use only clean numeric values; bad values are already counted above
    clean_prices = {
        d: (lo, hi, mod) for d, r in prices.items()
        if None not in (lo := _numeric(r.get("min_price")), hi := _numeric(r.get("max_price")),
                        mod := _numeric(r.get("modal_price")))
    }
    below_min = sorted(d for d, (lo, hi, mod) in clean_prices.items() if mod < lo <= hi)
    above_max = sorted(d for d, (lo, hi, mod) in clean_prices.items() if lo <= hi < mod)
    modal = [mod for _, _, mod in clean_prices.values()]
    clean_qty = {d: q for d, r in quantities.items() if (q := _numeric(r.get("quantity"))) is not None}
    qty = list(clean_qty.values())

    return {
        "chunks_expected": len(expected_ids),
        "chunks_found": len(expected_ids) - len(missing_files),
        "supplementary_chunks": sorted(set(manifest_chunks) - expected_ids),
        "supplementary_mismatches": supplementary_mismatches,
        "missing_files": missing_files,
        "checksum_failures": checksum_failures,
        "schema_failures": schema_failures,
        "record_failure_counts": dict(sorted(counts.items())),
        "price_records_count": len(prices),
        "quantity_records_count": len(quantities),
        "duplicate_price_keys": duplicates["prices"],
        "duplicate_quantity_keys": duplicates["quantities"],
        "null_values": counts["null"],
        "numeric_violations": counts["non_numeric"] + counts["negative"] + counts["min_gt_max"],
        "modal_bounds_warnings": len(below_min) + len(above_max),
        "modal_below_min_count": len(below_min),
        "modal_above_max_count": len(above_max),
        "modal_below_min_by_year": dict(sorted(Counter(d.year for d in below_min).items())),
        "modal_bounds_first_last": (
            [min(below_min + above_max).isoformat(), max(below_min + above_max).isoformat()]
            if below_min or above_max else []
        ),
        "modal_above_max_dates": [d.isoformat() for d in above_max],
        "calendar_days": len(calendar),
        "missing_price_days": len(missing_price),
        "missing_quantity_days": len(missing_qty),
        "missing_price_days_by_year": dict(sorted(Counter(d.year for d in missing_price).items())),
        "price_gaps_count": len(price_gaps),
        "max_consecutive_price_gap": max((g[2] for g in price_gaps), default=0),
        "price_gap_length_histogram": dict(sorted(Counter(g[2] for g in price_gaps).items())),
        "price_gaps_summary": price_gaps,
        "quantity_gaps_count": len(qty_gaps),
        "max_consecutive_quantity_gap": max((g[2] for g in qty_gaps), default=0),
        "price_only_dates": sorted(d.isoformat() for d in set(prices) - set(quantities)),
        "quantity_only_dates": sorted(d.isoformat() for d in set(quantities) - set(prices)),
        "iou": len(common) / len(union) if union else 0.0,
        "match_rate": len(common) / len(prices) if prices else 0.0,
        "price_min": min(modal, default=None),
        "price_max": max(modal, default=None),
        "price_mean": sum(modal) / len(modal) if modal else None,
        "quantity_min": min(qty, default=None),
        "quantity_max": max(qty, default=None),
        "quantity_mean": sum(qty) / len(qty) if qty else None,
        "quantity_smallest_5": [[v, d.isoformat()] for v, d in sorted((q, d) for d, q in clean_qty.items())[:5]],
        "min_date": min(union).isoformat() if union else None,
        "max_date": max(union).isoformat() if union else None,
    }


def request_timing(manifest: Dict[str, Any], expected_ids_by_series: Dict[str, set]) -> Dict[str, Any]:
    """
    Spacing between historical chunk `fetched_at` timestamps. These are recorded after each
    response is saved, so they approximate (not equal) request send times.
    """
    stamps = sorted(
        datetime.datetime.fromisoformat(c["fetched_at"])
        for sid, ids in expected_ids_by_series.items()
        for c in manifest.get("series", {}).get(sid, {}).get("chunks", [])
        if c["chunk_id"] in ids
    )
    if len(stamps) < 2:
        return {"n": len(stamps)}
    gaps = [(b - a).total_seconds() for a, b in zip(stamps, stamps[1:])]
    hour = datetime.timedelta(hours=1)
    peak = max(sum(1 for t in stamps if s <= t < s + hour) for s in stamps)
    return {
        "n": len(stamps),
        "first": stamps[0].isoformat(),
        "last": stamps[-1].isoformat(),
        "spacing_min_seconds": min(gaps),
        "spacing_max_seconds": max(gaps),
        "max_in_any_rolling_hour": peak,
    }


def run_audit(
    manifest_path: Path = Path("data/raw/ceda_manifest.json"),
    raw_dir: Path = Path("data/raw/ceda"),
    start_date: str = "2016-01-01",
    end_date: str = "2022-12-31",
    chunk_months: int = 6,
    series_specs: List[Tuple[str, int, int]] = SERIES_SPECS,
) -> Dict[str, Any]:
    """Build the full audit report for all series."""
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    chunks = generate_date_chunks(start_date, end_date, chunk_months=chunk_months)

    series_metrics = {
        sid: audit_series(sid, c_id, s_id, manifest, raw_dir, chunks, start_date, end_date)
        for sid, c_id, s_id in series_specs
    }
    expected_ids = {sid: {f"{ep}_{a}_{b}" for ep in ENDPOINTS for a, b in chunks} for sid, _, _ in series_specs}

    def collect(key: str) -> List[str]:
        return [item for m in series_metrics.values() for item in m[key]]

    hard_failures = (
        collect("missing_files") + collect("checksum_failures") + collect("schema_failures")
        + collect("supplementary_mismatches")
        + [f"{sid}: {m['duplicate_price_keys'] + m['duplicate_quantity_keys']} duplicate keys"
           for sid, m in series_metrics.items() if m["duplicate_price_keys"] or m["duplicate_quantity_keys"]]
        + [f"{sid}: {m['null_values']} nulls" for sid, m in series_metrics.items() if m["null_values"]]
        + [f"{sid}: {m['numeric_violations']} numeric violations"
           for sid, m in series_metrics.items() if m["numeric_violations"]]
    )
    warnings = [
        f"{sid}: {m['modal_bounds_warnings']} records with modal_price outside [min_price, max_price]"
        for sid, m in series_metrics.items() if m["modal_bounds_warnings"]
    ]

    return {
        "audit_generator": "src.data.validate",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "window": {"start_date": start_date, "end_date": end_date, "chunk_months": chunk_months},
        "total_chunks_expected": sum(m["chunks_expected"] for m in series_metrics.values()),
        "total_chunks_found": sum(m["chunks_found"] for m in series_metrics.values()),
        "missing_files": collect("missing_files"),
        "checksum_failures": collect("checksum_failures"),
        "schema_failures": collect("schema_failures"),
        "passed": not hard_failures,
        "hard_failures": hard_failures,
        "warnings": warnings,
        "request_timing": request_timing(manifest, expected_ids),
        "series_metrics": series_metrics,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Offline CropCast M-2 raw data validation audit")
    parser.add_argument("--manifest", type=str, default="data/raw/ceda_manifest.json")
    parser.add_argument("--raw-dir", type=str, default="data/raw/ceda")
    parser.add_argument("--start-date", type=str, default="2016-01-01")
    parser.add_argument("--end-date", type=str, default="2022-12-31")
    parser.add_argument("--chunk-months", type=int, default=6)
    parser.add_argument("--output", type=str, default=None, help="Write the audit JSON to this path")
    args = parser.parse_args(argv)

    report = run_audit(
        manifest_path=Path(args.manifest),
        raw_dir=Path(args.raw_dir),
        start_date=args.start_date,
        end_date=args.end_date,
        chunk_months=args.chunk_months,
    )
    text = json.dumps(report, indent=2)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(".tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(out)
    print(text)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
