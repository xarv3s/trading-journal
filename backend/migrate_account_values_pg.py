from sqlalchemy import text
from app.core.database import engine

def migrate_data():
    print("Connecting to database...")
    with engine.connect() as conn:
        try:
            # Check if source table exists
            result = conn.execute(text("SELECT to_regclass('public.account_value_candles')"))
            if not result.scalar():
                print("Source table 'account_value_candles' does not exist. Nothing to migrate.")
                return

            # Check if destination table exists
            result = conn.execute(text("SELECT to_regclass('public.account_values')"))
            if not result.scalar():
                print("Destination table 'account_values' does not exist. Please ensure the app has created it.")
                # We could create it here if needed, but usually the app startup handles it via Base.metadata.create_all(bind=engine)
                # Let's assume the app is running and has created it.
                return

            print("Migrating data from 'account_value_candles' to 'account_values'...")
            
            # Copy data
            # Postgres supports INSERT INTO ... SELECT ...
            # We use ON CONFLICT DO NOTHING to avoid duplicates if run multiple times
            query = text("""
                INSERT INTO account_values (timestamp, open, high, low, close)
                SELECT timestamp, open, high, low, close FROM account_value_candles
                ON CONFLICT (timestamp) DO NOTHING
            """)
            
            result = conn.execute(query)
            print(f"Migrated rows. (Row count might not be available for INSERT ... SELECT in some drivers)")
            
            conn.commit()
            print("Migration successful.")

        except Exception as e:
            print(f"An error occurred: {e}")
            conn.rollback()

if __name__ == "__main__":
    migrate_data()
