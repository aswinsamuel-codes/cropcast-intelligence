"""
M-8 CEDA feasibility pilot: a bounded, logged sequence of CEDA API requests.

Unlike the ingestion pipeline, this client never retries on its own: every HTTP attempt counts
against a hard cap (default 26, the researcher-approved pilot budget) and a 429 stops the run.
Requests are spaced 95 s apart (<= 38 per hour, under CEDA's 40 per hour limit).

Raw responses go to data/raw/ceda_pilot_m8/ (git-ignored; CEDA redistribution not granted).
The request log (parameters, timestamps, HTTP status, row counts, date ranges; no data values,
no credentials) goes to reports/pilot_m8/request_log.json.

Usage:
    python -m src.data.ceda_pilot phase1            # fixed requests (geographies, coverage, national)
    python -m src.data.ceda_pilot phase2 --state 27 --districts 1,2,3 --from 2022-01-01 --to 2022-03-31
    python -m src.data.ceda_pilot markets --state 27 --district 5
    python -m src.data.ceda_pilot market-level --state 27 --district 5 --markets 10,11 --from ... --to ...
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import REPO_ROOT
from src.data.ingest_ceda import BASE_URL, load_api_key

RAW_DIR = REPO_ROOT / "data" / "raw" / "ceda_pilot_m8"
LOG_PATH = REPO_ROOT / "reports" / "pilot_m8" / "request_log.json"
BUDGET = 26
SPACING_SECONDS = 95.0

ONION, POTATO = 23, 24
# Candidate pilot states; codes are checked against /geographies before any data request.
PILOT_STATES = {29: "karnataka", 19: "west bengal"}


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


class PilotClient:
    def __init__(self, budget: int = BUDGET):
        self.key = load_api_key(REPO_ROOT / ".env")
        self.log: Dict[str, Any] = (json.loads(LOG_PATH.read_text(encoding="utf-8")) if LOG_PATH.exists()
                                    else {"budget": budget, "requests": []})
        self.budget = self.log["budget"]
        # Spacing also holds across separate runs: start from the last logged request time.
        last = self.log["requests"][-1]["requested_at"] if self.log["requests"] else None
        self._last = datetime.datetime.fromisoformat(last).timestamp() if last else 0.0
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    @property
    def used(self) -> int:
        return len(self.log["requests"])

    def _save_log(self) -> None:
        LOG_PATH.write_text(json.dumps(self.log, indent=1) + "\n", encoding="utf-8")

    def call(self, label: str, method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """One HTTP attempt. Returns the unpacked `data`, [] for an empty result, or None on failure."""
        if self.used >= self.budget:
            raise RuntimeError(f"Pilot budget of {self.budget} requests reached; stopping before {label}.")
        wait = SPACING_SECONDS - (time.time() - self._last)
        if self._last and wait > 0:
            time.sleep(wait)
        entry: Dict[str, Any] = {"n": self.used + 1, "label": label, "method": method, "path": path,
                                 "payload": payload, "requested_at": _now()}
        req = urllib.request.Request(
            BASE_URL + path, data=json.dumps(payload).encode() if payload is not None else None, method=method,
            headers={"Accept": "application/json", "Content-Type": "application/json",
                     "Authorization": f"Bearer {self.key}", "User-Agent": "CropCast-Research/1.0"})
        data, raw = None, None
        t0 = time.time()
        self._last = t0
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                entry["http_status"] = resp.status
                entry["rate_limit_remaining"] = resp.headers.get("RateLimit-Remaining")
                raw = resp.read()
        except urllib.error.HTTPError as e:
            entry["http_status"] = e.code
            entry["error"] = e.read().decode("utf-8", errors="replace")[:300]
        except Exception as e:  # timeouts, connection errors: logged, never retried automatically
            entry["http_status"] = None
            entry["error"] = f"{type(e).__name__}: {e}"
        entry["seconds"] = round(time.time() - t0, 1)
        if raw is not None:
            body = json.loads(raw.decode("utf-8"))
            out = body.get("output", body) if isinstance(body, dict) else body
            entry["envelope_type"] = out.get("type") if isinstance(out, dict) else None
            entry["envelope_message"] = out.get("message") if isinstance(out, dict) else None
            data = out.get("data", out) if isinstance(out, dict) else out
            fname = f"{entry['n']:02d}_{label}.json"
            (RAW_DIR / fname).write_text(json.dumps(body), encoding="utf-8")
            entry["raw_file"] = f"data/raw/ceda_pilot_m8/{fname}"
            entry["raw_sha256"] = hashlib.sha256((RAW_DIR / fname).read_bytes()).hexdigest()
            entry["response_bytes"] = len(raw)
            if isinstance(data, list):
                entry["rows"] = len(data)
                dates = sorted({r["date"][:10] for r in data if isinstance(r, dict) and r.get("date")})
                if dates:
                    entry["date_min"], entry["date_max"], entry["unique_dates"] = dates[0], dates[-1], len(dates)
                if data and isinstance(data[0], dict):
                    entry["fields"] = sorted(data[0].keys())
        self.log["requests"].append(entry)
        self._save_log()
        status = entry.get("http_status")
        print(f"[{entry['n']:02d}/{self.budget}] {label}: HTTP {status}, rows {entry.get('rows')}, "
              f"{entry.get('date_min', '')}..{entry.get('date_max', '')} ({entry['seconds']}s) {entry.get('error', '')}",
              flush=True)
        if status == 429:
            raise RuntimeError("HTTP 429 received; stopping the pilot to protect the quota.")
        return data if status == 200 else None


def _range(commodity: int, state: int, start: str, end: str, **extra) -> Dict[str, Any]:
    return {"commodity_id": commodity, "state_id": state, "from_date": start, "to_date": end, **extra}


def phase1(c: PilotClient) -> None:
    geo = c.call("geographies", "GET", "/agmarknet/geographies")
    if geo is None:
        raise RuntimeError("geographies request failed; stopping before any data request")
    names = {}
    for g in geo:
        sid = g.get("state_id", g.get("census_state_id"))
        names[sid] = (g.get("state_name") or g.get("census_state_name") or "").lower()
    for sid, want in PILOT_STATES.items():
        if want not in names.get(sid, ""):
            raise RuntimeError(f"state code {sid} is {names.get(sid)!r}, expected {want!r}; stopping")
    # 2023-2025 coverage for one new onion state and one new potato state, in 12-month chunks
    for commodity, state, tag in ((ONION, 29, "onion_karnataka"), (POTATO, 19, "potato_west_bengal")):
        for year in (2023, 2024, 2025):
            for ep in ("prices", "quantities"):
                c.call(f"{tag}_{ep}_{year}", "POST", f"/agmarknet/{ep}", _range(commodity, state, f"{year}-01-01", f"{year}-12-31"))
    # National series for 2022, overlapping the v1 state data
    for commodity, tag in ((ONION, "onion_national"), (POTATO, "potato_national")):
        for ep in ("prices", "quantities"):
            c.call(f"{tag}_{ep}_2022", "POST", f"/agmarknet/{ep}", _range(commodity, 0, "2022-01-01", "2022-12-31"))
    # Freshness: latest national onion price record
    c.call("onion_national_prices_2026", "POST", "/agmarknet/prices", _range(ONION, 0, "2026-01-01", datetime.date.today().isoformat()))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("phase", choices=["phase1", "phase2", "markets", "market-level", "probe"])
    p.add_argument("--label", help="probe: request label (uses every district of --state, or all 640 for --state 0)")
    p.add_argument("--commodity", type=int, default=ONION)
    p.add_argument("--state", type=int)
    p.add_argument("--district", type=int)
    p.add_argument("--districts")
    p.add_argument("--markets")
    p.add_argument("--from", dest="start")
    p.add_argument("--to", dest="end")
    a = p.parse_args()
    c = PilotClient()
    try:
        if a.phase == "phase1":
            phase1(c)
        elif a.phase == "phase2":
            ids = [int(x) for x in a.districts.split(",")]
            for ep in ("prices", "quantities"):
                c.call(f"district_{a.commodity}_{a.state}_{ep}", "POST", f"/agmarknet/{ep}",
                       _range(a.commodity, a.state, a.start, a.end, district_id=ids))
        elif a.phase == "probe":
            # Exactly one `prices` request with an explicit district list taken from the stored geographies.
            geo = json.loads((RAW_DIR / "01_geographies.json").read_text(encoding="utf-8"))["output"]["data"]
            ids = sorted({g["census_district_id"] for g in geo if a.state == 0 or g["census_state_id"] == a.state})
            print(f"probe {a.label}: commodity {a.commodity}, state {a.state}, {len(ids)} district IDs, {a.start}..{a.end}")
            c.call(a.label, "POST", "/agmarknet/prices", _range(a.commodity, a.state, a.start, a.end, district_id=ids))
        elif a.phase == "markets":
            c.call(f"markets_{a.commodity}_{a.state}_{a.district}", "POST", "/agmarknet/markets",
                   {"commodity_id": a.commodity, "state_id": a.state, "district_id": a.district, "indicator": "price"})
        else:
            ids = [int(x) for x in a.markets.split(",")]
            for ep in ("prices", "quantities"):
                c.call(f"market_{a.commodity}_{a.state}_{a.district}_{ep}", "POST", f"/agmarknet/{ep}",
                       _range(a.commodity, a.state, a.start, a.end, district_id=[a.district], market_id=ids))
    finally:
        print(f"requests used: {c.used}/{c.budget}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
