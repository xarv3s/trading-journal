import sys
import os
from sqlalchemy import text

# Add the current directory to sys.path to allow imports from app
sys.path.append(os.getcwd())

from app.core.database import SessionLocal

def migrate_stop_loss():
    print("Starting migration: Adding stop_loss column to open_trades table...")
    
    db = SessionLocal()
    try:
        # Check if column exists using PostgreSQL compatible query
        result = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='open_trades' AND column_name='stop_loss'"))
        exists = result.fetchone()
        
        if not exists:
            print("Adding stop_loss column...")
            db.execute(text("ALTER TABLE open_trades ADD COLUMN stop_loss FLOAT"))
            db.commit()
            print("Column added successfully.")
        else:
            print("Column stop_loss already exists.")
            
    except Exception as e:
        print(f"Error during migration: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_stop_loss()
