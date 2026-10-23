"""
Unit tests for analysis dataset assembly (`src.data.dataset`). Synthetic fixtures only.
"""

import json
import unittest

import pandas as pd

import test_validate as tv
from src.data.dataset import (
    REQUIRED_COLUMNS,
    ConflictingDuplicatesError,
    SchemaError,
    build_dataset,
    drop_exact_duplicates,
    missing_report,
    validate_schema,
)


def frame(rows):
    return pd.DataFrame(rows, columns=["series_id", "date", "commodity", "market", "modal_price"])


class TestSchemaValidation(unittest.TestCase):
    def test_valid_schema_passes(self):
        validate_schema(frame([["s", "2021-01-01", "Onion", "M", 1.0]]))

    def test_each_missing_required_column_raises(self):
        base = frame([["s", "2021-01-01", "Onion", "M", 1.0]])
        for col in REQUIRED_COLUMNS:
            with self.subTest(col=col):
                with self.assertRaises(SchemaError) as ctx:
                    validate_schema(base.drop(columns=col))
                self.assertEqual(ctx.exception.missing, [col])


class TestDuplicates(unittest.TestCase):
    def test_exact_duplicates_dropped_and_counted(self):
        df = frame([["s", "2021-01-01", "Onion", "M", 1.0], ["s", "2021-01-01", "Onion", "M", 1.0],
                    ["s", "2021-01-02", "Onion", "M", 2.0]])
        out, dropped = drop_exact_duplicates(df, ["series_id", "date"])
        self.assertEqual(dropped, 1)
        self.assertEqual(len(out), 2)
        self.assertLessEqual(len(out), len(df))  # Req 9.7: cleaning never adds rows

    def test_conflicting_duplicates_halt_with_details(self):
        df = frame([["s", "2021-01-01", "Onion", "M", 1.0], ["s", "2021-01-01", "Onion", "M", 9.0]])
        with self.assertRaises(ConflictingDuplicatesError) as ctx:
            drop_exact_duplicates(df, ["series_id", "date"])
        self.assertEqual(len(ctx.exception.groups), 2)
        self.assertEqual(sorted(ctx.exception.groups["modal_price"]), [1.0, 9.0])

    def test_empty_frame_raises(self):
        with self.assertRaises(ValueError):
            drop_exact_duplicates(frame([]), ["series_id", "date"])


class TestMissingReport(unittest.TestCase):
    def test_counts_and_percentage(self):
        df = frame([["s", pd.Timestamp("2021-01-01"), "Onion", "M", 1.0],
                    ["s", pd.Timestamp("2021-01-03"), "Onion", "M", 2.0]])
        rep = missing_report(df, "2021-01-01", "2021-01-04")
        self.assertEqual(rep.loc[0, "observed_days"], 2)
        self.assertEqual(rep.loc[0, "missing_days"], 2)
        self.assertEqual(rep.loc[0, "missing_pct"], 50.0)

    def test_empty_frame_raises(self):
        with self.assertRaises(ValueError):
            missing_report(frame([]), "2021-01-01", "2021-01-02")


class TestBuildDataset(tv.AuditFixture):
    def config(self):
        return {
            "paths": {"raw_dir": str(self.raw_dir), "manifest": str(self.manifest_path)},
            "dataset": {
                "version": "test", "start_date": tv.START, "end_date": tv.END, "chunk_months": 1,
                "extreme_value_factor": 100.0,
                "series": {"test_series": {"commodity": "Onion", "state": "Testland",
                                           "commodity_id": 23, "census_state_id": 27}},
            },
            "attribution": "test",
        }

    def test_builds_one_row_per_observed_day_with_exact_values(self):
        df, meta = build_dataset(self.config())
        self.assertEqual(len(df), 59)
        self.assertEqual(meta["missing_report"][0]["missing_days"], 0)
        first = df.iloc[0]
        self.assertEqual(first["date"], pd.Timestamp("2021-01-01"))
        self.assertEqual(first["modal_price"], 1500.0)
        self.assertEqual(first["arrival_qty"], 5000.0)
        self.assertFalse(df["flag_modal_outside_bounds"].any())

    def test_pilot_chunk_is_excluded(self):
        pilot = [tv.price_rec(d, modal=1.0) for d in tv.days("2021-01-01", "2021-01-15")]
        self.write_chunk("prices_2021-01-01_2021-01-15", pilot, envelope=False)
        df, _ = build_dataset(self.config())
        self.assertEqual(len(df), 59)
        self.assertNotIn(1.0, set(df["modal_price"]))

    def test_flags_mark_but_do_not_change_values(self):
        recs = self.chunk_records["prices_2021-01-01_2021-01-31"]
        recs[0] = tv.price_rec("2021-01-01", modal=900.0)
        self.write_chunk("prices_2021-01-01_2021-01-31", recs)
        qrecs = self.chunk_records["quantities_2021-01-01_2021-01-31"]
        qrecs[1]["quantity"] = 2.0
        self.write_chunk("quantities_2021-01-01_2021-01-31", qrecs)
        df, meta = build_dataset(self.config())
        row0, row1 = df.iloc[0], df.iloc[1]
        self.assertTrue(row0["flag_modal_outside_bounds"])
        self.assertEqual(row0["modal_price"], 900.0)
        self.assertTrue(row1["flag_extreme_arrival"])
        self.assertEqual(row1["arrival_qty"], 2.0)
        self.assertEqual(meta["flag_counts"]["test_series"],
                         {"flag_modal_outside_bounds": 1, "flag_extreme_arrival": 1})

    def test_missing_days_reported_not_imputed(self):
        recs = [r for r in self.chunk_records["prices_2021-01-01_2021-01-31"] if r["date"][:10] != "2021-01-10"]
        self.write_chunk("prices_2021-01-01_2021-01-31", recs)
        qrecs = [r for r in self.chunk_records["quantities_2021-01-01_2021-01-31"] if r["date"][:10] != "2021-01-10"]
        self.write_chunk("quantities_2021-01-01_2021-01-31", qrecs)
        df, meta = build_dataset(self.config())
        self.assertEqual(len(df), 58)
        self.assertNotIn(pd.Timestamp("2021-01-10"), set(df["date"]))
        self.assertEqual(meta["missing_report"][0]["missing_days"], 1)

    def test_checksum_mismatch_raises(self):
        path = self.raw_dir / "test_series" / "prices_2021-01-01_2021-01-31.json"
        path.write_text(path.read_text(encoding="utf-8") + " ", encoding="utf-8")
        with self.assertRaises(ValueError):
            build_dataset(self.config())

    def test_non_completed_manifest_entry_raises(self):
        for c in self.manifest["series"]["test_series"]["chunks"]:
            c["status"] = "empty"
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        with self.assertRaises(ValueError):
            build_dataset(self.config())


if __name__ == "__main__":
    unittest.main()
