"""
CropCast forecasting experiment runner (M-5), following docs/forecasting_protocol.md v1.1.

Stages per series:
1. Validation: walk-forward (refit every `validation_refit_every`) for every candidate
   configuration; SARIMA orders are first ranked by training-set AIC.
2. Selection: the best configuration per model family by validation MAE.
3. Test: walk-forward with refit every `test_refit_every` for the selected models and baselines.
4. Metrics, Diebold-Mariano tests with one BH adjustment, breakdowns, residual plots, run log.

Usage:
    python -m src.forecasting.run
"""

from __future__ import annotations

import itertools
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from statsmodels.stats.diagnostic import acorr_ljungbox  # noqa: E402
from statsmodels.stats.multitest import multipletests  # noqa: E402

from src.config import load_config, resolve_path  # noqa: E402
from src.data.dataset import dataset_version_id, load_dataset  # noqa: E402
from src.evaluation.metrics import diebold_mariano, mae, mape, mase, rmse  # noqa: E402
from src.experiment import (  # noqa: E402
    RunRecorder, WarningTally, config_hash, require_keys, seed_everything, software_versions,
)
from src.features.build import build_features  # noqa: E402
from src.forecasting.models import (  # noqa: E402
    EtsModel, ForecastModel, Naive, SarimaModel, SeasonalNaive, SeriesData, make_feature_model,
    split_origins, walk_forward,
)

logger = logging.getLogger("cropcast.forecasting.run")
LABELS = {"onion_maharashtra": "Maharashtra onion", "potato_uttar_pradesh": "Uttar Pradesh potato"}


def check_config(fc: Dict[str, Any]) -> None:
    """Req 10.5: refuse to run unless every parameter the run needs is in configuration."""
    require_keys(fc, ["protocol_version", "split", "seasonal_period", "test_refit_every",
                      "validation_refit_every", "features", "models", "comparison"], "forecasting")
    m = fc["models"]
    require_keys(m, ["naive", "seasonal_naive", "linear_regression", "decision_tree", "random_forest", "sarima", "ets"],
                 "forecasting.models")
    require_keys(m["seasonal_naive"], ["period"], "seasonal_naive")
    require_keys(m["decision_tree"], ["grid"], "decision_tree")
    require_keys(m["random_forest"], ["grid", "n_estimators", "n_jobs"], "random_forest")
    require_keys(m["sarima"], ["d", "seasonal_period", "grid", "top_k_by_aic", "maxiter"], "sarima")
    require_keys(m["ets"], ["seasonal_period", "grid"], "ets")
    require_keys(fc["comparison"], ["baseline", "dm_loss", "fdr_alpha"], "comparison")


def grid(spec: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
    keys = sorted(spec)
    return [dict(zip(keys, vals)) for vals in itertools.product(*(spec[k] for k in keys))]


class Runner:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        self.fc = cfg["forecasting"]
        check_config(self.fc)
        self.seed = cfg["random_seed"]
        self.version = dataset_version_id(cfg)
        self.log_path = resolve_path(cfg["paths"]["experiment_log"])
        self.out_dir = resolve_path(cfg["paths"]["forecasts_dir"])
        self.tables = resolve_path(cfg["paths"]["tables_dir"])
        self.figs = resolve_path(cfg["paths"]["figures_dir"])
        for p in (self.out_dir, self.tables, self.figs):
            p.mkdir(parents=True, exist_ok=True)
        self.versions = software_versions()
        self.recorder: RunRecorder | None = None
        seed_everything(self.seed)

    # --- model factory -------------------------------------------------------------------------
    def build(self, data: SeriesData, family: str, params: Dict[str, Any]) -> ForecastModel:
        m = self.fc["models"]
        if family == "naive":
            return Naive(data)
        if family == "seasonal_naive":
            return SeasonalNaive(data, period=m["seasonal_naive"]["period"])
        if family in ("linear_regression", "decision_tree"):
            return make_feature_model(data, family, params, self.seed)
        if family == "random_forest":
            return make_feature_model(data, family, dict(params, n_estimators=m["random_forest"]["n_estimators"]),
                                      self.seed, n_jobs=m["random_forest"]["n_jobs"])
        if family == "sarima":
            s = m["sarima"]["seasonal_period"]
            return SarimaModel(data, (params["p"], m["sarima"]["d"], params["q"]), (params["P"], 0, params["Q"], s),
                               maxiter=m["sarima"]["maxiter"])
        if family == "ets":
            return EtsModel(data, params["trend"], seasonal_period=m["ets"]["seasonal_period"])
        raise ValueError(family)

    def log(self, series_id: str, stage: str, family: str, params: Dict[str, Any], refit_every: int,
            metrics: Dict[str, Any], seconds: float) -> str:
        model_params = {"family": family, "params": params, "refit_every": refit_every,
                        "protocol_version": self.fc["protocol_version"], "series_id": series_id, "stage": stage}
        h = config_hash(self.version, self.seed, self.fc["features"], model_params)
        self.recorder.log_record({"config_hash": h, "dataset_version": self.version, "random_seed": self.seed,
                                  "feature_definition": self.fc["features"], "model_params_for_hash": model_params,
                                  **model_params, "metrics": metrics, "runtime_seconds": round(seconds, 2),
                                  "software": self.versions})
        return h

    def run_one(self, data: SeriesData, series_id: str, stage: str, family: str, params: Dict[str, Any],
                origins: List[int], refit_every: int) -> Tuple[pd.DataFrame, str, float]:
        start = time.time()
        model = self.build(data, family, params)
        preds = walk_forward(model, origins, refit_every)
        secs = time.time() - start
        metric = {"mae": mae(preds["actual"], preds["forecast"]), "rmse": rmse(preds["actual"], preds["forecast"]),
                  "n": len(preds)}
        h = self.log(series_id, stage, family, params, refit_every, metric, secs)
        logger.info("%s %s %-15s %-60s MAE=%.3f (%.1fs)", series_id, stage, family, json.dumps(params, default=str),
                    metric["mae"], secs)
        return preds, h, secs

    # --- stages ----------------------------------------------------------------------------------
    def sarima_aic_ranking(self, data: SeriesData, train_end: int, series_id: str) -> pd.DataFrame:
        rows = []
        for params in grid(self.fc["models"]["sarima"]["grid"]):
            model = self.build(data, "sarima", params)
            start = time.time()
            try:
                model.fit(train_end - 1)
                rows.append({"series_id": series_id, **params, "aic": model.aic(),
                             "ljung_box_p_lag14": float(acorr_ljungbox(model.res.resid[1:], lags=[14])["lb_pvalue"].iloc[0]),
                             "fit_seconds": time.time() - start})
            except Exception as e:  # recorded, not hidden
                rows.append({"series_id": series_id, **params, "aic": np.nan, "error": str(e)})
        return pd.DataFrame(rows).sort_values("aic")

    def validate(self, data: SeriesData, series_id: str, origins: List[int], train_end: int):
        refit = self.fc["validation_refit_every"]
        m = self.fc["models"]
        candidates: List[Tuple[str, Dict[str, Any]]] = [("naive", {}), ("seasonal_naive", {}), ("linear_regression", {})]
        candidates += [("decision_tree", p) for p in grid(m["decision_tree"]["grid"])]
        candidates += [("random_forest", p) for p in grid(m["random_forest"]["grid"])]
        candidates += [("ets", p) for p in grid(m["ets"]["grid"])]
        aic = self.sarima_aic_ranking(data, train_end, series_id)
        top = aic.dropna(subset=["aic"]).head(m["sarima"]["top_k_by_aic"])
        candidates += [("sarima", {k: int(r[k]) for k in ("p", "q", "P", "Q")}) for _, r in top.iterrows()]
        rows, val_preds = [], {}
        for family, params in candidates:
            preds, h, secs = self.run_one(data, series_id, "validation", family, params, origins, refit)
            key = f"{family}|{json.dumps(params, sort_keys=True, default=str)}"
            val_preds[key] = preds
            rows.append({"series_id": series_id, "family": family, "params": json.dumps(params, sort_keys=True, default=str),
                         "val_mae": mae(preds["actual"], preds["forecast"]),
                         "val_rmse": rmse(preds["actual"], preds["forecast"]), "config_hash": h, "seconds": secs})
        return pd.DataFrame(rows), aic, val_preds

    def run(self) -> List[Path]:
        """Execute the full protocol under a run record; returns the artifact paths."""
        self.recorder = RunRecorder(self.cfg, "forecasting").start()
        logger.info("run %s started", self.recorder.run_id)
        try:
            with WarningTally(self.recorder, logger):
                artifacts = self._run()
            self.recorder.complete(artifacts)
        except BaseException as e:
            self.recorder.fail(e)
            raise
        logger.info("run %s completed", self.recorder.run_id)
        return artifacts

    def _run(self) -> List[Path]:
        df = load_dataset(self.cfg)
        split = self.fc["split"]
        all_val, all_aic, selection, test_frames = [], [], [], {}
        for series_id, g in df.groupby("series_id"):
            data = SeriesData(build_features(g))
            sp = split_origins(len(data.y), split["train"], split["validation"])
            val, aic, _ = self.validate(data, series_id, sp["validation"], sp["train_end"])
            all_val.append(val)
            all_aic.append(aic)
            # Selection: best validation MAE within each family (baselines and OLS have one config)
            chosen = val.loc[val.groupby("family")["val_mae"].idxmin()]
            test_preds = None
            for _, row in chosen.iterrows():
                params = json.loads(row["params"])
                preds, h, secs = self.run_one(data, series_id, "test", row["family"], params, sp["test"],
                                              self.fc["test_refit_every"])
                if test_preds is None:
                    test_preds = preds[["origin_index", "origin_date", "target_date", "y_origin", "actual"]].copy()
                test_preds[row["family"]] = preds["forecast"].to_numpy()
                selection.append({"series_id": series_id, "model": row["family"], "selected_params": row["params"],
                                  "val_mae": row["val_mae"], "config_hash": h, "test_seconds": secs})
            test_preds.to_csv(self.out_dir / f"test_{series_id}.csv", index=False)
            test_frames[series_id] = test_preds
        # Full precision everywhere: rounded tables cannot be verified against predictions (ISS-013)
        pd.concat(all_val).to_csv(self.tables / "forecast_validation_results.csv", index=False)
        pd.concat(all_aic).to_csv(self.tables / "forecast_sarima_aic.csv", index=False)
        selection = pd.DataFrame(selection)
        selection.to_csv(self.tables / "forecast_test_selection.csv", index=False)
        metrics = evaluate(self.cfg, df, test_frames, selection)
        metrics.to_csv(self.tables / "forecast_test_metrics.csv", index=False)
        self.breakdowns(test_frames, df)
        self.plots(test_frames, metrics)
        print(metrics[["series_id", "model", "mae", "rmse", "mape_pct", "mase", "dm_stat", "p_bh", "verdict"]]
              .to_string(index=False))
        return ([self.out_dir / f"test_{sid}.csv" for sid in test_frames]
                + [self.tables / n for n in ("forecast_validation_results.csv", "forecast_sarima_aic.csv",
                                             "forecast_test_selection.csv", "forecast_test_metrics.csv",
                                             "forecast_test_breakdown.csv")]
                + [self.figs / f"fig13_residuals_{sid}.png" for sid in test_frames]
                + [self.figs / "fig14_test_forecasts.png"])

    # --- comparison and reporting ------------------------------------------------------------------
    def breakdowns(self, frames: Dict[str, pd.DataFrame], df: pd.DataFrame) -> None:
        rows = []
        flags = df.set_index(["series_id", "date"])
        for sid, f in frames.items():
            models = [c for c in f.columns if c not in ("origin_index", "origin_date", "target_date", "y_origin", "actual")]
            f = f.copy()
            f["target_date"] = pd.to_datetime(f["target_date"])
            groups = {
                "half_year": f["target_date"].dt.year.astype(str) + "-H" + np.where(f["target_date"].dt.month <= 6, "1", "2"),
                "target_weekday": f["target_date"].dt.day_name(),
                "target_gap": np.where((f["target_date"] - pd.to_datetime(f["origin_date"])).dt.days > 1, "after gap", "consecutive"),
                "flagged_row": np.where([bool(flags.loc[(sid, d), ["flag_modal_outside_bounds", "flag_extreme_arrival"]].any())
                                         for d in f["target_date"]], "flagged", "unflagged"),
            }
            for gname, key in groups.items():
                for level, idx in f.groupby(key).groups.items():
                    sub = f.loc[idx]
                    for m in models:
                        rows.append({"series_id": sid, "breakdown": gname, "level": level, "model": m, "n": len(sub),
                                     "mae": mae(sub["actual"], sub[m])})
        pd.DataFrame(rows).to_csv(self.tables / "forecast_test_breakdown.csv", index=False)

    def plots(self, frames: Dict[str, pd.DataFrame], metrics: pd.DataFrame) -> None:
        credit = self.cfg["attribution"]
        for sid, f in frames.items():
            models = list(metrics[metrics["series_id"] == sid]["model"])
            fig, axes = plt.subplots(len(models), 2, figsize=(10, 1.9 * len(models)), squeeze=False)
            for i, m in enumerate(models):
                resid = f["actual"] - f[m]
                axes[i, 0].plot(pd.to_datetime(f["target_date"]), resid, lw=0.6, color="#333333")
                axes[i, 0].axhline(0, color="k", lw=0.5)
                axes[i, 0].set_ylabel(m, fontsize=7)
                axes[i, 1].hist(resid, bins=60, color="#777777")
            axes[0, 0].set_title(f"{LABELS[sid]}: test residuals (actual − forecast, INR/quintal)")
            axes[0, 1].set_title("Residual distribution")
            fig.text(0.01, -0.005, credit, fontsize=6.5, color="#555555", ha="left", va="top")
            fig.tight_layout()
            fig.savefig(self.figs / f"fig13_residuals_{sid}.png", dpi=150, bbox_inches="tight")
            plt.close(fig)
        fig, axes = plt.subplots(2, 1, figsize=(10, 5.5))
        for ax, (sid, f) in zip(axes, frames.items()):
            best = metrics[(metrics["series_id"] == sid) & (metrics["model"] != "naive")].iloc[0]["model"]
            d = pd.to_datetime(f["target_date"])
            ax.plot(d, f["actual"], color="k", lw=0.9, label="Actual")
            ax.plot(d, f["naive"], color="#999999", lw=0.7, label="Naive")
            ax.plot(d, f[best], color="#d95f02", lw=0.7, label=f"{best} (lowest-MAE non-naive)")
            ax.set_title(f"{LABELS[sid]}: test period one-step forecasts")
            ax.set_ylabel("INR per quintal")
            ax.legend(frameon=False, fontsize=7)
        fig.text(0.01, -0.005, credit, fontsize=6.5, color="#555555", ha="left", va="top")
        fig.tight_layout()
        fig.savefig(self.figs / "fig14_test_forecasts.png", dpi=150, bbox_inches="tight")
        plt.close(fig)


def evaluate(cfg: Dict[str, Any], df: pd.DataFrame, frames: Dict[str, pd.DataFrame], selection: pd.DataFrame) -> pd.DataFrame:
    """
    Test metrics, Diebold-Mariano/HLN tests against the baseline, one BH adjustment across all
    comparisons, and the protocol verdict. This is the single metric path, used by live runs and
    when regenerating metrics from saved predictions.
    """
    fc = cfg["forecasting"]
    base, loss, alpha = fc["comparison"]["baseline"], fc["comparison"]["dm_loss"], fc["comparison"]["fdr_alpha"]
    rows = []
    for _, sel in selection.iterrows():
        sid, m = sel["series_id"], sel["model"]
        y = df[df["series_id"] == sid].sort_values("date")["modal_price"].to_numpy()
        train_end = split_origins(len(y), fc["split"]["train"], fc["split"]["validation"])["train_end"]
        insample = mae(y[1:train_end], y[:train_end - 1])  # one-step naive MAE on training targets
        f = frames[sid]
        mp, note = mape(f["actual"], f[m])
        row = {"series_id": sid, "model": m, "selected_params": sel["selected_params"], "n": len(f),
               "mae": mae(f["actual"], f[m]), "rmse": rmse(f["actual"], f[m]), "mape_pct": mp,
               "mase": mase(f["actual"], f[m], insample), "mape_note": note, "val_mae": sel["val_mae"],
               "config_hash": sel["config_hash"], "test_seconds": sel["test_seconds"],
               "dm_stat": np.nan, "p_value": np.nan}
        if m != base:
            res = diebold_mariano(f[m] - f["actual"], f[base] - f["actual"], h=1, loss=loss)
            row.update(dm_stat=res["dm_stat"], p_value=res["p_value"])
        rows.append(row)
    metrics = pd.DataFrame(rows)
    mask = metrics["model"] != base
    _, p_bh, *_ = multipletests(metrics.loc[mask, "p_value"], alpha=alpha, method="fdr_bh")
    metrics["p_bh"] = np.nan
    metrics.loc[mask, "p_bh"] = p_bh
    base_mae = metrics[metrics["model"] == base].set_index("series_id")["mae"]

    def verdict(r):
        if r["model"] == base:
            return "baseline"
        if r["p_bh"] < alpha:
            return "improves on naive" if r["mae"] < base_mae[r["series_id"]] else "significantly worse than naive"
        return "no significant difference"
    metrics["verdict"] = metrics.apply(verdict, axis=1)
    metrics["mae_vs_naive_pct"] = 100 * (metrics["mae"] / metrics["series_id"].map(base_mae) - 1)
    return metrics.sort_values(["series_id", "mae"]).reset_index(drop=True)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    for name in ("matplotlib", "matplotlib.category"):
        logging.getLogger(name).setLevel(logging.WARNING)
    Runner(load_config()).run()


if __name__ == "__main__":
    main()
