import os
import sys
import json
from app.core.config import get_settings

settings = get_settings()
from app.services.kite_service import KiteClient
from app.repositories.trade_repository import TradeRepository
from app.core.database import SessionLocal

# Setup
db = SessionLocal()
repo = TradeRepository(db)

def debug_margin():
    # 1. Load Trade
    trades = repo.get_unified_trades()
    # Handle both object and dict (just in case)
    target_trade = next((t for t in trades if (getattr(t, 'id', None) or t.get('id')) == 'OPEN_53'), None)
    
    if not target_trade:
        print("Trade OPEN_53 not found!")
        return

    # Normalize to dict if it's an object
    if not isinstance(target_trade, dict):
        target_trade = target_trade.__dict__

    print(f"Found Trade: {target_trade['id']}")
    
    # 2. Prepare Margin Items
    items = []
    if target_trade.get('is_basket') == 1:
        # Construct basket order params
        orders = []
        for c in target_trade['constituents']:
            # Constituents might be dicts too
            if not isinstance(c, dict):
                c = c.__dict__
                
            orders.append({
                "exchange": c['exchange'],
                "tradingsymbol": c['trading_symbol'] if 'trading_symbol' in c else c.get('symbol'),
                "transaction_type": 'BUY' if c['type'] == 'LONG' else 'SELL', # Map LONG/SHORT to BUY/SELL
                "variety": "regular",
                "product": c.get('order_type', 'NRML'), # MIS/NRML
                "order_type": "MARKET",
                "quantity": c['qty'],
                "price": 0,
                "trigger_price": 0
            })
        items.append({
            "type": "BASKET",
            "id": target_trade['id'],
            "orders": orders
        })
    else:
        print("Trade is not a basket.")
        return

    # 3. Fetch Margins
    token = KiteClient.load_access_token()
    if not token:
        print("No access token found.")
        return
        
    kite = KiteClient(api_key=settings.KITE_API_KEY, access_token=token)
    
    print("\n--- Fetching Margins ---")
    try:
        # Call the raw kite method to see full response
        response = kite.kite.basket_order_margins(items[0]['orders'])
        print(json.dumps(response, indent=2, default=str))
        
        initial = response.get('initial', {}).get('total', 0)
        final = response.get('final', {}).get('total', 0)
        
        print(f"\nSummary:")
        print(f"Initial (Total) Margin: {initial}")
        print(f"Final (Required) Margin: {final}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_margin()
