from sqlalchemy import create_engine, text
from app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.SUPABASE_URL)

def migrate():
    with engine.connect() as conn:
        try:
            # Check if column exists
            result = conn.execute(text("PRAGMA table_info(closed_trades)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'open_trade_id' not in columns:
                print("Adding open_trade_id column to closed_trades...")
                conn.execute(text("ALTER TABLE closed_trades ADD COLUMN open_trade_id INTEGER"))
                print("Column added successfully.")
            else:
                print("Column open_trade_id already exists.")
                
        except Exception as e:
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
