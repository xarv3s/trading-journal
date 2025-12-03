from app.core.database import SessionLocal, engine
from sqlalchemy import text

def migrate():
    db = SessionLocal()
    try:
        print("Adding 'type' column to trade_constituents table...")
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE trade_constituents ADD COLUMN type VARCHAR"))
            conn.commit()
        print("Migration successful.")
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
