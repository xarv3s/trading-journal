import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.kite_service import KiteClient
from app.core.config import get_settings

settings = get_settings()

def check_kite():
    print("Checking Kite Connectivity...")
    token = KiteClient.load_access_token()
    if not token:
        print("No access token found.")
        return

    print(f"Token found: {token[:10]}...")
    kite = KiteClient(api_key=settings.KITE_API_KEY, access_token=token)
    
    if kite.validate_token():
        print("Token is valid.")
    else:
        print("Token is INVALID.")
        return

    print("Fetching LTP for NSE:NIFTY 50...")
    ltp = kite.fetch_ltp(["NSE:NIFTY 50"])
    print(f"LTP: {ltp}")

    print("Fetching Margins for a sample trade...")
    # Sample trade item
    item = {
        'type': 'TRADE',
        'id': 'test_trade',
        'constituents': [{
            'exchange': 'NSE',
            'tradingsymbol': 'SBIN',
            'transaction_type': 'BUY',
            'quantity': 1,
            'product': 'MIS',
            'variety': 'regular',
            'price': 0
        }]
    }
    margins = kite.fetch_margins([item])
    print(f"Margins: {margins}")

if __name__ == "__main__":
    check_kite()
