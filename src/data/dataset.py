"""
CropCast analysis dataset assembly and freeze.

Builds one row per (series, observed market day) from the authoritative
historical CEDA chunks only (pilot chunks are excluded, ISS-005), joins prices
and arrivals on (date, commodity_id, census_state_id), and writes a versioned
CSV plus a metadata file recording construction rules and checksums.

Rules (Req 3):
- Schema is validated; missing required columns raise SchemaError.
- Exact duplicates are counted and dropped; conflicting duplicates raise
  ConflictingDuplicatesError with full details (never resolved automatically).
- Missing market days are reported, never imputed.
- Source values are never modified; data-quality concerns are flag columns.

Usage:
    python -m src.data.dataset
"""

from __future__ import annotations

import datetime
import hashlib
import json
import logging
import statistics
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

from src.config import load_config, resolve_path
from src.data.ingest_ceda import generate_date_chunks
from src.data.validate import load_chunk_records

logger = logging.getLogger("cropcast.data.dataset")

REQUIRED_COLUMNS = ("date", "commodity", "market", "modal_price")
OUTPUT_COLUMNS = [
    "series_id", "commodity", "state", "market", "commodity_id", "census_state_id", "date",
    "min_price", "max_price", "modal_price", "arrival_qty",
    "flag_modal_outside_bounds", "flag_extreme_arrival",
]
UNITS = {
    "min_price": "INR per quintal",
    "max_price": "INR per quintal",
    "modal_price": "INR per quintal",
    "arrival_qty": "tonnes",
}


class SchemaError(ValueError):
    """Raised when required columns are missing."""

    def __init__(self, missing: List[str]):
        self.missing = missing
        super().__init__(f"Missing required columns: {missing}")


class ConflictingDuplicatesError(ValueError):
    """Raised when rows share a key but differ in values; requires a researcher decision."""

    def __init__(self, groups: pd.DataFrame):
        self.groups = groups
        super().__init__(f"{groups.groupby(['series_id', 'date']).ngroups} conflicting duplicate key groups:\n"
                         f"{groups.to_string(index=False)}")


def validate_schema(df: pd.DataFrame, required: Tuple[str, ...] = REQUIRED_COLUMNS) -> None:
    """Raise SchemaError listing every required column that is absent."""
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise SchemaError(missing)


def drop_exact_duplicates(df: pd.DataFrame, key: List[str]) -> Tuple[pd.DataFrame, int]:
    """
    Drop rows that duplicate another row in every column. Raise if any rows share
    `key` while differing elsewhere. Returns the de-duplicated frame and the drop count.
    """
    if df.empty:
        raise ValueError("drop_exact_duplicates received an empty DataFrame")
    deduped = df.drop_duplicates()
    dropped = len(df) - len(deduped)
    conflicting = deduped[deduped.duplicated(subset=key, keep=False)]
    if not conflicting.empty:
        raise ConflictingDuplicatesError(conflicting.sort_values(key))
    if dropped:
        logger.info("Dropped %d exact duplicate rows", dropped)
    return deduped.reset_index(drop=True), dropped


def missing_report(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    """Per-series count and percentage of calendar days without a modal price (Req 3.4)."""
    if df.empty:
        raise ValueError("missing_report received an empty DataFrame")
    days = (pd.Timestamp(end) - pd.Timestamp(start)).days + 1
    rows = []
    for (sid, commodity, market), g in df.groupby(["series_id", "commodity", "market"]):
        observed = g["modal_price"].notna().sum()
        rows.append({
            "series_id": sid, "commodity": commodity, "market": market, "calendar_days": days,
            "observed_days": int(observed), "missing_days": int(days - observed),
            "missing_pct": round(100 * (days - observed) / days, 3),
        })
    return pd.DataFrame(rows)


def _read_endpoint(raw_dir: Path, manifest: Dict[str, Any], series_id: str, endpoint: str,
                   chunks: List[Tuple[str, str]]) -> Tuple[pd.DataFrame, List[Dict[str, str]]]:
    """Read the expected historical chunks for one endpoint, verifying each checksum."""
    entries = {c["chunk_id"]: c for c in manifest["series"][series_id]["chunks"]}
    frames, sources = [], []
    for a, b in chunks:
        chunk_id = f"{endpoint}_{a}_{b}"
        path = raw_dir / series_id / f"{chunk_id}.json"
        entry = entries.get(chunk_id)
        if entry is None or entry.get("status") != "completed":
            raise ValueError(f"{series_id}/{chunk_id}: not a completed manifest entry")
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        if sha != entry["sha256"]:
            raise ValueError(f"{series_id}/{chunk_id}: checksum mismatch")
        frames.append(pd.DataFrame(load_chunk_records(path)))
        sources.append({"chunk_id": chunk_id, "sha256": sha})
    return pd.concat(frames, ignore_index=True), sources


def build_dataset(cfg: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Assemble the analysis dataset and its provenance record."""
    ds = cfg["dataset"]
    raw_dir = resolve_path(cfg["paths"]["raw_dir"])
    manifest_path = resolve_path(cfg["paths"]["manifest"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    chunks = generate_date_chunks(ds["start_date"], ds["end_date"], chunk_months=ds["chunk_months"])

    frames, provenance = [], {}
    for series_id, spec in ds["series"].items():
        prices, price_src = _read_endpoint(raw_dir, manifest, series_id, "prices", chunks)
        qty, qty_src = _read_endpoint(raw_dir, manifest, series_id, "quantities", chunks)
        for part in (prices, qty):
            if not ((part["commodity_id"] == spec["commodity_id"]).all()
                    and (part["census_state_id"] == spec["census_state_id"]).all()):
                raise ValueError(f"{series_id}: unexpected commodity/state IDs in source records")
            part["date"] = pd.to_datetime(part["date"].str[:10], format="%Y-%m-%d", errors="raise")
        key = ["date", "commodity_id", "census_state_id"]
        merged = prices.merge(qty.rename(columns={"quantity": "arrival_qty"}), on=key, how="outer",
                              validate="one_to_one", indicator=True)
        unmatched = int((merged["_merge"] != "both").sum())
        merged = merged.drop(columns="_merge")
        merged["series_id"] = series_id
        merged["commodity"] = spec["commodity"]
        merged["state"] = spec["state"]
        merged["market"] = f"{spec['state']} (state aggregate)"
        frames.append(merged)
        provenance[series_id] = {"price_chunks": price_src, "quantity_chunks": qty_src,
                                 "unmatched_price_quantity_dates": unmatched}

    df = pd.concat(frames, ignore_index=True)
    validate_schema(df)
    for col in ("min_price", "max_price", "modal_price", "arrival_qty"):
        df[col] = df[col].astype("float64")
    df, exact_dropped = drop_exact_duplicates(df, ["series_id", "date"])

    # Flags only: values are never altered or removed
    df["flag_modal_outside_bounds"] = ~df["modal_price"].between(df["min_price"], df["max_price"])
    factor = ds["extreme_value_factor"]
    medians = df.groupby("series_id")["arrival_qty"].transform("median")
    df["flag_extreme_arrival"] = (df["arrival_qty"] < medians / factor) | (df["arrival_qty"] > medians * factor)

    df = df.sort_values(["series_id", "date"]).reset_index(drop=True)[OUTPUT_COLUMNS]
    miss = missing_report(df, ds["start_date"], ds["end_date"])
    meta = {
        "dataset_version": ds["version"],
        "construction_rules": [
            "Only the 14 six-month historical chunks per series and endpoint are read; pilot chunks are excluded (ISS-005).",
            "Each chunk must be a 'completed' manifest entry whose SHA-256 matches the file.",
            "Prices and arrivals are joined one-to-one on (date, commodity_id, census_state_id).",
            "Exact duplicate rows are dropped and counted; conflicting duplicates halt the build.",
            "Missing market days are not imputed; rows exist only for observed days.",
            "No source value is modified. flag_modal_outside_bounds marks modal_price outside [min_price, max_price] (ISS-002); "
            f"flag_extreme_arrival marks arrival_qty below 1/{factor:g} or above {factor:g}x the series median (ISS-003).",
        ],
        "units": UNITS,
        "units_note": "Units follow CEDA/Agmarknet conventions recorded in RES-008; the API payload carries no unit fields.",
        "attribution": cfg["attribution"],
        "window": {"start_date": ds["start_date"], "end_date": ds["end_date"]},
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "source_chunks": provenance,
        "rows": int(len(df)),
        "rows_by_series": {k: int(v) for k, v in df.groupby("series_id").size().items()},
        "exact_duplicates_dropped": int(exact_dropped),
        "missing_report": miss.to_dict(orient="records"),
        "flag_counts": {
            sid: {"flag_modal_outside_bounds": int(g["flag_modal_outside_bounds"].sum()),
                  "flag_extreme_arrival": int(g["flag_extreme_arrival"].sum())}
            for sid, g in df.groupby("series_id")
        },
        "limitations": [
            "State-level aggregates: one market per commodity, so peer-market features and signals are unavailable.",
            "CEDA's state aggregation method is not documented publicly (README returned HTTP 404 on 2026-10-23); cause of ISS-002 unknown.",
            "Raw and processed data are not redistributed; rebuild requires CEDA API access.",
        ],
    }
    return df, meta


def write_dataset(df: pd.DataFrame, meta: Dict[str, Any], out_dir: Path, version: str) -> Tuple[Path, Path]:
    """Write the CSV deterministically and the metadata including the CSV's SHA-256."""
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"cropcast_analysis_{version}.csv"
    out = df.copy()
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    # Default float formatting is shortest round-trip repr: lossless and deterministic
    csv_bytes = out.to_csv(index=False, lineterminator="\n").encode("utf-8")
    csv_path.write_bytes(csv_bytes)
    meta = dict(meta, csv_file=csv_path.name, csv_sha256=hashlib.sha256(csv_bytes).hexdigest(),
                built_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
    meta_path = out_dir / f"cropcast_analysis_{version}.meta.json"
    meta_path.write_text(json.dumps(meta, indent=2, default=str) + "\n", encoding="utf-8")
    return csv_path, meta_path


def load_dataset(cfg: Dict[str, Any], verify: bool = True) -> pd.DataFrame:
    """Load the frozen dataset, checking its SHA-256 against the metadata file."""
    out_dir = resolve_path(cfg["paths"]["processed_dir"])
    version = cfg["dataset"]["version"]
    csv_path = out_dir / f"cropcast_analysis_{version}.csv"
    if verify:
        meta = json.loads((out_dir / f"cropcast_analysis_{version}.meta.json").read_text(encoding="utf-8"))
        if hashlib.sha256(csv_path.read_bytes()).hexdigest() != meta["csv_sha256"]:
            raise ValueError(f"{csv_path.name} does not match its recorded checksum; rebuild the dataset")
    df = pd.read_csv(csv_path, parse_dates=["date"])
    if df.empty:
        raise ValueError(f"{csv_path.name} is empty")
    return df


def dataset_version_id(cfg: Dict[str, Any]) -> str:
    """Version identifier used in experiment hashes: '<version>:<first 12 hex of CSV SHA-256>'."""
    out_dir = resolve_path(cfg["paths"]["processed_dir"])
    version = cfg["dataset"]["version"]
    meta = json.loads((out_dir / f"cropcast_analysis_{version}.meta.json").read_text(encoding="utf-8"))
    return f"{version}:{meta['csv_sha256'][:12]}"


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    cfg = load_config()
    df, meta = build_dataset(cfg)
    csv_path, meta_path = write_dataset(df, meta, resolve_path(cfg["paths"]["processed_dir"]), cfg["dataset"]["version"])
    print(f"Wrote {csv_path} ({len(df)} rows) and {meta_path}")
    print(json.dumps({k: meta[k] for k in ("rows_by_series", "exact_duplicates_dropped", "flag_counts")}, indent=2))
    print(pd.DataFrame(meta["missing_report"]).to_string(index=False))


if __name__ == "__main__":
    main()
