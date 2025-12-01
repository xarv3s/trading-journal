import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv("credentials.env")
DATABASE_URL = os.getenv("SUPABASE_URL")

def run_migration():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Starting migration for strategy_type...")
        
        # Rename market_type column to strategy_type
        print("Renaming 'market_type' to 'strategy_type'...")
        tables = ['open_trades', 'closed_trades']
        
        for table in tables:
            try:
                conn.execute(text(f"ALTER TABLE {table} RENAME COLUMN market_type TO strategy_type"))
                print(f"Renamed market_type to strategy_type in {table}")
            except Exception as e:
                print(f"Error renaming column in {table}: {e}")
            
        conn.commit()
        print("Migration completed successfully.")

if __name__ == "__main__":
    run_migration()
