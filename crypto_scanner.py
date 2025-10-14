#!/usr/bin/env python3
"""
Mobile-ready Crypto Scanner Example
Pre-loaded with 5 tokens for immediate results.
Requires Python 3 and free API keys from Etherscan.
"""
import os
import csv
import time
import requests
from datetime import datetime, timezone
from .github.scripts.fetch_onchain import main as fetch_onchain_main

COINGECKO_BASE = 'https://api.coingecko.com/api/v3'
ETHERSCAN_API_KEY = os.environ.get('ETHERSCAN_API_KEY') or 'YOUR_ETHERSCAN_KEY'

WATCHLIST = [
    {'ticker':'PRIME', 'coingecko_id':'echelon-prime'},
    {'ticker':'LKI', 'coingecko_id':'laika-ai'},
    {'ticker':'TAO', 'coingecko_id':'bittensor'},
    {'ticker':'RNDR', 'coingecko_id':'render-token'},
    {'ticker':'PYTH', 'coingecko_id':'pyth-network'},
]

OUTPUT_CSV = 'scan_output.csv'

def get_price_info(coingecko_id):
    try:
        url = f"{COINGECKO_BASE}/coins/{coingecko_id}"
        params = {'localization':'false','tickers':'false','market_data':'true','community_data':'false','developer_data':'false','sparkline':'false'}
        r = requests.get(url, params=params, timeout=20)
        j = r.json()
        md = j.get('market_data',{})
        return {
            'current_price': md.get('current_price',{}).get('usd'),
            'change_24h': md.get('price_change_percentage_24h'),
            'change_7d': md.get('price_change_percentage_7d'),
            'market_cap': md.get('market_cap',{}).get('usd'),
            'volume_24h': md.get('total_volume',{}).get('usd')
        }
    except:
        return {}

def main():
    rows = []
    for t in WATCHLIST:
        cg = get_price_info(t['coingecko_id'])
        onchain = fetch_onchain(t['contract_address'])  # <--- add this line

        row = {
            'Ticker': t['ticker'],
            'Price': cg.get('current_price'),
            '24h%': cg.get('change_24h'),
            '7d%': cg.get('change_7d'),
            'MarketCap': cg.get('market_cap'),
            '24hVol': cg.get('volume_24h'),
            'Holders': onchain.get('holders'),
            'RecentTransfers_100': onchain.get('recent_transfers_100'),
            'ExchangeTransferCount_100': onchain.get('exchange_transfer_count_100'),
            'LastUpdated': datetime.now(timezone.utc).isoformat()
        }

        rows.append(row)
        time.sleep(1)

    keys = list(rows[0].keys())
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    print(f"Wrote {OUTPUT_CSV} with {len(rows)} rows")

if __name__ == '__main__':
    main()

    # Run on-chain scanner after price data is done
    try:
        import subprocess
        print("Running on-chain tracker...")
        subprocess.run(['python', '.github/scripts/fetch_onchain.py'], check=True)
    except Exception as e:
        print("Error running on-chain tracker:", e)
