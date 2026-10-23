"""
Tests for anomaly scoring (Req 9.5, 9.6) with hand-computed values and causality checks.
"""

import unittest

import numpy as np
import pandas as pd

from src.anomaly_detection.scoring import (
    MAD_SCALE, causal_standardize, composite_score, inject_shocks, residuals, robust_weekday_score,
    rolling_zscore, spaced_positions,
)


class TestResiduals(unittest.TestCase):
    def test_log_and_level(self):
        a = pd.Series([110.0, 90.0])
        f = pd.Series([100.0, 100.0])
        np.testing.assert_allclose(residuals(a, f, log=False), [10.0, -10.0])
        np.testing.assert_allclose(residuals(a, f), np.log([1.1, 0.9]))

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            residuals(pd.Series([], dtype=float), pd.Series([], dtype=float))


class TestRollingZscore(unittest.TestCase):
    def test_hand_computed_values(self):
        e = pd.Series([1.0, 2.0, 3.0, 4.0, 10.0])
        z = rolling_zscore(e, window=3)
        # Index 3: prior window [1, 2, 3], mean 2, SD 1, so z = (4 - 2) / 1 = 2
        self.assertAlmostEqual(z.iloc[3], 2.0)
        # Index 4: prior window [2, 3, 4], mean 3, SD 1, so z = 7
        self.assertAlmostEqual(z.iloc[4], 7.0)
        self.assertTrue(z.iloc[:3].isna().all())

    def test_causal(self):
        e = pd.Series(np.random.default_rng(0).normal(size=100))
        z1 = rolling_zscore(e, 30)
        e2 = e.copy()
        e2.iloc[60:] = 100.0
        z2 = rolling_zscore(e2, 30)
        pd.testing.assert_series_equal(z1.iloc[:60], z2.iloc[:60])


class TestRobustScore(unittest.TestCase):
    def test_spike_scores_high_and_is_causal(self):
        rng = np.random.default_rng(1)
        n = 400
        logy = pd.Series(np.log(1000) + np.cumsum(rng.normal(0, 0.005, n)))
        weekday = pd.Series(np.arange(n) % 7)
        base = robust_weekday_score(logy, weekday)
        # Burn-in: 28 (level) + 26 same-weekday occurrences (~182) + 56 (scale) market days
        self.assertTrue(base.iloc[:260].isna().all())
        self.assertTrue(base.iloc[280:].notna().all())
        spiked = logy.copy()
        spiked.iloc[350] += np.log(1.3)
        s = robust_weekday_score(spiked, weekday)
        pd.testing.assert_series_equal(base.iloc[:350], s.iloc[:350])
        self.assertGreater(s.iloc[350], 10)

    def test_weekday_offset_is_removed(self):
        n = 400
        weekday = pd.Series(np.arange(n) % 7)
        logy = pd.Series(np.log(1000) + np.where(weekday == 6, 0.05, 0.0)
                         + np.random.default_rng(2).normal(0, 0.003, n))
        s = robust_weekday_score(logy, weekday)
        sundays = s[(weekday == 6) & s.notna()]
        self.assertLess(abs(sundays.median()), 1.0)


class TestCompositeAndStandardise(unittest.TestCase):
    def test_causal_standardize_uses_prior_only(self):
        s = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        z = causal_standardize(s, min_periods=3)
        prior = np.array([1.0, 2.0, 3.0])
        self.assertAlmostEqual(z.iloc[3], (4.0 - prior.mean()) / prior.std(ddof=1))

    def test_weights_validated(self):
        s = pd.Series(np.arange(10.0))
        with self.assertRaises(ValueError):
            composite_score({"a": s, "b": s}, {"a": 0.7, "b": 0.7})
        with self.assertRaises(ValueError):
            composite_score({}, {})

    def test_mad_scale_constant(self):
        self.assertAlmostEqual(MAD_SCALE, 1.4826)


class TestShockInjection(unittest.TestCase):
    def test_shocks_at_positions_only(self):
        y = pd.Series([100.0] * 10)
        out = inject_shocks(y, [2, 7], 0.25)
        self.assertEqual(list(out.iloc[[2, 7]]), [125.0, 125.0])
        self.assertTrue((out.drop(index=[2, 7]) == 100.0).all())
        self.assertTrue((y == 100.0).all())  # input unchanged

    def test_negative_shock_and_validation(self):
        y = pd.Series([200.0] * 5)
        self.assertEqual(inject_shocks(y, [1], -0.5).iloc[1], 100.0)
        with self.assertRaises(ValueError):
            inject_shocks(y, [1], -1.0)
        with self.assertRaises(ValueError):
            inject_shocks(y, [9], 0.1)

    def test_spaced_positions(self):
        rng = np.random.default_rng(0)
        pos = spaced_positions(100, 500, 6, 60, rng)
        self.assertEqual(len(pos), 6)
        self.assertTrue(all(100 <= p < 500 for p in pos))
        self.assertTrue(all(b - a >= 60 for a, b in zip(pos, pos[1:])))
        self.assertEqual(pos, spaced_positions(100, 500, 6, 60, np.random.default_rng(0)))
        with self.assertRaises(ValueError):
            spaced_positions(0, 50, 5, 20, rng)


if __name__ == "__main__":
    unittest.main()
