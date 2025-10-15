#!/usr/bin/env python3
"""
crypto_scanner.py - robust market scanner (clean, error-tolerant)

What it does:
- Fetches market data (CoinGecko) for the WATCHLIST
- Writes scan_output.csv
- Attempts to run two helper scripts (if present) via subprocess:
    .github/scripts/fetch_onchain.py   -> produces onchain_output.csv
    .github/scripts/fetch_dev_activity.py -> produces dev_output.csv
- Captures and prints subprocess stdout/stderr so you can debug in Actions logs
- Never raises unhandled exceptions (prints them and continues) so workflow doesn't fail silently
"""

import os
import time
import csv
import requests
from datetime import datetime, timezone

COINGECKO_BASE = "https://api.coingecko.com/api/v3"
OUTPUT_CSV = "scan_output.csv"

# Simple watchlist: update these entries yourself later if needed
WATCHLIST = [
    {"ticker": "PRIME", "coingecko_id": "echelon-prime", "contract": "0xb23d80f5fefcddaa212212f028021b41ded428cf"},
    {"ticker": "LKI",   "coingecko_id": "laika-ai",      "contract": "0x3D1A0e1dE8e17bD50A865A340a3F5D8D1f46A1F1"},
    {"ticker": "TAO",   "coingecko_id": "bittensor",     "contract": "0x7c81509037a9c0fddf02e0e4e8a855f1e1b1941a"},
    {"ticker": "RNDR",  "coingecko_id": "render-token",  "contract": "0x6de037ef9ad2725eb40118bb1702ebb27e4aeb24"},
    {"ticker": "PYTH",  "coingecko_id": "pyth-network",   "contract": "0x0c9c7712c83b3c70e7c5e11100d33d9401f18538"},
]

def safe_get(d, *keys, default=None):
    try:
        cur = d
        for k in keys:
            cur = cur[k]
        return cur
    except Exception:
        return default

def get_price_info(coingecko_id):
    """Return a dict with current_price, change_24h, change_7d, market_cap, volume_24h"""
    try:
        url = f"{COINGECKO_BASE}/coins/{coingecko_id}"
        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false",
            "sparkline": "false",
        }
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        j = r.json()
        md = j.get("market_data", {})
        return {
            "current_price": safe_get(md, "current_price", "usd"),
            "change_24h": md.get("price_change_percentage_24h"),
            "change_7d": md.get("price_change_percentage_7d"),
            "market_cap": safe_get(md, "market_cap", "usd"),
            "volume_24h": safe_get(md, "total_volume", "usd"),
        }
    except Exception as e:
        print(f"[WARN] CoinGecko fetch failed for {coingecko_id}: {e}")
        return {
            "current_price": None,
            "change_24h": None,
            "change_7d": None,
            "market_cap": None,
            "volume_24h": None,
        }

def write_csv(path, rows):
    if not rows:
        print(f"[WARN] No rows to write for {path}")
        return
    keys = list(rows[0].keys())
    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)
        print(f"[OK] Wrote {path} ({len(rows)} rows)")
    except Exception as e:
        print(f"[ERROR] Failed to write {path}: {e}")

def run_subprocess_script(script_path):
    """
    Run another python script via subprocess, capture stdout/stderr, and return True/False.
    This avoids import issues and ensures scripts run in separate process.
    """
    import subprocess
    if not os.path.exists(script_path):
        print(f"[INFO] Script not found, skipping: {script_path}")
        return False

    try:
        print(f"[INFO] Running {script_path} ...")
        result = subprocess.run(
            ["python", script_path],
            capture_output=True,
            text=True,
            check=False
        )
        # Print stdout/stderr for debugging in Actions logs
        if result.stdout:
            print(f"[{os.path.basename(script_path)} stdout]\n{result.stdout}")
        if result.stderr:
            print(f"[{os.path.basename(script_path)} stderr]\n{result.stderr}")
        if result.returncode == 0:
            print(f"[OK] {script_path} finished successfully")
            return True
        else:
            print(f"[WARN] {script_path} exited with code {result.returncode}")
            return False
    except Exception as e:
        print(f"[ERROR] Running {script_path} failed: {e}")
        return False

def main():
    rows = []
    for t in WATCHLIST:
        cg = get_price_info(t.get("coingecko_id"))
        row = {
            "Ticker": t.get("ticker"),
            "Contract": t.get("contract"),
            "Price": cg.get("current_price"),
            "24h%": cg.get("change_24h"),
            "7d%": cg.get("change_7d"),
            "MarketCap": cg.get("market_cap"),
            "24hVol": cg.get("volume_24h"),
            "LastUpdated": datetime.now(timezone.utc).isoformat(),
        }
        rows.append(row)
        time.sleep(1.0)  # friendly to API limits

    write_csv(OUTPUT_CSV, rows)

if __name__ == "__main__":
    # 1) Run main scanner to produce scan_output.csv
    try:
        main()
    except Exception as e:
        print(f"[ERROR] Main scanner failed: {e}")

    # 2) Run on-chain fetcher if available
    run_subprocess_script(".github/scripts/fetch_onchain.py")

    # 3) Run dev-activity fetcher if available
    run_subprocess_script(".github/scripts/fetch_dev_activity.py")

    # 4) Done. Actions workflow will collect artifacts (CSV files) if they exist.
    print("[INFO] crypto_scanner.py finished")
