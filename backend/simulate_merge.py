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
from app.models.all_models import OpenTrade, ClosedTrade

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def simulate_merge():
    print("Starting merge simulation...")
    
    db = next(get_db())
    repo = TradeRepository(db)
    
    # Clean up first
    db.query(OpenTrade).filter(OpenTrade.symbol == 'TESTMERGE').delete()
    db.query(ClosedTrade).filter(ClosedTrade.symbol == 'TESTMERGE').delete()
    db.commit()
    
    # Step 1: Buy 10 @ 100
    now = datetime.now()
    order1 = {
        "order_id": str(uuid.uuid4()), "status": "COMPLETE", "order_timestamp": now,
        "tradingsymbol": "TESTMERGE", "transaction_type": "BUY", "quantity": 10, "average_price": 100.0,
        "exchange": "NSE", "product": "CNC", "instrument_token": 111
    }
    
    kite = KiteClient(api_key="dummy")
    
    print("Step 1: Buy 10")
    ops1 = kite.process_trades(pd.DataFrame([order1]), db_open_trades=repo.get_all_open_trades())
    repo.apply_trade_operations(ops1)
    
    # Step 2: Sell 5 @ 110 (Partial)
    print("Step 2: Sell 5 (Partial)")
    order2 = {
        "order_id": str(uuid.uuid4()), "status": "COMPLETE", "order_timestamp": now,
        "tradingsymbol": "TESTMERGE", "transaction_type": "SELL", "quantity": 5, "average_price": 110.0,
        "exchange": "NSE", "product": "CNC", "instrument_token": 111
    }
    ops2 = kite.process_trades(pd.DataFrame([order2]), db_open_trades=repo.get_all_open_trades(), db_closed_trades=repo.get_partial_closed_trades())
    repo.apply_trade_operations(ops2)
    
    # Verify Partial
    closed = db.query(ClosedTrade).filter(ClosedTrade.symbol == 'TESTMERGE').all()
    print(f"Closed Trades after Step 2: {len(closed)}")
    if len(closed) == 1 and closed[0].closure_type == 'PARTIAL':
        print(" - Correct: 1 Partial Trade")
    else:
        print(f" - ERROR: Expected 1 Partial, got {len(closed)}")
        
    # Step 3: Sell 5 @ 120 (Full) -> Should Merge
    print("Step 3: Sell 5 (Full - Should Merge)")
    order3 = {
        "order_id": str(uuid.uuid4()), "status": "COMPLETE", "order_timestamp": now,
        "tradingsymbol": "TESTMERGE", "transaction_type": "SELL", "quantity": 5, "average_price": 120.0,
        "exchange": "NSE", "product": "CNC", "instrument_token": 111
    }
    ops3 = kite.process_trades(pd.DataFrame([order3]), db_open_trades=repo.get_all_open_trades(), db_closed_trades=repo.get_partial_closed_trades())
    
    print("Operations generated:")
    for op in ops3:
        print(f" - {op['action']}")
        
    repo.apply_trade_operations(ops3)
    
    # Verify Final
    closed_final = db.query(ClosedTrade).filter(ClosedTrade.symbol == 'TESTMERGE').all()
    print(f"Closed Trades after Step 3: {len(closed_final)}")
    
    if len(closed_final) == 1:
        t = closed_final[0]
        print(f" - ID: {t.id}")
        print(f" - Qty: {t.qty} (Expected 10)")
        print(f" - Type: {t.closure_type} (Expected FULL)")
        print(f" - Exit Price: {t.exit_price} (Expected 115.0)")
        
        if t.qty == 10 and t.closure_type == 'FULL' and t.exit_price == 115.0:
            print("TEST PASSED: Merged successfully")
        else:
            print("TEST FAILED: Data mismatch")
    else:
        print(f"TEST FAILED: Expected 1 trade, got {len(closed_final)}")

if __name__ == "__main__":
    simulate_merge()
