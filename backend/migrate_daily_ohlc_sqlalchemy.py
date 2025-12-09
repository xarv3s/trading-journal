from sqlalchemy import text
from app.core.database import engine

def migrate():
    with engine.connect() as conn:
        try:
            # Add columns if they don't exist
            columns = ['open', 'high', 'low']
            for col in columns:
                try:
                    conn.execute(text(f"ALTER TABLE daily_equity ADD COLUMN {col} FLOAT"))
                    print(f"Added column {col}")
                except Exception as e:
                    if "duplicate column" in str(e) or "already exists" in str(e):
                        print(f"Column {col} already exists")
                    else:
                        print(f"Error adding column {col}: {e}")
                        
            # Backfill
            conn.execute(text("UPDATE daily_equity SET open = account_value WHERE open IS NULL"))
            conn.execute(text("UPDATE daily_equity SET high = account_value WHERE high IS NULL"))
            conn.execute(text("UPDATE daily_equity SET low = account_value WHERE low IS NULL"))
            print("Backfilled OHLC data")
            
            conn.commit()
            print("Migration successful")
            
        except Exception as e:
            print(f"Migration failed: {e}")
            conn.rollback()

if __name__ == "__main__":
    migrate()
