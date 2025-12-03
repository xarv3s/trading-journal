import sys
import os
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.all_models import OpenTrade, ClosedTrade, Orderbook

def verify():
    db = SessionLocal()
    try:
        print("--- Open Trades ---")
        open_trades = db.query(OpenTrade).all()
        for t in open_trades:
            print(f"Symbol: {t.symbol}, Qty: {t.qty}, Avg Price: {t.avg_price}")
            
        print("\n--- Closed Trades ---")
        closed_trades = db.query(ClosedTrade).all()
        for t in closed_trades:
            print(f"Symbol: {t.symbol}, Qty: {t.qty}, Entry: {t.entry_price}, Exit: {t.exit_price}, PnL: {t.pnl}")
            
        print("\n--- Orderbook (Last 5) ---")
        orders = db.query(Orderbook).order_by(Orderbook.order_timestamp.desc()).limit(5).all()
        for o in orders:
            print(f"Symbol: {o.tradingsymbol}, Type: {o.transaction_type}, Qty: {o.quantity}, Status: {o.status}")
            
    finally:
        db.close()

if __name__ == "__main__":
    verify()
