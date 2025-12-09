import sys
import os
from sqlalchemy.orm import Session

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.repositories.trade_repository import TradeRepository

def run_aggregation():
    db = SessionLocal()
    try:
        repo = TradeRepository(db)
        print("Starting aggregation...")
        stats = repo.aggregate_account_values()
        print(f"Aggregation complete. Stats: {stats}")
    except Exception as e:
        print(f"Error during aggregation: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_aggregation()
