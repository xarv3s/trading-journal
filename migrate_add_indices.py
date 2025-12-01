import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv("credentials.env")
DATABASE_URL = os.getenv("SUPABASE_URL")

def run_migration():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Starting migration for index columns...")
        
        columns = [
            "nifty50 DOUBLE PRECISION",
            "nifty_midcap150 DOUBLE PRECISION",
            "nifty_smallcap250 DOUBLE PRECISION"
        ]
        
        for col in columns:
            col_name = col.split()[0]
            print(f"Adding column '{col_name}'...")
            try:
                conn.execute(text(f"ALTER TABLE daily_equity ADD COLUMN IF NOT EXISTS {col}"))
                print(f"Added {col_name}")
            except Exception as e:
                print(f"Error adding {col_name}: {e}")
            
        conn.commit()
        print("Migration completed successfully.")

if __name__ == "__main__":
    run_migration()
