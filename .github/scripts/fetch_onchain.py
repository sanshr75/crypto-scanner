#!/usr/bin/env python3
"""
fetch_onchain.py
Lightweight on-chain data fetcher (free-data).
Outputs: onchain_output.csv with simple holder and transfer metrics.

Notes:
- Requires ETHERSCAN_API_KEY in environment (GitHub Secrets used by Actions).
- Works for tokens deployed on EVM chains where Etherscan-compatible explorer exists.
- This is an incremental, simple heuristic version we will improve later.
"""

import os
import time
import csv
import requests
from datetime import datetime, timezone, timedelta

ETHERSCAN_API = 'https://api.etherscan.io/api'
ETHERSCAN_API_KEY = os.environ.get('ETHERSCAN_API_KEY') or ''

# Minimal watchlist format: use same tickers/ids as your scanner
WATCHLIST = [
    {'ticker': 'PRIME', 'contract': '0xb23d80f5fefcddaa212212f028021b41ded428cf', 'chain': 'ethereum'},
    {'ticker': 'LKI',   'contract': '0x3D1A0e1dE8e17bD50A865A340a3F5D8D1f46A1F1', 'chain': 'ethereum'},  # Lyka AI (double-check later)
    {'ticker': 'TAO',   'contract': '0x7c81509037a9c0fddf02e0e4e8a855f1e1b1941a', 'chain': 'ethereum'},
    {'ticker': 'RNDR',  'contract': '0x6de037ef9ad2725eb40118bb1702ebb27e4aeb24', 'chain': 'ethereum'},
    {'ticker': 'PYTH',  'contract': '0x0c9c7712c83b3c70e7c5e11100d33d9401f18538', 'chain': 'ethereum'},
]

OUTPUT_CSV = 'onchain_output.csv'

# Small list of known exchange addresses (example). Not exhaustive.
# We'll use these to mark transfers to exchanges as 'possible sell' signals.
KNOWN_EXCHANGE_ADDRESSES = {
    # Binance hot wallet example (short list). We will use a tiny set; expand later.
    'binance': [
        '0xbe0eb53f46cd790cd13851d5eff43d12404d33e8', # this is an example address
    ],
    # Add known exchange addresses later for more accuracy.
}

def safe_get(d, *keys, default=None):
    try:
        cur = d
        for k in keys:
            cur = cur[k]
        return cur
    except:
        return default

def get_holder_count(contract):
    """
    Uses Etherscan 'tokenholdercount' if available.
    """
    try:
        params = {'module':'token','action':'tokenholdercount','contractaddress': contract, 'apikey': ETHERSCAN_API_KEY}
        r = requests.get(ETHERSCAN_API, params=params, timeout=15)
        j = r.json()
        if j.get('status') == '1' and 'result' in j:
            return int(j['result'])
    except Exception as e:
        # ignore and return None
        pass
    return None

def get_recent_transfers(contract, offset=100):
    """
    Returns recent token transfers (basic) using tokentx endpoint.
    """
    try:
        params = {'module':'account','action':'tokentx','contractaddress':contract,'page':1,'offset':offset,'sort':'desc','apikey':ETHERSCAN_API_KEY}
        r = requests.get(ETHERSCAN_API, params=params, timeout=20)
        j = r.json()
        if j.get('status') == '1' and isinstance(j.get('result'), list):
            return j.get('result')
    except Exception as e:
        pass
    return []

def count_transfers_to_exchanges(transfers):
    """
    Heuristic: count transfers where 'to' matches any known exchange addresses.
    Returns count and estimated token amount (we don't try to decode decimals here).
    """
    cnt = 0
    for tx in transfers:
        to_addr = tx.get('to','').lower()
        for ex, addrs in KNOWN_EXCHANGE_ADDRESSES.items():
            if to_addr in [a.lower() for a in addrs]:
                cnt += 1
    return cnt

def main():
    rows = []
    now_iso = datetime.now(timezone.utc).isoformat()
    for t in WATCHLIST:
        contract = t.get('contract','').lower()
        holders = get_holder_count(contract)
        transfers = get_recent_transfers(contract, offset=100)
        transfer_count = len(transfers)
        exflow_count = count_transfers_to_exchanges(transfers)

        row = {
            'Ticker': t['ticker'],
            'Contract': contract,
            'Holders': holders if holders is not None else '',
            'RecentTransfers_100': transfer_count,
            'ExchangeTransferCount_100': exflow_count,
            'LastUpdated': now_iso
        }
        rows.append(row)
        time.sleep(1.1)  # friendly to API rate limits

     # Debug: see what data we're collecting before writing CSV
    print("=== DEBUG: Raw Results ===")
    print(rows)

    # Write CSV
    keys = list(rows[0].keys()) if rows else ['Ticker','Contract','Holders','RecentTransfers_100','ExchangeTransferCount_100','LastUpdated']
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    print(f"Wrote {OUTPUT_CSV} with {len(rows)} rows")

if __name__ == '__main__':
    main()

def get_onchain_data(contract_address):
    # Dummy fallback in case real fetch fails
    return {
        'holders': 0,
        'recent_transfers_100': 0,
        'exchange_transfer_count_100': 0
    }
