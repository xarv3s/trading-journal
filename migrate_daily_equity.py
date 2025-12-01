import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv("credentials.env")
DATABASE_URL = os.getenv("SUPABASE_URL")

def run_migration():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Starting migration for daily_equity...")
        
        # Create daily_equity table
        print("Creating 'daily_equity' table...")
        
        sql = """
        CREATE TABLE IF NOT EXISTS daily_equity (
            date DATE PRIMARY KEY,
            account_value DOUBLE PRECISION,
            realized_pnl DOUBLE PRECISION,
            unrealized_pnl DOUBLE PRECISION,
            total_capital DOUBLE PRECISION
        );
        """
        
        try:
            conn.execute(text(sql))
            conn.commit()
            print("Table 'daily_equity' created successfully.")
        except Exception as e:
            print(f"Error creating table: {e}")

if __name__ == "__main__":
    run_migration()
