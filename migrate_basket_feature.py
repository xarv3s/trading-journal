import os
from sqlalchemy import create_engine, text

# Manually load credentials.env
def load_env_file(filepath):
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key] = value

load_env_file("credentials.env")
DATABASE_URL = os.getenv("SUPABASE_URL")

def run_migration():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Starting Basket Feature migration...")
        
        # 1. Add is_basket column
        print("Adding 'is_basket' column...")
        try:
            conn.execute(text("ALTER TABLE open_trades ADD COLUMN IF NOT EXISTS is_basket INTEGER DEFAULT 0"))
            conn.execute(text("ALTER TABLE closed_trades ADD COLUMN IF NOT EXISTS is_basket INTEGER DEFAULT 0"))
        except Exception as e:
            print(f"Error adding is_basket: {e}")
            
        # 2. Create trade_constituents table
        print("Creating 'trade_constituents' table...")
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS trade_constituents (
                    id SERIAL PRIMARY KEY,
                    open_trade_id INTEGER,
                    closed_trade_id INTEGER,
                    symbol TEXT,
                    instrument_token INTEGER,
                    qty INTEGER,
                    avg_price FLOAT,
                    entry_date TIMESTAMP,
                    exchange TEXT,
                    product TEXT
                )
            """))
            # Add indices
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tc_open_trade_id ON trade_constituents (open_trade_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tc_closed_trade_id ON trade_constituents (closed_trade_id)"))
        except Exception as e:
            print(f"Error creating trade_constituents table: {e}")
                
        conn.commit()
        print("Migration completed successfully.")

if __name__ == "__main__":
    run_migration()
