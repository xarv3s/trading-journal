import sys
import os

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.all_models import OpenTrade, TradeConstituent

def inspect_basket():
    db = SessionLocal()
    try:
        # Find the basket
        basket = db.query(OpenTrade).filter(OpenTrade.is_basket == 1).first()
        if not basket:
            print("No basket found.")
            return

        print(f"Basket ID: {basket.id}, Symbol: {basket.symbol}, Qty: {basket.qty}")
        
        constituents = db.query(TradeConstituent).filter(TradeConstituent.open_trade_id == basket.id).all()
        print(f"Found {len(constituents)} constituents:")
        for c in constituents:
            print(f"  - ID: {c.id}, Symbol: {c.symbol}, Type: {c.type}, Qty: {c.qty}, Product: {c.product}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_basket()
