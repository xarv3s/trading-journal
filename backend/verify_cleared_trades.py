import sys
import os
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.all_models import (
    OpenTrade, ClosedTrade, TradeConstituent, DailyCost, 
    DailyEquity, Journal, Transaction, Orderbook
)

def verify_cleared():
    db = SessionLocal()
    try:
        counts = {
            "open_trades": db.query(OpenTrade).count(),
            "closed_trades": db.query(ClosedTrade).count(),
            "trade_constituents": db.query(TradeConstituent).count(),
            "orderbook": db.query(Orderbook).count(),
            "daily_costs": db.query(DailyCost).count(),
            "daily_equity": db.query(DailyEquity).count(),
            "journal": db.query(Journal).count(),
            "transactions": db.query(Transaction).count()
        }
        
        print("Table Row Counts:")
        for table, count in counts.items():
            print(f"  {table}: {count}")
            
        if counts["transactions"] > 0:
            print("\nSUCCESS: Transactions table has data.")
        else:
            print("\nNOTE: Transactions table is empty (this might be expected if it was already empty).")
            
        trades_cleared = all(counts[t] == 0 for t in counts if t != "transactions")
        if trades_cleared:
            print("SUCCESS: All trade tables are empty.")
        else:
            print("ERROR: Some trade tables are not empty.")
            
    except Exception as e:
        print(f"Error verifying: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_cleared()
