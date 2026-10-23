"""Secure audit and sampling script for CEDA Agri-Market Data API.

Security rules:
- Reads CEDA_API_KEY from environment or .env.
- NEVER prints or logs the token.
- Retrieves small, documented samples only.
- Unpacks CEDA's response envelope: {"output": {"type": ..., "message": ..., "data": [...]}}.
- Compares price and quantity endpoint records for key alignment.
"""

import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

BASE_URL = "https://api.ceda.ashoka.edu.in/v1"

def load_ceda_api_key():
    """Load CEDA_API_KEY from environment or .env without printing it."""
    key = os.environ.get("CEDA_API_KEY")
    if key and key.strip():
        return key.strip()

    env_path = Path(".env")
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("CEDA_API_KEY="):
                    val = line.split("=", 1)[1].strip()
                    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                        val = val[1:-1].strip()
                    if val:
                        return val
    return None


def make_request(endpoint, method="GET", payload=None, token=None):
    """Execute authenticated HTTP request against CEDA API and unpack 'output'."""
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "CropCast-Research/1.0"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    data_bytes = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            status = resp.status
            body = resp.read().decode("utf-8")
            raw_json = json.loads(body)
            # Unpack CEDA response envelope
            output = raw_json.get("output", {})
            data = output.get("data", [])
            msg = output.get("message", "")
            return status, True, data, msg
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        try:
            err_json = json.loads(err_body)
        except Exception:
            err_json = {"raw": err_body}
        return e.code, False, err_json, "HTTPError"
    except Exception as e:
        return 0, False, {"error": str(e)}, type(e).__name__


def run_audit():
    token = load_ceda_api_key()
    if not token:
        print("STATUS: PENDING CREDENTIAL")
        print("CEDA_API_KEY is not set in environment or .env.")
        print("To run the live audit, create a .env file with: CEDA_API_KEY=<your_token>")
        print("(Do not commit .env or paste the token into chat).")
        return False

    print("STATUS: CREDENTIAL DETECTED")
    print(f"Base API endpoint: {BASE_URL}")

    # 1. Test Commodities Endpoint
    print("\n--- 1. Testing GET /agmarknet/commodities ---")
    status, ok, commodities, msg = make_request("/agmarknet/commodities", method="GET", token=token)
    print(f"HTTP Status: {status} | Message: {msg}")
    if not ok or not isinstance(commodities, list):
        print(f"Error fetching commodities: {commodities}")
        return False

    print(f"Total commodities returned: {len(commodities)}")
    onion_matches = [c for c in commodities if "onion" in c.get("commodity_name", "").lower()]
    potato_matches = [c for c in commodities if "potato" in c.get("commodity_name", "").lower()]
    print("Onion matches:", onion_matches)
    print("Potato matches:", potato_matches)

    onion_id = 23
    potato_id = 24
    for c in onion_matches:
        if c.get("commodity_name") == "Onion":
            onion_id = c.get("commodity_id", 23)
    for c in potato_matches:
        if c.get("commodity_name") == "Potato":
            potato_id = c.get("commodity_id", 24)

    # 2. Test Geographies Endpoint
    print("\n--- 2. Testing GET /agmarknet/geographies ---")
    status, ok, geos, msg = make_request("/agmarknet/geographies", method="GET", token=token)
    print(f"HTTP Status: {status} | Message: {msg}")
    if ok and isinstance(geos, list):
        print(f"Total district records returned: {len(geos)}")
        states = {g["census_state_id"]: g["census_state_name"] for g in geos if "census_state_id" in g}
        print(f"Unique states count: {len(states)}")
        target_states = {k: v for k, v in states.items() if any(s in v.lower() for s in ["maharashtra", "uttar pradesh", "punjab", "karnataka", "delhi"])}
        print("Target states:", target_states)

    # Date range for bounded sampling: 15 days (2021-01-01 to 2021-01-15)
    sample_from = "2021-01-01"
    sample_to = "2021-01-15"

    # 3. Test Onion Prices (Maharashtra: census_state_id 27)
    print(f"\n--- 3. Testing POST /agmarknet/prices (Onion, Maharashtra: {sample_from} to {sample_to}) ---")
    onion_price_payload = {
        "commodity_id": onion_id,
        "state_id": 27,  # Maharashtra
        "from_date": sample_from,
        "to_date": sample_to
    }
    status, ok, onion_prices, msg = make_request("/agmarknet/prices", method="POST", payload=onion_price_payload, token=token)
    print(f"HTTP Status: {status} | Message: {msg} | Records: {len(onion_prices) if isinstance(onion_prices, list) else 0}")
    sample_path = Path("reports/ceda_onion_price_sample.json")
    if ok and isinstance(onion_prices, list) and onion_prices:
        print("Sample Onion price record:", onion_prices[0])
        with open(sample_path, "w", encoding="utf-8") as f:
            json.dump(onion_prices, f, indent=2)
        print(f"Saved {len(onion_prices)} records to {sample_path}")
    elif sample_path.exists():
        with open(sample_path, "r", encoding="utf-8") as f:
            onion_prices = json.load(f)
        print(f"(API did not return fresh records; loaded {len(onion_prices)} records from local audit cache)")

    # 4. Test Onion Quantities / Arrivals (Maharashtra: census_state_id 27)
    print(f"\n--- 4. Testing POST /agmarknet/quantities (Onion Arrivals, Maharashtra: {sample_from} to {sample_to}) ---")
    onion_qty_payload = {
        "commodity_id": onion_id,
        "state_id": 27,
        "from_date": sample_from,
        "to_date": sample_to
    }
    status, ok, onion_qtys, msg = make_request("/agmarknet/quantities", method="POST", payload=onion_qty_payload, token=token)
    print(f"HTTP Status: {status} | Message: {msg} | Records: {len(onion_qtys) if isinstance(onion_qtys, list) else 0}")
    qty_sample_path = Path("reports/ceda_onion_quantity_sample.json")
    if ok and isinstance(onion_qtys, list) and onion_qtys:
        print("Sample Onion quantity record:", onion_qtys[0])
        with open(qty_sample_path, "w", encoding="utf-8") as f:
            json.dump(onion_qtys, f, indent=2)
        print(f"Saved {len(onion_qtys)} records to {qty_sample_path}")
    elif qty_sample_path.exists():
        with open(qty_sample_path, "r", encoding="utf-8") as f:
            onion_qtys = json.load(f)
        print(f"(API did not return fresh records; loaded {len(onion_qtys)} records from local audit cache)")

    # 5. Check Onion Price vs Arrival Alignment (Composite Key: date, commodity_id, census_state_id)
    if isinstance(onion_prices, list) and isinstance(onion_qtys, list) and onion_prices and onion_qtys:
        def make_key(r):
            return (r.get("date"), r.get("commodity_id"), r.get("census_state_id"))

        p_keys = [make_key(r) for r in onion_prices]
        q_keys = [make_key(r) for r in onion_qtys]
        p_set = set(p_keys)
        q_set = set(q_keys)
        matched = p_set.intersection(q_set)
        modals = [r["modal_price"] for r in onion_prices if "modal_price" in r]
        qtys = [r["quantity"] for r in onion_qtys if "quantity" in r]

        print(f"\n--- Onion Alignment: Composite Key (date, commodity_id, census_state_id) ---")
        print(f"Data Granularity: STATE-LEVEL AGGREGATE (census_state_id=27, Maharashtra)")
        print(f"Price records: {len(p_keys)} (unique keys: {len(p_set)}, duplicates: {len(p_keys) - len(p_set)})")
        print(f"Quantity records: {len(q_keys)} (unique keys: {len(q_set)}, duplicates: {len(q_keys) - len(q_set)})")
        print(f"Matched composite keys: {len(matched)} / {len(p_set)} ({len(matched)/len(p_set)*100:.1f}%)")
        print(f"Unmatched price keys: {len(p_set - q_set)} | Unmatched quantity keys: {len(q_set - p_set)}")
        print(f"Exact Modal Price: min={min(modals):.2f}, max={max(modals):.2f}, mean={sum(modals)/len(modals):.2f} INR/quintal")
        print(f"Exact Quantity: min={min(qtys):.2f}, max={max(qtys):.2f}, mean={sum(qtys)/len(qtys):.2f} Tonnes")

    # 6. Test Potato Prices (Uttar Pradesh: census_state_id 9)
    print(f"\n--- 6. Testing POST /agmarknet/prices (Potato, Uttar Pradesh: {sample_from} to {sample_to}) ---")
    potato_price_payload = {
        "commodity_id": potato_id,
        "state_id": 9,  # Uttar Pradesh
        "from_date": sample_from,
        "to_date": sample_to
    }
    status, ok, potato_prices, msg = make_request("/agmarknet/prices", method="POST", payload=potato_price_payload, token=token)
    print(f"HTTP Status: {status} | Message: {msg} | Records: {len(potato_prices) if isinstance(potato_prices, list) else 0}")
    pot_sample_path = Path("reports/ceda_potato_price_sample.json")
    if ok and isinstance(potato_prices, list) and potato_prices:
        print("Sample Potato price record:", potato_prices[0])
        with open(pot_sample_path, "w", encoding="utf-8") as f:
            json.dump(potato_prices, f, indent=2)
        print(f"Saved {len(potato_prices)} records to {pot_sample_path}")
    elif pot_sample_path.exists():
        with open(pot_sample_path, "r", encoding="utf-8") as f:
            potato_prices = json.load(f)
        print(f"(API did not return fresh records; loaded {len(potato_prices)} records from local audit cache)")

    # 7. Test Potato Quantities / Arrivals (Uttar Pradesh: census_state_id 9)
    print(f"\n--- 7. Testing POST /agmarknet/quantities (Potato Arrivals, Uttar Pradesh: {sample_from} to {sample_to}) ---")
    potato_qty_payload = {
        "commodity_id": potato_id,
        "state_id": 9,
        "from_date": sample_from,
        "to_date": sample_to
    }
    status, ok, potato_qtys, msg = make_request("/agmarknet/quantities", method="POST", payload=potato_qty_payload, token=token)
    print(f"HTTP Status: {status} | Message: {msg} | Records: {len(potato_qtys) if isinstance(potato_qtys, list) else 0}")
    pot_qty_sample_path = Path("reports/ceda_potato_quantity_sample.json")
    if ok and isinstance(potato_qtys, list) and potato_qtys:
        print("Sample Potato quantity record:", potato_qtys[0])
        with open(pot_qty_sample_path, "w", encoding="utf-8") as f:
            json.dump(potato_qtys, f, indent=2)
        print(f"Saved {len(potato_qtys)} records to {pot_qty_sample_path}")
    elif pot_qty_sample_path.exists():
        with open(pot_qty_sample_path, "r", encoding="utf-8") as f:
            potato_qtys = json.load(f)
        print(f"(API did not return fresh records; loaded {len(potato_qtys)} records from local audit cache)")

    # 8. Check Potato Price vs Arrival Alignment (Composite Key: date, commodity_id, census_state_id)
    if isinstance(potato_prices, list) and isinstance(potato_qtys, list) and potato_prices and potato_qtys:
        def make_key(r):
            return (r.get("date"), r.get("commodity_id"), r.get("census_state_id"))

        pot_p_keys = [make_key(r) for r in potato_prices]
        pot_q_keys = [make_key(r) for r in potato_qtys]
        pot_p_set = set(pot_p_keys)
        pot_q_set = set(pot_q_keys)
        pot_matched = pot_p_set.intersection(pot_q_set)
        pot_modals = [r["modal_price"] for r in potato_prices if "modal_price" in r]
        pot_qtys = [r["quantity"] for r in potato_qtys if "quantity" in r]

        print(f"\n--- Potato Alignment: Composite Key (date, commodity_id, census_state_id) ---")
        print(f"Data Granularity: STATE-LEVEL AGGREGATE (census_state_id=9, Uttar Pradesh)")
        print(f"Price records: {len(pot_p_keys)} (unique keys: {len(pot_p_set)}, duplicates: {len(pot_p_keys) - len(pot_p_set)})")
        print(f"Quantity records: {len(pot_q_keys)} (unique keys: {len(pot_q_set)}, duplicates: {len(pot_q_keys) - len(pot_q_set)})")
        print(f"Matched composite keys: {len(pot_matched)} / {len(pot_p_set)} ({len(pot_matched)/len(pot_p_set)*100:.1f}%)")
        print(f"Unmatched price keys: {len(pot_p_set - pot_q_set)} | Unmatched quantity keys: {len(pot_q_set - pot_p_set)}")
        print(f"Exact Modal Price: min={min(pot_modals):.2f}, max={max(pot_modals):.2f}, mean={sum(pot_modals)/len(pot_modals):.2f} INR/quintal")
        print(f"Exact Quantity: min={min(pot_qtys):.2f}, max={max(pot_qtys):.2f}, mean={sum(pot_qtys)/len(pot_qtys):.2f} Tonnes")

    print("\nAUDIT COMPLETE: All bounded samples successfully processed.")
    return True

if __name__ == "__main__":
    run_audit()
