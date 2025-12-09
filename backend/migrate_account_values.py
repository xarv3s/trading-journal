import sqlite3
import os

# Database path
DB_PATH = "trading_journal.db"

def migrate_data():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if source table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='account_value_candles'")
        if not cursor.fetchone():
            print("Source table 'account_value_candles' does not exist. Nothing to migrate.")
            return

        # Check if destination table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='account_values'")
        if not cursor.fetchone():
            print("Destination table 'account_values' does not exist. Please run the app once to create it.")
            return

        print("Migrating data from 'account_value_candles' to 'account_values'...")
        
        # Copy data
        cursor.execute("""
            INSERT OR IGNORE INTO account_values (timestamp, open, high, low, close)
            SELECT timestamp, open, high, low, close FROM account_value_candles
        """)
        
        rows_affected = cursor.rowcount
        print(f"Migrated {rows_affected} rows.")
        
        conn.commit()
        print("Migration successful.")

    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_data()
