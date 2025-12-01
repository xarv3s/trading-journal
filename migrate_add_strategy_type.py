import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv("credentials.env")
DATABASE_URL = os.getenv("SUPABASE_URL")

def run_migration():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Starting migration for strategy_type...")
        
        # Add strategy_type column directly
        print("Adding 'strategy_type' column...")
        tables = ['open_trades', 'closed_trades']
        
        for table in tables:
            try:
                # Check if column exists first to avoid error
                result = conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}' AND column_name='strategy_type'"))
                if result.rowcount == 0:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN strategy_type TEXT DEFAULT 'TRENDING'"))
                    print(f"Added strategy_type to {table}")
                else:
                    print(f"strategy_type already exists in {table}")
            except Exception as e:
                print(f"Error adding strategy_type to {table}: {e}")
            
        conn.commit()
        print("Migration completed successfully.")

if __name__ == "__main__":
    run_migration()
