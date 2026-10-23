"""
Unit tests for CropCast CEDA ingestion pipeline (`src.data.ingest_ceda`).
"""

import datetime
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.data.ingest_ceda import (
    CedaConfig,
    CedaIngestionPipeline,
    ValidationSummary,
    generate_date_chunks,
)


class TestDateChunking(unittest.TestCase):
    def test_single_short_chunk(self):
        chunks = generate_date_chunks("2021-01-01", "2021-01-15", chunk_months=1)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], ("2021-01-01", "2021-01-15"))

    def test_multi_month_chunks(self):
        chunks = generate_date_chunks("2021-01-01", "2021-12-31", chunk_months=6)
        self.assertGreaterEqual(len(chunks), 2)
        self.assertEqual(chunks[0][0], "2021-01-01")
        self.assertEqual(chunks[-1][1], "2021-12-31")

    def test_invalid_date_order(self):
        with self.assertRaises(ValueError):
            generate_date_chunks("2021-12-31", "2021-01-01")


class TestEnvelopeUnpacking(unittest.TestCase):
    def test_unpack_success(self):
        envelope = {
            "output": {
                "type": "success",
                "message": "Data exists",
                "data": [{"date": "2021-01-01", "modal_price": 2000.0}]
            }
        }
        res = CedaIngestionPipeline._unpack_envelope(envelope)
        self.assertEqual(res["type"], "success")
        self.assertEqual(len(res["data"]), 1)

    def test_unpack_empty(self):
        envelope = {
            "output": {
                "type": "error",
                "message": "No data found",
                "data": []
            }
        }
        res = CedaIngestionPipeline._unpack_envelope(envelope)
        self.assertEqual(res["type"], "empty")
        self.assertEqual(len(res["data"]), 0)

    def test_unpack_malformed(self):
        with self.assertRaises(ValueError):
            CedaIngestionPipeline._unpack_envelope({"wrong_key": 123})


class TestRecordValidation(unittest.TestCase):
    def setUp(self):
        self.config = CedaConfig(
            commodity_id=23,
            state_id=27,
            start_date="2021-01-01",
            end_date="2021-01-15",
            output_dir=Path(tempfile.mkdtemp()),
            manifest_path=Path(tempfile.mktemp(suffix=".json")),
        )
        self.pipeline = CedaIngestionPipeline(self.config, api_key="dummy_test_token")

    def test_valid_price_records(self):
        records = [
            {
                "date": "2021-01-01T00:00:00.000Z",
                "commodity_id": 23,
                "census_state_id": 27,
                "min_price": 1000.0,
                "max_price": 2000.0,
                "modal_price": 1500.0,
            },
            {
                "date": "2021-01-02T00:00:00.000Z",
                "commodity_id": 23,
                "census_state_id": 27,
                "min_price": 1100.0,
                "max_price": 2100.0,
                "modal_price": 1600.0,
            },
        ]
        summary = self.pipeline.validate_records(records, "prices", "test_series")
        self.assertTrue(summary.is_valid)
        self.assertEqual(summary.record_count, 2)
        self.assertEqual(summary.duplicate_composite_keys, 0)
        self.assertEqual(summary.price_min, 1500.0)
        self.assertEqual(summary.price_max, 1600.0)

    def test_duplicate_composite_key(self):
        records = [
            {
                "date": "2021-01-01T00:00:00.000Z",
                "commodity_id": 23,
                "census_state_id": 27,
                "min_price": 1000.0,
                "max_price": 2000.0,
                "modal_price": 1500.0,
            },
            {
                "date": "2021-01-01T00:00:00.000Z",
                "commodity_id": 23,
                "census_state_id": 27,
                "min_price": 1050.0,
                "max_price": 2050.0,
                "modal_price": 1550.0,
            },
        ]
        summary = self.pipeline.validate_records(records, "prices", "test_series")
        self.assertFalse(summary.is_valid)
        self.assertEqual(summary.duplicate_composite_keys, 1)

    def test_numeric_violation_min_greater_than_max(self):
        records = [
            {
                "date": "2021-01-01T00:00:00.000Z",
                "commodity_id": 23,
                "census_state_id": 27,
                "min_price": 3000.0,
                "max_price": 2000.0,
                "modal_price": 2500.0,
            }
        ]
        summary = self.pipeline.validate_records(records, "prices", "test_series")
        self.assertFalse(summary.is_valid)
        self.assertGreater(summary.numeric_violations, 0)

    def test_modal_outside_bounds_is_warning_not_error(self):
        records = [
            {
                "date": "2021-01-01T00:00:00.000Z",
                "commodity_id": 23,
                "census_state_id": 27,
                "min_price": 1000.0,
                "max_price": 2000.0,
                "modal_price": 950.0,
            },
            {
                "date": "2021-01-02T00:00:00.000Z",
                "commodity_id": 23,
                "census_state_id": 27,
                "min_price": 1000.0,
                "max_price": 2000.0,
                "modal_price": 2100.0,
            },
        ]
        summary = self.pipeline.validate_records(records, "prices", "test_series")
        self.assertTrue(summary.is_valid)
        self.assertEqual(summary.numeric_violations, 0)
        self.assertEqual(summary.modal_bounds_warnings, 2)
        self.assertEqual(len(summary.warnings), 2)
        self.assertEqual(summary.validation_errors, [])

    def test_valid_quantity_records(self):
        records = [
            {
                "date": "2021-01-01T00:00:00.000Z",
                "commodity_id": 23,
                "census_state_id": 27,
                "quantity": 12500.5,
            }
        ]
        summary = self.pipeline.validate_records(records, "quantities", "test_series")
        self.assertTrue(summary.is_valid)
        self.assertEqual(summary.quantity_min, 12500.5)

    def test_negative_quantity(self):
        records = [
            {
                "date": "2021-01-01T00:00:00.000Z",
                "commodity_id": 23,
                "census_state_id": 27,
                "quantity": -50.0,
            }
        ]
        summary = self.pipeline.validate_records(records, "quantities", "test_series")
        self.assertFalse(summary.is_valid)
        self.assertGreater(summary.numeric_violations, 0)


class TestAlignment(unittest.TestCase):
    def test_price_quantity_alignment(self):
        pipeline = CedaIngestionPipeline(
            CedaConfig(
                commodity_id=23,
                state_id=27,
                start_date="2021-01-01",
                end_date="2021-01-03",
                output_dir=Path(tempfile.mkdtemp()),
                manifest_path=Path(tempfile.mktemp(suffix=".json")),
            ),
            api_key="dummy",
        )
        prices = [
            {"date": "2021-01-01", "commodity_id": 23, "census_state_id": 27, "modal_price": 100},
            {"date": "2021-01-02", "commodity_id": 23, "census_state_id": 27, "modal_price": 110},
        ]
        quantities = [
            {"date": "2021-01-01", "commodity_id": 23, "census_state_id": 27, "quantity": 500},
            {"date": "2021-01-03", "commodity_id": 23, "census_state_id": 27, "quantity": 600},
        ]
        res = pipeline.align_prices_and_quantities(prices, quantities)
        self.assertEqual(res["total_price_records"], 2)
        self.assertEqual(res["total_quantity_records"], 2)
        self.assertEqual(res["aligned_records"], 1)
        self.assertEqual(res["price_only_dates"], ["2021-01-02"])
        self.assertEqual(res["quantity_only_dates"], ["2021-01-03"])


class TestManifestCheckpointing(unittest.TestCase):
    def test_manifest_resumes_without_redownload(self):
        temp_dir = Path(tempfile.mkdtemp())
        manifest_file = temp_dir / "manifest.json"

        config = CedaConfig(
            commodity_id=23,
            state_id=27,
            start_date="2021-01-01",
            end_date="2021-01-05",
            output_dir=temp_dir / "ceda",
            manifest_path=manifest_file,
        )
        pipeline = CedaIngestionPipeline(config, api_key="dummy")

        mock_data = [
            {
                "date": "2021-01-01T00:00:00.000Z",
                "commodity_id": 23,
                "census_state_id": 27,
                "min_price": 1000.0,
                "max_price": 2000.0,
                "modal_price": 1500.0,
            }
        ]
        pipeline.make_request = MagicMock(return_value={"type": "success", "data": mock_data})

        # Fetch chunk first time
        recs1, path1 = pipeline.fetch_chunk("prices", "2021-01-01", "2021-01-05", "test_series")
        self.assertEqual(len(recs1), 1)
        self.assertEqual(pipeline.make_request.call_count, 1)
        self.assertTrue(path1.exists())

        # Second fetch: should read from disk, not call make_request again
        pipeline.make_request.reset_mock()
        recs2, path2 = pipeline.fetch_chunk("prices", "2021-01-01", "2021-01-05", "test_series")
        self.assertEqual(len(recs2), 1)
        self.assertEqual(pipeline.make_request.call_count, 0)
        self.assertEqual(path1, path2)

    def test_modal_bounds_warning_does_not_trigger_refetch(self):
        temp_dir = Path(tempfile.mkdtemp())
        config = CedaConfig(
            commodity_id=24,
            state_id=9,
            start_date="2016-03-01",
            end_date="2016-03-05",
            output_dir=temp_dir / "ceda",
            manifest_path=temp_dir / "manifest.json",
        )
        pipeline = CedaIngestionPipeline(config, api_key="dummy")
        mock_data = [
            {
                "date": "2016-03-04T00:00:00.000Z",
                "commodity_id": 24,
                "census_state_id": 9,
                "min_price": 600.0,
                "max_price": 700.0,
                "modal_price": 590.0,
            }
        ]
        pipeline.make_request = MagicMock(return_value={"type": "success", "data": mock_data})
        pipeline.fetch_chunk("prices", "2016-03-01", "2016-03-05", "test_series")

        pipeline.make_request.reset_mock()
        recs, _ = pipeline.fetch_chunk("prices", "2016-03-01", "2016-03-05", "test_series")
        self.assertEqual(pipeline.make_request.call_count, 0)
        self.assertEqual(recs, mock_data)


class TestCheckpointIntegrity(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.manifest_file = self.temp_dir / "manifest.json"
        self.config = CedaConfig(
            commodity_id=23,
            state_id=27,
            start_date="2021-01-01",
            end_date="2021-01-05",
            output_dir=self.temp_dir / "ceda",
            manifest_path=self.manifest_file,
        )
        self.mock_data = [
            {
                "date": "2021-01-01T00:00:00.000Z",
                "commodity_id": 23,
                "census_state_id": 27,
                "min_price": 1000.0,
                "max_price": 2000.0,
                "modal_price": 1500.0,
            }
        ]

    def test_missing_raw_file_triggers_refetch(self):
        pipeline = CedaIngestionPipeline(self.config, api_key="dummy")
        pipeline.make_request = MagicMock(return_value={"type": "success", "data": self.mock_data})

        # 1. Fetch chunk
        recs1, path1 = pipeline.fetch_chunk("prices", "2021-01-01", "2021-01-05", "test_series")
        self.assertEqual(pipeline.make_request.call_count, 1)

        # 2. Delete raw file on disk (simulating missing file while manifest still has record)
        path1.unlink()
        self.assertFalse(path1.exists())

        # 3. Next fetch: must detect missing file and re-fetch via network
        pipeline.make_request.reset_mock()
        recs2, path2 = pipeline.fetch_chunk("prices", "2021-01-01", "2021-01-05", "test_series")
        self.assertEqual(pipeline.make_request.call_count, 1)
        self.assertTrue(path2.exists())

    def test_truncated_raw_file_triggers_refetch(self):
        pipeline = CedaIngestionPipeline(self.config, api_key="dummy")
        pipeline.make_request = MagicMock(return_value={"type": "success", "data": self.mock_data})

        # 1. Fetch chunk
        _, path1 = pipeline.fetch_chunk("prices", "2021-01-01", "2021-01-05", "test_series")

        # 2. Corrupt / truncate raw file
        with open(path1, "w", encoding="utf-8") as f:
            f.write('{"data": [corrupted json...')

        # 3. Next fetch: must catch decode error and re-fetch via network
        pipeline.make_request.reset_mock()
        recs2, path2 = pipeline.fetch_chunk("prices", "2021-01-01", "2021-01-05", "test_series")
        self.assertEqual(pipeline.make_request.call_count, 1)
        self.assertEqual(len(recs2), 1)

    def test_mismatched_checksum_triggers_refetch(self):
        pipeline = CedaIngestionPipeline(self.config, api_key="dummy")
        pipeline.make_request = MagicMock(return_value={"type": "success", "data": self.mock_data})

        # 1. Fetch chunk
        _, path1 = pipeline.fetch_chunk("prices", "2021-01-01", "2021-01-05", "test_series")

        # 2. Tamper with file contents (valid JSON but different content/sha256)
        with open(path1, "w", encoding="utf-8") as f:
            json.dump({"data": [{"date": "2021-01-02", "commodity_id": 23, "census_state_id": 27, "modal_price": 999.0}]}, f)

        # 3. Next fetch: must detect checksum mismatch against manifest and re-fetch
        pipeline.make_request.reset_mock()
        recs2, path2 = pipeline.fetch_chunk("prices", "2021-01-01", "2021-01-05", "test_series")
        self.assertEqual(pipeline.make_request.call_count, 1)

    def test_corrupt_manifest_recovery(self):
        # Write corrupted manifest JSON
        with open(self.manifest_file, "w", encoding="utf-8") as f:
            f.write("{manifest_corrupt: false...")

        # Pipeline init should not crash; it should back up / recreate clean manifest
        pipeline = CedaIngestionPipeline(self.config, api_key="dummy")
        self.assertEqual(pipeline.manifest["manifest_version"], "1.0")
        backups = list(self.temp_dir.glob("manifest.corrupt-*.json"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(encoding="utf-8"), "{manifest_corrupt: false...")

    def test_empty_response_marked_empty_and_not_refetched(self):
        pipeline = CedaIngestionPipeline(self.config, api_key="dummy")
        pipeline.make_request = MagicMock(return_value={"type": "empty", "message": "No data found", "data": []})

        recs, path = pipeline.fetch_chunk("prices", "2021-01-01", "2021-01-05", "test_series")
        entry = pipeline.manifest["series"]["test_series"]["chunks"][0]
        self.assertEqual(recs, [])
        self.assertTrue(path.exists())
        self.assertEqual(entry["status"], "empty")
        self.assertEqual(entry["record_count"], 0)

        # Rerun resumes from disk and keeps the 'empty' status visible
        pipeline.make_request.reset_mock()
        pipeline.fetch_chunk("prices", "2021-01-01", "2021-01-05", "test_series")
        self.assertEqual(pipeline.make_request.call_count, 0)
        self.assertEqual(pipeline.manifest["series"]["test_series"]["chunks"][0]["status"], "empty")

    def test_checksum_verified_source_violation_not_refetched(self):
        pipeline = CedaIngestionPipeline(self.config, api_key="dummy")
        bad = [dict(self.mock_data[0], min_price=3000.0, max_price=2000.0)]
        pipeline.make_request = MagicMock(return_value={"type": "success", "data": bad})

        _, path = pipeline.fetch_chunk("prices", "2021-01-01", "2021-01-05", "test_series")
        original = path.read_bytes()
        self.assertFalse(pipeline.manifest["series"]["test_series"]["chunks"][0]["is_valid"])

        pipeline.make_request.reset_mock()
        recs, _ = pipeline.fetch_chunk("prices", "2021-01-01", "2021-01-05", "test_series")
        self.assertEqual(pipeline.make_request.call_count, 0)
        self.assertEqual(recs, bad)
        self.assertEqual(path.read_bytes(), original)

    def test_unregistered_invalid_file_is_refetched(self):
        # A file with no manifest entry cannot be checksum-verified, so invalid content is re-fetched
        pipeline = CedaIngestionPipeline(self.config, api_key="dummy")
        path = self.config.output_dir / "test_series" / "prices_2021-01-01_2021-01-05.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        bad = [dict(self.mock_data[0], min_price=3000.0, max_price=2000.0)]
        path.write_text(json.dumps({"data": bad}), encoding="utf-8")

        pipeline.make_request = MagicMock(return_value={"type": "success", "data": self.mock_data})
        recs, _ = pipeline.fetch_chunk("prices", "2021-01-01", "2021-01-05", "test_series")
        self.assertEqual(pipeline.make_request.call_count, 1)
        self.assertEqual(recs, self.mock_data)


class TestRateLimitingAndRetries(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = CedaConfig(
            commodity_id=23,
            state_id=27,
            start_date="2021-01-01",
            end_date="2021-01-05",
            output_dir=self.temp_dir / "ceda",
            manifest_path=self.temp_dir / "manifest.json",
            rate_limit_delay=0.1,  # Fast for test
            wait_on_rate_limit=True,
            max_rate_limit_wait=300.0,
        )
        self.pipeline = CedaIngestionPipeline(self.config, api_key="dummy")

    @patch("time.sleep")
    @patch("urllib.request.urlopen")
    def test_http_429_retry_after_wait_and_succeed(self, mock_urlopen, mock_sleep):
        # 1st call: raises HTTPError 429 with Retry-After: 45
        # 2nd call: returns HTTP 200 with data
        import urllib.error
        from http.client import HTTPMessage

        headers_429 = HTTPMessage()
        headers_429.add_header("Retry-After", "45")
        err_429 = urllib.error.HTTPError(
            url="http://mock", code=429, msg="Too Many Requests", hdrs=headers_429, fp=None
        )

        mock_resp_success = MagicMock()
        mock_resp_success.read.return_value = json.dumps({
            "output": {"type": "success", "message": "OK", "data": [{"date": "2021-01-01"}]}
        }).encode("utf-8")
        mock_resp_success.__enter__.return_value = mock_resp_success

        mock_urlopen.side_effect = [err_429, mock_resp_success]

        res = self.pipeline.make_request("http://mock", {"dummy": 1})
        self.assertEqual(res["type"], "success")
        self.assertEqual(mock_urlopen.call_count, 2)
        # Verify sleep was called with retry_after + grace (45 + 2 = 47)
        mock_sleep.assert_any_call(47.0)

    @patch("urllib.request.urlopen")
    def test_http_429_no_wait_raises_runtime_error(self, mock_urlopen):
        self.pipeline.config.wait_on_rate_limit = False
        import urllib.error
        from http.client import HTTPMessage

        headers_429 = HTTPMessage()
        headers_429.add_header("Retry-After", "120")
        err_429 = urllib.error.HTTPError(
            url="http://mock", code=429, msg="Too Many Requests", hdrs=headers_429, fp=None
        )
        mock_urlopen.side_effect = err_429

        with self.assertRaises(RuntimeError) as ctx:
            self.pipeline.make_request("http://mock", {})
        self.assertIn("120s", str(ctx.exception))
        self.assertIn("rate limit exceeded", str(ctx.exception).lower())

    @patch("time.sleep")
    @patch("urllib.request.urlopen")
    def test_http_500_exponential_backoff_and_retry(self, mock_urlopen, mock_sleep):
        import urllib.error
        from http.client import HTTPMessage

        headers_500 = HTTPMessage()
        err_500 = urllib.error.HTTPError(url="http://mock", code=500, msg="Server Error", hdrs=headers_500, fp=None)

        mock_resp_success = MagicMock()
        mock_resp_success.read.return_value = json.dumps({
            "output": {"type": "success", "message": "OK", "data": []}
        }).encode("utf-8")
        mock_resp_success.__enter__.return_value = mock_resp_success

        mock_urlopen.side_effect = [err_500, mock_resp_success]

        res = self.pipeline.make_request("http://mock", {})
        self.assertEqual(res["type"], "success")
        self.assertEqual(mock_urlopen.call_count, 2)
        # First retry backs off (2 ** 1) * 2.0 = 4.0 seconds
        mock_sleep.assert_any_call(4.0)

    @patch("time.sleep")
    @patch("urllib.request.urlopen")
    def test_read_timeout_is_retried(self, mock_urlopen, mock_sleep):
        mock_resp_success = MagicMock()
        mock_resp_success.read.return_value = json.dumps({
            "output": {"type": "success", "message": "OK", "data": []}
        }).encode("utf-8")
        mock_resp_success.__enter__.return_value = mock_resp_success

        mock_urlopen.side_effect = [TimeoutError("The read operation timed out"), mock_resp_success]

        res = self.pipeline.make_request("http://mock", {})
        self.assertEqual(res["type"], "success")
        self.assertEqual(mock_urlopen.call_count, 2)
        mock_sleep.assert_any_call(4.0)

    @patch("time.sleep")
    @patch("urllib.request.urlopen")
    def test_persistent_timeouts_exhaust_retries(self, mock_urlopen, mock_sleep):
        mock_urlopen.side_effect = TimeoutError("The read operation timed out")
        with self.assertRaises(RuntimeError):
            self.pipeline.make_request("http://mock", {})
        self.assertEqual(mock_urlopen.call_count, self.config.max_retries)

    @patch("time.sleep")
    @patch("urllib.request.urlopen")
    def test_interrupted_run_resumes_only_pending_chunks(self, mock_urlopen, mock_sleep):
        # Configure a 2-chunk run
        self.config.start_date = "2021-01-01"
        self.config.end_date = "2021-02-28"
        self.config.chunk_months = 1
        pipeline = CedaIngestionPipeline(self.config, api_key="dummy")

        mock_resp_price = MagicMock()
        mock_resp_price.read.return_value = json.dumps({
            "output": {"type": "success", "message": "OK", "data": [
                {"date": "2021-01-01T00:00:00.000Z", "commodity_id": 23, "census_state_id": 27,
                 "min_price": 1000.0, "max_price": 2000.0, "modal_price": 1500.0}
            ]}
        }).encode("utf-8")
        mock_resp_price.__enter__.return_value = mock_resp_price

        mock_resp_qty = MagicMock()
        mock_resp_qty.read.return_value = json.dumps({
            "output": {"type": "success", "message": "OK", "data": [
                {"date": "2021-01-01T00:00:00.000Z", "commodity_id": 23, "census_state_id": 27,
                 "quantity": 5000.0}
            ]}
        }).encode("utf-8")
        mock_resp_qty.__enter__.return_value = mock_resp_qty

        import urllib.error
        from http.client import HTTPMessage
        headers_500 = HTTPMessage()
        err_500 = urllib.error.HTTPError(url="http://mock", code=500, msg="Server Error", hdrs=headers_500, fp=None)

        # 1st run: prices chunk 1 succeeds, quantities chunk 1 succeeds, prices chunk 2 fails 3 times
        mock_urlopen.side_effect = [
            mock_resp_price, mock_resp_qty,       # chunk 1 prices & quantities
            err_500, err_500, err_500             # chunk 2 prices fails on 3 retries
        ]

        with self.assertRaises(RuntimeError):
            pipeline.run("test_series")

        # Verify Chunk 1 is saved in manifest
        series_meta = pipeline.manifest["series"].get("test_series", {})
        self.assertEqual(len(series_meta.get("chunks", [])), 2)  # chunk 1 prices & quantities completed

        # Now resume: create a new pipeline instance (simulating restart)
        pipeline_resumed = CedaIngestionPipeline(self.config, api_key="dummy")
        # On resume, chunk 1 loads from disk. Only chunk 2 prices & quantities need network calls:
        mock_urlopen.reset_mock()
        mock_urlopen.side_effect = [mock_resp_price, mock_resp_qty]

        summary = pipeline_resumed.run("test_series")

        # Chunk 1 was read from disk without network calls;
        # exactly 2 network calls made (chunk 2 prices + chunk 2 quantities)
        self.assertEqual(mock_urlopen.call_count, 2)
        self.assertEqual(len(pipeline_resumed.manifest["series"]["test_series"]["chunks"]), 4)

    def test_api_explicit_error_message_raises_value_error(self):
        envelope = {
            "output": {
                "type": "error",
                "message": "Invalid commodity ID specified",
                "data": []
            }
        }
        with self.assertRaises(ValueError) as ctx:
            CedaIngestionPipeline._unpack_envelope(envelope)
        self.assertIn("Invalid commodity ID", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
