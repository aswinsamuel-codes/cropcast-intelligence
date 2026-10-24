"""
Summarise the M-8 CEDA pilot responses (see src/data/ceda_pilot.py) into aggregate statistics.

Reads raw pilot responses from data/raw/ceda_pilot_m8/ and the local v1 dataset; writes only
aggregate measurements (counts, shares, correlations, match rates) to
reports/pilot_m8/pilot_summary.json. No daily values are written.

Usage:
    python -m src.analysis.pilot_m8
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from src.config import REPO_ROOT

RAW = REPO_ROOT / "data" / "raw" / "ceda_pilot_m8"
LOG = REPO_ROOT / "reports" / "pilot_m8" / "request_log.json"
OUT = REPO_ROOT / "reports" / "pilot_m8" / "pilot_summary.json"
V1 = REPO_ROOT / "data" / "processed" / "cropcast_analysis_v1.csv"
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _records(entry: Dict[str, Any]) -> pd.DataFrame:
    body = json.loads((REPO_ROOT / entry["raw_file"]).read_text(encoding="utf-8"))
    out = body.get("output", body)
    df = pd.DataFrame(out.get("data", []) if isinstance(out, dict) else out)
    if "date" in df:
        df["date"] = pd.to_datetime(df["date"].str[:10])
    return df


def _gaps(dates: pd.DatetimeIndex, start: str, end: str) -> Dict[str, Any]:
    cal = pd.date_range(start, end, freq="D")
    present = cal.isin(dates)
    missing = cal[~present]
    runs, cur = [], 0
    for p in present:
        if not p:
            cur += 1
        elif cur:
            runs.append(cur)
            cur = 0
    if cur:
        runs.append(cur)
    return {"calendar_days": len(cal), "observed_days": int(present.sum()), "missing_days": int((~present).sum()),
            "coverage_pct": round(100 * present.mean(), 2), "gaps": len(runs), "longest_gap_days": max(runs, default=0),
            "missing_by_weekday": {d: int((missing.day_of_week == i).sum()) for i, d in enumerate(WEEKDAYS)}}


def coverage(log: List[Dict[str, Any]], tag: str, start: str, end: str) -> Optional[Dict[str, Any]]:
    pe = [e for e in log if e["label"].startswith(f"{tag}_prices") and e.get("raw_file")]
    qe = [e for e in log if e["label"].startswith(f"{tag}_quantities") and e.get("raw_file")]
    if not pe:
        return None
    p = pd.concat([_records(e) for e in pe], ignore_index=True)
    q = pd.concat([_records(e) for e in qe], ignore_index=True) if qe else pd.DataFrame(columns=["date"])
    res: Dict[str, Any] = {"requested": f"{start}..{end}", "price_fields": sorted(p.columns.astype(str)),
                           "quantity_fields": sorted(q.columns.astype(str)), "price_rows": len(p), "quantity_rows": len(q)}
    if p.empty:
        res["note"] = "no price records returned"
        return res
    res["price_date_range"] = [str(p.date.min().date()), str(p.date.max().date())]
    res["duplicate_price_dates"] = int(p.date.duplicated().sum())
    res["price_coverage"] = _gaps(pd.DatetimeIndex(p.date.unique()), start, end)
    if len(q):
        res["quantity_date_range"] = [str(q.date.min().date()), str(q.date.max().date())]
        res["quantity_coverage"] = _gaps(pd.DatetimeIndex(q.date.unique()), start, end)
        pd_, qd = set(p.date), set(q.date)
        res["price_quantity_date_iou"] = round(len(pd_ & qd) / len(pd_ | qd), 6)
        res["price_dates_without_quantity"] = len(pd_ - qd)
        res["quantity_dates_without_price"] = len(qd - pd_)
        res["zero_quantity_rows"] = int((q["quantity"] == 0).sum())
        res["null_quantity_rows"] = int(q["quantity"].isna().sum())
    res["modal_outside_min_max"] = int(((p.modal_price < p.min_price) | (p.modal_price > p.max_price)).sum())
    res["zero_or_null_modal"] = int(((p.modal_price == 0) | p.modal_price.isna()).sum())
    return res


def national_vs_state(log, commodity: str, series_id: str) -> Optional[Dict[str, Any]]:
    tag = f"{commodity}_national"
    pe = next((e for e in log if e["label"] == f"{tag}_prices_2022" and e.get("raw_file")), None)
    qe = next((e for e in log if e["label"] == f"{tag}_quantities_2022" and e.get("raw_file")), None)
    if not pe:
        return None
    v1 = pd.read_csv(V1, parse_dates=["date"])
    s = v1[(v1.series_id == series_id) & (v1.date.dt.year == 2022)].set_index("date")
    n = _records(pe).set_index("date")
    res: Dict[str, Any] = {"state_series": series_id, "national_fields": sorted(_records(pe).columns.astype(str)),
                           "national_price_days_2022": len(n), "state_price_days_2022": len(s)}
    j = s[["modal_price"]].join(n[["modal_price"]].rename(columns={"modal_price": "modal_price_national"}), how="inner")
    res["overlap_days"] = len(j)
    ratio = j.modal_price_national / j.modal_price
    res["national_to_state_price_ratio"] = {"median": round(float(ratio.median()), 4), "min": round(float(ratio.min()), 4),
                                            "max": round(float(ratio.max()), 4)}
    r = np.log(j).diff().dropna()
    res["daily_log_change_correlation"] = round(float(r.corr().iloc[0, 1]), 4)
    if qe:
        qn = _records(qe).set_index("date")
        jq = s[["arrival_qty"]].join(qn[["quantity"]], how="inner")
        share = jq.arrival_qty / jq.quantity
        res["state_share_of_national_arrivals"] = {"median": round(float(share.median()), 4), "min": round(float(share.min()), 4),
                                                   "max": round(float(share.max()), 4)}
        res["days_state_arrivals_exceed_national"] = int((jq.arrival_qty > jq.quantity * (1 + 1e-9)).sum())
    return res


def composition(log) -> Dict[str, Any]:
    """Mandi-level records from a request with district_id (CEDA returns market rows, not district totals)."""
    dp = next((e for e in log if e["label"].startswith("district_") and e["label"].endswith("_prices") and e.get("raw_file")), None)
    dq = next((e for e in log if e["label"].startswith("district_") and e["label"].endswith("_quantities") and e.get("raw_file")), None)
    if not dp:
        return {}
    p, q = _records(dp), (_records(dq) if dq else pd.DataFrame())
    pl = dp["payload"]
    v1 = pd.read_csv(V1, parse_dates=["date"])
    state = v1[(v1.census_state_id == pl["state_id"]) & (v1.commodity_id == pl["commodity_id"])].set_index("date")
    state = state.loc[pl["from_date"]:pl["to_date"]]
    key = ["date", "census_district_id", "market_id"]
    r: Dict[str, Any] = {
        "payload": {k: (len(v) if isinstance(v, list) else v) for k, v in pl.items()},
        "price_fields": sorted(p.columns.astype(str)), "quantity_fields": sorted(q.columns.astype(str)),
        "price_rows": len(p), "quantity_rows": len(q),
        "districts_requested": len(pl["district_id"]), "districts_with_price_rows": int(p.census_district_id.nunique()),
        "markets_with_price_rows": int(p.market_id.nunique()), "markets_with_quantity_rows": int(q.market_id.nunique()) if len(q) else 0,
        "price_rows_sharing_market_day": int(p.duplicated(key, keep=False).sum()),
        "max_price_rows_per_market_day": int(p.groupby(key).size().max()),
        "quantity_rows_sharing_market_day": int(q.duplicated(key, keep=False).sum()) if len(q) else 0,
    }
    cnt = p.groupby("date").market_id.nunique()
    r["markets_reporting_price_per_day"] = {"min": int(cnt.min()), "median": float(cnt.median()), "max": int(cnt.max())}
    r["mean_markets_reporting_by_weekday"] = {WEEKDAYS[i]: round(float(v), 2) for i, v in cnt.groupby(cnt.index.day_of_week).mean().items()}
    j = pd.concat([cnt.rename("n"), state.arrival_qty], axis=1, join="inner")
    r["spearman_markets_reporting_vs_state_arrivals"] = round(float(j.n.corr(j.arrival_qty, method="spearman")), 4)
    r["days_compared_with_v1_state"] = len(j)
    # How is the state modal price built from the mandi rows?
    g = p.groupby("date")
    per_market = p.groupby(key).modal_price.mean().groupby("date")
    cand = {"mean_of_all_price_rows": g.modal_price.mean(), "median_of_all_price_rows": g.modal_price.median(),
            "mean_of_market_means": per_market.mean()}
    if len(q):
        m = p.merge(q[key + ["quantity"]], on=key, how="inner")
        m = m[m.quantity > 0]
        cand["arrival_weighted_mean_of_rows"] = m.groupby("date").apply(lambda d: np.average(d.modal_price, weights=d.quantity))
    rec = {}
    for name, series in cand.items():
        jj = pd.concat([state.modal_price.rename("state"), series.rename("agg")], axis=1, join="inner").dropna()
        rel = (jj["agg"] - jj["state"]).abs() / jj["state"]
        rec[name] = {"days_compared": len(jj), "share_of_days_within_1e-9": round(float((rel < 1e-9).mean()), 4),
                     "median_relative_difference": float(f"{rel.median():.3g}")}
    for col in ("min_price", "max_price"):
        jj = pd.concat([state[col].rename("state"), g[col].mean().rename("agg")], axis=1, join="inner")
        rec[f"{col}_equals_mean_of_rows_share"] = round(float((((jj["agg"] - jj["state"]).abs() / jj["state"]) < 1e-9).mean()), 4)
    r["state_price_reconstruction"] = rec
    if len(q):
        qs = q.groupby("date").quantity.sum()
        jq = pd.concat([qs.rename("s"), state.arrival_qty], axis=1, join="inner")
        r["state_arrivals_equal_sum_of_market_quantities_share"] = round(float(((jq.s - jq.arrival_qty).abs() <= 1e-6 * jq.arrival_qty).mean()), 4)
        pk = set(map(tuple, p[key].drop_duplicates().itertuples(index=False)))
        qk = set(map(tuple, q[key].itertuples(index=False)))
        r["market_days_with_price_but_no_quantity_row"] = len(pk - qk)
        r["market_days_with_quantity_but_no_price_row"] = len(qk - pk)
        r["zero_quantity_rows"] = int((q.quantity == 0).sum())
        r["null_quantity_rows"] = int(q.quantity.isna().sum())
        calendar = pd.date_range(pl["from_date"], pl["to_date"])
        r["calendar_days"] = len(calendar)
        r["days_with_no_price_rows"] = int((~calendar.isin(p.date.unique())).sum())
    return r


def main() -> int:
    log = json.loads(LOG.read_text(encoding="utf-8"))["requests"]
    today = pd.Timestamp.today().normalize()
    summary: Dict[str, Any] = {
        "requests": {"attempted": len(log), "http_200": sum(e.get("http_status") == 200 for e in log),
                     "failed": [{k: e.get(k) for k in ("n", "label", "http_status", "error")} for e in log if e.get("http_status") != 200],
                     "http_200_but_empty": [{k: e.get(k) for k in ("n", "label", "envelope_message")} for e in log
                                            if e.get("http_status") == 200 and e.get("rows") == 0]},
        "coverage": {
            "onion_karnataka_2023_2025": coverage(log, "onion_karnataka", "2023-01-01", "2025-10-30"),
            "potato_west_bengal_2023_2025": coverage(log, "potato_west_bengal", "2023-01-01", "2025-10-30"),
        },
        "national_vs_state_2022": {
            "onion": national_vs_state(log, "onion", "onion_maharashtra"),
            "potato": national_vs_state(log, "potato", "potato_uttar_pradesh"),
        },
        "composition": composition(log),
    }
    fe = next((e for e in log if e["label"] == "onion_national_prices_2026"), None)
    if fe:
        summary["freshness"] = {"requested": f"2026-01-01..{fe['requested_at'][:10]}", "http_status": fe.get("http_status"),
                                "rows": fe.get("rows"), "latest_record_date": fe.get("date_max"),
                                "lag_days_at_request": (pd.Timestamp(fe["requested_at"][:10]) - pd.Timestamp(fe["date_max"])).days if fe.get("date_max") else None}
    OUT.write_text(json.dumps(summary, indent=1, default=str) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
