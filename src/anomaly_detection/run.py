"""
CropCast market-relative anomaly screening (M-6).

Scores (all causal; DEC-017 replaces peer divergence with a robust own-history signal):
  residual  rolling z-score (prior 30 days) of one-step SARIMA log residuals (Req 6.1-6.2)
  robust    weekday-adjusted trailing-median deviation scaled by MAD
  composite causally standardised weighted sum of both (Req 6.4)
Each score is re-standardised with prior data only, and a day is flagged when |score| > threshold.

Evaluation, reported separately (Req 6.6-6.7):
  1. Real data: event counts, event classification (coverage / ISS-002 band / weekend
     composition / other), threshold sensitivity.
  2. Weak-label agreement with ICTD-IITD windows, with a circular-shift randomisation baseline.
  3. Synthetic shock recall on the held-out test segment.

Usage:
    python -m src.anomaly_detection.run
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.anomaly_detection.scoring import (  # noqa: E402
    causal_standardize, inject_shocks, robust_weekday_score, rolling_zscore, spaced_positions,
)
from src.config import load_config, resolve_path  # noqa: E402
from src.data.dataset import dataset_version_id, load_dataset  # noqa: E402
from src.evaluation.metrics import precision_recall_f1  # noqa: E402
from src.experiment import (  # noqa: E402
    RunRecorder, WarningTally, config_hash, require_keys, seed_everything, software_versions,
)
from src.features.build import build_features  # noqa: E402
from src.forecasting.models import SarimaModel, SeriesData, split_origins  # noqa: E402

logger = logging.getLogger("cropcast.anomaly_detection.run")
METHODS = ("residual", "robust", "composite")
LABELS = {"onion_maharashtra": "Maharashtra onion", "potato_uttar_pradesh": "Uttar Pradesh potato"}


def check_config(a: Dict[str, Any]) -> None:
    require_keys(a, ["protocol_version", "residual_burn_in_market_days", "residual_refit_every", "zscore_window",
                     "robust", "standardize_min_periods", "weights", "threshold", "threshold_sensitivity",
                     "coverage_arrival_fraction_of_median", "weak_labels", "shocks"], "anomaly")
    require_keys(a["robust"], ["level_window", "weekday_history", "scale_window"], "anomaly.robust")
    require_keys(a["shocks"], ["magnitudes", "shocks_per_run", "min_gap_market_days", "repeats",
                               "exclude_days_after_shock"], "anomaly.shocks")


def sarima_residuals(data: SeriesData, order_row: pd.Series, origins: List[int], refit_every: int,
                     freeze: bool = False, initial_fit_at: int | None = None) -> pd.Series:
    """
    One-step log residuals log(y_{t+1}) - log(yhat_{t+1}) indexed by target position.
    With freeze=True parameters are estimated once at `initial_fit_at` and only the state is updated.
    """
    model = SarimaModel(data, (int(order_row.p), 1, int(order_row.q)), (int(order_row.P), 0, int(order_row.Q), 7))
    out = {}
    for i, t in enumerate(origins):
        if i == 0:
            model.fit(initial_fit_at if initial_fit_at is not None else t)
            if initial_fit_at is not None and initial_fit_at < t:
                model.update(t)
        elif not freeze and i % refit_every == 0:
            model.fit(t)
        else:
            model.update(t)
        out[t + 1] = data.logy[t + 1] - np.log(model.forecast(t))
    return pd.Series(out)


def scores_for(logy: pd.Series, weekday: pd.Series, resid: pd.Series, a: Dict[str, Any]) -> pd.DataFrame:
    """All three scores on the market-day index, each re-standardised causally."""
    n = len(logy)
    e = resid.reindex(range(n))
    s_res = rolling_zscore(e, a["zscore_window"])
    rb = a["robust"]
    s_rob = robust_weekday_score(logy, weekday, rb["level_window"], rb["weekday_history"], rb["scale_window"])
    mp = a["standardize_min_periods"]
    z_res = causal_standardize(s_res, mp)
    z_rob = causal_standardize(s_rob, mp)
    w = a["weights"]
    comp = causal_standardize(w["residual"] * z_res + w["robust"] * z_rob, mp)
    return pd.DataFrame({"residual": z_res, "robust": z_rob, "composite": comp, "raw_residual": e,
                         "raw_residual_z": s_res, "raw_robust": s_rob})


class AnomalyRunner:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        self.a = cfg["anomaly"]
        check_config(self.a)
        seed_everything(cfg["random_seed"])
        self.recorder = None
        self.seed = cfg["random_seed"]
        self.version = dataset_version_id(cfg)
        self.tables = resolve_path(cfg["paths"]["tables_dir"])
        self.figs = resolve_path(cfg["paths"]["figures_dir"])
        self.log_path = resolve_path(cfg["paths"]["experiment_log"])
        self.aic = pd.read_csv(self.tables / "forecast_sarima_aic.csv")

    def best_order(self, sid: str) -> pd.Series:
        rows = self.aic[(self.aic["series_id"] == sid) & self.aic["aic"].notna()].sort_values("aic")
        if rows.empty:
            raise ValueError(f"no training-AIC SARIMA ranking for {sid}; run src.forecasting.run first")
        return rows.iloc[0]

    def weak_labels(self, sid: str, dates: pd.Series) -> pd.Series:
        spec = self.cfg["dataset"]["series"][sid]
        lab = pd.read_csv(resolve_path(self.cfg["paths"]["ictd_labels"][sid]), encoding="utf-8-sig")
        lab = lab[lab["STATENAME"] == spec["ictd_state"]]
        wl = self.a["weak_labels"]
        pos = lab[(lab[wl["label_columns"]] == wl["positive_value"]).any(axis=1)]
        flag = pd.Series(False, index=dates.index)
        for _, r in pos.iterrows():
            flag |= dates.between(pd.Timestamp(r["STARTDATE"]), pd.Timestamp(r["ENDDATE"]))
        return flag, int(len(lab)), int(len(pos)), pd.Timestamp(lab["ENDDATE"].max())

    def run(self) -> Dict[str, Any]:
        """Execute the anomaly study under a run record."""
        self.recorder = RunRecorder(self.cfg, "anomaly").start()
        try:
            with WarningTally(self.recorder, logger):
                summary = self._run()
            names = ["anomaly_scores.csv", "anomaly_events.csv", "anomaly_weak_label_agreement.csv",
                     "anomaly_shock_runs.csv", "anomaly_shock_recall.csv", "anomaly_threshold_sensitivity.csv",
                     "anomaly_event_classes.csv", "anomaly_summary.json"]
            figs = ["fig15_anomaly_score_distributions.png", "fig16_shock_recall.png", "fig17_anomaly_timeline.png",
                    "fig18_threshold_sensitivity.png"]
            self.recorder.complete([self.tables / n for n in names] + [self.figs / f for f in figs])
        except BaseException as e:
            self.recorder.fail(e)
            raise
        return summary

    def _run(self) -> Dict[str, Any]:
        df = load_dataset(self.cfg)
        a = self.a
        rng = np.random.default_rng(self.seed)
        summary: Dict[str, Any] = {}
        all_scores, events, weak_rows, shock_rows, sens_rows = [], [], [], [], []
        for sid, g in df.groupby("series_id"):
            start = time.time()
            g = g.sort_values("date").reset_index(drop=True)
            data = SeriesData(build_features(g))
            order = self.best_order(sid)
            n = len(g)
            burn = a["residual_burn_in_market_days"]
            resid = sarima_residuals(data, order, list(range(burn, n - 1)), a["residual_refit_every"])
            logy = pd.Series(np.log(g["modal_price"].to_numpy()))
            weekday = g["date"].dt.day_of_week
            sc = scores_for(logy, weekday, resid, a)
            sc.insert(0, "date", g["date"])
            sc.insert(1, "series_id", sid)
            sc["modal_price"] = g["modal_price"]
            sc["arrival_qty"] = g["arrival_qty"]
            cov_thr = a["coverage_arrival_fraction_of_median"] * g["arrival_qty"].median()
            sc["coverage_anomaly"] = (g["arrival_qty"] < cov_thr) | g["flag_extreme_arrival"]
            sc["band_violation"] = g["flag_modal_outside_bounds"]
            defined = sc[list(METHODS)].notna().all(axis=1)
            sc["scored"] = defined
            all_scores.append(sc)
            ev = sc[defined]
            k = a["threshold"]

            # 1. Real-data detections and classification
            for m in METHODS:
                det = ev[ev[m].abs() > k]
                cls = np.select([det["coverage_anomaly"], det["band_violation"], det["date"].dt.day_of_week.isin([6, 0])],
                                ["coverage anomaly (ISS-003 type)", "min/max band violation (ISS-002 type)",
                                 "Sunday/Monday (composition-prone)"], "other")
                for (_, r), c in zip(det.iterrows(), cls):
                    events.append({"series_id": sid, "method": m, "date": r["date"].date(), "score": r[m],
                                   "modal_price": r["modal_price"], "arrival_qty": r["arrival_qty"],
                                   "weekday": r["date"].day_name(), "class": c})
                for kk in a["threshold_sensitivity"]:
                    sens_rows.append({"series_id": sid, "method": m, "threshold": kk,
                                      "detections": int((ev[m].abs() > kk).sum()), "scored_days": int(len(ev)),
                                      "rate_pct": 100 * float((ev[m].abs() > kk).mean())})

            # 2. Weak-label agreement (ICTD windows, endogenous mandi-level flags)
            flags, n_windows, n_pos, label_end = self.weak_labels(sid, sc["date"])
            in_cov = defined & (sc["date"] <= label_end)
            y_true = flags[in_cov].to_numpy()
            for m in METHODS:
                y_pred = (sc.loc[in_cov, m].abs() > k).to_numpy()
                prf = precision_recall_f1(y_true, y_pred)
                base_rate = float(y_true.mean())
                # Randomisation baseline: circularly shift detections (keeps their count and clustering)
                n_cov = len(y_pred)
                null_prec = []
                shifts = np.random.default_rng(self.seed + 1).integers(30, n_cov - 30, a["weak_labels"]["permutations"])
                for s in shifts:
                    yp = np.roll(y_pred, s)
                    null_prec.append(y_true[yp].mean() if yp.any() else np.nan)
                null_prec = np.array(null_prec)
                p_val = float((np.sum(null_prec >= prf["precision"]) + 1) / (np.sum(~np.isnan(null_prec)) + 1)) \
                    if not np.isnan(prf["precision"]) else float("nan")
                weak_rows.append({"series_id": sid, "method": m, "threshold": k, "ictd_windows_state": n_windows,
                                  "ictd_positive_windows": n_pos, "evaluated_days": int(n_cov),
                                  "label_base_rate": base_rate, **prf,
                                  "precision_lift_over_base": prf["precision"] / base_rate if base_rate else np.nan,
                                  "null_precision_median": float(np.nanmedian(null_prec)),
                                  "randomisation_p_precision": p_val})

            # 3. Synthetic shocks on the held-out test segment, residual parameters frozen at segment start
            sp = split_origins(n, self.cfg["forecasting"]["split"]["train"], self.cfg["forecasting"]["split"]["validation"])
            seg_start = sp["test"][0] + 1  # first test target position
            sh = a["shocks"]
            clean_resid_pre = resid[resid.index < seg_start]
            for mag in sh["magnitudes"]:
                for rep in range(sh["repeats"]):
                    pos = spaced_positions(seg_start + 30, n - 1, sh["shocks_per_run"], sh["min_gap_market_days"], rng)
                    shocked = inject_shocks(g["modal_price"], pos, mag)
                    g2 = g.copy()
                    g2["modal_price"] = shocked
                    d2 = SeriesData(build_features(g2))
                    seg_resid = sarima_residuals(d2, order, list(range(seg_start - 1, n - 1)), a["residual_refit_every"],
                                                 freeze=True, initial_fit_at=seg_start - 1)
                    r2 = pd.concat([clean_resid_pre, seg_resid])
                    sc2 = scores_for(pd.Series(np.log(shocked.to_numpy())), weekday, r2, a)
                    excl = set(p + j for p in pos for j in range(0, sh["exclude_days_after_shock"] + 1))
                    seg_idx = [i for i in range(seg_start, n) if i not in excl]
                    for m in METHODS:
                        hit = (sc2[m].iloc[pos].abs() > k).to_numpy()
                        fp = float((sc2[m].iloc[seg_idx].abs() > k).mean())
                        shock_rows.append({"series_id": sid, "method": m, "magnitude": mag, "repeat": rep,
                                           "shocks": len(pos), "detected": int(hit.sum()), "recall": float(hit.mean()),
                                           "false_positive_rate_clean_days": fp})
            secs = time.time() - start
            summary[sid] = {"sarima_order": {k2: int(order[k2]) for k2 in ("p", "q", "P", "Q")},
                            "scored_days": int(defined.sum()), "first_scored_date": str(ev["date"].min().date()),
                            "runtime_seconds": round(secs, 1)}
            params_for_hash = {"series_id": sid, **summary[sid]["sarima_order"]}
            h = config_hash(self.version, self.seed, {"anomaly": a}, params_for_hash)
            self.recorder.log_record({"config_hash": h, "dataset_version": self.version, "random_seed": self.seed,
                                      "feature_definition": {"anomaly": a}, "model_params_for_hash": params_for_hash,
                                      "stage": "anomaly", "series_id": sid, "summary": summary[sid],
                                      "software": software_versions()})
            logger.info("%s anomaly run done in %.1fs", sid, secs)

        scores = pd.concat(all_scores)
        scores.to_csv(self.tables / "anomaly_scores.csv", index=False)
        events = pd.DataFrame(events)
        events.to_csv(self.tables / "anomaly_events.csv", index=False)
        weak = pd.DataFrame(weak_rows)
        weak.to_csv(self.tables / "anomaly_weak_label_agreement.csv", index=False)
        shocks = pd.DataFrame(shock_rows)
        shocks.to_csv(self.tables / "anomaly_shock_runs.csv", index=False)
        shock_summary = shocks.groupby(["series_id", "method", "magnitude"]).agg(
            recall=("recall", "mean"), recall_sd=("recall", "std"),
            fpr=("false_positive_rate_clean_days", "mean")).reset_index()
        shock_summary.to_csv(self.tables / "anomaly_shock_recall.csv", index=False)
        sens = pd.DataFrame(sens_rows)
        sens.to_csv(self.tables / "anomaly_threshold_sensitivity.csv", index=False)
        cls = events.groupby(["series_id", "method", "class"]).size().unstack(fill_value=0)
        cls.to_csv(self.tables / "anomaly_event_classes.csv")
        summary["event_classes"] = {f"{i[0]}|{i[1]}": row.to_dict() for i, row in cls.iterrows()}
        with open(self.tables / "anomaly_summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, default=str)
        self.plots(scores, events, shock_summary, sens)
        return summary

    def plots(self, scores, events, shock_summary, sens) -> None:
        credit = self.cfg["attribution"]
        k = self.a["threshold"]
        colors = {"residual": "#1b9e77", "robust": "#7570b3", "composite": "#d95f02"}
        fig, axes = plt.subplots(1, 2, figsize=(10, 3.2))
        for ax, (sid, s) in zip(axes, scores[scores["scored"]].groupby("series_id")):
            for m in METHODS:
                ax.hist(s[m].clip(-10, 10), bins=120, histtype="step", color=colors[m], label=m, density=True)
            ax.axvline(k, ls="--", c="k", lw=0.7)
            ax.axvline(-k, ls="--", c="k", lw=0.7)
            ax.set_yscale("log")
            ax.set_title(f"{LABELS[sid]}: anomaly score distribution")
            ax.set_xlabel("Standardised score (clipped to ±10)")
            ax.legend(frameon=False, fontsize=7)
        fig.text(0.01, -0.01, credit, fontsize=6.5, color="#555555", ha="left", va="top")
        fig.savefig(self.figs / "fig15_anomaly_score_distributions.png", dpi=150, bbox_inches="tight")
        plt.close(fig)

        fig, axes = plt.subplots(1, 2, figsize=(10, 3.2), sharey=True)
        for ax, (sid, s) in zip(axes, shock_summary.groupby("series_id")):
            for m in METHODS:
                sm = s[s["method"] == m].sort_values("magnitude")
                ax.plot(100 * sm["magnitude"], sm["recall"], marker="o", color=colors[m], label=m)
            ax.set_title(f"{LABELS[sid]}: synthetic shock recall (|score| > {k:g})")
            ax.set_xlabel("Injected one-day shock (%)")
            ax.set_ylabel("Recall")
            ax.set_ylim(-0.02, 1.02)
            ax.legend(frameon=False, fontsize=7)
        fig.text(0.01, -0.01, "Synthetic evaluation on the held-out test segment; not real anomalies. " + credit,
                 fontsize=6.5, color="#555555", ha="left", va="top")
        fig.savefig(self.figs / "fig16_shock_recall.png", dpi=150, bbox_inches="tight")
        plt.close(fig)

        fig, axes = plt.subplots(2, 1, figsize=(10, 5.5))
        for ax, (sid, s) in zip(axes, scores.groupby("series_id")):
            ax.plot(s["date"], s["modal_price"], color="#555555", lw=0.6)
            ev = events[(events["series_id"] == sid) & (events["method"] == "composite")]
            marker = {"coverage anomaly (ISS-003 type)": ("s", "#e7298a"),
                      "min/max band violation (ISS-002 type)": ("^", "#66a61e"),
                      "Sunday/Monday (composition-prone)": ("v", "#7570b3"), "other": ("o", "#d95f02")}
            for c, (mk, col) in marker.items():
                e = ev[ev["class"] == c]
                if len(e):
                    ax.scatter(pd.to_datetime(e["date"]), e["modal_price"], marker=mk, color=col, s=16, zorder=3,
                               label=f"{c} ({len(e)})")
            ax.set_title(f"{LABELS[sid]}: composite-score detections (|score| > {k:g})")
            ax.set_ylabel("INR per quintal")
            ax.legend(frameon=False, fontsize=7, loc="upper left")
        fig.text(0.01, -0.005, credit, fontsize=6.5, color="#555555", ha="left", va="top")
        fig.tight_layout()
        fig.savefig(self.figs / "fig17_anomaly_timeline.png", dpi=150, bbox_inches="tight")
        plt.close(fig)

        fig, axes = plt.subplots(1, 2, figsize=(10, 3), sharey=True)
        for ax, (sid, s) in zip(axes, sens.groupby("series_id")):
            for m in METHODS:
                sm = s[s["method"] == m]
                ax.plot(sm["threshold"], sm["rate_pct"], marker="o", color=colors[m], label=m)
            ax.set_yscale("log")
            ax.set_title(f"{LABELS[sid]}: detection rate vs threshold")
            ax.set_xlabel("Threshold on |score|")
            ax.set_ylabel("% of scored days flagged")
            ax.legend(frameon=False, fontsize=7)
        fig.text(0.01, -0.01, credit, fontsize=6.5, color="#555555", ha="left", va="top")
        fig.savefig(self.figs / "fig18_threshold_sensitivity.png", dpi=150, bbox_inches="tight")
        plt.close(fig)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    for name in ("matplotlib", "matplotlib.category"):
        logging.getLogger(name).setLevel(logging.WARNING)
    summary = AnomalyRunner(load_config()).run()
    print(json.dumps({k: v for k, v in summary.items() if k != "event_classes"}, indent=1))


if __name__ == "__main__":
    main()
