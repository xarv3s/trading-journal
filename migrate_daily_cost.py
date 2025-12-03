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
        print("Starting Daily Cost migration...")
        
        # Create daily_costs table
        print("Creating 'daily_costs' table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS daily_costs (
                date DATE PRIMARY KEY,
                brokerage FLOAT DEFAULT 0.0,
                taxes FLOAT DEFAULT 0.0,
                mtf_interest FLOAT DEFAULT 0.0,
                total FLOAT DEFAULT 0.0
            );
        """))
        
        print("Migration completed successfully.")
        conn.commit()

if __name__ == "__main__":
    run_migration()
