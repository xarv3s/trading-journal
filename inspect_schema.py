import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect

load_dotenv("credentials.env")
DATABASE_URL = os.getenv("SUPABASE_URL")

def inspect_db():
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    # Define the list of tables to inspect
    tables = ['open_trades', 'closed_trades', 'daily_equity']

    # Loop through each table and print its columns
    for table_name in tables:
        print(f"\n--- Table: {table_name} ---")
        columns = inspector.get_columns(table_name)
        for col in columns:
            print(f"{col['name']} ({col['type']})")

if __name__ == "__main__":
    inspect_db()
