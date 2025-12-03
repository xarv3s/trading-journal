import sys
import os
sys.path.append(os.getcwd())

from app.core.database import SessionLocal, engine
from app.models.all_models import (
    OpenTrade, ClosedTrade, TradeConstituent, DailyCost, 
    DailyEquity, Journal, Transaction, Orderbook, Base
)

def reset_database():
    print("WARNING: This will delete ALL data from the database.")
    confirm = input("Are you sure? (type 'yes' to confirm): ")
    if confirm != 'yes':
        print("Aborted.")
        return

    db = SessionLocal()
    try:
        print("Deleting data from all tables...")
        
        # Delete in order of dependencies (if any, though cascade might handle it)
        # Constituents depend on Open/Closed trades
        db.query(TradeConstituent).delete()
        db.query(OpenTrade).delete()
        db.query(ClosedTrade).delete()
        
        db.query(DailyCost).delete()
        db.query(DailyEquity).delete()
        db.query(Journal).delete()
        db.query(Transaction).delete()
        db.query(Orderbook).delete()
        
        db.commit()
        print("All data deleted successfully.")
        
    except Exception as e:
        print(f"Error resetting database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Bypass input for automation if argument provided
    if len(sys.argv) > 1 and sys.argv[1] == '--force':
        class MockInput:
            def __eq__(self, other): return True
        
        # Re-implement logic to skip input
        db = SessionLocal()
        try:
            print("Force deleting data from all tables...")
            db.query(TradeConstituent).delete()
            db.query(OpenTrade).delete()
            db.query(ClosedTrade).delete()
            db.query(DailyCost).delete()
            db.query(DailyEquity).delete()
            db.query(Journal).delete()
            db.query(Transaction).delete()
            db.query(Orderbook).delete()
            db.commit()
            print("All data deleted successfully.")
        except Exception as e:
            print(f"Error: {e}")
            db.rollback()
        finally:
            db.close()
    else:
        reset_database()
