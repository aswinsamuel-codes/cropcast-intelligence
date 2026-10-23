"""
Forecasting models and walk-forward evaluation (Req 5).

Every model implements:
    fit(t)       estimate parameters using information up to and including origin index t
    update(t)    advance to origin t without re-estimating parameters
    forecast(t)  next-market-day modal price forecast made at origin t

Feature models train on rows whose target index is <= t (origins <= t - 1).
Univariate models use log prices with index <= t. Neither ever reads data after t.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.base import RegressorMixin, clone
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX

from src.features.build import model_inputs, target_log_return


class SeriesData:
    """Feature table plus aligned arrays for one series."""

    def __init__(self, feat: pd.DataFrame):
        if feat.empty:
            raise ValueError("SeriesData received an empty feature table")
        self.feat = feat.reset_index(drop=True)
        self.y = self.feat["y_origin"].to_numpy(dtype=float)
        self.logy = np.log(self.y)
        self.X = model_inputs(self.feat).to_numpy(dtype=float)
        self.r = target_log_return(self.feat).to_numpy(dtype=float)
        self.valid = self.feat["is_valid"].to_numpy() & np.isfinite(self.r)


class ForecastModel:
    name = "base"

    def __init__(self, data: SeriesData):
        self.data = data

    def fit(self, t: int) -> None:
        pass

    def update(self, t: int) -> None:
        pass

    def forecast(self, t: int) -> float:
        raise NotImplementedError


class Naive(ForecastModel):
    name = "naive"

    def forecast(self, t: int) -> float:
        return float(self.data.y[t])


class SeasonalNaive(ForecastModel):
    name = "seasonal_naive"

    def __init__(self, data: SeriesData, period: int = 7):
        super().__init__(data)
        self.period = period

    def forecast(self, t: int) -> float:
        # Target index t + 1; same position one period earlier is t + 1 - period
        idx = t + 1 - self.period
        if idx < 0:
            raise ValueError("not enough history for seasonal naive")
        return float(self.data.y[idx])


class FeatureModel(ForecastModel):
    """Wraps a scikit-learn regressor predicting the next log return."""

    def __init__(self, data: SeriesData, estimator: RegressorMixin, name: str):
        super().__init__(data)
        self.template = estimator
        self.name = name
        self.model: Optional[RegressorMixin] = None

    def fit(self, t: int) -> None:
        rows = np.flatnonzero(self.data.valid[:t])  # origins 0..t-1 → targets up to index t
        if rows.size == 0:
            raise ValueError(f"{self.name}: no valid training rows before origin {t}")
        self.model = clone(self.template).fit(self.data.X[rows], self.data.r[rows])
        # Fit in parallel, predict serially: parallel prediction sums tree outputs in thread order,
        # which is not bit-reproducible (ISS-012)
        if "n_jobs" in self.model.get_params():
            self.model.set_params(n_jobs=1)

    def forecast(self, t: int) -> float:
        if self.model is None:
            raise RuntimeError(f"{self.name}: forecast called before fit")
        r_hat = float(self.model.predict(self.data.X[t:t + 1])[0])
        return float(self.data.y[t] * np.exp(r_hat))


class SarimaModel(ForecastModel):
    """SARIMA(p,1,q)(P,0,Q)_s on log price; the forecast is exp of the predicted mean log (a median forecast)."""

    def __init__(self, data: SeriesData, order, seasonal_order, maxiter: int = 200):
        super().__init__(data)
        self.order = tuple(order)
        self.seasonal_order = tuple(seasonal_order)
        self.maxiter = maxiter
        self.name = f"sarima{self.order}{self.seasonal_order}"
        self.res = None
        self.n_seen = 0
        self.start_params = None

    def _model(self, endog):
        return SARIMAX(endog, order=self.order, seasonal_order=self.seasonal_order,
                       trend="n", enforce_stationarity=True, enforce_invertibility=True)

    def fit(self, t: int) -> None:
        # Warnings (e.g. ConvergenceWarning) propagate to the caller, which counts them per run
        self.res = self._model(self.data.logy[:t + 1]).fit(
            start_params=self.start_params, disp=False, maxiter=self.maxiter)
        self.start_params = self.res.params
        self.n_seen = t + 1

    def update(self, t: int) -> None:
        if self.res is None:
            raise RuntimeError("update called before fit")
        if t + 1 > self.n_seen:
            self.res = self.res.append(self.data.logy[self.n_seen:t + 1], refit=False)
            self.n_seen = t + 1

    def forecast(self, t: int) -> float:
        if self.n_seen != t + 1:
            raise RuntimeError("model state is not at origin t")
        return float(np.exp(self.res.forecast(1)[0]))

    def aic(self) -> float:
        return float(self.res.aic)


class EtsModel(ForecastModel):
    """Holt-Winters exponential smoothing on log price, additive weekly seasonality."""

    def __init__(self, data: SeriesData, trend: Optional[str], seasonal_period: int = 7):
        super().__init__(data)
        self.trend = "add" if trend == "add_damped" else trend
        self.damped = trend == "add_damped"
        self.period = seasonal_period
        self.name = f"ets(trend={trend})"
        self.params: Optional[Dict[str, Any]] = None
        self.fitted_t = -1
        self.current = None

    def _spec(self, endog):
        return ExponentialSmoothing(endog, trend=self.trend, damped_trend=self.damped,
                                    seasonal="add", seasonal_periods=self.period,
                                    initialization_method="estimated")

    def fit(self, t: int) -> None:
        self.current = self._spec(self.data.logy[:t + 1]).fit(optimized=True)
        self.params = dict(self.current.params)
        self.fitted_t = t

    def update(self, t: int) -> None:
        # Re-filter the longer history with the parameters estimated at the last refit
        p = self.params
        model = ExponentialSmoothing(self.data.logy[:t + 1], trend=self.trend, damped_trend=self.damped,
                                     seasonal="add", seasonal_periods=self.period,
                                     initialization_method="known", initial_level=p["initial_level"],
                                     initial_trend=p["initial_trend"] if self.trend else None,
                                     initial_seasonal=p["initial_seasons"])
        kwargs = dict(smoothing_level=p["smoothing_level"], smoothing_seasonal=p["smoothing_seasonal"],
                      optimized=False)
        if self.trend:
            kwargs["smoothing_trend"] = p["smoothing_trend"]
        if self.damped:
            kwargs["damping_trend"] = p["damping_trend"]
        self.current = model.fit(**kwargs)

    def forecast(self, t: int) -> float:
        if self.current is None or len(self.current.model.endog) != t + 1:
            raise RuntimeError("model state is not at origin t")
        return float(np.exp(self.current.forecast(1)[0]))


def make_feature_model(data: SeriesData, kind: str, params: Dict[str, Any], seed: int, n_jobs: int = 1) -> FeatureModel:
    if kind == "linear_regression":
        return FeatureModel(data, LinearRegression(), "linear_regression")
    if kind == "decision_tree":
        est = DecisionTreeRegressor(random_state=seed, **params)
        return FeatureModel(data, est, f"decision_tree{_fmt(params)}")
    if kind == "random_forest":
        est = RandomForestRegressor(random_state=seed, n_jobs=n_jobs, **params)
        return FeatureModel(data, est, f"random_forest{_fmt(params)}")
    raise ValueError(f"unknown feature model {kind!r}")


def _fmt(params: Dict[str, Any]) -> str:
    return "(" + ",".join(f"{k}={v}" for k, v in sorted(params.items()) if k not in ("n_jobs",)) + ")"


def walk_forward(model: ForecastModel, origins: List[int], refit_every: int) -> pd.DataFrame:
    """
    Produce one-step forecasts at each origin. Parameters are re-estimated every `refit_every`
    origins; in between, the model state advances without re-estimation.
    """
    if not origins:
        raise ValueError("walk_forward needs at least one origin")
    if refit_every < 1:
        raise ValueError("refit_every must be >= 1")
    feat = model.data.feat
    rows = []
    for i, t in enumerate(origins):
        if i % refit_every == 0:
            model.fit(t)
        else:
            model.update(t)
        rows.append({"origin_index": t, "origin_date": feat.at[t, "origin_date"],
                     "target_date": feat.at[t, "target_date"], "y_origin": feat.at[t, "y_origin"],
                     "actual": feat.at[t, "target"], "forecast": model.forecast(t)})
    return pd.DataFrame(rows)


def split_origins(n: int, train: float, validation: float) -> Dict[str, List[int]]:
    """
    Origins whose targets fall in each split. With n market days, targets with index in
    [int(train*n), int((train+validation)*n)) are validation and the rest are test.
    """
    a, b = int(train * n), int((train + validation) * n)
    return {"validation": list(range(a - 1, b - 1)), "test": list(range(b - 1, n - 1)), "train_end": a}
