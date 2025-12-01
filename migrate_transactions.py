import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv("credentials.env")
DATABASE_URL = os.getenv("SUPABASE_URL")

def run_migration():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Starting migration for transactions table...")
        
        # Create transactions table
        print("Creating 'transactions' table...")
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    date DATE,
                    amount DOUBLE PRECISION,
                    type TEXT,
                    notes TEXT
                )
            """))
            # Add index on date
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_transactions_date ON transactions (date)"))
            
            conn.commit()
            print("Transactions table created successfully.")
        except Exception as e:
            print(f"Error creating transactions table: {e}")

if __name__ == "__main__":
    run_migration()
