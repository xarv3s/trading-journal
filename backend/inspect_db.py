from app.core.database import SessionLocal
from app.models.all_models import ClosedTrade
from sqlalchemy import inspect

def inspect_db():
    db = SessionLocal()
    try:
        # Check columns in DB for orderbook
        inspector = inspect(db.get_bind())
        columns = [c['name'] for c in inspector.get_columns('orderbook')]
        print(f"Columns in orderbook: {columns}")
        
        if 'order_id' in columns:
            print("order_id column EXISTS in orderbook.")
        else:
            print("order_id column MISSING in orderbook.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_db()
