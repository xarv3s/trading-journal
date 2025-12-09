import sys
import os
from sqlalchemy import text

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine

def migrate():
    print("Checking for open_trade_id column in closed_trades...")
    with engine.connect() as conn:
        # Check if column exists
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='closed_trades' AND column_name='open_trade_id'"))
        if result.fetchone():
            print("Column open_trade_id already exists.")
            return

        print("Adding open_trade_id column...")
        try:
            conn.execute(text("ALTER TABLE closed_trades ADD COLUMN open_trade_id INTEGER"))
            conn.commit()
            print("Column added successfully.")
        except Exception as e:
            print(f"Error adding column: {e}")

if __name__ == "__main__":
    migrate()
