from app.core.database import SessionLocal
from app.repositories.trade_repository import TradeRepository
import traceback

def debug_aggregation():
    db = SessionLocal()
    repo = TradeRepository(db)
    try:
        print("Starting aggregation...")
        result = repo.aggregate_account_values()
        print("Aggregation result:", result)
    except Exception:
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_aggregation()
