import sys
import os
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.all_models import OpenTrade, ClosedTrade

def verify_close():
    db = SessionLocal()
    try:
        print("--- Open Trades ---")
        open_trades = db.query(OpenTrade).filter(OpenTrade.symbol == 'TATASTEEL').all()
        if not open_trades:
            print("TATASTEEL not found in Open Trades (Correct)")
        else:
            print(f"ERROR: TATASTEEL still in Open Trades: {open_trades[0].qty}")
            
        print("\n--- Closed Trades (TATASTEEL) ---")
        closed_trades = db.query(ClosedTrade).filter(ClosedTrade.symbol == 'TATASTEEL').all()
        for t in closed_trades:
            print(f"ID: {t.id}, Qty: {t.qty}, Type: {t.closure_type}, PnL: {t.pnl}")
            
    finally:
        db.close()

if __name__ == "__main__":
    verify_close()
