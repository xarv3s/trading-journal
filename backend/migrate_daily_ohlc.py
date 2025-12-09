import sqlite3

def migrate():
    conn = sqlite3.connect('trading_journal.db')
    cursor = conn.cursor()
    
    try:
        # Add columns if they don't exist
        columns = ['open', 'high', 'low']
        for col in columns:
            try:
                cursor.execute(f"ALTER TABLE daily_equity ADD COLUMN {col} FLOAT")
                print(f"Added column {col}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"Column {col} already exists")
                else:
                    raise e
                    
        # Backfill
        cursor.execute("UPDATE daily_equity SET open = account_value WHERE open IS NULL")
        cursor.execute("UPDATE daily_equity SET high = account_value WHERE high IS NULL")
        cursor.execute("UPDATE daily_equity SET low = account_value WHERE low IS NULL")
        print("Backfilled OHLC data")
        
        conn.commit()
        print("Migration successful")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
