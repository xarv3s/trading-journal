import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv("credentials.env")
DATABASE_URL = os.getenv("SUPABASE_URL")

def run_migration():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Starting migration for market_type...")
        
        # Add market_type column
        print("Adding 'market_type' column...")
        tables = ['open_trades', 'closed_trades']
        
        for table in tables:
            try:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS market_type TEXT DEFAULT 'TRENDING'"))
                print(f"Added market_type to {table}")
            except Exception as e:
                print(f"Error adding market_type to {table}: {e}")
            
        conn.commit()
        print("Migration completed successfully.")

if __name__ == "__main__":
    run_migration()
