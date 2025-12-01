import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import time

load_dotenv("credentials.env")
DATABASE_URL = os.getenv("SUPABASE_URL")

def diagnose():
    print(f"Connecting to DB...")
    try:
        engine = create_engine(DATABASE_URL, connect_args={'connect_timeout': 10})
        with engine.connect() as conn:
            print("Connected.")
            
            # Check version
            ver = conn.execute(text("SELECT version()")).scalar()
            print(f"DB Version: {ver}")
            
            # Check for locks
            print("Checking for locks...")
            locks = conn.execute(text("SELECT pid, usename, application_name, state, query FROM pg_stat_activity WHERE state != 'idle'")).fetchall()
            for lock in locks:
                print(f"Active Query: {lock}")
                
            # Try to add column
            print("Attempting to add column 'strategy_type' to open_trades...")
            try:
                conn.execute(text("ALTER TABLE open_trades ADD COLUMN IF NOT EXISTS strategy_type TEXT DEFAULT 'TRENDING'"))
                conn.commit()
                print("Column added (or already exists).")
            except Exception as e:
                print(f"Error adding column: {e}")
                
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    diagnose()
