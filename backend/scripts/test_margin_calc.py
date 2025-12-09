import sys
import os
import json

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.kite_service import KiteClient
from app.core.config import get_settings

def test_margin_calc():
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
    
    print("Fetching margins directly from Kite...")
    orders = []
    for c in item['constituents']:
        orders.append({
            "exchange": c['exchange'],
            "tradingsymbol": c['tradingsymbol'],
            "transaction_type": c['transaction_type'],
            "variety": c.get('variety', 'regular'),
            "product": c['product'],
            "order_type": "MARKET",
            "quantity": c['quantity'],
            "price": 0,
            "trigger_price": 0
        })
        
    try:
        margins = kite_service.kite.basket_order_margins(orders)
        print("Final Margin:")
        print(json.dumps(margins.get('final'), indent=2))
        print("Initial Margin:")
        print(json.dumps(margins.get('initial'), indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_margin_calc()
