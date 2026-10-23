"""
Unit tests for the offline CropCast M-2 validation audit (`src.data.validate`).
All fixtures are synthetic; no real CEDA data or network access is used.
"""

import contextlib
import datetime
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from src.data.validate import find_gaps, load_chunk_records, main, run_audit

SERIES = [("test_series", 23, 27)]
START, END = "2021-01-01", "2021-02-28"
CHUNKS = [("2021-01-01", "2021-01-31"), ("2021-02-01", "2021-02-28")]


def price_rec(day, min_p=1000.0, max_p=2000.0, modal=1500.0):
    return {
        "date": f"{day}T00:00:00.000Z",
        "commodity_id": 23,
        "census_state_id": 27,
        "min_price": min_p,
        "max_price": max_p,
        "modal_price": modal,
    }


def qty_rec(day, qty=5000.0):
    return {"date": f"{day}T00:00:00.000Z", "commodity_id": 23, "census_state_id": 27, "quantity": qty}


def days(a, b):
    start, end = datetime.date.fromisoformat(a), datetime.date.fromisoformat(b)
    return [(start + datetime.timedelta(i)).isoformat() for i in range((end - start).days + 1)]


class AuditFixture(unittest.TestCase):
    """Builds a temporary manifest and raw chunk tree with complete, clean data."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.raw_dir = self.root / "ceda"
        self.manifest_path = self.root / "manifest.json"
        self.manifest = {"manifest_version": "1.0", "series": {"test_series": {"chunks": []}}}
        self.chunk_records = {}
        for a, b in CHUNKS:
            self.chunk_records[f"prices_{a}_{b}"] = [price_rec(d) for d in days(a, b)]
            self.chunk_records[f"quantities_{a}_{b}"] = [qty_rec(d) for d in days(a, b)]
        for chunk_id, recs in self.chunk_records.items():
            self.write_chunk(chunk_id, recs)

    def write_chunk(self, chunk_id, recs, envelope=True, minutes=None):
        endpoint, from_date, to_date = chunk_id.split("_")
        path = self.raw_dir / "test_series" / f"{chunk_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        doc = {"metadata": {"endpoint": endpoint}, "data": recs} if envelope else recs
        raw = json.dumps(doc, indent=2).encode("utf-8")
        path.write_bytes(raw)
        chunks = self.manifest["series"]["test_series"]["chunks"]
        chunks[:] = [c for c in chunks if c["chunk_id"] != chunk_id]
        offset = len(chunks) * 2 if minutes is None else minutes
        chunks.append({
            "chunk_id": chunk_id,
            "endpoint": endpoint,
            "from_date": from_date,
            "to_date": to_date,
            "status": "completed",
            "record_count": len(recs),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "fetched_at": (datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
                           + datetime.timedelta(minutes=offset)).isoformat(),
            "is_valid": True,
        })
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        return path

    def audit(self):
        return run_audit(
            manifest_path=self.manifest_path,
            raw_dir=self.raw_dir,
            start_date=START,
            end_date=END,
            chunk_months=1,
            series_specs=SERIES,
        )


class TestCleanAudit(AuditFixture):
    def test_clean_data_passes(self):
        report = self.audit()
        m = report["series_metrics"]["test_series"]
        self.assertTrue(report["passed"])
        self.assertEqual(report["hard_failures"], [])
        self.assertEqual(report["warnings"], [])
        self.assertEqual(report["total_chunks_expected"], 4)
        self.assertEqual(report["total_chunks_found"], 4)
        self.assertEqual(m["price_records_count"], 59)
        self.assertEqual(m["missing_price_days"], 0)
        self.assertEqual(m["iou"], 1.0)
        self.assertEqual(m["match_rate"], 1.0)

    def test_request_timing_from_manifest(self):
        timing = self.audit()["request_timing"]
        self.assertEqual(timing["n"], 4)
        self.assertEqual(timing["spacing_min_seconds"], 120.0)
        self.assertEqual(timing["max_in_any_rolling_hour"], 4)


class TestIntegrityFailures(AuditFixture):
    def test_missing_file_fails(self):
        (self.raw_dir / "test_series" / "quantities_2021-02-01_2021-02-28.json").unlink()
        report = self.audit()
        self.assertFalse(report["passed"])
        self.assertEqual(report["total_chunks_found"], 3)
        self.assertEqual(report["missing_files"], ["test_series/quantities_2021-02-01_2021-02-28"])

    def test_checksum_mismatch_fails(self):
        path = self.raw_dir / "test_series" / "prices_2021-01-01_2021-01-31.json"
        path.write_text(path.read_text(encoding="utf-8") + " ", encoding="utf-8")
        report = self.audit()
        self.assertFalse(report["passed"])
        self.assertEqual(report["checksum_failures"], ["test_series/prices_2021-01-01_2021-01-31"])

    def test_wrong_key_set_is_schema_failure(self):
        recs = self.chunk_records["prices_2021-01-01_2021-01-31"]
        recs[0]["extra_field"] = 1
        self.write_chunk("prices_2021-01-01_2021-01-31", recs)
        report = self.audit()
        self.assertFalse(report["passed"])
        self.assertEqual(len(report["schema_failures"]), 1)

    def test_date_outside_chunk_is_schema_failure(self):
        recs = self.chunk_records["prices_2021-01-01_2021-01-31"]
        recs[-1] = price_rec("2021-02-01")
        self.write_chunk("prices_2021-01-01_2021-01-31", recs)
        report = self.audit()
        counts = report["series_metrics"]["test_series"]["record_failure_counts"]
        self.assertFalse(report["passed"])
        self.assertEqual(counts["date_outside_chunk"], 1)


class TestRecordChecks(AuditFixture):
    def test_min_greater_than_max_is_hard_failure(self):
        recs = self.chunk_records["prices_2021-01-01_2021-01-31"]
        recs[0] = price_rec("2021-01-01", min_p=2500.0, max_p=2000.0)
        self.write_chunk("prices_2021-01-01_2021-01-31", recs)
        report = self.audit()
        m = report["series_metrics"]["test_series"]
        self.assertFalse(report["passed"])
        self.assertEqual(m["numeric_violations"], 1)
        self.assertEqual(m["modal_bounds_warnings"], 0)

    def test_null_and_negative_values_fail(self):
        recs = self.chunk_records["quantities_2021-01-01_2021-01-31"]
        recs[0]["quantity"] = None
        recs[1]["quantity"] = -1.0
        self.write_chunk("quantities_2021-01-01_2021-01-31", recs)
        m = self.audit()["series_metrics"]["test_series"]
        self.assertEqual(m["null_values"], 1)
        self.assertEqual(m["numeric_violations"], 1)

    def test_modal_outside_bounds_is_warning_only(self):
        recs = self.chunk_records["prices_2021-01-01_2021-01-31"]
        recs[2] = price_rec("2021-01-03", modal=900.0)
        recs[5] = price_rec("2021-01-06", modal=2100.0)
        self.write_chunk("prices_2021-01-01_2021-01-31", recs)
        report = self.audit()
        m = report["series_metrics"]["test_series"]
        self.assertTrue(report["passed"])
        self.assertEqual(len(report["warnings"]), 1)
        self.assertEqual(m["modal_below_min_count"], 1)
        self.assertEqual(m["modal_above_max_count"], 1)
        self.assertEqual(m["modal_above_max_dates"], ["2021-01-06"])
        self.assertEqual(m["modal_bounds_first_last"], ["2021-01-03", "2021-01-06"])

    def test_duplicate_date_across_chunks_fails(self):
        recs = self.chunk_records["prices_2021-02-01_2021-02-28"]
        recs.append(price_rec("2021-02-28"))
        self.write_chunk("prices_2021-02-01_2021-02-28", recs)
        report = self.audit()
        self.assertFalse(report["passed"])
        self.assertEqual(report["series_metrics"]["test_series"]["duplicate_price_keys"], 1)


class TestCoverageAndAlignment(AuditFixture):
    def test_missing_dates_produce_gaps_and_misalignment(self):
        drop = {"2021-01-10", "2021-01-11", "2021-01-20"}
        recs = [r for r in self.chunk_records["prices_2021-01-01_2021-01-31"] if r["date"][:10] not in drop]
        self.write_chunk("prices_2021-01-01_2021-01-31", recs)
        report = self.audit()
        m = report["series_metrics"]["test_series"]
        self.assertTrue(report["passed"])
        self.assertEqual(m["missing_price_days"], 3)
        self.assertEqual(m["price_gaps_count"], 2)
        self.assertEqual(m["max_consecutive_price_gap"], 2)
        self.assertEqual(m["price_gap_length_histogram"], {1: 1, 2: 1})
        self.assertEqual(m["quantity_only_dates"], sorted(drop))
        self.assertAlmostEqual(m["iou"], 56 / 59)

    def test_find_gaps_groups_consecutive_runs(self):
        d = datetime.date
        gaps = find_gaps([d(2020, 4, 8), d(2020, 4, 9), d(2020, 4, 20)])
        self.assertEqual(gaps, [("2020-04-08", "2020-04-09", 2), ("2020-04-20", "2020-04-20", 1)])


class TestSupplementaryChunks(AuditFixture):
    def test_identical_bare_list_pilot_chunk_passes(self):
        pilot = self.chunk_records["prices_2021-01-01_2021-01-31"][:15]
        self.write_chunk("prices_2021-01-01_2021-01-15", pilot, envelope=False)
        report = self.audit()
        m = report["series_metrics"]["test_series"]
        self.assertTrue(report["passed"])
        self.assertEqual(m["supplementary_chunks"], ["prices_2021-01-01_2021-01-15"])
        self.assertEqual(m["supplementary_mismatches"], [])
        self.assertEqual(m["price_records_count"], 59)

    def test_disagreeing_pilot_chunk_fails(self):
        pilot = [price_rec("2021-01-01", modal=1499.0)]
        self.write_chunk("prices_2021-01-01_2021-01-15", pilot, envelope=False)
        report = self.audit()
        self.assertFalse(report["passed"])
        self.assertEqual(
            report["series_metrics"]["test_series"]["supplementary_mismatches"],
            ["test_series/prices_2021-01-01_2021-01-15: 2021-01-01"],
        )

    def test_load_chunk_records_accepts_both_formats(self):
        path = self.raw_dir / "list.json"
        path.write_text(json.dumps([qty_rec("2021-01-01")]), encoding="utf-8")
        self.assertEqual(len(load_chunk_records(path)), 1)
        path.write_text(json.dumps({"metadata": {}, "data": [qty_rec("2021-01-01")]}), encoding="utf-8")
        self.assertEqual(len(load_chunk_records(path)), 1)


class TestCli(AuditFixture):
    def run_cli(self):
        out = self.root / "audit.json"
        with contextlib.redirect_stdout(io.StringIO()):
            code = main([
                "--manifest", str(self.manifest_path),
                "--raw-dir", str(self.raw_dir),
                "--start-date", START,
                "--end-date", END,
                "--chunk-months", "1",
                "--output", str(out),
            ])
        return code, out

    def test_cli_writes_report_and_exit_code(self):
        # The CLI audits the real approved series IDs, which are absent from this fixture
        code, out = self.run_cli()
        self.assertEqual(code, 1)
        report = json.loads(out.read_text(encoding="utf-8"))
        self.assertFalse(report["passed"])
        self.assertEqual(report["total_chunks_found"], 0)
        self.assertEqual(report["audit_generator"], "src.data.validate")


if __name__ == "__main__":
    unittest.main()
