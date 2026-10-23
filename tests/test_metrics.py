"""
Tests for evaluation metrics (Req 9.4) and experiment provenance (Req 10).
"""

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from src.evaluation.metrics import diebold_mariano, mae, mape, mase, precision_recall_f1, rmse
from src.experiment import IncompleteConfigError, append_run, config_hash, require_keys
from src.forecasting.run import check_config


class TestForecastMetrics(unittest.TestCase):
    actual = [100.0, 200.0, 300.0, 400.0]
    forecast = [110.0, 190.0, 330.0, 400.0]

    def test_mae(self):
        self.assertAlmostEqual(mae(self.actual, self.forecast), (10 + 10 + 30 + 0) / 4)

    def test_rmse(self):
        self.assertAlmostEqual(rmse(self.actual, self.forecast), np.sqrt((100 + 100 + 900 + 0) / 4))

    def test_mape_and_note(self):
        value, note = mape(self.actual, self.forecast)
        self.assertAlmostEqual(value, 100 * (0.1 + 0.05 + 0.1 + 0.0) / 4)
        self.assertIn("no zero", note)

    def test_mape_near_zero_flagged(self):
        value, note = mape([0.0, 100.0], [5.0, 110.0])
        self.assertAlmostEqual(value, 10.0)
        self.assertIn("1 actual values are zero", note)

    def test_mase(self):
        self.assertAlmostEqual(mase(self.actual, self.forecast, 25.0), 12.5 / 25.0)
        with self.assertRaises(ValueError):
            mase(self.actual, self.forecast, 0.0)

    def test_empty_and_mismatch_raise(self):
        with self.assertRaises(ValueError):
            mae([], [])
        with self.assertRaises(ValueError):
            rmse([1.0], [1.0, 2.0])


class TestDieboldMariano(unittest.TestCase):
    def test_hand_computed_statistic(self):
        e1 = np.array([1.0, -2.0, 1.0, -1.0, 2.0])
        e2 = np.array([2.0, -2.0, 3.0, -1.0, 3.0])
        d = np.abs(e1) - np.abs(e2)  # [-1, 0, -2, 0, -1]
        n = 5
        var = np.mean((d - d.mean()) ** 2) / n
        expected = d.mean() / np.sqrt(var) * np.sqrt((n + 1 - 2) / n)
        res = diebold_mariano(e1, e2)
        self.assertAlmostEqual(res["dm_stat"], expected)
        self.assertLess(res["dm_stat"], 0)

    def test_identical_errors_give_nan(self):
        e = np.array([1.0, 2.0, 3.0])
        self.assertTrue(np.isnan(diebold_mariano(e, e)["dm_stat"]))

    def test_clear_difference_is_significant(self):
        rng = np.random.default_rng(0)
        e_good = rng.normal(0, 1, 400)
        e_bad = rng.normal(0, 3, 400)
        self.assertLess(diebold_mariano(e_good, e_bad)["p_value"], 0.001)


class TestDetectionMetrics(unittest.TestCase):
    def test_precision_recall_f1(self):
        res = precision_recall_f1([1, 1, 0, 0, 1], [1, 0, 1, 0, 1])
        self.assertEqual((res["tp"], res["fp"], res["fn"]), (2, 1, 1))
        self.assertAlmostEqual(res["precision"], 2 / 3)
        self.assertAlmostEqual(res["recall"], 2 / 3)
        self.assertAlmostEqual(res["f1"], 2 / 3)

    def test_no_predictions(self):
        res = precision_recall_f1([1, 0], [0, 0])
        self.assertTrue(np.isnan(res["precision"]))
        self.assertEqual(res["recall"], 0.0)
        self.assertEqual(res["f1"], 0.0)


class TestProvenance(unittest.TestCase):
    def test_hash_is_deterministic_and_sensitive(self):
        a = config_hash("v1:abc", 1, {"lags": [1, 2]}, {"m": {"depth": 3}})
        self.assertEqual(a, config_hash("v1:abc", 1, {"lags": [1, 2]}, {"m": {"depth": 3}}))
        self.assertNotEqual(a, config_hash("v1:abc", 2, {"lags": [1, 2]}, {"m": {"depth": 3}}))
        self.assertNotEqual(a, config_hash("v1:abc", 1, {"lags": [1, 2]}, {"m": {"depth": 4}}))

    def test_append_run_writes_jsonl(self):
        path = Path(tempfile.mkdtemp()) / "log.jsonl"
        append_run(path, {"config_hash": "x", "metrics": {"mae": 1.0}})
        append_run(path, {"config_hash": "y"})
        lines = path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(json.loads(lines[0])["config_hash"], "x")

    def test_incomplete_config_refused(self):
        with self.assertRaises(IncompleteConfigError):
            require_keys({"a": 1}, ["a", "b"], "test")
        with self.assertRaises(IncompleteConfigError):
            check_config({"protocol_version": "1.1"})


if __name__ == "__main__":
    unittest.main()
