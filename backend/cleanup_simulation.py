import sys
import os
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.all_models import OpenTrade, ClosedTrade, Orderbook

def cleanup():
    db = SessionLocal()
    try:
        print("Cleaning up simulated trades...")
        
        # Delete Open Trades
        db.query(OpenTrade).filter(OpenTrade.symbol.in_(['TATASTEEL', 'INFY'])).delete(synchronize_session=False)
        
        # Delete Closed Trades
        db.query(ClosedTrade).filter(ClosedTrade.symbol.in_(['TATASTEEL', 'INFY'])).delete(synchronize_session=False)
        
        # Delete Orders (This is a bit riskier if we don't track IDs, but for this session it's fine)
        # Better to not delete orders blindly if we are not sure. 
        # But since I know I just added them...
        # I'll skip deleting orders to be safe, or delete by symbol + date range?
        # Let's just delete the trades for now.
        
        db.commit()
        print("Cleanup complete (Trades only).")
        
    finally:
        db.close()

if __name__ == "__main__":
    cleanup()
