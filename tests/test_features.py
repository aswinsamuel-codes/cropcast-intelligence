"""
Tests for feature construction (Req 9.2, 9.3, 9.8) and walk-forward look-ahead safety.
"""

import unittest

import numpy as np
import pandas as pd

from src.features.build import (
    build_features, feature_audit_table, lag_features, model_inputs, rolling_features, target_log_return,
)
from src.forecasting.models import (
    EtsModel, Naive, SarimaModel, SeasonalNaive, SeriesData, make_feature_model, split_origins, walk_forward,
)


def series(n=60, seed=0, start="2021-01-01"):
    rng = np.random.default_rng(seed)
    price = 1000 * np.exp(np.cumsum(rng.normal(0, 0.02, n)))
    return pd.DataFrame({"date": pd.date_range(start, periods=n, freq="D"), "modal_price": price,
                         "arrival_qty": rng.integers(1000, 20000, n).astype(float)})


class TestLagsAndRolling(unittest.TestCase):
    def test_lag_values(self):
        y = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0])
        lags = lag_features(y)
        # price_lag_k at origin t equals y[t-(k-1)]
        self.assertEqual(lags.at[7, "price_lag_1"], 17.0)
        self.assertEqual(lags.at[7, "price_lag_2"], 16.0)
        self.assertEqual(lags.at[7, "price_lag_3"], 15.0)
        self.assertEqual(lags.at[7, "price_lag_5"], 13.0)
        self.assertEqual(lags.at[7, "price_lag_7"], 11.0)
        self.assertTrue(np.isnan(lags.at[5, "price_lag_7"]))

    def test_rolling_matches_hand_computation(self):
        y = pd.Series(np.arange(1.0, 16.0))  # 1..15
        r = rolling_features(y)
        # Window of 7 ending at index 6: values 1..7, mean 4, sample SD sqrt(14/3)
        self.assertAlmostEqual(r.at[6, "roll_mean_7"], 4.0)
        self.assertAlmostEqual(r.at[6, "roll_std_7"], np.sqrt(28 / 6))
        self.assertTrue(np.isnan(r.at[5, "roll_mean_7"]))
        # Window of 14 ending at index 14: values 2..15, mean 8.5
        self.assertAlmostEqual(r.at[14, "roll_mean_14"], 8.5)
        self.assertAlmostEqual(r.at[14, "roll_std_14"], np.std(np.arange(2.0, 16.0), ddof=1))

    def test_empty_inputs_raise(self):
        with self.assertRaises(ValueError):
            lag_features(pd.Series([], dtype=float))
        with self.assertRaises(ValueError):
            rolling_features(pd.Series([], dtype=float))
        with self.assertRaises(ValueError):
            build_features(pd.DataFrame(columns=["date", "modal_price", "arrival_qty"]))


class TestBuildFeatures(unittest.TestCase):
    def test_no_leakage_perturbing_future(self):
        g = series()
        base = build_features(g)
        t = 30
        perturbed = g.copy()
        perturbed.loc[t + 1:, "modal_price"] *= 7.0
        perturbed.loc[t + 1:, "arrival_qty"] *= 3.0
        after = build_features(perturbed)
        feature_cols = [c for c in base.columns if c not in ("target", "target_date", "target_gap_days")]
        pd.testing.assert_frame_equal(base.loc[:t, feature_cols], after.loc[:t, feature_cols])
        pd.testing.assert_frame_equal(model_inputs(base).loc[:t], model_inputs(after).loc[:t])
        # Only the target of row t may see the change
        self.assertNotEqual(base.at[t, "target"], after.at[t, "target"])

    def test_idempotent(self):
        g = series()
        pd.testing.assert_frame_equal(build_features(g), build_features(g.copy()))

    def test_validity_and_target(self):
        f = build_features(series())
        self.assertFalse(f.loc[:12, "is_valid"].any())
        self.assertTrue(f.loc[13:, "is_valid"].all())
        self.assertTrue(np.isnan(f["target"].iloc[-1]))
        self.assertEqual(f.at[20, "target"], f.at[21, "y_origin"])
        self.assertAlmostEqual(target_log_return(f).iloc[20], np.log(f.at[21, "y_origin"] / f.at[20, "y_origin"]))

    def test_market_day_lags_skip_missing_dates(self):
        g = series(20)
        g = g.drop(index=10).reset_index(drop=True)  # one missing calendar day
        f = build_features(g)
        self.assertEqual(f.at[10, "price_lag_2"], g.at[9, "modal_price"])
        self.assertEqual(f.at[9, "target_gap_days"], 2)

    def test_audit_table_covers_all_features(self):
        audit = feature_audit_table()
        f = build_features(series())
        for col in [c for c in f.columns if c.startswith(("price_lag_", "roll_", "arrival_lag_", "dow_", "month_"))]:
            self.assertIn(col, set(audit["feature"]))
        self.assertTrue((audit["uses_future_data"] == "No").all())


class TestWalkForwardNoLookAhead(unittest.TestCase):
    def _forecasts(self, g, model_factory, origins, refit_every):
        data = SeriesData(build_features(g))
        return walk_forward(model_factory(data), origins, refit_every)["forecast"].to_numpy()

    def test_forecasts_unchanged_when_future_perturbed(self):
        g = series(120, seed=3)
        origins = list(range(60, 80))
        last = origins[-1]
        perturbed = g.copy()
        perturbed.loc[last + 1:, "modal_price"] *= 5.0
        factories = {
            "naive": lambda d: Naive(d),
            "snaive": lambda d: SeasonalNaive(d, 7),
            "ols": lambda d: make_feature_model(d, "linear_regression", {}, 1),
            "tree": lambda d: make_feature_model(d, "decision_tree", {"max_depth": 3, "min_samples_leaf": 5}, 1),
            "sarima": lambda d: SarimaModel(d, (1, 1, 0), (0, 0, 0, 7), maxiter=50),
            "ets": lambda d: EtsModel(d, None, 7),
        }
        for name, fac in factories.items():
            for refit in (1, 7):
                with self.subTest(model=name, refit=refit):
                    a = self._forecasts(g, fac, origins, refit)
                    b = self._forecasts(perturbed, fac, origins, refit)
                    np.testing.assert_allclose(a, b, rtol=1e-9)

    def test_baseline_values(self):
        g = series(40)
        data = SeriesData(build_features(g))
        p = walk_forward(Naive(data), [20, 21], 1)
        self.assertEqual(list(p["forecast"]), [data.y[20], data.y[21]])
        p = walk_forward(SeasonalNaive(data, 7), [20], 1)
        self.assertEqual(p["forecast"].iloc[0], data.y[14])  # target index 21 -> 21 - 7
        self.assertEqual(p["actual"].iloc[0], data.y[21])

    def test_split_origins(self):
        sp = split_origins(100, 0.6, 0.2)
        self.assertEqual(sp["validation"][0], 59)
        self.assertEqual(sp["validation"][-1], 78)
        self.assertEqual(sp["test"], list(range(79, 99)))
        self.assertEqual(sp["train_end"], 60)

    def test_refit_every_must_be_positive(self):
        data = SeriesData(build_features(series(40)))
        with self.assertRaises(ValueError):
            walk_forward(Naive(data), [20], 0)


if __name__ == "__main__":
    unittest.main()
