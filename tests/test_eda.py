"""
Unit tests for EDA helpers (`src.analysis.eda`) with hand-computed expectations.
"""

import unittest

import numpy as np
import pandas as pd

from src.analysis.eda import block_bootstrap_corr, decomposition_model, describe, gap_table, market_day_log_returns


class TestDescribe(unittest.TestCase):
    def test_known_values(self):
        d = describe(pd.Series([1.0, 2.0, 3.0, 4.0, 5.0]))
        self.assertEqual(d["n"], 5)
        self.assertEqual(d["mean"], 3.0)
        self.assertEqual(d["median"], 3.0)
        self.assertAlmostEqual(d["std"], np.sqrt(2.5))
        self.assertEqual(d["q25"], 2.0)
        self.assertEqual(d["q75"], 4.0)
        self.assertAlmostEqual(d["cv"], np.sqrt(2.5) / 3.0)
        self.assertAlmostEqual(d["skewness"], 0.0)

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            describe(pd.Series([], dtype=float))


class TestGapsAndReturns(unittest.TestCase):
    def test_gap_runs(self):
        dates = pd.to_datetime(["2021-01-01", "2021-01-02", "2021-01-05", "2021-01-07"])
        gaps = gap_table(pd.Series(dates), "2021-01-01", "2021-01-08")
        self.assertEqual(gaps["days"].tolist(), [2, 1, 1])
        self.assertEqual(str(gaps.loc[0, "first_missing"]), "2021-01-03")

    def test_returns_are_between_consecutive_market_days(self):
        g = pd.DataFrame({"date": pd.to_datetime(["2021-01-01", "2021-01-03"]), "modal_price": [100.0, 110.0]})
        r = market_day_log_returns(g)
        self.assertEqual(len(r), 1)
        self.assertAlmostEqual(r.iloc[0], np.log(1.1))
        self.assertEqual(r.index[0], pd.Timestamp("2021-01-03"))


class TestDecompositionRule(unittest.TestCase):
    def test_dispersion_scaling_with_level_is_multiplicative(self):
        idx = pd.date_range("2016-01-01", periods=72, freq="MS")
        level = np.repeat(np.arange(1, 7) * 100.0, 12)
        seasonal = 1 + 0.2 * np.sin(2 * np.pi * np.arange(72) / 12)
        self.assertEqual(decomposition_model(pd.Series(level * seasonal, index=idx))["model"], "multiplicative")

    def test_constant_dispersion_is_additive(self):
        idx = pd.date_range("2016-01-01", periods=72, freq="MS")
        level = np.repeat(np.array([500.0, 900.0, 600.0, 1000.0, 700.0, 800.0]), 12)
        amp = np.repeat(np.array([60.0, 40.0, 55.0, 45.0, 50.0, 52.0]), 12)
        y = level + amp * np.sin(2 * np.pi * np.arange(72) / 12)
        self.assertEqual(decomposition_model(pd.Series(y, index=idx))["model"], "additive")


class TestBlockBootstrap(unittest.TestCase):
    def test_reproducible_with_seed_and_brackets_strong_correlation(self):
        x = np.arange(60, dtype=float)
        y = -x + np.sin(x)
        ci1 = block_bootstrap_corr(x, y, np.random.default_rng(1), block=6, reps=200)
        ci2 = block_bootstrap_corr(x, y, np.random.default_rng(1), block=6, reps=200)
        self.assertEqual(ci1, ci2)
        self.assertLess(ci1[1], -0.9)


if __name__ == "__main__":
    unittest.main()
