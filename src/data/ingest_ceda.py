"""
CropCast CEDA Ashoka Ingestion Pipeline
======================================
Acquires daily state-level wholesale price and arrival volume data from
the Centre for Economic Data and Analysis (CEDA) Agri-Market API.

Design Principles:
1. Security: Credentials read from local environment/`.env`; never printed or logged.
2. Compliance: Enforces <= 40 requests/hour; honors `Retry-After` on HTTP 429.
3. Resilience: Bounded chunking, checkpointed progress, safe resumption on interruption.
4. Integrity: Strict envelope, schema, data-type, and duplicate key validation.
5. Isolation: Raw data written strictly to git-ignored `data/raw/`.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import logging
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("cropcast.data.ingest_ceda")

# Approved candidate series mappings per DEC-015
APPROVED_COMMODITIES: Dict[str, int] = {
    "onion": 23,
    "potato": 24,
}
APPROVED_STATES: Dict[str, int] = {
    "maharashtra": 27,
    "uttar_pradesh": 9,
}

BASE_URL = "https://api.ceda.ashoka.edu.in/v1"
PRICES_ENDPOINT = f"{BASE_URL}/agmarknet/prices"
QUANTITIES_ENDPOINT = f"{BASE_URL}/agmarknet/quantities"

# Server enforces 40 req/hour (3600 seconds)
MIN_REQUEST_INTERVAL_SECONDS = 95.0  # Safe inter-request spacing guaranteeing <=37 req/hr


@dataclass
class CedaConfig:
    """Configuration for CEDA API ingestion."""
    commodity_id: int
    state_id: int
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD
    chunk_months: int = 6
    output_dir: Path = Path("data/raw/ceda")
    manifest_path: Path = Path("data/raw/ceda_manifest.json")
    rate_limit_delay: float = MIN_REQUEST_INTERVAL_SECONDS
    max_retries: int = 3
    timeout: float = 30.0
    wait_on_rate_limit: bool = True
    max_rate_limit_wait: float = 3600.0


@dataclass
class ValidationSummary:
    """Summary of data quality and validation checks."""
    series_id: str
    endpoint: str
    record_count: int
    unique_dates: int
    min_date: Optional[str]
    max_date: Optional[str]
    missing_dates_count: int
    duplicate_composite_keys: int
    null_value_count: int
    numeric_violations: int
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    price_mean: Optional[float] = None
    quantity_min: Optional[float] = None
    quantity_max: Optional[float] = None
    quantity_mean: Optional[float] = None
    modal_bounds_warnings: int = 0
    is_valid: bool = False
    validation_errors: List[str] = field(default_factory=list)
    # Non-fatal findings: reported but never affect `is_valid` (so they never trigger a re-fetch)
    warnings: List[str] = field(default_factory=list)


def load_api_key(env_path: Optional[Path] = None) -> str:
    """
    Safely load CEDA_API_KEY from environment or .env without printing credentials.
    """
    key = os.environ.get("CEDA_API_KEY", "").strip()
    if key:
        return key

    target_env = env_path or Path(".env")
    if target_env.exists():
        try:
            with open(target_env, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("CEDA_API_KEY="):
                        val = line.split("=", 1)[1].strip()
                        val = val.strip('"').strip("'")
                        if val:
                            return val
        except Exception as e:
            logger.error("Failed to read .env file: %s", str(e))

    raise ValueError(
        "CEDA_API_KEY not found in environment or .env file. "
        "Please provide the credential locally."
    )


def generate_date_chunks(start_date_str: str, end_date_str: str, chunk_months: int = 6) -> List[Tuple[str, str]]:
    """
    Split a date range into chronological chunks of at most `chunk_months`.
    Dates are formatted as YYYY-MM-DD.
    """
    start = datetime.date.fromisoformat(start_date_str)
    end = datetime.date.fromisoformat(end_date_str)

    if start > end:
        raise ValueError(f"start_date {start_date_str} is after end_date {end_date_str}")

    chunks: List[Tuple[str, str]] = []
    curr = start

    while curr <= end:
        # Approximate month addition: 30 days * chunk_months or advance to next milestone
        # Use calendar calculation for exact boundaries
        year = curr.year + (curr.month + chunk_months - 1) // 12
        month = (curr.month + chunk_months - 1) % 12 + 1
        # Try same day or last day of month
        import calendar
        _, last_day = calendar.monthrange(year, month)
        target_day = min(curr.day, last_day)
        next_chunk_end = datetime.date(year, month, target_day) - datetime.timedelta(days=1)

        chunk_end = min(next_chunk_end, end)
        chunks.append((curr.isoformat(), chunk_end.isoformat()))

        curr = chunk_end + datetime.timedelta(days=1)

    return chunks


class CedaIngestionPipeline:
    """
    Ingestion pipeline for CEDA Ashoka state-aggregate prices and quantities.
    """

    def __init__(self, config: CedaConfig, api_key: Optional[str] = None):
        self.config = config
        self._api_key = api_key or load_api_key()
        self._last_request_time: float = 0.0

        # Ensure directories exist
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        self.manifest = self._load_manifest()

    def _load_manifest(self) -> Dict[str, Any]:
        """Load or initialize the ingestion manifest."""
        if self.config.manifest_path.exists():
            try:
                with open(self.config.manifest_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning("Corrupt manifest found, backing up and recreating: %s", str(e))
        return {
            "manifest_version": "1.0",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "series": {},
        }

    def _save_manifest(self) -> None:
        """Atomically persist manifest to disk."""
        self.manifest["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.config.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.config.manifest_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(self.manifest, f, indent=2)
        temp_path.replace(self.config.manifest_path)

    def _throttle(self) -> None:
        """Enforce spacing between live network requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.config.rate_limit_delay:
            sleep_needed = self.config.rate_limit_delay - elapsed
            logger.info("Throttling request (spacing %.1fs to respect rate limit)...", sleep_needed)
            time.sleep(sleep_needed)

    def make_request(self, endpoint_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an authenticated POST request with rate limiting, Retry-After handling,
        envelope parsing, and bounded exponential backoff.
        Credentials are never logged.
        """
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
            "User-Agent": "CropCast-Research/1.0",
        }
        body = json.dumps(payload).encode("utf-8")

        rate_limit_resets = 0
        max_rate_limit_resets = 3
        attempt = 1

        while attempt <= self.config.max_retries:
            self._throttle()
            req = urllib.request.Request(endpoint_url, data=body, headers=headers, method="POST")

            try:
                self._last_request_time = time.time()
                with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
                    raw_bytes = resp.read()
                    data = json.loads(raw_bytes.decode("utf-8"))
                    return self._unpack_envelope(data)

            except urllib.error.HTTPError as e:
                # Check for rate limit 429
                if e.code == 429:
                    retry_after_str = e.headers.get("Retry-After") or e.headers.get("RateLimit-Reset")
                    retry_after = 60.0  # fallback
                    if retry_after_str:
                        try:
                            retry_after = float(retry_after_str)
                        except ValueError:
                            pass

                    logger.warning(
                        "HTTP 429 Too Many Requests received. Retry-After: %.1f seconds.",
                        retry_after
                    )

                    if self.config.wait_on_rate_limit and retry_after <= self.config.max_rate_limit_wait:
                        rate_limit_resets += 1
                        if rate_limit_resets > max_rate_limit_resets:
                            raise RuntimeError(
                                f"Exceeded maximum consecutive rate limit resets ({max_rate_limit_resets}). "
                                f"Execution paused to protect quota."
                            ) from e
                        logger.info(
                            "Waiting %.1f seconds for rate limit reset window (window %d/%d)...",
                            retry_after, rate_limit_resets, max_rate_limit_resets
                        )
                        time.sleep(retry_after + 2.0)  # Add 2s grace
                        # Do not increment attempt; re-try request cleanly after reset window
                        continue
                    else:
                        raise RuntimeError(
                            f"CEDA API rate limit exceeded (HTTP 429). Retry-After is {retry_after:.0f}s. "
                            f"Execution paused to protect quota."
                        ) from e

                # Check for server errors (5xx)
                if 500 <= e.code < 600:
                    backoff = (2 ** attempt) * 2.0
                    logger.warning(
                        "Server error HTTP %d on attempt %d/%d. Backing off for %.1fs...",
                        e.code, attempt, self.config.max_retries, backoff
                    )
                    time.sleep(backoff)
                    attempt += 1
                    continue

                # Client errors (400, 401, 403, 404)
                err_body = ""
                try:
                    err_body = e.read().decode("utf-8", errors="replace")[:200]
                except Exception:
                    pass
                raise RuntimeError(f"HTTPError {e.code}: {err_body}") from e

            except urllib.error.URLError as e:
                backoff = (2 ** attempt) * 2.0
                logger.warning("Network URLError on attempt %d: %s. Retrying in %.1fs...", attempt, str(e), backoff)
                time.sleep(backoff)
                attempt += 1
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to decode CEDA API response as JSON: {str(e)}") from e

        raise RuntimeError(f"Exceeded max retries ({self.config.max_retries}) for {endpoint_url}")

    @staticmethod
    def _unpack_envelope(response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and unpack CEDA's response envelope:
        Expected structure: `{"output": {"type": "success", "data": [...]}}`
        """
        if not isinstance(response_data, dict):
            raise ValueError(f"Unexpected response type: {type(response_data)}")

        output = response_data.get("output")
        if not isinstance(output, dict):
            raise ValueError(f"Missing 'output' dictionary in response envelope. Keys: {list(response_data.keys())}")

        resp_type = output.get("type")
        message = output.get("message", "")

        if resp_type != "success":
            # Some queries return 'error' with message 'No data found'
            if "no data" in message.lower() or "not found" in message.lower():
                return {"type": "empty", "message": message, "data": []}
            raise ValueError(f"API returned non-success response: type={resp_type}, message={message}")

        records = output.get("data")
        if not isinstance(records, list):
            raise ValueError(f"Expected 'data' to be a list in envelope, got {type(records)}")

        return {"type": "success", "message": message, "data": records}

    def validate_records(
        self,
        records: List[Dict[str, Any]],
        endpoint: str,
        series_id: str,
    ) -> ValidationSummary:
        """
        Perform rigorous schema, numeric, and duplicate key validation on records.
        """
        summary = ValidationSummary(
            series_id=series_id,
            endpoint=endpoint,
            record_count=len(records),
            unique_dates=0,
            min_date=None,
            max_date=None,
            missing_dates_count=0,
            duplicate_composite_keys=0,
            null_value_count=0,
            numeric_violations=0,
            validation_errors=[],
        )

        if not records:
            summary.is_valid = True
            return summary

        seen_keys: set[Tuple[str, int, int]] = set()
        dates: List[datetime.date] = []
        prices: List[float] = []
        quantities: List[float] = []

        required_price_fields = {"date", "commodity_id", "census_state_id", "min_price", "max_price", "modal_price"}
        required_qty_fields = {"date", "commodity_id", "census_state_id", "quantity"}

        for i, rec in enumerate(records):
            # Check nulls
            for k, v in rec.items():
                if v is None:
                    summary.null_value_count += 1
                    summary.validation_errors.append(f"Row {i}: Field '{k}' is null.")

            # Validate schema
            req_fields = required_price_fields if endpoint == "prices" else required_qty_fields
            missing_fields = req_fields - set(rec.keys())
            if missing_fields:
                summary.validation_errors.append(f"Row {i}: Missing required fields {missing_fields}")
                continue

            # Parse date
            raw_date = rec.get("date", "")
            clean_date_str = raw_date.split("T")[0] if "T" in str(raw_date) else str(raw_date)
            try:
                dt = datetime.date.fromisoformat(clean_date_str)
                dates.append(dt)
            except ValueError:
                summary.validation_errors.append(f"Row {i}: Invalid date format '{raw_date}'")

            # Check composite key
            c_id = rec.get("commodity_id")
            s_id = rec.get("census_state_id")
            key = (clean_date_str, c_id, s_id)
            if key in seen_keys:
                summary.duplicate_composite_keys += 1
                summary.validation_errors.append(f"Row {i}: Duplicate composite key {key}")
            seen_keys.add(key)

            # Commodity and state matching
            if c_id != self.config.commodity_id:
                summary.validation_errors.append(f"Row {i}: Commodity ID {c_id} != expected {self.config.commodity_id}")
            if s_id != self.config.state_id:
                summary.validation_errors.append(f"Row {i}: State ID {s_id} != expected {self.config.state_id}")

            # Numeric checks
            if endpoint == "prices":
                try:
                    min_p = float(rec["min_price"])
                    max_p = float(rec["max_price"])
                    mod_p = float(rec["modal_price"])

                    if min_p < 0 or max_p < 0 or mod_p < 0:
                        summary.numeric_violations += 1
                        summary.validation_errors.append(f"Row {i}: Negative price detected.")
                    if min_p > max_p:
                        summary.numeric_violations += 1
                        summary.validation_errors.append(f"Row {i}: min_price ({min_p}) > max_price ({max_p}).")
                    elif not (min_p <= mod_p <= max_p):
                        # Observed in source data (ISS-002); flagged, never dropped or corrected
                        summary.modal_bounds_warnings += 1
                        summary.warnings.append(
                            f"Row {i}: modal_price ({mod_p}) outside [min_price ({min_p}), max_price ({max_p})]."
                        )

                    prices.append(mod_p)
                except (ValueError, TypeError) as e:
                    summary.numeric_violations += 1
                    summary.validation_errors.append(f"Row {i}: Non-numeric price: {e}")

            elif endpoint == "quantities":
                try:
                    qty = float(rec["quantity"])
                    if qty < 0:
                        summary.numeric_violations += 1
                        summary.validation_errors.append(f"Row {i}: Negative arrival quantity ({qty}).")
                    quantities.append(qty)
                except (ValueError, TypeError) as e:
                    summary.numeric_violations += 1
                    summary.validation_errors.append(f"Row {i}: Non-numeric quantity: {e}")

        # Summary statistics
        if dates:
            unique_dts = sorted(set(dates))
            summary.unique_dates = len(unique_dts)
            summary.min_date = unique_dts[0].isoformat()
            summary.max_date = unique_dts[-1].isoformat()
            calendar_days = (unique_dts[-1] - unique_dts[0]).days + 1
            summary.missing_dates_count = max(0, calendar_days - len(unique_dts))

        if prices:
            summary.price_min = min(prices)
            summary.price_max = max(prices)
            summary.price_mean = sum(prices) / len(prices)

        if quantities:
            summary.quantity_min = min(quantities)
            summary.quantity_max = max(quantities)
            summary.quantity_mean = sum(quantities) / len(quantities)

        summary.is_valid = (
            summary.duplicate_composite_keys == 0
            and summary.numeric_violations == 0
            and len(summary.validation_errors) == 0
        )

        return summary

    def align_prices_and_quantities(
        self,
        price_records: List[Dict[str, Any]],
        quantity_records: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Verify alignment between price and quantity records on composite key
        `(date, commodity_id, census_state_id)`.
        """
        def make_key(rec: Dict[str, Any]) -> Tuple[str, int, int]:
            raw_date = rec.get("date", "")
            d_str = raw_date.split("T")[0] if "T" in str(raw_date) else str(raw_date)
            return (d_str, int(rec["commodity_id"]), int(rec["census_state_id"]))

        price_map = {make_key(r): r for r in price_records}
        qty_map = {make_key(r): r for r in quantity_records}

        common_keys = set(price_map.keys()) & set(qty_map.keys())
        price_only = set(price_map.keys()) - set(qty_map.keys())
        qty_only = set(qty_map.keys()) - set(price_map.keys())

        return {
            "total_price_records": len(price_records),
            "total_quantity_records": len(quantity_records),
            "aligned_records": len(common_keys),
            "price_only_dates": sorted([k[0] for k in price_only]),
            "quantity_only_dates": sorted([k[0] for k in qty_only]),
            "alignment_rate": len(common_keys) / max(1, len(price_records)),
        }

    def fetch_chunk(
        self,
        endpoint: str,
        from_date: str,
        to_date: str,
        series_id: str,
    ) -> Tuple[List[Dict[str, Any]], Path]:
        """
        Fetch a single chunk, validate it, save to disk, and update manifest.
        Resumes safely if already downloaded.
        """
        series_dir = self.config.output_dir / series_id
        series_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{endpoint}_{from_date}_{to_date}.json"
        target_path = series_dir / filename

        # Check manifest or existing file on disk
        series_meta = self.manifest["series"].setdefault(series_id, {"chunks": []})
        manifest_chunk = next(
            (c for c in series_meta["chunks"]
             if c["endpoint"] == endpoint and c["from_date"] == from_date and c["to_date"] == to_date),
            None
        )

        if target_path.exists():
            try:
                # 1. Check SHA-256 integrity against manifest if already recorded
                with open(target_path, "rb") as f:
                    file_sha256 = hashlib.sha256(f.read()).hexdigest()

                if manifest_chunk and manifest_chunk.get("status") == "completed":
                    expected_sha = manifest_chunk.get("sha256")
                    if expected_sha and file_sha256 != expected_sha:
                        logger.warning(
                            "Checksum mismatch for %s (found %s, expected %s). Re-fetching.",
                            filename, file_sha256[:8], expected_sha[:8]
                        )
                        raise ValueError(f"Checksum mismatch for {filename}")

                # 2. Parse JSON and validate schema
                with open(target_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                records = saved.get("data") if isinstance(saved, dict) and "data" in saved else saved
                if isinstance(records, list):
                    val = self.validate_records(records, endpoint, series_id)
                    if not val.is_valid:
                        logger.warning("Existing file %s failed schema validation. Re-fetching.", filename)
                        raise ValueError(f"Schema validation failed for {filename}")

                    logger.info("Found existing valid chunk %s on disk. Resuming from disk.", filename)
                    if manifest_chunk is None:
                        # Register in manifest
                        try:
                            stored_path = str(target_path.relative_to(Path.cwd()))
                        except ValueError:
                            stored_path = str(target_path)
                        chunk_entry = {
                            "chunk_id": f"{endpoint}_{from_date}_{to_date}",
                            "endpoint": endpoint,
                            "from_date": from_date,
                            "to_date": to_date,
                            "status": "completed",
                            "record_count": len(records),
                            "file_path": stored_path,
                            "sha256": file_sha256,
                            "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                            "is_valid": val.is_valid,
                        }
                        series_meta["chunks"].append(chunk_entry)
                        self._save_manifest()
                    return records, target_path
            except Exception as e:
                logger.warning("Existing file %s could not be loaded or validated (%s). Re-fetching.", filename, str(e))

        # Execute network call
        url = PRICES_ENDPOINT if endpoint == "prices" else QUANTITIES_ENDPOINT
        payload = {
            "commodity_id": self.config.commodity_id,
            "state_id": self.config.state_id,
            "from_date": from_date,
            "to_date": to_date,
        }

        logger.info(
            "Fetching %s for %s (%s to %s)...",
            endpoint, series_id, from_date, to_date
        )
        response = self.make_request(url, payload)
        records = response.get("data", [])

        # Validate schema
        val = self.validate_records(records, endpoint, series_id)
        if not val.is_valid:
            logger.warning("Validation warnings for %s: %s", filename, val.validation_errors[:5])

        # Save to disk atomically via temporary file
        content_to_save = {
            "metadata": {
                "series_id": series_id,
                "commodity_id": self.config.commodity_id,
                "state_id": self.config.state_id,
                "endpoint": endpoint,
                "from_date": from_date,
                "to_date": to_date,
                "record_count": len(records),
                "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "attribution": "CEDA Agri Market Data (CEDA-AMD), Centre for Economic Data & Analysis, Ashoka University",
            },
            "data": records,
        }

        raw_bytes = json.dumps(content_to_save, indent=2).encode("utf-8")
        file_sha256 = hashlib.sha256(raw_bytes).hexdigest()

        temp_target = target_path.with_suffix(".tmp")
        with open(temp_target, "wb") as f:
            f.write(raw_bytes)
        temp_target.replace(target_path)

        # Update manifest
        try:
            stored_path = str(target_path.relative_to(Path.cwd()))
        except ValueError:
            stored_path = str(target_path)

        chunk_entry = {
            "chunk_id": f"{endpoint}_{from_date}_{to_date}",
            "endpoint": endpoint,
            "from_date": from_date,
            "to_date": to_date,
            "status": "completed",
            "record_count": len(records),
            "file_path": stored_path,
            "sha256": file_sha256,
            "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "is_valid": val.is_valid,
        }

        # Replace or append chunk
        series_meta["chunks"] = [
            c for c in series_meta["chunks"]
            if not (c["endpoint"] == endpoint and c["from_date"] == from_date and c["to_date"] == to_date)
        ]
        series_meta["chunks"].append(chunk_entry)
        self._save_manifest()

        return records, target_path

    def run(self, series_id: str) -> Dict[str, Any]:
        """
        Run the ingestion pipeline for the configured series across all date chunks.
        """
        chunks = generate_date_chunks(
            self.config.start_date,
            self.config.end_date,
            chunk_months=self.config.chunk_months
        )
        logger.info(
            "Starting ingestion for %s: %d date chunks (%s to %s)",
            series_id, len(chunks), self.config.start_date, self.config.end_date
        )

        all_prices: List[Dict[str, Any]] = []
        all_quantities: List[Dict[str, Any]] = []

        for from_date, to_date in chunks:
            # 1. Prices
            price_recs, _ = self.fetch_chunk("prices", from_date, to_date, series_id)
            all_prices.extend(price_recs)

            # 2. Quantities
            qty_recs, _ = self.fetch_chunk("quantities", from_date, to_date, series_id)
            all_quantities.extend(qty_recs)

        # Full series validation
        price_val = self.validate_records(all_prices, "prices", series_id)
        qty_val = self.validate_records(all_quantities, "quantities", series_id)
        alignment = self.align_prices_and_quantities(all_prices, all_quantities)

        return {
            "series_id": series_id,
            "price_validation": asdict(price_val),
            "quantity_validation": asdict(qty_val),
            "alignment": alignment,
        }


def run_bounded_pilot(
    api_key: Optional[str] = None,
    output_dir: Path = Path("data/raw/ceda"),
    start_date: str = "2021-01-01",
    end_date: str = "2021-01-15",
) -> Dict[str, Any]:
    """
    Execute a bounded pilot ingestion run for the two approved candidate series:
    1. Maharashtra Onion (state_id=27, commodity_id=23)
    2. Uttar Pradesh Potato (state_id=9, commodity_id=24)
    """
    logger.info("Initializing Bounded Pilot for approved candidate series...")
    pilot_results = {}

    series_specs = [
        ("onion_maharashtra", APPROVED_COMMODITIES["onion"], APPROVED_STATES["maharashtra"]),
        ("potato_uttar_pradesh", APPROVED_COMMODITIES["potato"], APPROVED_STATES["uttar_pradesh"]),
    ]

    for series_id, c_id, s_id in series_specs:
        logger.info("Running pilot for %s (commodity=%d, state=%d)...", series_id, c_id, s_id)
        cfg = CedaConfig(
            commodity_id=c_id,
            state_id=s_id,
            start_date=start_date,
            end_date=end_date,
            chunk_months=1,
            output_dir=output_dir,
            rate_limit_delay=MIN_REQUEST_INTERVAL_SECONDS,
            wait_on_rate_limit=True,
        )
        pipeline = CedaIngestionPipeline(cfg, api_key=api_key)
        res = pipeline.run(series_id)
        pilot_results[series_id] = res

    # Save pilot validation report
    pilot_summary_path = output_dir.parent / "pilot_validation_summary.json"
    with open(pilot_summary_path, "w", encoding="utf-8") as f:
        json.dump(pilot_results, f, indent=2)

    logger.info("Pilot completed successfully. Summary saved to %s", pilot_summary_path)
    return pilot_results


def build_cli() -> argparse.ArgumentParser:
    """Build command line argument parser."""
    parser = argparse.ArgumentParser(
        description="CropCast CEDA Ashoka Ingestion Pipeline (Rate-throttled, Checkpointed)"
    )
    parser.add_argument("--commodity", type=str, default="onion", help="Commodity name (onion, potato) or integer ID")
    parser.add_argument("--state", type=str, default="maharashtra", help="State name (maharashtra, uttar_pradesh) or integer ID")
    parser.add_argument("--start-date", type=str, default="2021-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, default="2021-01-15", help="End date (YYYY-MM-DD)")
    parser.add_argument("--chunk-months", type=int, default=6, help="Chunk size in months")
    parser.add_argument("--pilot", action="store_true", help="Run bounded pilot on approved series")
    parser.add_argument("--all-approved", action="store_true", help="Ingest all approved series (Maharashtra Onion and Uttar Pradesh Potato)")
    parser.add_argument("--output-dir", type=str, default="data/raw/ceda", help="Output directory")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser


def main() -> None:
    parser = build_cli()
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    if args.pilot:
        print("Starting bounded pilot ingestion...")
        results = run_bounded_pilot(
            output_dir=Path(args.output_dir),
            start_date=args.start_date,
            end_date=args.end_date,
        )
        print("\n=== PILOT INGESTION SUMMARY ===")
        print(json.dumps(results, indent=2))
        return

    if args.all_approved:
        logger.info("Executing extraction for all approved series (%s to %s)...", args.start_date, args.end_date)
        all_results = {}
        last_req_time = 0.0

        for series_id, c_id, s_id in [
            ("onion_maharashtra", APPROVED_COMMODITIES["onion"], APPROVED_STATES["maharashtra"]),
            ("potato_uttar_pradesh", APPROVED_COMMODITIES["potato"], APPROVED_STATES["uttar_pradesh"]),
        ]:
            logger.info("Starting ingestion for approved series: %s (commodity=%d, state=%d)", series_id, c_id, s_id)
            cfg = CedaConfig(
                commodity_id=c_id,
                state_id=s_id,
                start_date=args.start_date,
                end_date=args.end_date,
                chunk_months=args.chunk_months,
                output_dir=Path(args.output_dir),
                rate_limit_delay=MIN_REQUEST_INTERVAL_SECONDS,
                wait_on_rate_limit=True,
            )
            pipeline = CedaIngestionPipeline(cfg)
            pipeline._last_request_time = last_req_time
            res = pipeline.run(series_id)
            last_req_time = pipeline._last_request_time
            all_results[series_id] = res

        summary_path = Path(args.output_dir).parent / "historical_extraction_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2)
        print("\n=== HISTORICAL EXTRACTION SUMMARY ===")
        print(json.dumps(all_results, indent=2))
        return

    # Single series ingestion
    comm_val = args.commodity.lower()
    c_id = APPROVED_COMMODITIES.get(comm_val, int(comm_val) if comm_val.isdigit() else None)
    if c_id is None:
        sys.exit(f"Invalid commodity: {args.commodity}")

    state_val = args.state.lower()
    s_id = APPROVED_STATES.get(state_val, int(state_val) if state_val.isdigit() else None)
    if s_id is None:
        sys.exit(f"Invalid state: {args.state}")

    series_id = f"{args.commodity}_{args.state}".lower()
    cfg = CedaConfig(
        commodity_id=c_id,
        state_id=s_id,
        start_date=args.start_date,
        end_date=args.end_date,
        chunk_months=args.chunk_months,
        output_dir=Path(args.output_dir),
    )

    pipeline = CedaIngestionPipeline(cfg)
    summary = pipeline.run(series_id)
    print("\n=== INGESTION SUMMARY ===")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
