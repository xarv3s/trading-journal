import sys
import os
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.all_models import OpenTrade, TradeConstituent

def remove_duplicate_basket(basket_id):
    db = SessionLocal()
    try:
        print(f"Removing basket {basket_id} and its constituents...")
        
        # Delete constituents first
        deleted_constituents = db.query(TradeConstituent).filter(TradeConstituent.open_trade_id == basket_id).delete()
        print(f"Deleted {deleted_constituents} constituents.")
        
        # Delete basket
        deleted_basket = db.query(OpenTrade).filter(OpenTrade.id == basket_id).delete()
        print(f"Deleted {deleted_basket} basket.")
        
        db.commit()
        print("Successfully removed duplicate basket.")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Hardcoded ID 54 based on inspection
    remove_duplicate_basket(54)
