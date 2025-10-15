import os
import gspread
from google.oauth2 import service_account
import pandas as pd

SHEET_NAME = "Crypto Market Tracker"
csv_files = ["scan_output.csv", "onchain_output.csv", "dev_output.csv"]

creds_path = "credentials.json"
creds = service_account.Credentials.from_service_account_file(
    creds_path,
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
)
gc = gspread.authorize(creds)
sh = gc.open(SHEET_NAME)

for csv_file in csv_files:
    if not os.path.exists(csv_file):
        print(f"⚠️ {csv_file} not found, skipping.")
        continue
    df = pd.read_csv(csv_file)
    ws_name = csv_file.replace(".csv", "")
    try:
        ws = sh.worksheet(ws_name)
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title=ws_name, rows="100", cols="20")
    ws.clear()
    ws.update([df.columns.values.tolist()] + df.values.tolist())

print("✅ All CSV files uploaded to Google Sheets.")
