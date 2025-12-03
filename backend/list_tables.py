import sys
import os
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from sqlalchemy import inspect, text

def list_tables():
    db = SessionLocal()
    try:
        inspector = inspect(db.get_bind())
        tables = inspector.get_table_names()
        print("Tables in database:")
        for table in tables:
            # Count rows
            try:
                count = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                print(f" - {table}: {count} rows")
            except Exception as e:
                print(f" - {table}: Error counting rows ({e})")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    list_tables()
