#!/usr/bin/env python3
"""
fetch_dev_activity.py
Pulls basic GitHub repository metrics for listed coins.
Outputs: dev_output.csv
Uses only public GitHub API (no token needed, rate-limited but fine for 5–10 coins).
"""

import csv
import requests
from datetime import datetime, timezone

# --- Update these mappings with each coin’s main repo ---
REPOS = {
    'PRIME': 'echelonfoundation/prime-sdk',    # Example placeholder
    'LKI':   'LykaLabs/lyka-core',              # Example placeholder
    'TAO':   'bittensor/bittensor',
    'RNDR':  'rendernetwork/render-token',
    'PYTH':  'pyth-network/pyth-client'
}

OUTPUT_FILE = 'dev_output.csv'

def fetch_repo_stats(repo_full_name):
    """Return commits (30d), stars, forks, and open issues."""
    base = f'https://api.github.com/repos/{repo_full_name}'
    info = requests.get(base, timeout=15).json()

    # Basic stats
    stars = info.get('stargazers_count', 0)
    forks = info.get('forks_count', 0)
    issues = info.get('open_issues_count', 0)

    # Commit activity (last 30 days)
    commits_url = f'{base}/stats/commit_activity'
    commits_data = requests.get(commits_url, timeout=15).json()
    recent_commits = 0
    if isinstance(commits_data, list) and commits_data:
        recent_commits = commits_data[-4:][0]['total'] if len(commits_data) >= 4 else sum(w['total'] for w in commits_data[-4:])

    return {
        'Repo': repo_full_name,
        'Stars': stars,
        'Forks': forks,
        'OpenIssues': issues,
        'RecentCommits(4w)': recent_commits
    }

def main():
    rows = []
    now_iso = datetime.now(timezone.utc).isoformat()
    for ticker, repo in REPOS.items():
        try:
            stats = fetch_repo_stats(repo)
            stats['Ticker'] = ticker
            stats['LastUpdated'] = now_iso
            rows.append(stats)
        except Exception as e:
            rows.append({'Ticker': ticker, 'Repo': repo, 'Error': str(e)})

    keys = ['Ticker','Repo','Stars','Forks','OpenIssues','RecentCommits(4w)','LastUpdated']
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {OUTPUT_FILE} with {len(rows)} rows")

if __name__ == '__main__':
    main()
