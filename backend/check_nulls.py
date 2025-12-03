from app.core.database import SessionLocal
from app.models.all_models import OpenTrade, ClosedTrade
from sqlalchemy import text

def check_null_types():
    db = SessionLocal()
    try:
        print("Checking OpenTrade...")
        open_nulls = db.query(OpenTrade).filter(OpenTrade.type == None).count()
        print(f"OpenTrade with NULL type: {open_nulls}")
        
        print("Checking ClosedTrade...")
        closed_nulls = db.query(ClosedTrade).filter(ClosedTrade.type == None).count()
        print(f"ClosedTrade with NULL type: {closed_nulls}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_null_types()
