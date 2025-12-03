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

def simulate_orders():
    print("Starting order simulation...")
    
    # 1. Setup DB
    db = next(get_db())
    repo = TradeRepository(db)
    
    # 2. Create Simulated Orders
    # Scenario:
    # 1. Buy 10 TATASTEEL @ 100 (New Position)
    # 2. Buy 20 INFY @ 1500 (New Position)
    # 3. Sell 5 TATASTEEL @ 110 (Partial Exit)
    
    now = datetime.now()
    
    orders_data = [
        {
            "order_id": str(uuid.uuid4()),
            "status": "COMPLETE",
            "order_timestamp": now,
            "tradingsymbol": "TATASTEEL",
            "transaction_type": "BUY",
            "quantity": 10,
            "average_price": 100.0,
            "exchange": "NSE",
            "product": "CNC",
            "instrument_token": 123456,
            "filled_quantity": 10,
            "pending_quantity": 0,
            "cancelled_quantity": 0
        },
        {
            "order_id": str(uuid.uuid4()),
            "status": "COMPLETE",
            "order_timestamp": now,
            "tradingsymbol": "INFY",
            "transaction_type": "BUY",
            "quantity": 20,
            "average_price": 1500.0,
            "exchange": "NSE",
            "product": "CNC",
            "instrument_token": 789012,
            "filled_quantity": 20,
            "pending_quantity": 0,
            "cancelled_quantity": 0
        },
        {
            "order_id": str(uuid.uuid4()),
            "status": "COMPLETE",
            "order_timestamp": now,
            "tradingsymbol": "TATASTEEL",
            "transaction_type": "SELL",
            "quantity": 5,
            "average_price": 110.0,
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
    
    # 3. Fetch existing state
    open_trades = repo.get_all_open_trades()
    constituents = repo.get_basket_constituents()
    print(f"Fetched {len(open_trades)} open trades and {len(constituents)} basket constituents")
    
    # 4. Process Trades
    # We can instantiate KiteClient with dummy credentials as we only use process_trades
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
    simulate_orders()
