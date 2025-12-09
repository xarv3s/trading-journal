import sys
import os
import json

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.kite_service import KiteClient
from app.core.config import get_settings

def verify_margin_fix():
    settings = get_settings()
    token = KiteClient.load_access_token()
    if not token:
        print("No access token found.")
        return

    kite_service = KiteClient(api_key=settings.KITE_API_KEY, access_token=token)
    
    # Construct the item as per page.tsx logic
    item = {
        'type': 'BASKET',
        'id': 'TEST_BASKET',
        'constituents': [
            {'exchange': 'NFO', 'tradingsymbol': 'NIFTY25DEC26500CE', 'transaction_type': 'BUY', 'quantity': 75, 'product': 'NRML', 'variety': 'regular', 'price': 0},
            {'exchange': 'NFO', 'tradingsymbol': 'NIFTY25DEC26500PE', 'transaction_type': 'BUY', 'quantity': 75, 'product': 'NRML', 'variety': 'regular', 'price': 0},
            {'exchange': 'NFO', 'tradingsymbol': 'NIFTY25DEC26000PE', 'transaction_type': 'BUY', 'quantity': 75, 'product': 'NRML', 'variety': 'regular', 'price': 0},
            {'exchange': 'NFO', 'tradingsymbol': 'NIFTY25DEC26000CE', 'transaction_type': 'BUY', 'quantity': 75, 'product': 'NRML', 'variety': 'regular', 'price': 0}
        ]
    }
    
    print("Fetching margins via KiteService...")
    margins = kite_service.fetch_margins([item])
    print(f"Margins: {json.dumps(margins, indent=2)}")
    
    if margins.get('TEST_BASKET', 0) > 0:
        print("SUCCESS: Margin is positive.")
    else:
        print("FAILURE: Margin is still negative or zero.")

if __name__ == "__main__":
    verify_margin_fix()
