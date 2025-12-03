import sys
import os
import pandas as pd

# Add the current directory to sys.path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.repositories.trade_repository import TradeRepository
from app.services.analytics_service import AnalyticsService

def reproduce_error():
    print("Starting reproduction script...")
    db = SessionLocal()
    try:
        repo = TradeRepository(db)
        # unified_trades = repo.get_unified_trades()
        unified_trades = []
        print(f"Testing with {len(unified_trades)} unified trades (EMPTY).")
        
        analytics = AnalyticsService(unified_trades)
        print("Initialized AnalyticsService.")
        print(f"DataFrame shape: {analytics.df.shape}")
        print(f"Columns: {analytics.df.columns.tolist()}")
        
        # Check for duplicate columns
        if len(analytics.df.columns) != len(set(analytics.df.columns)):
            print("WARNING: Duplicate columns found!")
            import collections
            print([item for item, count in collections.Counter(analytics.df.columns).items() if count > 1])
        else:
            print("No duplicate columns found.")
            
        analytics.enrich_data()
        print("Enriched data.")
        
        dist = analytics.get_pnl_distribution()
        print(f"get_pnl_distribution returned type: {type(dist)}")
        
        if isinstance(dist, list):
            print("Success: Returned list.")
        else:
            print(f"ERROR: Returned {type(dist)} instead of list.")
            
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    reproduce_error()
