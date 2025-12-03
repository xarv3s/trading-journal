import sys
import os
import pandas as pd
from datetime import datetime, timedelta
import uuid
import random

# Add the current directory to sys.path
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

def simulate_complex():
    print("Starting complex simulation...")
    db = next(get_db())
    repo = TradeRepository(db)
    kite = KiteClient(api_key="dummy")
    
    # Base time
    base_time = datetime.now() - timedelta(days=1)
    
    orders = []
    
    def add_order(symbol, txn_type, qty, price, minutes_offset):
        orders.append({
            "order_id": str(uuid.uuid4()),
            "status": "COMPLETE",
            "order_timestamp": base_time + timedelta(minutes=minutes_offset),
            "tradingsymbol": symbol,
            "transaction_type": txn_type,
            "quantity": qty,
            "average_price": float(price),
            "exchange": "NSE",
            "product": "CNC",
            "instrument_token": random.randint(1000, 9999)
        })

    # 1. RELIANCE (Winning, Partial -> Full)
    # Buy 100 @ 2500 -> Sell 50 @ 2550 -> Sell 50 @ 2600
    add_order("RELIANCE", "BUY", 100, 2500, 0)
    add_order("RELIANCE", "SELL", 50, 2550, 60)
    add_order("RELIANCE", "SELL", 50, 2600, 120)

    # 2. TCS (Losing, Direct Full)
    # Buy 50 @ 3500 -> Sell 50 @ 3400
    add_order("TCS", "BUY", 50, 3500, 10)
    add_order("TCS", "SELL", 50, 3400, 130)

    # 3. INFY (Winning, Partial -> Partial -> Full)
    # Buy 100 @ 1500 -> Sell 30 @ 1520 -> Sell 30 @ 1540 -> Sell 40 @ 1550
    add_order("INFY", "BUY", 100, 1500, 20)
    add_order("INFY", "SELL", 30, 1520, 70)
    add_order("INFY", "SELL", 30, 1540, 100)
    add_order("INFY", "SELL", 40, 1550, 140)

    # 4. HDFCBANK (Losing, Partial -> Full)
    # Buy 100 @ 1600 -> Sell 50 @ 1580 -> Sell 50 @ 1550
    add_order("HDFCBANK", "BUY", 100, 1600, 30)
    add_order("HDFCBANK", "SELL", 50, 1580, 80)
    add_order("HDFCBANK", "SELL", 50, 1550, 150)

    # 5. TATAMOTORS (Winning, Direct Full)
    # Buy 200 @ 500 -> Sell 200 @ 550
    add_order("TATAMOTORS", "BUY", 200, 500, 40)
    add_order("TATAMOTORS", "SELL", 200, 550, 160)
    
    # 6. SBIN (Winning, Direct Full)
    add_order("SBIN", "BUY", 100, 600, 45)
    add_order("SBIN", "SELL", 100, 610, 165)

    # 7. WIPRO (Losing, Direct Full)
    add_order("WIPRO", "BUY", 100, 400, 50)
    add_order("WIPRO", "SELL", 100, 390, 170)

    # 8. ICICIBANK (Winning, Partial -> Full)
    add_order("ICICIBANK", "BUY", 100, 900, 55)
    add_order("ICICIBANK", "SELL", 50, 920, 110)
    add_order("ICICIBANK", "SELL", 50, 940, 180)

    # Sort orders by timestamp to simulate real-time flow
    orders.sort(key=lambda x: x['order_timestamp'])
    
    print(f"Generated {len(orders)} orders.")
    
    # Process orders one by one to simulate real-time ingestion
    # In reality, we might process batches, but one-by-one ensures strict sequencing for this test
    for i, order in enumerate(orders):
        print(f"Processing Order {i+1}/{len(orders)}: {order['transaction_type']} {order['tradingsymbol']} Qty: {order['quantity']} @ {order['average_price']}")
        
        # Fetch current state
        open_trades = repo.get_all_open_trades()
        constituents = repo.get_basket_constituents()
        partial_closed = repo.get_partial_closed_trades()
        
        # Process
        df = pd.DataFrame([order])
        ops = kite.process_trades(df, db_open_trades=open_trades, db_constituents=constituents, db_closed_trades=partial_closed)
        
        # Apply
        repo.apply_trade_operations(ops)
        
    print("\nSimulation Complete.")
    
    # Verify
    print("\n--- Final State ---")
    closed_trades = db.query(ClosedTrade).all()
    print(f"Total Closed Trades: {len(closed_trades)}")
    for t in closed_trades:
        print(f"Symbol: {t.symbol}, Status: {t.closure_type}, Qty: {t.qty}, PnL: {t.pnl}, Exit Price: {t.exit_price:.2f}")

if __name__ == "__main__":
    simulate_complex()
