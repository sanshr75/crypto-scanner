# Mobile-Friendly Crypto Scanner

Beginner-friendly crypto scanner ready for GitHub mobile upload.

## Setup Steps
1. Create a free GitHub account (done).
2. Create a new repository: crypto-scanner.
3. Upload all files from this ZIP to the repo.
4. Go to Settings → Secrets → New repository secret → Name: ETHERSCAN_API_KEY → Value: your free API key from https://etherscan.io.
5. Once uploaded, the GitHub Action will automatically run every 6 hours.
6. After the first run, download CSV output from Actions → Artifacts → scan_output.zip.
7. (Optional) Later you can integrate Google Sheets for live view.