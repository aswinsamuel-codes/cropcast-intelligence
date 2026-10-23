"""
CropCast exploratory data analysis (M-3).

Reads the frozen analysis dataset, writes tables to `reports/tables/`, figures to
`figures/`, and a machine-readable summary to `reports/tables/eda_summary.json`.
All randomness (block bootstrap) uses the configured seed.

Usage:
    python -m src.analysis.eda
"""

from __future__ import annotations

import json
import logging
import warnings
from pathlib import Path
from typing import Any, Dict, List

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402
from statsmodels.stats.multitest import multipletests  # noqa: E402
from statsmodels.tsa.seasonal import STL  # noqa: E402
from statsmodels.tsa.stattools import acf, adfuller, kpss  # noqa: E402

from src.config import load_config, resolve_path  # noqa: E402
from src.data.dataset import load_dataset  # noqa: E402

logger = logging.getLogger("cropcast.analysis.eda")

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 10,
    "axes.titlesize": 11,
    "figure.dpi": 150,
    "savefig.bbox": "tight",
})
COLORS = {"onion_maharashtra": "#8c2d04", "potato_uttar_pradesh": "#225ea8"}
LABELS = {"onion_maharashtra": "Maharashtra onion", "potato_uttar_pradesh": "Uttar Pradesh potato"}


def describe(series: pd.Series) -> Dict[str, float]:
    """Req 3.5 descriptive statistics plus skewness and excess kurtosis."""
    s = series.dropna()
    if s.empty:
        raise ValueError("describe received an empty series")
    return {
        "n": int(s.size), "mean": s.mean(), "median": s.median(), "std": s.std(ddof=1),
        "min": s.min(), "q25": s.quantile(0.25), "q75": s.quantile(0.75), "max": s.max(),
        "cv": s.std(ddof=1) / s.mean(), "skewness": stats.skew(s), "excess_kurtosis": stats.kurtosis(s),
    }


def market_day_log_returns(g: pd.DataFrame) -> pd.Series:
    """Log change in modal price between consecutive market days, indexed by the later date."""
    s = np.log(g.set_index("date")["modal_price"])
    return s.diff().dropna()


def gap_table(dates: pd.Series, start: str, end: str) -> pd.DataFrame:
    """Runs of consecutive calendar days with no observation."""
    observed = set(pd.to_datetime(dates))
    missing = [d for d in pd.date_range(start, end, freq="D") if d not in observed]
    runs: List[List[pd.Timestamp]] = []
    for d in missing:
        if runs and (d - runs[-1][-1]).days == 1:
            runs[-1].append(d)
        else:
            runs.append([d])
    return pd.DataFrame([{"first_missing": r[0].date(), "last_missing": r[-1].date(), "days": len(r)} for r in runs],
                        columns=["first_missing", "last_missing", "days"])


def stationarity_tests(x: pd.Series) -> Dict[str, float]:
    """ADF (H0: unit root) and KPSS (H0: level-stationary)."""
    x = x.dropna()
    adf_stat, adf_p, *_ = adfuller(x, autolag="AIC", result_object=False)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # KPSS p-values are interpolated within table bounds
        kpss_stat, kpss_p, *_ = kpss(x, regression="c", nlags="auto")
    return {"adf_stat": adf_stat, "adf_p": adf_p, "kpss_stat": kpss_stat, "kpss_p_bounded": kpss_p}


def block_bootstrap_corr(x: np.ndarray, y: np.ndarray, rng: np.random.Generator, block: int, reps: int) -> List[float]:
    """Moving-block bootstrap 95% CI for the Spearman correlation of two aligned series."""
    n = len(x)
    starts_max = n - block + 1
    out = []
    for _ in range(reps):
        idx = np.concatenate([np.arange(s, s + block) for s in rng.integers(0, starts_max, size=int(np.ceil(n / block)))])[:n]
        out.append(stats.spearmanr(x[idx], y[idx]).statistic)
    return [float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))]


def decomposition_model(monthly: pd.Series) -> Dict[str, Any]:
    """
    Req 3.6 rule: if within-year dispersion scales with the level, use a multiplicative
    model (STL on log prices); otherwise additive. Scaling is judged by the Spearman
    correlation between each year's mean and standard deviation of monthly prices:
    rho > 0.5 indicates multiplicative behaviour.
    """
    yearly = monthly.groupby(monthly.index.year).agg(["mean", "std"])
    rho = stats.spearmanr(yearly["mean"], yearly["std"]).statistic
    cv = (yearly["std"] / yearly["mean"])
    return {"yearly_mean_std_spearman": float(rho), "yearly_cv_min": float(cv.min()), "yearly_cv_max": float(cv.max()),
            "model": "multiplicative" if rho > 0.5 else "additive"}


def add_credit(fig: plt.Figure, cfg: Dict[str, Any]) -> None:
    fig.text(0.01, -0.01, cfg["attribution"], fontsize=6.5, color="#555555", ha="left", va="top")


def run(cfg: Dict[str, Any]) -> Dict[str, Any]:
    df = load_dataset(cfg)
    ds = cfg["dataset"]
    figs = resolve_path(cfg["paths"]["figures_dir"])
    tables = resolve_path(cfg["paths"]["tables_dir"])
    figs.mkdir(parents=True, exist_ok=True)
    tables.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(cfg["random_seed"])
    eda_cfg = cfg["eda"]
    summary: Dict[str, Any] = {"dataset_rows": int(len(df))}
    series_ids = list(ds["series"])
    groups = {sid: g.sort_values("date").reset_index(drop=True) for sid, g in df.groupby("series_id")}

    # --- Descriptive statistics (Req 3.5) ---
    desc_rows = []
    for sid, g in groups.items():
        for col in ("modal_price", "min_price", "max_price", "arrival_qty"):
            desc_rows.append({"series_id": sid, "variable": col, **describe(g[col])})
        # CV is undefined for a mean-zero variable such as log returns
        desc_rows.append({"series_id": sid, "variable": "log_return_modal",
                          **dict(describe(market_day_log_returns(g)), cv=float("nan"))})
    desc = pd.DataFrame(desc_rows)
    desc.to_csv(tables / "eda_descriptive_stats.csv", index=False, float_format="%.6g")
    summary["descriptive"] = desc.to_dict(orient="records")

    # --- Coverage and gaps ---
    coverage = {}
    for sid, g in groups.items():
        gaps = gap_table(g["date"], ds["start_date"], ds["end_date"])
        gaps.insert(0, "series_id", sid)
        gaps.to_csv(tables / f"eda_gaps_{sid}.csv", index=False)
        years = g.groupby(g["date"].dt.year).size()
        all_days = pd.date_range(ds["start_date"], ds["end_date"], freq="D")
        missing_days = all_days.difference(pd.DatetimeIndex(g["date"]))
        coverage[sid] = {
            "observed_days": int(len(g)), "calendar_days": int(len(all_days)),
            "gaps": int(len(gaps)), "max_gap_days": int(gaps["days"].max()) if len(gaps) else 0,
            "observed_by_year": {int(k): int(v) for k, v in years.items()},
            "missing_by_weekday": {d: int((missing_days.day_of_week == i).sum())
                                   for i, d in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])},
        }
    summary["coverage"] = coverage

    # --- Annual and monthly summaries ---
    annual = []
    monthly_profile = []
    for sid, g in groups.items():
        r = market_day_log_returns(g)
        for yr, gy in g.groupby(g["date"].dt.year):
            ry = r[r.index.year == yr]
            annual.append({"series_id": sid, "year": yr, "days": len(gy), "modal_mean": gy["modal_price"].mean(),
                           "modal_median": gy["modal_price"].median(), "modal_min": gy["modal_price"].min(),
                           "modal_max": gy["modal_price"].max(), "modal_cv": gy["modal_price"].std() / gy["modal_price"].mean(),
                           "return_std": ry.std(), "arrival_mean": gy["arrival_qty"].mean(),
                           "arrival_total": gy["arrival_qty"].sum()})
        for m, gm in g.groupby(g["date"].dt.month):
            monthly_profile.append({"series_id": sid, "month": m, "modal_median": gm["modal_price"].median(),
                                    "modal_q25": gm["modal_price"].quantile(0.25), "modal_q75": gm["modal_price"].quantile(0.75),
                                    "arrival_median": gm["arrival_qty"].median()})
    annual = pd.DataFrame(annual)
    annual.to_csv(tables / "eda_annual_summary.csv", index=False, float_format="%.6g")
    monthly_profile = pd.DataFrame(monthly_profile)
    monthly_profile.to_csv(tables / "eda_monthly_profile.csv", index=False, float_format="%.6g")
    summary["annual"] = annual.to_dict(orient="records")
    summary["monthly_profile"] = monthly_profile.to_dict(orient="records")

    # --- Stationarity, autocorrelation, seasonal period (feeds Req 5.2 and 5.5) ---
    stat_rows, acf_rows = [], []
    seasonal = {}
    for sid, g in groups.items():
        logp = np.log(g.set_index("date")["modal_price"])
        r = logp.diff().dropna()
        for name, x in (("log_level", logp), ("log_return", r)):
            stat_rows.append({"series_id": sid, "transform": name, **stationarity_tests(x)})
        # ACF on the market-day sequence (onion gaps are 1.3% of days)
        a_ret = acf(r.values, nlags=400, fft=True)
        a_lvl = acf(logp.values, nlags=400, fft=True)
        for lag in (1, 2, 7, 14, 30, 182, 364, 365):
            acf_rows.append({"series_id": sid, "lag_market_days": lag, "acf_log_level": a_lvl[lag], "acf_log_return": a_ret[lag]})
        # Weekday effect on returns: Kruskal-Wallis across weekdays (robust to heavy tails)
        kw = stats.kruskal(*[r[r.index.day_of_week == d].values for d in range(7)])
        conf = 1.96 / np.sqrt(len(r))
        weekly_sig = bool(abs(a_ret[7]) > conf)
        seasonal[sid] = {
            "acf_return_lag7": float(a_ret[7]), "acf_return_band_95": float(conf),
            "weekday_kruskal_H": float(kw.statistic), "weekday_kruskal_p": float(kw.pvalue),
            "acf_level_lag365": float(a_lvl[365]), "acf_level_lag182": float(a_lvl[182]),
            "weekly_return_acf_significant": weekly_sig,
        }
        fig, axes = plt.subplots(1, 2, figsize=(9, 2.8))
        axes[0].bar(range(1, 31), a_ret[1:31], color=COLORS[sid])
        axes[0].axhline(conf, ls="--", c="k", lw=0.7)
        axes[0].axhline(-conf, ls="--", c="k", lw=0.7)
        axes[0].set_title(f"ACF of daily log returns — {LABELS[sid]}")
        axes[0].set_xlabel("Lag (market days)")
        axes[1].plot(range(0, 401), a_lvl, color=COLORS[sid])
        axes[1].axvline(365, ls=":", c="k", lw=0.7)
        axes[1].set_title(f"ACF of log modal price — {LABELS[sid]}")
        axes[1].set_xlabel("Lag (market days)")
        add_credit(fig, cfg)
        fig.savefig(figs / f"fig06_acf_{sid}.png")
        plt.close(fig)
    stat_df = pd.DataFrame(stat_rows)
    stat_df.to_csv(tables / "eda_stationarity.csv", index=False, float_format="%.6g")
    pd.DataFrame(acf_rows).to_csv(tables / "eda_acf.csv", index=False, float_format="%.6g")
    kw_p = [seasonal[s]["weekday_kruskal_p"] for s in series_ids]
    reject, p_adj, *_ = multipletests(kw_p, alpha=0.05, method="fdr_bh")
    for s, rj, pa in zip(series_ids, reject, p_adj):
        seasonal[s]["weekday_kruskal_p_bh"] = float(pa)
        seasonal[s]["weekday_effect_significant_bh"] = bool(rj)
    summary["stationarity"] = stat_df.to_dict(orient="records")
    summary["seasonality"] = seasonal

    # --- Weekday composition effect: arrivals and price deviation from centred 7-day mean ---
    weekday_rows = []
    fig, axes = plt.subplots(1, 2, figsize=(9, 3))
    names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for sid, g in groups.items():
        gi = g.set_index("date")
        lp = np.log(gi["modal_price"])
        dev = lp - lp.rolling(7, center=True, min_periods=5).mean()
        r = lp.diff()
        wd = gi.index.day_of_week
        for d in range(7):
            weekday_rows.append({"series_id": sid, "weekday": names[d], "days": int((wd == d).sum()),
                                 "arrival_median": gi["arrival_qty"][wd == d].median(),
                                 "log_price_dev_from_centred_7d_mean_pct": 100 * dev[wd == d].mean(),
                                 "mean_abs_log_return_pct": 100 * r[wd == d].abs().mean()})
        sub = pd.DataFrame([w for w in weekday_rows if w["series_id"] == sid])
        axes[0].plot(names, sub["arrival_median"], marker="o", color=COLORS[sid], label=LABELS[sid])
        axes[1].plot(names, sub["log_price_dev_from_centred_7d_mean_pct"], marker="o", color=COLORS[sid], label=LABELS[sid])
    axes[0].set_title("Median arrivals by weekday")
    axes[0].set_ylabel("Tonnes")
    axes[1].axhline(0, c="k", lw=0.5)
    axes[1].set_title("Modal price vs centred 7-day mean")
    axes[1].set_ylabel("Mean deviation (%)")
    axes[1].legend(frameon=False, fontsize=7)
    add_credit(fig, cfg)
    fig.savefig(figs / "fig12_weekday_composition.png")
    plt.close(fig)
    weekday = pd.DataFrame(weekday_rows)
    weekday.to_csv(tables / "eda_weekday_profile.csv", index=False, float_format="%.6g")
    summary["weekday_profile"] = weekday.to_dict(orient="records")

    # --- Decomposition (Req 3.6) on monthly means ---
    decomp = {}
    fig, axes = plt.subplots(4, 2, figsize=(10, 7.5), sharex=True)
    for j, (sid, g) in enumerate(groups.items()):
        monthly = g.set_index("date")["modal_price"].resample("MS").mean()
        choice = decomposition_model(monthly)
        y = np.log(monthly) if choice["model"] == "multiplicative" else monthly
        res = STL(y, period=12, robust=True).fit()
        var_resid = np.var(res.resid)
        choice["seasonal_strength"] = float(max(0.0, 1 - var_resid / np.var(res.seasonal + res.resid)))
        choice["trend_strength"] = float(max(0.0, 1 - var_resid / np.var(res.trend + res.resid)))
        choice["seasonal_peak_month"] = int(res.seasonal.groupby(res.seasonal.index.month).mean().idxmax())
        choice["seasonal_trough_month"] = int(res.seasonal.groupby(res.seasonal.index.month).mean().idxmin())
        decomp[sid] = choice
        scale = "log " if choice["model"] == "multiplicative" else ""
        for i, (comp, name) in enumerate(((y, f"Observed ({scale}monthly mean)"), (res.trend, "Trend"),
                                          (res.seasonal, "Seasonal"), (res.resid, "Remainder"))):
            axes[i, j].plot(comp.index, comp.values, color=COLORS[sid], lw=1)
            axes[i, j].set_ylabel(name, fontsize=8)
        axes[0, j].set_title(f"{LABELS[sid]} — STL ({choice['model']})")
    add_credit(fig, cfg)
    fig.savefig(figs / "fig05_stl_decomposition.png")
    plt.close(fig)
    summary["decomposition"] = decomp

    # --- Volatility, extreme moves, variance across years ---
    extremes, vol = [], {}
    fig, ax = plt.subplots(figsize=(10, 3))
    for sid, g in groups.items():
        r = market_day_log_returns(g)
        top = r.abs().sort_values(ascending=False).head(10)
        for d in top.index:
            extremes.append({"series_id": sid, "date": d.date(), "log_return": r[d],
                             "pct_change": 100 * (np.exp(r[d]) - 1)})
        rv = r.rolling(30).std()
        ax.plot(rv.index, rv.values, color=COLORS[sid], lw=0.9, label=LABELS[sid])
        lev = stats.levene(*[r[r.index.year == y].values for y in sorted(set(r.index.year))], center="median")
        vol[sid] = {"brown_forsythe_stat": float(lev.statistic), "brown_forsythe_p": float(lev.pvalue),
                    "share_abs_return_gt_10pct": float((r.abs() > np.log(1.1)).mean())}
    ax.set_title("Rolling 30-market-day standard deviation of daily log returns")
    ax.set_ylabel("Std. dev. of log return")
    ax.legend(frameon=False)
    add_credit(fig, cfg)
    fig.savefig(figs / "fig07_rolling_volatility.png")
    plt.close(fig)
    pd.DataFrame(extremes).to_csv(tables / "eda_extreme_moves.csv", index=False, float_format="%.6g")
    summary["volatility"] = vol
    summary["extreme_moves"] = pd.DataFrame(extremes).astype({"date": str}).to_dict(orient="records")

    # --- Price–arrival relationship (monthly; differences to avoid spurious level correlation) ---
    pa = {}
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.3))
    for j, (sid, g) in enumerate(groups.items()):
        m = g.set_index("date")[["modal_price", "arrival_qty"]].resample("MS").mean()
        lm = np.log(m)
        d = lm.diff().dropna()
        level_rho = stats.spearmanr(lm["modal_price"], lm["arrival_qty"]).statistic
        diff_rho = stats.spearmanr(d["modal_price"], d["arrival_qty"]).statistic
        ci = block_bootstrap_corr(d["modal_price"].values, d["arrival_qty"].values, rng,
                                  eda_cfg["bootstrap_block_months"], eda_cfg["bootstrap_reps"])
        ccf = {}
        for lag in range(0, 4):  # arrivals leading prices by `lag` months
            x = d["arrival_qty"].shift(lag)
            ok = x.notna()
            ccf[lag] = float(stats.spearmanr(x[ok], d["modal_price"][ok]).statistic)
        pa[sid] = {"months": int(len(m)), "spearman_log_levels": float(level_rho),
                   "spearman_monthly_log_diff": float(diff_rho), "diff_block_bootstrap_ci95": ci,
                   "spearman_lagged_arrival_diff": ccf}
        axes[j].scatter(d["arrival_qty"], d["modal_price"], s=12, color=COLORS[sid])
        axes[j].axhline(0, c="k", lw=0.5)
        axes[j].axvline(0, c="k", lw=0.5)
        axes[j].set_xlabel("Monthly change in log arrivals")
        axes[j].set_ylabel("Monthly change in log modal price")
        axes[j].set_title(f"{LABELS[sid]} (Spearman ρ = {diff_rho:.2f})")
    add_credit(fig, cfg)
    fig.savefig(figs / "fig08_price_arrival_monthly_changes.png")
    plt.close(fig)
    summary["price_arrival"] = pa

    # --- Correlation heatmap (Req 3.8; peer markets unavailable, DEC-017) ---
    monthly_all = {}
    for sid, g in groups.items():
        m = g.set_index("date")[["modal_price", "min_price", "max_price", "arrival_qty"]].resample("MS").mean()
        for c in m:
            monthly_all[f"{LABELS[sid].split()[-1]}: {c}"] = np.log(m[c])
    mat = pd.DataFrame(monthly_all).corr(method="spearman")
    mat.to_csv(tables / "eda_monthly_spearman_matrix.csv", float_format="%.4f")
    fig, ax = plt.subplots(figsize=(6.4, 5.4))
    im = ax.imshow(mat.values, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(mat)), mat.columns, rotation=60, ha="right", fontsize=7)
    ax.set_yticks(range(len(mat)), mat.index, fontsize=7)
    for (i, k), v in np.ndenumerate(mat.values):
        ax.text(k, i, f"{v:.2f}", ha="center", va="center", fontsize=6)
    fig.colorbar(im, ax=ax, fraction=0.046)
    ax.set_title("Spearman correlation of monthly log levels")
    add_credit(fig, cfg)
    fig.savefig(figs / "fig09_correlation_heatmap.png")
    plt.close(fig)
    summary["cross_commodity_monthly_spearman_log_modal"] = float(mat.loc["onion: modal_price", "potato: modal_price"])

    # --- ISS-002: modal position within the [min, max] band ---
    iss002 = {}
    fig, ax = plt.subplots(figsize=(10, 3))
    for sid, g in groups.items():
        pos = ((g["modal_price"] - g["min_price"]) / (g["max_price"] - g["min_price"])).set_axis(g["date"])
        flagged = g[g["flag_modal_outside_bounds"]]
        ratio = (g["max_price"] / g["min_price"]).set_axis(g["date"])
        period = (g["date"] >= "2016-03-04") & (g["date"] <= "2017-04-02")
        iss002[sid] = {
            "flagged_rows": int(len(flagged)),
            "modal_position_median_2016-03-04_2017-04-02": float(pos[period.values].median()),
            "modal_position_median_other": float(pos[~period.values].median()),
            "max_min_ratio_median_2016-03-04_2017-04-02": float(ratio[period.values].median()),
            "max_min_ratio_median_other": float(ratio[~period.values].median()),
            "flagged_months": {str(k): int(v) for k, v in flagged.groupby(flagged["date"].dt.to_period("M")).size().items()},
        }
        ax.plot(pos.index, pos.rolling(30, min_periods=10).median(), color=COLORS[sid], lw=1,
                label=f"{LABELS[sid]} (30-day rolling median)")
    ax.axhline(0, c="k", lw=0.6)
    ax.axhline(1, c="k", lw=0.6)
    ax.axvspan(pd.Timestamp("2016-03-04"), pd.Timestamp("2017-04-02"), color="#cccccc", alpha=0.5, label="Potato modal < min period")
    ax.set_ylabel("(modal − min) / (max − min)")
    ax.set_title("Position of the modal price within the reported [min, max] band")
    ax.legend(frameon=False, fontsize=8)
    add_credit(fig, cfg)
    fig.savefig(figs / "fig10_modal_position_iss002.png")
    plt.close(fig)
    summary["iss002"] = iss002

    # --- ISS-003: extreme arrivals and price context ---
    iss003 = []
    for sid, g in groups.items():
        gi = g.set_index("date")
        for d in g.loc[g["flag_extreme_arrival"], "date"]:
            window = gi.loc[d - pd.Timedelta(days=14): d - pd.Timedelta(days=1)]
            iss003.append({"series_id": sid, "date": d.date(), "arrival_qty": gi.at[d, "arrival_qty"],
                           "prior_14d_median_arrival": window["arrival_qty"].median(),
                           "modal_price": gi.at[d, "modal_price"],
                           "prior_14d_median_modal": window["modal_price"].median(),
                           "min_price": gi.at[d, "min_price"], "max_price": gi.at[d, "max_price"]})
    iss003 = pd.DataFrame(iss003)
    iss003.to_csv(tables / "eda_iss003_extreme_arrivals.csv", index=False, float_format="%.6g")
    summary["iss003"] = iss003.astype({"date": str}).to_dict(orient="records")
    # A state mean over many mandis is rarely a whole number; integer modal prices suggest
    # that only one or a few mandis reported that day (indirect evidence; mandi counts are not in the data)
    integer_share = {}
    for sid, g in groups.items():
        is_int = np.isclose(g["modal_price"], np.round(g["modal_price"]))
        low = g["arrival_qty"] < g["arrival_qty"].median() / 10
        integer_share[sid] = {
            "share_integer_modal_all_days": float(is_int.mean()),
            "share_integer_modal_flag_extreme_arrival": float(is_int[g["flag_extreme_arrival"]].mean())
            if g["flag_extreme_arrival"].any() else None,
            "share_integer_modal_arrival_below_tenth_of_median": float(is_int[low].mean()) if low.any() else None,
            "days_arrival_below_tenth_of_median": int(low.sum()),
            "fisher_exact_p_flagged_vs_rest": float(stats.fisher_exact(pd.crosstab(g["flag_extreme_arrival"], is_int)).pvalue)
            if g["flag_extreme_arrival"].any() else None,
        }
    summary["integer_modal_share"] = integer_share

    # --- Figures: series, arrivals, missingness, monthly box plots, returns ---
    fig, axes = plt.subplots(2, 1, figsize=(10, 5.5), sharex=True)
    for ax, (sid, g) in zip(axes, groups.items()):
        ax.fill_between(g["date"], g["min_price"], g["max_price"], color=COLORS[sid], alpha=0.18, lw=0, label="[min, max]")
        ax.plot(g["date"], g["modal_price"], color=COLORS[sid], lw=0.8, label="Modal price")
        ax.set_ylabel("INR per quintal")
        ax.set_title(LABELS[sid])
        ax.legend(frameon=False, fontsize=8, loc="upper left")
    axes[-1].xaxis.set_major_locator(mdates.YearLocator())
    add_credit(fig, cfg)
    fig.savefig(figs / "fig01_price_series.png")
    plt.close(fig)

    fig, axes = plt.subplots(2, 1, figsize=(10, 5), sharex=True)
    for ax, (sid, g) in zip(axes, groups.items()):
        ax.plot(g["date"], g["arrival_qty"], color=COLORS[sid], lw=0.6)
        fl = g[g["flag_extreme_arrival"]]
        ax.scatter(fl["date"], fl["arrival_qty"], color="k", s=14, zorder=3, label="Flagged (<1/100 of median)")
        ax.set_yscale("log")
        ax.set_ylabel("Arrivals (tonnes, log scale)")
        ax.set_title(LABELS[sid])
        if len(fl):
            ax.legend(frameon=False, fontsize=8)
    add_credit(fig, cfg)
    fig.savefig(figs / "fig02_arrival_series.png")
    plt.close(fig)

    fig, axes = plt.subplots(2, 1, figsize=(10, 3.6))
    for ax, (sid, g) in zip(axes, groups.items()):
        days = pd.date_range(ds["start_date"], ds["end_date"], freq="D")
        obs = pd.Series(days.isin(pd.DatetimeIndex(g["date"])), index=days)
        grid = np.full((7, 366), np.nan)
        for d, v in obs.items():
            grid[d.year - 2016, d.day_of_year - 1] = 1.0 if v else 0.0
        ax.imshow(grid, aspect="auto", cmap="Greys_r", vmin=0, vmax=1, interpolation="nearest")
        ax.set_yticks(range(7), range(2016, 2023), fontsize=7)
        ax.set_title(f"{LABELS[sid]}: observed days (white) and missing days (black)", fontsize=9)
    axes[-1].set_xlabel("Day of year")
    add_credit(fig, cfg)
    fig.savefig(figs / "fig03_missingness_heatmap.png")
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.4))
    for ax, (sid, g) in zip(axes, groups.items()):
        data = [g.loc[g["date"].dt.month == m, "modal_price"].values for m in range(1, 13)]
        ax.boxplot(data, tick_labels=["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"],
                   flierprops={"markersize": 2})
        ax.set_title(f"{LABELS[sid]}: modal price by calendar month")
        ax.set_ylabel("INR per quintal")
    add_credit(fig, cfg)
    fig.savefig(figs / "fig04_monthly_boxplots.png")
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(9, 3))
    for ax, (sid, g) in zip(axes, groups.items()):
        r = market_day_log_returns(g)
        ax.hist(r, bins=120, color=COLORS[sid], density=True)
        xs = np.linspace(r.min(), r.max(), 300)
        ax.plot(xs, stats.norm.pdf(xs, r.mean(), r.std()), "k--", lw=0.8, label="Normal (same mean, s.d.)")
        ax.set_title(f"{LABELS[sid]}: daily log returns")
        ax.legend(frameon=False, fontsize=7)
    add_credit(fig, cfg)
    fig.savefig(figs / "fig11_return_distributions.png")
    plt.close(fig)

    with open(tables / "eda_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)
    return summary


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    summary = run(load_config())
    print(json.dumps({k: summary[k] for k in ("coverage", "seasonality", "decomposition", "volatility",
                                              "price_arrival", "iss002")}, indent=1, default=str))


if __name__ == "__main__":
    main()
