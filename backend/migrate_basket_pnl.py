from sqlalchemy import create_engine, text
from app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.SUPABASE_URL)

def migrate():
    with engine.connect() as conn:
        print("Migrating database...")
        
        # Add realized_pnl to open_trades
        try:
            conn.execute(text("ALTER TABLE open_trades ADD COLUMN realized_pnl FLOAT DEFAULT 0.0"))
            print("Added realized_pnl to open_trades")
        except Exception as e:
            print(f"Skipping open_trades update: {e}")

        # Add basket_id to closed_trades
        try:
            conn.execute(text("ALTER TABLE closed_trades ADD COLUMN basket_id INTEGER DEFAULT NULL"))
            print("Added basket_id to closed_trades")
        except Exception as e:
            print(f"Skipping closed_trades update: {e}")
            
        conn.commit()
        print("Migration complete.")

if __name__ == "__main__":
    migrate()
