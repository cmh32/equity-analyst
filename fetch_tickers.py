import requests
import json
import os

DATA_DIR = "data"
TICKERS_FILE = os.path.join(DATA_DIR, "tickers.json")
SEC_URL = "https://www.sec.gov/files/company_tickers.json"

def fetch_and_save_tickers():
    print(f"Fetching tickers from {SEC_URL}...")
    headers = {
        "User-Agent": "EquityAnalyst/1.0 (colin@example.com)"  # SEC requires a User-Agent with email
    }
    
    try:
        response = requests.get(SEC_URL, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Extract just the tickers into a sorted list
        # data is a dict of dicts: {"0": {"ticker": "AAPL", ...}, "1": ...}
        valid_tickers = sorted([entry["ticker"] for entry in data.values()])
        
        # Save to file
        with open(TICKERS_FILE, "w") as f:
            json.dump(valid_tickers, f, indent=2)
            
        print(f"✅ Successfully saved {len(valid_tickers)} tickers to {TICKERS_FILE}")
        
    except Exception as e:
        print(f"❌ Error fetching tickers: {e}")

if __name__ == "__main__":
    fetch_and_save_tickers()
