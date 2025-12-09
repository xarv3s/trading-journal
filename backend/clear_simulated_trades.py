import sys
import os
sys.path.append(os.getcwd())

from app.core.database import engine
from sqlalchemy import text

def clear_simulated_trades():
    print("Clearing all simulated trades and related data...")
    print("Preserving 'transactions' table.")

    with engine.connect() as conn:
        try:
            # Truncate tables that contain trade data and derived data
            # We use CASCADE to handle foreign key constraints
            tables_to_clear = [
                "trade_constituents",
                "open_trades",
                "closed_trades",
                "orderbook",
                "daily_costs",
                "daily_equity",
                "journal"
            ]
            
            print(f"Truncating tables: {', '.join(tables_to_clear)}")
            
            # Construct the TRUNCATE command
            # PostgreSQL supports truncating multiple tables in one command
            tables_str = ", ".join(tables_to_clear)
            conn.execute(text(f"TRUNCATE TABLE {tables_str} CASCADE"))
            
            conn.commit()
            print("Successfully cleared simulated trades.")
            
        except Exception as e:
            print(f"Error clearing trades: {e}")
            conn.rollback()

if __name__ == "__main__":
    clear_simulated_trades()
