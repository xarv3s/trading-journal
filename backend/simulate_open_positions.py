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

def simulate_open_positions():
    print("Starting open positions simulation...")
    
    # 1. Setup DB
    db = next(get_db())
    repo = TradeRepository(db)
    
    # 2. Create Simulated Orders
    now = datetime.now()
    
    orders_data = [
        # 1. CNC Trade: RELIANCE
        {
            "order_id": str(uuid.uuid4()),
            "status": "COMPLETE",
            "order_timestamp": now,
            "tradingsymbol": "RELIANCE",
            "transaction_type": "BUY",
            "quantity": 50,
            "average_price": 2500.0,
            "exchange": "NSE",
            "product": "CNC",
            "instrument_token": 738561,
            "filled_quantity": 50,
            "pending_quantity": 0,
            "cancelled_quantity": 0
        },
        # 2. MTF Trade: TATASTEEL
        {
            "order_id": str(uuid.uuid4()),
            "status": "COMPLETE",
            "order_timestamp": now,
            "tradingsymbol": "TATASTEEL",
            "transaction_type": "BUY",
            "quantity": 100,
            "average_price": 120.0,
            "exchange": "NSE",
            "product": "MTF",
            "instrument_token": 895745,
            "filled_quantity": 100,
            "pending_quantity": 0,
            "cancelled_quantity": 0
        },
        # 3. Futures Trade: NIFTY25DECFUT
        {
            "order_id": str(uuid.uuid4()),
            "status": "COMPLETE",
            "order_timestamp": now,
            "tradingsymbol": "NIFTY25DECFUT",
            "transaction_type": "BUY",
            "quantity": 50,
            "average_price": 21000.0,
            "exchange": "NFO",
            "product": "NRML",
            "instrument_token": 12345, # Dummy token
            "filled_quantity": 50,
            "pending_quantity": 0,
            "cancelled_quantity": 0
        },
        # 4. Another CNC Trade: INFY
        {
            "order_id": str(uuid.uuid4()),
            "status": "COMPLETE",
            "order_timestamp": now,
            "tradingsymbol": "INFY",
            "transaction_type": "BUY",
            "quantity": 25,
            "average_price": 1600.0,
            "exchange": "NSE",
            "product": "CNC",
            "instrument_token": 408065,
            "filled_quantity": 25,
            "pending_quantity": 0,
            "cancelled_quantity": 0
        }
    ]
    
    orders_df = pd.DataFrame(orders_data)
    print(f"Created {len(orders_df)} simulated orders")
    
    # 3. Fetch existing state
    open_trades = repo.get_all_open_trades()
    constituents = repo.get_basket_constituents()
    print(f"Fetched {len(open_trades)} open trades")
    
    # 4. Process Trades
    kite = KiteClient(api_key="dummy")
    
    print("Processing trades...")
    operations = kite.process_trades(orders_df, db_open_trades=open_trades, db_constituents=constituents)
    
    print(f"Generated {len(operations)} operations:")
    for op in operations:
        print(f" - {op['action']}: {op.get('symbol') or op.get('id')}")
        
    # 5. Apply Operations
    if operations:
        print("Applying operations to DB...")
        count = repo.apply_trade_operations(operations)
        print(f"Successfully applied {count} operations")
        
        # 6. Save Orders to Orderbook
        print("Saving orders to Orderbook...")
        repo.save_orders(orders_df)
        print("Done.")
    else:
        print("No operations to apply.")

if __name__ == "__main__":
    simulate_open_positions()
