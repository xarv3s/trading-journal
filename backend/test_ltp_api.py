import requests
import json
import os
import sys

# Add backend directory to path to import KiteClient if needed, 
# but we prefer to just read the file directly to avoid import issues if possible.
# However, we need the token.

def load_token():
    try:
        with open("backend/access_token.json", "r") as f:
            data = json.load(f)
            return data.get("access_token")
    except FileNotFoundError:
        try:
            with open("access_token.json", "r") as f:
                data = json.load(f)
                return data.get("access_token")
        except:
            return None

def test_ltp():
    token = load_token()
    if not token:
        print("Could not load token.")
        return

    url = "http://localhost:8000/api/v1/market-data/ltp"
    headers = {
        "Content-Type": "application/json",
        # We don't pass Authorization header because the backend currently 
        # loads the token from file internally (in get_ltp -> KiteClient.load_access_token).
        # But wait, does it?
        # Let's check market_data.py again.
    }
    
    # market_data.py:
    # token = KiteClient.load_access_token()
    # So it loads from file. It doesn't use the header.
    
    payload = ["NSE:NIFTY 50", "NSE:SBIN"]
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_ltp()
