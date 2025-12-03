import sys
import os
import pandas as pd
from datetime import datetime
import uuid

# Add the current directory to sys.path to allow imports from app
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.repositories.trade_repository import TradeRepository
from app.services.kite_service import KiteClient

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def simulate_close():
    print("Starting close trade simulation...")
    
    db = next(get_db())
    repo = TradeRepository(db)
    
    # Scenario:
    # Sell remaining 5 TATASTEEL @ 120 (Final Exit)
    
    now = datetime.now()
    
    orders_data = [
        {
            "order_id": str(uuid.uuid4()),
            "status": "COMPLETE",
            "order_timestamp": now,
            "tradingsymbol": "TATASTEEL",
            "transaction_type": "SELL",
            "quantity": 5,
            "average_price": 120.0,
            "exchange": "NSE",
            "product": "CNC",
            "instrument_token": 123456,
            "filled_quantity": 5,
            "pending_quantity": 0,
            "cancelled_quantity": 0
        }
    ]
    
    orders_df = pd.DataFrame(orders_data)
    print(f"Created {len(orders_df)} simulated orders")
    
    open_trades = repo.get_all_open_trades()
    constituents = repo.get_basket_constituents()
    
    # Check if TATASTEEL is in open trades
    tata_trade = next((t for t in open_trades if t.symbol == 'TATASTEEL'), None)
    if not tata_trade:
        print("WARNING: TATASTEEL not found in open trades! Simulation might not work as expected.")
    else:
        print(f"Found TATASTEEL in open trades. Qty: {tata_trade.qty}")
    
    kite = KiteClient(api_key="dummy")
    
    print("Processing trades...")
    operations = kite.process_trades(orders_df, db_open_trades=open_trades, db_constituents=constituents)
    
    print(f"Generated {len(operations)} operations:")
    for op in operations:
        print(f" - {op['action']}: {op.get('symbol') or op.get('id')}")
        if op['action'] == 'ADD_CLOSED_TRADE':
            print(f"   -> Qty: {op['data']['qty']}, Type: {op['data']['closure_type']}")
        
    if operations:
        print("Applying operations to DB...")
        count = repo.apply_trade_operations(operations)
        print(f"Successfully applied {count} operations")
        repo.save_orders(orders_df)
        print("Done.")
    else:
        print("No operations to apply.")

if __name__ == "__main__":
    simulate_close()
