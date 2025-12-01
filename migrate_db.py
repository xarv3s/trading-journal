import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv("credentials.env")
DATABASE_URL = os.getenv("SUPABASE_URL")

def run_migration():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Starting migration...")
        
        # 1. Add ID column (Primary Key)
        # For Postgres, we use SERIAL
        print("Adding 'id' column...")
        try:
            conn.execute(text("ALTER TABLE open_trades ADD COLUMN IF NOT EXISTS id SERIAL PRIMARY KEY"))
            conn.execute(text("ALTER TABLE closed_trades ADD COLUMN IF NOT EXISTS id SERIAL PRIMARY KEY"))
        except Exception as e:
            print(f"Error adding id: {e}")
            
        # 2. Add other missing columns to open_trades
        print("Adding columns to open_trades...")
        cols_open = [
            ("instrument_token", "INTEGER"),
            ("product", "TEXT"),
            ("max_exposure", "INTEGER DEFAULT 0"),
            ("setup_used", "TEXT"),
            ("mistakes_made", "TEXT"),
            ("notes", "TEXT"),
            ("screenshot_path", "TEXT"),
            ("is_mtf", "INTEGER DEFAULT 0")
        ]
        for col, dtype in cols_open:
            try:
                conn.execute(text(f"ALTER TABLE open_trades ADD COLUMN IF NOT EXISTS {col} {dtype}"))
            except Exception as e:
                print(f"Error adding {col} to open_trades: {e}")

        # 3. Add other missing columns to closed_trades
        print("Adding columns to closed_trades...")
        cols_closed = [
            ("instrument_token", "INTEGER"),
            ("product", "TEXT"),
            ("setup_used", "TEXT"),
            ("mistakes_made", "TEXT"),
            ("notes", "TEXT"),
            ("screenshot_path", "TEXT"),
            ("is_mtf", "INTEGER DEFAULT 0")
        ]
        for col, dtype in cols_closed:
            try:
                conn.execute(text(f"ALTER TABLE closed_trades ADD COLUMN IF NOT EXISTS {col} {dtype}"))
            except Exception as e:
                print(f"Error adding {col} to closed_trades: {e}")
                
        conn.commit()
        print("Migration completed successfully.")

if __name__ == "__main__":
    run_migration()
